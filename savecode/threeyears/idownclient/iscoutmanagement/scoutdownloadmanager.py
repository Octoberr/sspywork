"""
从数据库中拿任务，然后将任务分配给
plugmanager,再然后plugmanager去寻找响应的插件 去执行
create by swm 2019/07/09
"""

import threading
import time
import traceback
from datetime import datetime
from queue import PriorityQueue

import pytz

from datacontract import ETaskStatus, IdownCmd, IscoutTask, ECommandStatus
from idownclient.config_task import clienttaskconfig
from idownclient.config_spiders import scouterconf
from .scoutmanagebase import ScoutManageBase
from ..clientdbmanager.sqlcondition import ESqlComb, SqlCondition, SqlConditions
from ..scout import ScouterControler


class ScoutDownloadManager(ScoutManageBase):
    def __init__(self):
        ScoutManageBase.__init__(self)
        # 新任务队列
        self._new_scouttask_queue = PriorityQueue()
        # 循环任务队列
        # self._cycle_scouttask_queue = PriorityQueue()
        self.threads_num = scouterconf.get("scouter_threads", 10)
        # 正在处理的任务队列
        self._dealing_queue: dict = {}
        # 正在处理新任务队列,如果有新任务是不会执行循环下载任务的
        self._dealing_queue_locker = threading.RLock()
        # 并发队列任务数
        self._concur_num = clienttaskconfig.concurrent_number
        # 默认配置
        _defaultcmd: str = self._sqlfunc.get_default_iscout_cmd().get("cmd")
        self.d_cmd = IdownCmd(_defaultcmd)

    def on_task_complete(self, task: IscoutTask):
        """Task对象处理完毕的回调"""
        with self._dealing_queue_locker:
            if self._dealing_queue.__contains__(task.batchid):
                self._dealing_queue.pop(task.batchid, None)

    def _construct_task(self, filedata: dict) -> IscoutTask:
        """
        单独构造iscout task的函数，单独使用
        :param filedata:
        :return:
        """
        # 加载设置,包括补齐默认设置,已经证明了这个代码完全没用
        # 不一定，现在先这样用着吧
        # if tsk.cmd_id is None:
        #     tsk.cmd: IdownCmd = self.d_cmd
        # else:
        #     tsk.cmd.fill_defcmd(self.d_cmd)
        tsk: IscoutTask = IscoutTask(filedata)
        tsk.priority = tsk.cmd.stratagy.priority
        tsk.on_complete = self.on_task_complete
        return tsk

    def _process_task_execution_time(self, q_task: dict):
        """
        处理刚从数据库查出数据，检测任务是否在有效期
        和任务是否满足在执行时间段
        :param q_task:
        :return:
        """
        q_cmdid = q_task.get("cmdid")
        # 插个眼后面看用不用判断cmd，by judy 2020/03/26
        is_effective = True
        if q_cmdid is None or q_cmdid == "":
            # 这里的true表示默认的任务时没有任务活性和时间限制的
            # 目前来看是这样，如果使用时出问题再修改吧，judy190603
            return True
        cmd = IdownCmd(q_task.get("cmd"))
        # 因为任务里面保存的设置可能不是完整的，所以需要使用默认设置补齐
        cmd.fill_defcmd(self.d_cmd)

        # iscout task也没有继续下载的功能，所以暂停也是相当于将这个任务结束并且不再下载，这个周期的处理和iscan相似modify by judy 20200722
        if int(cmd.switch_control.download_switch) != 1:
            return False
        if int(cmd.stratagy.circulation_mode) == 2:
            return True

        # 每个任务都去判断一下并发数
        if int(cmd.stratagy.concur_num) != self._concur_num:
            self._concur_num = int(cmd.stratagy.concur_num)
        # 统一使用东8区的时间
        beijing = pytz.timezone("Asia/Shanghai")
        now_datetime = datetime.now(beijing)
        now_time = now_datetime.time()
        try:
            if cmd.stratagy.time_start is not None:
                task_time_start = datetime.strptime(
                    cmd.stratagy.time_start, "%Y-%m-%d %H:%M:%S"
                )
                if now_datetime >= beijing.localize(task_time_start):
                    is_effective = True
                else:
                    return False
            if cmd.stratagy.time_end is not None:
                task_time_end = datetime.strptime(
                    cmd.stratagy.time_end, "%Y-%m-%d %H:%M:%S"
                )
                if now_datetime <= beijing.localize(task_time_end):
                    is_effective = True
                else:
                    return False
            # ----------------------------------------------上面的判断为任务是否在有效时间
            # if len(cmd.stratagy.period) == 0:
            #     return is_effective
            # for t_p in cmd.stratagy.period:
            #     t_p_list = t_p.split("-")
            #     if (
            #         datetime.strptime(t_p_list[0], "%H:%M:%S").time()
            #         <= now_time
            #         <= datetime.strptime(t_p_list[1], "%H:%M:%S").time()
            #     ):
            #         is_effective = True
            #         break
            #     else:
            #         is_effective = False
            # ---------------------------------------------上面为判断任务是否在执行时间内

        except:
            self._logger.error(
                f"Determine the effective and execution time of the task error, err:{traceback.format_exc()}"
            )
        return is_effective

    def _get_new_iscouttask(self):
        """
        目前先不考虑基础设置策略
        主要是stratagyscout带的设置，搜索关键字和其他的一些什么
        :return:
        """
        new_task_list = []
        result_list = []
        try:
            with self._dealing_queue_locker:
                new_task = self._sqlfunc.query_iscout_task(
                    SqlConditions(
                        SqlCondition(
                            colname="taskstatus",
                            val=ETaskStatus.New.value,
                            comb=ESqlComb.Or,
                        ),
                        SqlCondition(
                            colname="taskstatus",
                            val=ETaskStatus.WaitForDeal.value,
                            comb=ESqlComb.Or,
                        ),
                        # SqlCondition(
                        #     colname='taskstatus',
                        #     val=ETaskStatus.Logining.value,
                        #     comb=ESqlComb.Or),
                        SqlCondition(
                            colname="taskstatus",
                            val=ETaskStatus.Downloading.value,
                            comb=ESqlComb.Or,
                        ),
                    )
                )
                for t_a in new_task:
                    # 这里是判断是否满足cmd设置的执行时间
                    try:
                        if self._process_task_execution_time(t_a):
                            new_task_list.append(t_a)
                    except:
                        self._logger.error(
                            f"Error task\ntaskid:{t_a.get('taskid')}\nerror:{traceback.format_exc()}"
                        )
                        # 修改数据库中的任务状态, 这样日志就不会一直报错
                        self._sqlfunc.update_iscout_status(
                            "taskstatus",
                            ETaskStatus.DownloadFailed.value,
                            t_a.get("batchid"),
                            t_a.get("taskid"),
                        )
                        # 但是还需要写回馈告诉前端任务执行失败了
                        self.write_iscoutback_dict(
                            t_a, ECommandStatus.Failed, "任务文件出错，任务文件体不完整，请检查后重试"
                        )
                        continue

                for dic in new_task_list:
                    if not isinstance(dic, dict):
                        continue
                    # 构造task
                    task: IscoutTask = None
                    try:
                        task = self._construct_task(dic)
                    except Exception:
                        self._logger.error(
                            "Construct iscouttask from dict error: {}".format(
                                traceback.format_exc()
                            )
                        )
                    if not isinstance(task, IscoutTask):
                        continue

                    # 校验Task
                    if (
                        not isinstance(task.taskid, str)
                        or task.taskid == ""
                        or not isinstance(task.batchid, str)
                        or task.batchid == ""
                    ):
                        continue

                    if self._dealing_queue.__contains__(task.batchid):
                        continue
                    # 修改任务状态为正在处理到对列
                    task.taskstatus = ETaskStatus.WaitForDeal
                    # 修改数据库中的任务状态
                    self._sqlfunc.update_iscout_status(
                        "taskstatus", task.taskstatus.value, task.batchid, task.taskid
                    )
                    self._dealing_queue[task.batchid] = task
                    result_list.append(task)
        except:
            self._logger.error(
                "Select executable iscout tasks error: {}".format(
                    traceback.format_exc()
                )
            )
        return result_list

    def _put_task_to_queue(self, tsk: IscoutTask, queue: PriorityQueue):
        """
        将任务放进队列的通用方法
        :param filedata:
        :param queue:
        :return:
        """
        if not isinstance(tsk, IscoutTask):
            raise Exception("Invalid Iscout Task")

        # 同时进行的最大的下载任务数,优先级高的任务直接处理
        # 正在下载的任务可能需要很久，所以每次sleep5秒即可
        queue.put(tsk)
        self._logger.info(
            f"Put an iscout task to queue\ntaskid:{tsk.taskid}\nbatchid:{tsk.batchid}"
        )
        self.write_iscoutback(tsk, ECommandStatus.Dealing, "任务加入下载队列成功，等待执行")
        return

    def put_new_iscouttask(self):
        """
        将新的iscouttask放入队列
        :return:
        """
        while True:
            new_tasks = self._get_new_iscouttask()
            if len(new_tasks) == 0:
                # 3秒钟扫描一次数据库
                time.sleep(1)
                continue
            try:
                for filedata in new_tasks:
                    self._put_task_to_queue(filedata, self._new_scouttask_queue)
            except:
                self._logger.error(
                    f"Make the iscouttask from sqlite wrong, err:{traceback.format_exc()}"
                )
            finally:
                # 5秒扫描一次，因为会扫描出很多重复的任务
                # 毛线...不能去重啊
                time.sleep(0.5)

    def execute_new_iscouttask(self):
        """
        不断的从新任务中取出任务,下载数据
        :return:
        """
        ident = threading.current_thread().ident
        self._logger.trace(f"Start a scouter thread, threading id: {ident}")
        got = False
        while True:
            if self._new_scouttask_queue.empty():
                # self._logger.info(f"There are no tasks in the queue.")
                time.sleep(1)
                continue
            got = False
            tsk: IscoutTask = self._new_scouttask_queue.get()
            got = True
            self._logger.info(
                f"iscouttask start: {tsk.batchid}, objecttype:{tsk._objecttype.value}, object:{tsk._object}"
            )
            try:
                control = ScouterControler(tsk)
                control.start()
                # 最后手动回收下对象，不然等python自动回收会等的有点久
                del control
            except:
                self._logger.error(
                    f"Execute iscouttask error, err:{traceback.format_exc()}"
                )
            finally:
                if got:
                    self._new_scouttask_queue.task_done()

    # -------------------------------------------------------------------循环下载
    # def _scouttask_usercfg_filter(self, l_e_time: int, cmdstr: str):
    #     """
    #     根据用户的设置来判断这个任务是否满足循环下载的条件
    #     :param l_e_time:
    #     :param cmdstr:
    #     :return:
    #     """
    #     res = False
    #     date_unix = int(time.time())
    #     if cmdstr is None or cmdstr == '':
    #         # 如果任务没有带有cmd，那么使用默认配置
    #         cmd: IdownCmd = self.d_cmd
    #     else:
    #         # 任务里带有的设置可能不是完整的，需要补齐设置
    #         cmd: IdownCmd = IdownCmd(cmdstr)
    #         cmd.fill_defcmd(self.d_cmd)
    #     # -----------新增判断任务模式,如果不是循环任务那么就不进行循环下载
    #     if int(cmd.stratagy.circulation_mode) != 2:
    #         return res
    #
    #     # 2、下载开着，3、监控开着
    #     if int(cmd.switch_control.download_switch) != 1:
    #         return res
    #     if int(cmd.switch_control.monitor_switch) != 1:
    #         return res
    #     if date_unix - int(l_e_time) >= int(cmd.stratagy.interval):
    #         res = True
    #     return res
    #
    # def _get_cycle_iscouttask(self):
    #     """
    #     获取需要循环下载的任务
    #     :return:
    #     """
    #     cycletask = []
    #     # 1、任务已经下载完成
    #     downloaded_tasks = self._sqlfunc.query_iscout_task(SqlConditions(
    #         SqlCondition(colname='taskstatus', val=ETaskStatus.DownloadSucceed.value), ))
    #     for task in downloaded_tasks:
    #         try:
    #             last_execute_time = task.get('lastexecutetime')
    #             filter_res = self._scouttask_usercfg_filter(last_execute_time, task.get('cmd'))
    #             # 满足了任务的有效时间，并且满足循环任务的条件那么才开始下载
    #             if self._process_task_execution_time(task) and filter_res:
    #                 cycletask.append(task)
    #         except:
    #             self._logger.error(f'Get cycle task error, err:{traceback.format_exc()}')
    #     return cycletask
    #
    # def _put_cycle_iscouttask(self):
    #     """
    #     将需要重复下载的任务假如队列
    #     这里考虑到因为是重复下载，所以不能和新任务抢资源
    #     每次等待的时间会比较长
    #     :return:
    #     """
    #     while True:
    #         with self._dealing_queue_locker:
    #             cycle_tasks = self._get_cycle_iscouttask()
    #             if len(cycle_tasks) == 0:
    #                 # 1分钟扫描一次数据库
    #                 time.sleep(60)
    #                 continue
    #             try:
    #                 for filedata in cycle_tasks:
    #                     # 不占用新任务的资源，当有任务在下载时主动等待，可能下载时间比较长，等待30秒
    #                     while len(self._dealing_queue) > 2:
    #                         time.sleep(30)
    #                     self._put_task_to_queue(filedata, self._cycle_scouttask_queue)
    #             except:
    #                 self._logger.error(f"Make the task from sqlite wrong, err:{traceback.format_exc()}")
    #             finally:
    #                 time.sleep(1)
    #
    # def execute_cycle_iscouttask(self):
    #     """
    #     不断的从循环任务队列中取出任务执行,下载数据
    #     :return:
    #     """
    #     got = False
    #     while True:
    #         if self._cycle_scouttask_queue.empty():
    #             # 这个的等待时间可以长一点
    #             time.sleep(5)
    #             continue
    #         got = False
    #         tsk: IscoutTask = self._cycle_scouttask_queue.get()
    #         got = True
    #         self._logger.info("Cycle task start: {} {} {}".format(tsk.batchid, tsk._objecttype.value, tsk._object))
    #         try:
    #             # 根据cmd中的设置访问网站，爬取不同的数据
    #             if self._scouterclass.__contains__(tsk._objecttype):
    #                 # 这里是找到了scouter,要传task和object
    #                 scouter = self._scouterclass[tsk._objecttype](tsk)
    #                 scouter.scout()
    #             else:
    #                 self._logger.error(f'Can not find scouter type, type:{tsk._objecttype.value}')
    #         except:
    #             self._logger.error(f"Execute iscouttask error, err:{traceback.format_exc()}")
    #         finally:
    #             time.sleep(1)  # 等待线程状态回执
    #             if got:
    #                 self._cycle_scouttask_queue.task_done()

    # --------------------------------------------------------------------------
    def start(self):
        """
        多线程开启任务执行
        :return:
        """
        thread1 = threading.Thread(
            target=self.put_new_iscouttask, name="iscouttaskscan"
        )
        thread1.start()
        for i in range(self.threads_num):
            thread = threading.Thread(
                target=self.execute_new_iscouttask, name=f"iscouttaskexecute_{i}"
            )
            thread.start()
