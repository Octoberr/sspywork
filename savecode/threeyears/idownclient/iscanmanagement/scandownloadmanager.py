"""
iscan task的下载分配
"""
import threading
import time
import traceback
from datetime import datetime
from queue import PriorityQueue

import pytz

from datacontract import IdownCmd, ETaskStatus, IscanTask, ECommandStatus
from idownclient.config_task import clienttaskconfig
from .scanmanagebase import ScanManageBase
from .scanplugmanager import ScanPlugManager
from ..clientdbmanager.sqlcondition import ESqlComb, SqlCondition, SqlConditions


class ScanDownloadManager(ScanManageBase):
    def __init__(self):
        ScanManageBase.__init__(self)
        # 新任务队列
        self._new_scantask_queue = PriorityQueue()
        # 正在处理的任务队列
        self._dealing_queue: dict = {}
        # 正在处理新任务队列,如果有新任务是不会执行循环下载任务的
        self._dealing_queue_locker = threading.Lock()
        # 并发队列任务数
        self._concur_num = clienttaskconfig.concurrent_number
        # 默认配置
        _defaultcmd: str = self._sqlfunc.get_default_iscan_cmd().get("cmd")
        self.d_cmd = IdownCmd(_defaultcmd)
        self._scan_plug_manger = ScanPlugManager()

    def on_task_complete(self, task: IscanTask):
        """Task对象处理完毕的回调"""
        with self._dealing_queue_locker:
            if self._dealing_queue.__contains__(task.taskid):
                self._dealing_queue.pop(task.taskid, None)

    def _process_task_execution_time(self, q_task: dict):
        """
        处理刚从数据库查出数据，检测任务是否在有效期
        和任务是否满足在执行时间段
        现在有这么一个问题，任务在server那边是在执行时间段中，但是到了client
        就不再是在执行时间段内，在server那边增加了一个功能就是判断周期任务是否在执行时间段中
        如果不在执行时间段中，那么就不再下发，而client无论如何都把最后一个周期执行完成
        modify by judy 20201126
        :param q_task:
        :return:
        """
        q_cmdid = q_task.get("cmdid")
        is_effective = True
        if q_cmdid is None or q_cmdid == "":
            # 这里的true表示默认的任务时没有任务活性和时间限制的
            # 目前来看是这样，如果使用时出问题再修改吧，judy190603
            return True
        cmd = IdownCmd(q_task.get("cmd"))
        # 因为任务里面保存的设置可能不是完整的，所以需要使用默认设置补齐
        cmd.fill_defcmd(self.d_cmd)
        # iscantask也是支持周期执行的，但是同时也支持周期暂停，但是扫描程序不会有继续下载的功能，所以暂停不仅是将当前下载暂停了，更是把这个周期暂停了
        # 所以如果发现字段是被暂停了的，那么就不再进行下载modify by judy 2020/07/23
        if int(cmd.switch_control.download_switch) != 1:
            # 暂停的任务不需要再执行，但是需要更新下数据库状态，并且将状态回馈给server
            return False

        # 重点区域扫描，如果是周期任务那么直接执行了，没有执行区间，只有有效时间 modify by judy 20201126
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

    def _get_new_iscantask(self):
        """
        目前先不考虑设置，不太清楚需不需要做循环下载
        :return:
        """
        new_task_list = []
        result_list = []
        try:
            with self._dealing_queue_locker:
                new_task = self._sqlfunc.query_iscan_task(
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
                if len(new_task) > 0:
                    for t_a in new_task:
                        # 检查任务是否在执行时间内，任务的有效时间和任务的执行时间段
                        if self._process_task_execution_time(t_a):
                            new_task_list.append(t_a)
                        else:
                            try:
                                pause_task = self._construct_task(t_a)
                                if pause_task.cmd.switch_control.download_switch == 0:
                                    # 如果是被暂停的任务那么就开始
                                    self._sqlfunc.update_iscan_status(
                                        "taskstatus",
                                        ETaskStatus.TemporarilyStop.value,
                                        pause_task.taskid,
                                    )
                                    self._sqlfunc.update_iscan_status(
                                        "sequence",
                                        pause_task._sequence,
                                        pause_task.taskid,
                                    )
                                    self.write_iscanback(
                                        pause_task, ECommandStatus.Cancelled, "任务已经被暂停"
                                    )
                                    self._logger.info(
                                        f"Mission suspended successfully, taskid:{pause_task.taskid}"
                                    )
                                    continue
                            except Exception:
                                self._logger.error(
                                    "Construct task from dict error: {}".format(
                                        traceback.format_exc()
                                    )
                                )

                for dic in new_task_list:
                    if not isinstance(dic, dict):
                        continue
                    # 构造Task
                    task: IscanTask = None
                    try:
                        task = self._construct_task(dic)
                    except Exception:
                        self._logger.error(
                            "Construct task from dict error: {}".format(
                                traceback.format_exc()
                            )
                        )
                    if not isinstance(task, IscanTask):
                        continue
                    # 校验Task
                    if not isinstance(task.taskid, str) or task.taskid == "":
                        continue

                    # 满足下载条件后立即开始查询重复
                    if self._dealing_queue.__contains__(task.taskid):
                        continue

                    # 修改任务状态为正在处理到队列
                    task.taskstatus = ETaskStatus.WaitForDeal
                    # 修改数据库中的任务状态
                    self._sqlfunc.update_iscan_status(
                        "taskstatus", task.taskstatus.value, task.taskid
                    )

                    # 唯一的任务放到去重字典里
                    self._dealing_queue[task.taskid] = task
                    result_list.append(task)
        except:
            self._logger.error(
                f"Select executable iscan tasks error, err:{traceback.format_exc()}"
            )
        return result_list

    def _construct_task(self, filedata: dict) -> IscanTask:
        """
        构造dict构造iscantask
        :param filedata:
        :return:
        """
        tsk: IscanTask = IscanTask(filedata)
        tsk.priority = tsk.cmd.stratagy.priority
        tsk.on_complete = self.on_task_complete
        return tsk

    def _put_task_to_queue(self, tsk: IscanTask, queue: PriorityQueue):
        """
        将任务放进队列的通用方法
        :param tsk:
        :param queue:
        :return:
        """

        if not isinstance(tsk, IscanTask):
            raise Exception("Invalid Task")

        # 同时进行的最大的下载任务数,优先级高的任务直接处理
        # 正在下载的任务可能需要很久，所以每次sleep5秒即可
        queue.put(tsk)
        self.write_iscanback(tsk, ECommandStatus.Dealing, "任务加入下载队列成功，等待执行")
        self._logger.debug(f"Put an iscan task to queue\ntaskid:{tsk.taskid}")
        return

    def put_new_iscantask(self):
        """
        将新的iscantask放入队列
        :return:
        """
        while True:
            new_tasks = self._get_new_iscantask()
            if len(new_tasks) == 0:
                # 3秒钟扫描一次数据库
                time.sleep(1)
                continue
            try:
                for filedata in new_tasks:
                    self._put_task_to_queue(filedata, self._new_scantask_queue)
            except:
                self._logger.error(
                    f"Make the task from sqlite wrong, err:{traceback.format_exc()}"
                )
            finally:
                # 因为有循环任务所以5秒扫描一次
                # 毛线...不能去重啊
                time.sleep(0.5)

    def execute_new_iscantask(self):
        """
        不断的从新任务中取出任务,下载数据
        :return:
        """
        got = False
        while True:
            if self._new_scantask_queue.empty():
                time.sleep(1)
                continue
            got = False
            tsk: IscanTask = self._new_scantask_queue.get()
            got = True
            self._logger.info(
                f"Task start: {tsk.taskid}, scantype:{tsk.scantype.value}"
            )
            try:
                # 根据cmd中的设置访问网站，爬取不同的数据
                self._scan_plug_manger.iscandownload(tsk)
            except:
                self._logger.error(
                    f"Execute iscantask error, err:{traceback.format_exc()}"
                )
            finally:
                if got:
                    self._new_scantask_queue.task_done()

    def start(self):
        """
        多线程开启任务执行
        :return:
        """
        thread1 = threading.Thread(target=self.put_new_iscantask, name="iscantaskscan")
        thread2 = threading.Thread(
            target=self.execute_new_iscantask, name="iscantaskexecute"
        )
        thread1.start()
        thread2.start()
