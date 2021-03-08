"""
告诉server我执行完成了
"""

from .automatedtask import AutomatedTask
from ..ecommandstatus import ECommandStatus
from ..outputdata import DataSeg
from ..outputdata import EStandardDataType
from ..taskbackbase import TaskBackBase


class AutotaskBack(TaskBackBase):
    """automated taskback"""

    @staticmethod
    def create_from_task(
            task: AutomatedTask,
            cmdstatus: ECommandStatus,
            recvmsg: str,
            currtime: str = None,
            batchcompletecount: int = -1,
            periodnum: int = None,
    ):
        autask: AutomatedTask = task
        return AutotaskBack(
            autask.taskid,
            autask.platform,
            cmdstatus,
            recvmsg,
            currtime,
            autask.lastendtime,
            task.sequence,
            periodnum if not periodnum is None else task.periodnum,
            task.progress,
            task.source,
            batchcompletecount,
        )

    @staticmethod
    def create_from_dataseg(seg: DataSeg, platform: str):
        """从解析好的数据段结构初始化 TaskBatchBack 对象"""
        seg: DataSeg = seg
        res = AutotaskBack.create_from_dict(seg._fields, platform)
        res.segindex = seg.segindex
        res.segline = seg.segline
        return res

    @staticmethod
    def create_from_dict(
            allfields: dict,
            platform: str = None,
    ):
        """从键值对字典创建 TaskBatchBack 对象，
        此情况一般是从数据中读出来 键值对 字典时使用。"""
        if not isinstance(allfields, dict) or len(allfields) < 1:
            raise Exception("Invalid initial fields dict for IScanTask")

        state = allfields.get('state')
        if state is None:
            state = allfields.get('status')
        if not state is None:
            state = ECommandStatus(int(state))

        return AutotaskBack(
            taskid=allfields.get('taskid'),
            platform=platform,
            cmdstatus=state,
            recvmsg=allfields.get('recvmsg'),
            currtime=allfields.get('time'),
            endtime=allfields.get('lastendtime'),
            sequence=allfields.get('sequence'),
            periodnum=allfields.get('periodnum'),
            progress=allfields.get('progress'),
            source=allfields.get('source'),
        )

    def __init__(
            self,
            taskid,
            platform,
            cmdstatus: ECommandStatus,
            recvmsg: str,
            currtime: str,
            endtime: int,
            sequence,
            periodnum: int = 1,
            progress: float = None,
            source: str = None,
            batchcompletecount: int = -1,
    ):
        TaskBackBase.__init__(self, EStandardDataType.Autotaskback, platform,
                              cmdstatus, recvmsg, currtime)
        if taskid is None:
            raise Exception("Autotaskback taskid cant be None.")
        self.taskid = taskid
        self.sequence = sequence
        self.endtime = endtime
        self.periodnum: int = periodnum
        if not isinstance(self.periodnum, int):
            self.periodnum = int(self.periodnum)

        self.progress: float = None
        self.source: str = source
        self.batchcompletecount: int = batchcompletecount

    def get_output_segs(self) -> iter:
        """"""
        # 数据段索引，非sequence
        self.segindex = 1
        if self.owner_data is None:
            self.owner_data = self
        yield self

    def get_output_fields(self):
        self.append_to_fields('taskid', self.taskid)
        self.append_to_fields('periodnum', self.periodnum)
        self.append_to_fields('state', self._cmdstatus.value)
        if isinstance(self.cmdrcvmsg, str) and not self.cmdrcvmsg == "":
            self.append_to_fields('recvmsg', self._cmdrcvmsg)
        if not self.progress is None and type(self.progress) in [int, float]:
            self.append_to_fields('progress', self.progress)
        self.append_to_fields('endtime', self.endtime)
        if isinstance(self.source, str) and not self.source == "":
            self.append_to_fields('sequence', self.sequence)
        return self._fields


class AutotaskBatchBack(TaskBackBase):
    """automated batch taskback"""

    @staticmethod
    def create_from_task(
            task: AutomatedTask,
            cmdstatus: ECommandStatus,
            recvmsg: str,
            currtime: str = None,
    ):
        autask: AutomatedTask = task
        return AutotaskBatchBack(
            autask.taskid,
            autask.batchid,
            autask.platform,
            task.periodnum,
            cmdstatus,
            recvmsg,
            currtime,
            autask.lastendtime,
            autask.sequence,
            autask.source,
            autask.progress,
        )

    @staticmethod
    def create_from_dataseg(seg: DataSeg, platform: str):
        """从解析好的数据段结构初始化 TaskBatchBack 对象"""
        seg: DataSeg = seg
        res = AutotaskBatchBack.create_from_dict(seg._fields, platform)
        res.segindex = seg.segindex
        res.segline = seg.segline
        return res

    @staticmethod
    def create_from_dict(
            allfields: dict,
            platform: str = None,
    ):
        """从键值对字典创建 TaskBatchBack 对象，
        此情况一般是从数据中读出来 键值对 字典时使用。"""
        if not isinstance(allfields, dict) or len(allfields) < 1:
            raise Exception("Invalid initial fields dict for IScanTask")

        state = allfields.get('state')
        if state is None:
            state = allfields.get('status')
        if not state is None:
            state = ECommandStatus(int(state))

        return AutotaskBatchBack(
            taskid=allfields.get('taskid'),
            batchid=allfields.get('batchid'),
            platform=platform,
            periodnum=allfields.get('periodnum'),
            cmdstatus=state,
            recvmsg=allfields.get('recvmsg'),
            currtime=allfields.get('time'),
            endtime=allfields.get('lastendtime'),
            sequence=allfields.get('sequence'),
            source=allfields.get('source'),
            progress=allfields.get('progress'),
        )

    def __init__(
            self,
            taskid,
            batchid,
            platform,
            periodnum,
            cmdstatus: ECommandStatus,
            recvmsg: str,
            currtime: str,
            endtime: int,
            sequence,
            source,
            progress: float = None,
    ):
        TaskBackBase.__init__(self, EStandardDataType.AutoBatchTaskBack, platform,
                              cmdstatus, recvmsg, currtime)
        if taskid is None:
            raise Exception("Autotaskback taskid cant be None.")
        self.taskid = taskid
        self.batchid = batchid
        self.sequence = sequence
        self.endtime = endtime
        self.periodnum = periodnum
        if isinstance(self.periodnum, str) and not self.periodnum == "":
            self.periodnum = int(self.periodnum)
        self.source = source
        self.progress: float = progress

    def get_output_segs(self) -> iter:
        """"""
        # 数据段索引，非sequence
        self.segindex = 1
        if self.owner_data is None:
            self.owner_data = self
        yield self

    def get_output_fields(self):
        self.append_to_fields('taskid', self.taskid)
        self.append_to_fields('batchid', self.batchid)
        self.append_to_fields('periodnum', self.periodnum)
        self.append_to_fields('state', self._cmdstatus.value)
        if isinstance(self.cmdrcvmsg, str) and not self.cmdrcvmsg == "":
            self.append_to_fields('recvmsg', self._cmdrcvmsg)
        if not self.progress is None and type(self.progress) in [int, float]:
            self.append_to_fields('progress', self.progress)
        self.append_to_fields('endtime', self.endtime)
        if isinstance(self.source, str) and not self.source == "":
            self.append_to_fields('source', self.source)
        self.append_to_fields('sequence', self.sequence)
        return self._fields
