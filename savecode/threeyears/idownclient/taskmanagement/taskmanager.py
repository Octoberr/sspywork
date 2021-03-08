"""
管理不同的任务队列
by judy 2018/10/15
增加idowncmd和iscantask
update by judy 2019/06/25
"""
import queue
import threading
import time
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import InputData, Task, IdownCmd, IscanTask, IscoutTask
from datacontract.automateddataset import AutomatedTask
from idownclient.autotaskmanagement import AutoTaskManager
from idownclient.cmdmanagement import CmdManager
from idownclient.iscanmanagement import ScanManager
from idownclient.iscoutmanagement import ScoutManager
from idownclient.dnsreq import DnsData, DnsReq
from idownclient.spidermanagent.spidermanagerallot import SpiderManagerAllot
from .taskparser.taskfileparser import TaskFileParser


class TaskManager:
    def __init__(self):
        # task队列
        self._idowntskqueue = queue.Queue()
        # cmd队列
        self._cmdqueue = queue.Queue()
        # iscantask队列
        self._iscanqueue = queue.Queue()
        # iscouttask队列
        self._iscoutqueue = queue.Queue()
        # autotask队列
        self._autoqueue = queue.Queue()
        # 新增dnsreq队列
        self._dnsqueue = queue.Queue()
        # --------------------------------------这里可能会增加iscan和iscout两个队列
        self._logger: MsLogger = MsLogManager.get_logger("TaskManager")
        # spidermanager
        self._task_allot = SpiderManagerAllot()
        # cmdmanager
        self._cmd_allot = CmdManager()
        # taskparser
        self._taskparser: TaskFileParser = TaskFileParser()
        # ---------------------------------------------------新增iscantask
        self._iscan_allot = ScanManager()
        # ---------------------------------------------------新增iscouttask
        self._iscout_allot = ScoutManager()
        # ---------------------------------------------------新增autotask
        self._autotask_allot = AutoTaskManager()
        # -----------------------------------------------新增dns
        self._dnsreq = DnsReq()

    def on_task_in(self, data: InputData):
        if not isinstance(data, InputData):
            raise Exception("Data is not inputdata cant be parse")
        # 一般来说data的处理是不会出错的，但是根据客户的反应来看是出现了问题的，所以加一个flag标志来判断下by judy 2020/08/24
        data_flag = False
        try:
            # self._logger.log("读取文件文件，filename:{}".format(data.name))
            # 流式解析，避免文件过大占满内存
            for tsk in self._taskparser.convert(data):
                # 进了这里处理才代表开始处理了任务
                data_flag = True
                try:
                    if isinstance(tsk, DnsData):
                        # 处理dnsdata
                        self._dnsqueue.put(tsk)
                        self._logger.info(
                            f"New dnsreq data, dns:{tsk.dnsdata.get('dnsreq')}"
                        )
                        continue

                    # idown的任务
                    if isinstance(tsk, Task):
                        # 换个位置保证东西是放进了队列里
                        self._idowntskqueue.put(tsk)
                        self._logger.info(f"New idown task:{tsk.batchid}")
                        continue
                    # 单独的cmd
                    # 这里会新增加一种idown.cmd，可以解析cmd
                    elif isinstance(tsk, IdownCmd):
                        self._cmdqueue.put(tsk)
                        self._logger.info(f"New cmd:{tsk.cmd_id}")
                        continue
                    # iscantask
                    elif isinstance(tsk, IscanTask):
                        self._iscanqueue.put(tsk)
                        self._logger.info(f"New iscan task:{tsk.taskid}")
                        continue
                    # iscouttask
                    elif isinstance(tsk, IscoutTask):
                        self._iscoutqueue.put(tsk)
                        self._logger.info(f"New iscout task:{tsk.batchid}")
                        continue
                    # autotask
                    elif isinstance(tsk, AutomatedTask):
                        self._autoqueue.put(tsk)
                        self._logger.info(f"New autotask task:{tsk.taskid}")
                        continue
                    else:
                        self._logger.error(
                            f"Parse task data failed:\ndata:{data._source}"
                        )
                        data_flag = False

                except Exception as err:
                    self._logger.info("Something wrong with queue, err:{}".format(err))
                    data_flag = False
        except Exception:
            self._logger.error(
                f"Task in error:\ndata:{data._source}\nerror:{traceback.format_exc()}"
            )
            data_flag = False
        finally:
            data.on_complete(data_flag)
            # 这样就可以去失败的文件夹寻找失败的任务文件

    def _process_task(self):
        """
        读取idowntask并预处理
        :return:
        """
        got: bool = False
        while True:
            if self._idowntskqueue.empty():
                time.sleep(1)
                continue
            try:
                got = False
                task: Task = self._idowntskqueue.get()
                got = True
                self._logger.info(
                    f"Get a idowntask[{task.tasktype.name}], batchid:{task.batchid}"
                )
                if task is None or task.batchid is None:
                    self._logger.warn(
                        f"This task is None, or batchid is None, "
                        f"so this task will be abandoned, taskid:{task.taskid}"
                    )
                    continue
                self._task_allot.manage_task(task)
            except Exception:
                self._logger.error(
                    "preprocess err, err:{}".format(traceback.format_exc())
                )
            finally:
                if got:
                    self._idowntskqueue.task_done()

    def _process_iscantask(self):
        """
        读取队列里的iscantask
        :return:
        """
        got = False
        while True:
            if self._iscanqueue.empty():
                time.sleep(1)
                continue
            try:
                got = False
                s_task: IscanTask = self._iscanqueue.get()
                got = True
                self._logger.info(f"Get a iscantask, taskid:{s_task.taskid}")
                if s_task is None or s_task.taskid is None:
                    self._logger.warn(
                        f"This idown task is None, or batchid is None, so this task will be abandoned, taskid:{s_task.taskid}"
                    )
                    continue
                self._iscan_allot.iscantask_manage(s_task)
            except Exception:
                self._logger.error(
                    "Preprocess err\nerr:{}".format(traceback.format_exc())
                )
            finally:
                if got:
                    self._iscanqueue.task_done()

    def _process_cmd(self):
        """
        处理cmd
        :return:
        """
        got = False
        while True:
            if self._cmdqueue.empty():
                # cmd 的队列可以等久一点，毕竟不是每个task都会有cmd
                time.sleep(2)
                continue
            try:
                got = False
                icmd: IdownCmd = self._cmdqueue.get()
                got = True
                if icmd is None:
                    self._logger.warn(
                        f"Get cmd data is None, this command will be abandoned."
                    )
                    continue
                self._cmd_allot.manage_cmd(icmd)
            except Exception:
                self._logger.error("Process cmd, err:{}".format(traceback.format_exc()))
            finally:
                if got:
                    self._cmdqueue.task_done()

    def _process_iscouttask(self):
        """
        读取队列里的iscouttask
        :return:
        """
        got = False
        while True:
            if self._iscoutqueue.empty():
                time.sleep(1)
                continue
            try:
                got = False
                s_task: IscoutTask = self._iscoutqueue.get()
                got = True
                self._logger.info(f"Get a iscouttask, batchid:{s_task.batchid}")
                if s_task is None or s_task.batchid is None:
                    self._logger.warn(
                        f"This iscout task is None, or batchid is None, "
                        f"so this task will be abandoned, taskid:{s_task.taskid}"
                    )
                    continue
                self._iscout_allot.iscouttask_manage(s_task)
            except Exception:
                self._logger.error(
                    "preprocess err, err:{}".format(traceback.format_exc())
                )
            finally:
                if got:
                    self._iscoutqueue.task_done()

    def _process_autotask(self):
        """
        读取队列里的autotask
        :return:
        """
        got = False
        while True:
            if self._autoqueue.empty():
                time.sleep(1)
                continue
            try:
                got = False
                a_task: AutomatedTask = self._autoqueue.get()
                got = True
                if a_task is None or a_task.batchid is None:
                    self._logger.warn(
                        f"This auto task is None, or batchid is None, "
                        f"so this task will be abandoned, taskid:{a_task.taskid}"
                    )
                    continue
                self._autotask_allot.autotask_manage(a_task)
            except Exception:
                self._logger.error(
                    "preprocess err, err:{}".format(traceback.format_exc())
                )
            finally:
                if got:
                    self._autoqueue.task_done()

    def _process_dnsreq(self):
        """
        处理dnsreq
        :return:
        """
        got = False
        while True:
            if self._dnsqueue.empty():
                time.sleep(1)
                continue
            try:
                got = False
                d_task: DnsData = self._dnsqueue.get()
                got = True
                self._dnsreq.dns_response(d_task.dnsdata)
                self._logger.info("Finish dns request and output data success")
            except Exception:
                self._logger.error(
                    "preprocess dns file error, err:{}".format(traceback.format_exc())
                )
            finally:
                if got:
                    self._dnsqueue.task_done()

    def start(self):
        thread1 = threading.Thread(target=self._process_task, name="taskpreprocess")
        thread1.start()
        # 增加一个处理cmd命令的线程
        thread2 = threading.Thread(target=self._process_cmd, name="taskcmdprocess")
        thread2.start()
        # 增加一个scan和scout任务的预处理和存储
        thread3 = threading.Thread(
            target=self._process_iscantask, name="iscantaskpreprocess"
        )
        thread3.start()
        thread4 = threading.Thread(
            target=self._process_iscouttask, name="iscouttaskpreprocess"
        )
        thread4.start()
        # 新增内部任务，由server下发
        thread5 = threading.Thread(
            target=self._process_autotask, name="autotaskprocess"
        )
        thread5.start()
        # 新增dnsreq的任务，由路由器下发，by judy 2020/03/04
        # thread6 = threading.Thread(target=self._process_dnsreq, name="dnsreqprocess")
        # thread6.start()
