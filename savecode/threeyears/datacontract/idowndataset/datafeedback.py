"""
子类插件下载的数据类型
create by judy 2018/10/12
modify by judy 2018/10/15
"""
import threading
from datetime import datetime

import pytz

from .task import ECommandStatus, Task
from ..outputdata import DataSeg, EStandardDataType
from ..taskbackbase import TaskBackBase


class EBackResult:
    Registerd = '#@11'

    UnRegisterd = '#@12'

    CheckRegisterdFail = '#@13'

    LoginSucess = '#@32'

    LoginFailed = '#@33'

    Online = '#@21'

    Offline = '#@22'

    Unknownline = '#@23'


class TaskBack(TaskBackBase):
    """
    控制端汇总之后 返回的总任务回馈\n
    task: 回馈数据关联的Task对象。\n
    cmdstatus: 指定任务回馈数据状态，若为None，则默认使用Task对象的_cmdstatus字段。\n
    cmdrcvmsg: 描述信息，若为空则会使用Task对象中自带的_cmdrcvmsg字段。\n
    result: 结果值，若为空则会使用Task对象中自带的_result字段。\n
    currenttime: 数据产生时间，若为空则使用当前时间。\n
    """

    def __init__(self,
                 task: Task,
                 cmdstatus: ECommandStatus = None,
                 cmdrcvmsg: str = None,
                 result: str = None,
                 currenttime: str = None,
                 batchcompletecount: int = -1):

        if not isinstance(task, Task):
            raise Exception(
                "Invalid task object while initialing TaskBack object")
        self._task: Task = task
        if cmdstatus is None:
            cmdstatus = self._task.cmdstatus
        TaskBackBase.__init__(self, EStandardDataType.TaskBack,
                              self._task.platform, cmdstatus, cmdrcvmsg,
                              currenttime)

        self._result: str = self._task._result
        if isinstance(result, str) and result != "":
            self._result = result
        # 当前时间, 字符串的datetime
        self.time: str = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        if currenttime is not None and currenttime != '':
            self.time = currenttime

        # 批处理任务的子任务已完成数量
        self.batchcompletecount: int = 0
        if isinstance(batchcompletecount, int) and batchcompletecount > 0:
            self.batchcompletecount = batchcompletecount
        else:
            self.batchcompletecount = task.batchcompletecount

    def get_output_segs(self) -> iter:
        """"""
        # 数据段索引，非sequence
        self.segindex = 1
        if self.owner_data is None:
            self.owner_data = self
        yield self

    def get_output_fields(self) -> dict:
        """"""
        # 对于一个总任务来说，其没有clientid字段，其每个子任务才有clientid
        # self.append_to_fields('clientid', self._task._clientid)
        self.append_to_fields('taskid', self._task.taskid)
        self.append_to_fields('state', self._cmdstatus.value)
        self.append_to_fields('recvmsg', self._cmdrcvmsg)
        self.append_to_fields('result', self._result)
        self.append_to_fields('time', self.time)
        self.append_to_fields('batchcompletecount', self.batchcompletecount)
        # 对应采集端来讲，每个任务都是子任务，直接使用task.sequence即可
        self.append_to_fields('sequence', self._task.sequence)
        return self._fields


