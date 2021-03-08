"""
scouter的控制器，主要是为了recursion_level=3
这个程序是不能一直运行，等到实例化后是需要被释放的
create by judy 20190719
新增暂停功能 modify by judy 2020/06/03
"""
import datetime
import inspect
import threading
import time
import traceback
from queue import Queue

import pytz
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import (
    ECommandStatus,
    EObjectType,
    ETaskStatus,
    IscoutBtaskBack,
    IscoutTask,
    IdownCmd,
)
from idownclient.config_spiders import scouterconf
from outputmanagement import OutputManagement
from ..clientdatafeedback.scoutdatafeedback import (
    ALL_SCOUT_ROOT_OBJ_TYPES,
    ScoutFeedBackBase,
)
from ..clientdbmanager import DbManager
from ..clientdbmanager.sqlcondition import ESqlComb, SqlCondition, SqlConditions

# 你在这引用ScoutMangeBase没有循环引用错误才是有点nb
# from idownclient.iscoutmanagement.scoutmanagebase import ScoutManageBase
from ..scout import ScouterBase, scouter


class ScouterControler(object):
    def __init__(self, task: IscoutTask):
        self.task: IscoutTask = task
        # 加载scouter
        self._scouterclass: dict = {}
        self._load_scouters()
        self._logger: MsLogger = MsLogManager.get_logger("Scouter control")
        # 这里就是线程的一些处理
        self.__controler_locker = threading.Lock()
        # scouter队列
        self._scouter_queue = Queue()

        self._sqlfunc = DbManager

        # 线程运行状态，运来判断项目是否该结束
        self.__scouter_thread_state = {}

        # 配置开启线程的数量，目前没有执行级数，只需要开启一个线程执行就可以了
        self.thread_num = scouterconf.get("scouter_thread_num", 1)
        # 新增暂停下载功能, 停止标志, 默认不停止, 1表示继续下载不停False, 0表示停止True
        self._stop_sign = False
        # 程序执行中
        self._running = True
        # 输出统计，modify by judy 2020/08/10
        self.output_count = 0

    def _load_scouters(self):
        """
        加载scouters
        :return:
        """
        clsmembers = inspect.getmembers(
            scouter,
            lambda o: inspect.isclass(o)
            and o is not ScouterBase
            and issubclass(o, ScouterBase),
        )
        for name, cls in clsmembers:
            self._scouterclass[cls.TARGET_OBJ_TYPE] = cls
        return

    # def put_task_to_queue(self, task: IscoutTask, objtype: EObjectType,
    #                       objvalue):
    #     """
    #     这个既是对外分配scouter的方法
    #     也是对内分配scouter的方法
    #     :param task:
    #     :return:
    #     """
    #     if self._scouterclass.__contains__(objtype):
    #         self._scouter_queue.put((task, objtype, objvalue))

    def put_task_to_queue(self, obj: ScoutFeedBackBase):
        """
        这个既是对外分配scouter的方法
        也是对内分配scouter的方法
        :param obj:
        :return:
        """
        if self._scouterclass.__contains__(obj._objtype):
            self._scouter_queue.put(obj)

    def make_task_from_backdata(self, res_data: ScoutFeedBackBase):
        """
        这个是不断的从结果队列中拿输出的结果，先输出一份，
        判断一下是否需要更深入的搜索，如果需要的话那么就
        修改object和objectype
        :return:
        """

        # 先判断下现在task的rec_level和设置中的rec_level比较，当task的level大于或者等于reclevel就不再去执行了
        # if task.rec_level >= task.cmd.stratagyscout.recursion_level:
        # 修改，用回馈数据的level判断，by judy 2019/08/22
        # 这里回来的数据都是需要重新下载的，数据里的level是已经下载了的level，所以需要先加一然后再进行判断
        # 所有的判断都在这里进行

        # 是否考虑使用原有的 obj 的 value 创建一个新的对象，传给下一级。
        # 因为并不敢保证把原有的东西的level改了不会出错。。
        # 使用 nextdata ↓
        # nextdata = self._create_obj(self.task, res_data._level + 1,
        #                             res_data.value, res_data._objtype)
        # 没问题，不用怀疑，就用下面那个，by judy 2019/08/27

        res_data._level += 1
        if res_data._level > self.task.cmd.stratagyscout.recursion_level:
            return
        try:
            self.put_task_to_queue(res_data)
            self._logger.debug(
                f"当前回馈数据加入队列，type:{res_data._objtype.name}, value:{res_data._value}, level:{res_data._level}"
            )
        except:
            self._logger.error(
                f"Make task from resdata error, maybe data is not formate,err:{traceback.format_exc()}"
            )

    def _is_complete(self) -> bool:
        """
        这里判断任务是否完成,程序全部执行完成了返回true
        任务没有执行完成返回false
        :return:
        """
        complete = False
        if (
            self._scouter_queue.empty()
            and True not in self.__scouter_thread_state.values()
        ):
            # 队列为空，并且已经没有任务正在执行中了
            complete = True
        return complete

    def execute_scouter(self):
        """
        在队列中拿出task，然后放入scouter执行
        :return:
        """
        # 当前线程的唯一标识
        ident = threading.current_thread().ident
        self._logger.debug(f"当前线程启动， 线程id：{ident}")
        with self.__controler_locker:
            # 执行状态，False表示没有拿到任务，程序没有执行，True表示程序拿到任务正在执行
            cur_state = False
            self.__scouter_thread_state[ident] = cur_state
        while True:
            # 这里表示如果任务执行完成了那么就结束该线程
            if self._is_complete():
                break
            # 如果任务没有执行完成，那么如果队列为空就需要继续等待
            if self._scouter_queue.empty():
                self._logger.trace(f"当前队列已经没有东西，但是其他程序还在运行所以会继续执行")
                time.sleep(1)
                continue

            obj: ScoutFeedBackBase = None
            try:
                # 第一次必定会有一个任务
                with self.__controler_locker:
                    obj = self._scouter_queue.get()
                    self._logger.debug(
                        f"当前线程{ident}拿到一个task, type:{obj._objtype.name}, value:{obj.value}"
                    )
                with self.__controler_locker:
                    # 改变执行状态
                    cur_state = True
                    self.__scouter_thread_state[ident] = cur_state
                # 在实例化之前将任务成功或者失败的统计加进去
                # self.task.success_count = self.success_count
                # self.task.fail_count = self.fail_count
                # 使用scouter class 通过class匹配scouter,这里应该就是传的objectvalue了
                scouter = self._scouterclass[obj._objtype](self.task)
                # for res_data in scouter.scout(task.rec_level, obj):
                for res_data in scouter.scout(obj._level, obj):
                    if self._stop_sign:
                        break
                    # 从数据中制作多级数据，目前不需要
                    self.make_task_from_backdata(res_data)
                    continue
                # 当前scouter执行完成了也释放下对象
                self.output_count += scouter.output_count
                del scouter

            except:
                self._logger.error(
                    f"{obj._objtype.value} {obj.value} execute error: {traceback.format_exc()}"
                )
            finally:
                # 还原状态, 这里表示一个任务执行完成了
                self._scouter_queue.task_done()
                with self.__controler_locker:
                    cur_state = False
                    self.__scouter_thread_state[ident] = cur_state

    def __del__(self):
        """
        释放对象要做的事
        :return:
        """
        # server不知道successed times 和failed times,所以用periodnum
        # 任务结束时间
        if self.output_count > 0:
            msg = "侦查到相关数据"
        else:
            msg = "未侦查到数据"
        taskstoptime = datetime.datetime.now(pytz.timezone("Asia/Shanghai")).timestamp()
        elapsed = taskstoptime - self.task.taskstarttime
        # 最后更新数据库的基本字段用于循环下载
        if self._stop_sign:
            self._update_task_status(ETaskStatus.TemporarilyStop)
            self._write_iscouttaskback(
                self.task,
                ECommandStatus.Cancelled,
                f"任务第{self.task.periodnum}次下载成功,{msg}",
                elapsed=elapsed,
            )
        elif self.task.successtimes > 0:
            # self.task.successtimes += 1
            self._update_task_status(ETaskStatus.DownloadSucceed)
            self._write_iscouttaskback(
                self.task,
                ECommandStatus.Succeed,
                f"任务第{self.task.periodnum}次下载成功, {msg}",
                elapsed=elapsed,
            )
        else:
            # self.task.failtimes += 1
            self._update_task_status(ETaskStatus.DownloadFailed)
            self._write_iscouttaskback(
                self.task,
                ECommandStatus.Failed,
                f"任务第{self.task.periodnum}次下载失败, {msg}",
            )
        # 不用再去修改状态了
        self.task.lastexecutetime = datetime.datetime.now(
            pytz.timezone("Asia/Shanghai")
        ).timestamp()
        self._sqlfunc.update_iscout_info(self.task)
        self._logger.info(
            f"In the end of scouting, success:{self.task.successtimes}, fail:{self.task.failtimes}, {msg}, misson accomplished"
        )
        # 等待线程状态回执,还有就是修改数据库的时候，如果在这之前查出来了数据，但是这时候把正在处理的队列移出去了就会造成刚执行完
        # 然后马上就又加入队列，这里等待1S是等待那边将在修改前的状态全剔除
        time.sleep(1)
        # 释放完成的任务
        if self.task is not None:
            if callable(self.task.on_complete):
                self.task.on_complete(self.task)

    def _update_task_status(self, task_status: ETaskStatus):
        """
        更新任务状态
        :param task_status:
        :return:
        """
        self._sqlfunc.update_iscout_status(
            "taskstatus", task_status.value, self.task.batchid, self.task.taskid
        )
        return

    def _create_obj(
        self, task: IscoutTask, level: int, obj: str, objtype: EObjectType
    ) -> ScoutFeedBackBase:
        """根据 侦察对象 和 侦察对象类型 创建 侦察对象实体"""
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid iscouttask for creating obj")
        if not isinstance(level, int) or level < 0:
            raise Exception("Invalid level for creating obj, level:{}".format(level))
        if not isinstance(obj, str) or obj == "":
            raise Exception(
                "Create ScoutObj failed:\ntaskid:{}\nbatchid:{}\nobj:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj, objtype.name
                )
            )
        if not isinstance(objtype, EObjectType):
            raise Exception(
                "Create ScoutObj failed:\ntaskid:{}\nbatchid:{}\nobj:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj, objtype.name
                )
            )

        res: ScoutFeedBackBase = None
        if not ALL_SCOUT_ROOT_OBJ_TYPES.__contains__(objtype):
            raise Exception(
                "Unknow objecttype:\ntaskid:{}\nbatchid:{}\nobj:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj, objtype.name
                )
            )

        res = ALL_SCOUT_ROOT_OBJ_TYPES[objtype](task, level, obj)
        return res

    def _write_iscouttaskback(
        self,
        iscouttask: IscoutTask,
        cmdstatus: ECommandStatus,
        scoutrecvmsg: str,
        currtime: str = None,
        elapsed: float = None,
    ):
        """
        通用方法编写iscantask的回馈
        :param iscouttask:
        :param cmdstatus:
        :param scanrecvmsg:
        :param currtime:
        :param elapsed:
        :return:
        """
        if iscouttask is None:
            raise Exception("Write iscantaskback iscantask cannot be None")
        scanback = IscoutBtaskBack.create_from_task(
            iscouttask, cmdstatus, scoutrecvmsg, currtime, elapsed
        )
        OutputManagement.output(scanback)
        return

    def _get_stop_sign(self):
        """
        单个线程不断在数据库中查询停止标志
        改变停止的状态
        :return:
        """
        # sql = '''
        # SELECT cmdid, cmd FROM iscantask
        # LEFT OUTER JOIN idowncmd USING (cmdid)
        # WHERE taskid=?
        # '''
        # pars = (self.task.taskid, )
        while self._running:
            try:
                res = self._sqlfunc.query_iscout_task(
                    SqlConditions(
                        SqlCondition(
                            colname="taskid", val=self.task.taskid, comb=ESqlComb.And
                        ),
                        SqlCondition(
                            colname="batchid", val=self.task.batchid, comb=ESqlComb.And
                        ),
                    )
                )
                if len(res) == 0 or res[0].get("cmd") is None:
                    continue
                cmd = IdownCmd(res[0].get("cmd"))

                self._logger.trace(f"Iscan get cmd, cmd:{cmd}")
                if (
                    cmd.switch_control is not None
                    and cmd.switch_control.download_switch is not None
                ):
                    self._stop_sign = int(cmd.switch_control.download_switch) == 0
            except:
                self._logger.error(
                    f"Something wrong when get stopsign,err:{traceback.format_exc()}"
                )
                continue
            finally:
                # 以防万一不要频繁的访问数据库,
                # 这个设置的时间可以等长一点，也许整个任务都不会有停止下载的设置
                time.sleep(1)

    def start(self):
        # 第一次执行会把第一个原始任务放入队列
        obj: ScoutFeedBackBase = self._create_obj(
            self.task, self.task.rec_level, self.task._object, self.task._objecttype
        )
        if not isinstance(obj, ScoutFeedBackBase):
            raise Exception(
                "Create ScoutObj failed:\ntaskid:{}\nbatchid:{}\nobj:{}\nobjtype:{}".format(
                    self.task.taskid,
                    self.task.batchid,
                    self.task._object,
                    self.task._objecttype.name,
                )
            )

        self.put_task_to_queue(obj)
        # self.put_task_to_queue(self.task, self.task._objecttype,
        #                        self.task._object)
        # 更新状态
        self._update_task_status(ETaskStatus.Downloading)
        # 获取任务是否提前终止
        t = threading.Thread(target=self._get_stop_sign, name="stop_singn_scan")
        t.start()

        tlist = [
            threading.Thread(target=self.execute_scouter, name=f"scouter{i + 1}")
            for i in range(self.thread_num)
        ]
        for tl in tlist:
            tl.start()
        for tl in tlist:
            tl.join()
        # 结束后
        self._running = False