class TaskBatchBack(TaskBackBase):
    """
    采集端回传的 子任务 回馈数据。\n
    task: 回馈数据关联的Task对象。\n
    cmdstatus: 指定任务回馈数据状态，若为None，则默认使用Task对象的_cmdstatus字段。\n
    cmdrcvmsg: 描述信息，若为空则会使用Task对象中自带的_cmdrcvmsg字段。\n
    result: 结果值，若为空则会使用Task对象中自带的_result字段。\n
    currenttime: 数据产生时间，若为空则使用当前时间。
    """

    @staticmethod
    def create_from_task(task: Task,
                         cmdstatus: ECommandStatus = None,
                         cmdrcvmsg: str = None,
                         result: str = None,
                         currenttime: str = None):
        """以已有 Task 对象为蓝本实例化并返回 TaskBatchBack 对象"""
        tsk: Task = task
        if not isinstance(cmdstatus, ECommandStatus):
            cmdstatus = tsk._cmdstatus
        if not isinstance(cmdrcvmsg, str) or cmdrcvmsg == '':
            cmdrcvmsg = tsk._cmdrcvmsg
        if not isinstance(result, str) or result == '':
            result = tsk._result

        return TaskBatchBack(
            platform=tsk._platform,
            clientid=tsk._clientid,
            taskid=tsk.taskid,
            batchid=tsk.batchid,
            cmdstatus=cmdstatus,
            sequence=tsk.sequence,
            parentbatchid=tsk.parentbatchid,
            progress=tsk.progress,
            cmdrcvmsg=cmdrcvmsg,
            result=result,
            otherfields=tsk.other_fields_json,
            currenttime=currenttime,
            isbatchcompletecountincreased=tsk.isbatchcompletecountincreased,
            source=tsk.source
        )

    @staticmethod
    def create_from_fields(platform: str,
                           clientid: str,
                           taskid: str,
                           batchid: str,
                           cmdstatus: ECommandStatus,
                           sequence: int,
                           parentbatchid: str = None,
                           progress: float = None,
                           cmdrcvmsg: str = None,
                           result: str = None,
                           otherfields: str = None,
                           currenttime: str = None,
                           isbatchcompletecountincreased: bool = False):
        """从指定参数创建 TaskBatchBack 对象"""
        return TaskBatchBack(
            platform=platform,
            clientid=clientid,
            taskid=taskid,
            batchid=batchid,
            cmdstatus=cmdstatus,
            sequence=sequence,
            parentbatchid=parentbatchid,
            progress=progress,
            cmdrcvmsg=cmdrcvmsg,
            result=result,
            otherfields=otherfields,
            currenttime=currenttime,
            isbatchcompletecountincreased=isbatchcompletecountincreased)

    @staticmethod
    def create_from_dict(allfields: dict):
        """从键值对字典创建 TaskBatchBack 对象，
        此情况一般是从数据中读出来 键值对 字典时使用。"""
        if not isinstance(allfields, dict) or len(allfields) < 1:
            raise Exception("Invalid initial fields dict for TaskBatchBack")

        return TaskBatchBack(
            TaskBatchBack._judge_static(allfields, 'platform', error=True),
            TaskBatchBack._judge_static(allfields, 'clientid', error=True),
            TaskBatchBack._judge_static(allfields, 'taskid', error=True),
            TaskBatchBack._judge_static(allfields, 'batchid', error=True),
            ECommandStatus(
                int(TaskBatchBack._judge_static(allfields, 'state'))),
            int(
                TaskBatchBack._judge_static(allfields, 'sequence',
                                            error=True)),
            TaskBatchBack._judge_static(allfields, 'parentbatchid'),
            TaskBatchBack._judge_static(allfields, 'progress'),
            TaskBatchBack._judge_static(allfields, 'recvmsg'),
            TaskBatchBack._judge_static(allfields, 'result'),
            TaskBatchBack._judge_static(allfields, 'otherfields'),
            TaskBatchBack._judge_static(allfields, 'time'),
            TaskBatchBack._judge_static(allfields,
                                        'isbatchcompletecountincreased'),
        )

    @staticmethod
    def create_from_dataseg(seg: DataSeg):
        """从解析好的数据段结构初始化 TaskBatchBack 对象"""
        seg: DataSeg = seg
        res = TaskBatchBack.create_from_dict(seg._fields)
        res.segindex = seg.segindex
        res.segline = seg.segline
        return res

    @property
    def cmdstatus(self) -> ECommandStatus:
        """当前子任务的命令状态"""
        return self._cmdstatus

    @cmdstatus.setter
    def cmdstatus(self, value):
        """"""
        if not isinstance(value, ECommandStatus):
            raise Exception(
                "Invalid ECommandStatus for TaskBatchBack object: {}".format(
                    value))
        self._cmdstatus = value

    @property
    def progress(self) -> float:
        """当前TaskBatchBack的子任务进度"""
        return self._progress

    @progress.setter
    def progress(self, value):
        """当前TaskBatchBack的子任务进度"""
        if not type(value) in [int, float]:
            return
        self._progress = value

    def __init__(self,
                 platform: str,
                 clientid: str,
                 taskid: str,
                 batchid: str,
                 cmdstatus: ECommandStatus,
                 sequence: int,
                 parentbatchid: str = None,
                 progress: float = None,
                 cmdrcvmsg: str = None,
                 result: str = None,
                 otherfields: str = None,
                 currenttime: str = None,
                 isbatchcompletecountincreased: bool = False,
                 source=None):

        TaskBackBase.__init__(self, EStandardDataType.TaskBatchBack, platform,
                              cmdstatus, cmdrcvmsg, currenttime)
        # OutputData.__init__(self, platform, EStandardDataType.TaskBatchBack)
        # OutputDataSeg.__init__(self)

        # if not isinstance(clientid, str) or clientid == '':
        #     raise Exception("Invalid param 'clientid' for TaskBatchBack")
        # clientid有可能为空，因为有可能在任务尚未分配到client的时候就已经出错了
        self._clientid = clientid

        if not isinstance(taskid, str) or taskid == '':
            raise Exception("Invalid param 'taskid' for TaskBatchBack")
        self._taskid = taskid

        if not isinstance(batchid, str) or batchid == '':
            raise Exception("Invalid param 'batchid' for TaskBatchBack")
        self._batchid = batchid

        self._parentbatchid: str = None
        if isinstance(parentbatchid, str) and not parentbatchid == "":
            self._parentbatchid = parentbatchid

        # if not isinstance(cmdstatus, ECommandStatus):
        #     raise Exception("Invalid param 'cmdstatus' for TaskBatchBack")
        # self._cmdstatus: ECommandStatus = cmdstatus

        self._progress: float = 0
        if isinstance(progress, str) and not progress == "":
            try:
                progress = float(progress)
            except Exception:
                pass
        if isinstance(progress, float) and progress > 0:
            self._progress = progress

        if not isinstance(sequence, int):
            raise Exception("Invalid param 'sequence' for TaskBatchBack")
        self._sequence: int = sequence
        self._sequencelocker = threading.RLock()

        self._cmdrcvmsg: str = ''
        if isinstance(cmdrcvmsg, str) and cmdrcvmsg != '':
            self._cmdrcvmsg = cmdrcvmsg

        self._result: str = ''
        if isinstance(result, str) and result != "":
            self._result = result

        # 当前时间, 字符串的datetime
        self.time: str = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        if currenttime is not None and currenttime != '':
            self.time = currenttime

        self.isbatchcompletecountincreased: bool = False
        if isinstance(isbatchcompletecountincreased, bool):
            self.isbatchcompletecountincreased = isbatchcompletecountincreased
        # -------------------------------------------新增字段190620
        self.source = source

    def get_output_segs(self) -> iter:
        """"""
        # 数据段索引，非sequence
        self.segindex = 1
        yield self

    def get_output_fields(self) -> dict:
        """"""
        self.append_to_fields('clientid', self._clientid)
        self.append_to_fields('taskid', self._taskid)
        self.append_to_fields('batchid', self._batchid)
        self.append_to_fields('platform', self._platform)
        self.append_to_fields('state', self._cmdstatus.value)
        self.append_to_fields('recvmsg', self._cmdrcvmsg)
        self.append_to_fields('progress', self._progress)
        self.append_to_fields('result', self._result)
        self.append_to_fields('time', self.time)
        # 对应采集端来讲，每个任务都是子任务，直接使用task.sequence即可
        self.append_to_fields('sequence', self._sequence)
        self.append_to_fields('source', self.source)
        return self._fields

    def increate_sequence(self, increament: int = 1):
        """增加当前TaskBatchBack的sequence序列号"""
        if not isinstance(increament, int) or increament < 1:
            raise Exception(
                "Invalid increament for TaskBatchBack sequence:\ntaskid:{}\nbatchid:{}\nsequence:{}"
                    .format(self._taskid, self._batchid, self._sequence))
        with self._sequencelocker:
            self._sequence += increament
