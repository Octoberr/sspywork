"""
Iscan的数据回馈
create by swm 2019/06/12
"""
from ..ecommandstatus import ECommandStatus
from ..outputdata import DataSeg, EStandardDataType
from ..taskbackbase import TaskBackBase
from .iscantask import IscanTask


class IscanTaskBack(TaskBackBase):
    """
    这个应该是控制端用的，我先写在这里
    参考的是task的datafeedback
    """

    @staticmethod
    def create_from_task(
            iscantask: IscanTask,
            cmdstatus: ECommandStatus,
            scanrecvmsg: str,
            currtime: str = None,
            elapsed: float = None,
    ):
        return IscanTaskBack(
            taskid=iscantask.taskid,
            clientid=iscantask._clientid,
            platform=iscantask._platform,
            cmdstatus=cmdstatus,
            scanrecvmsg=scanrecvmsg,
            sequence=iscantask.sequence,
            source=iscantask.source,
            currtime=currtime,
            periodnum=iscantask.periodnum,
            progress=iscantask.progress,
            elapsed=elapsed
        )

    @staticmethod
    def create_from_dataseg(seg: DataSeg, platform: str):
        """从解析好的数据段结构初始化 TaskBatchBack 对象"""
        seg: DataSeg = seg
        res = IscanTaskBack.create_from_dict(seg._fields, platform)
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

        return IscanTaskBack(
            taskid=allfields.get('taskid'),
            clientid=allfields.get('clientid'),
            platform=platform,
            cmdstatus=state,
            scanrecvmsg=allfields.get('recvmsg'),
            sequence=allfields.get('sequence'),
            source=allfields.get('source'),
            currtime=allfields.get('time'),
            periodnum=allfields.get('periodnum'),
            progress=allfields.get('progress'),
        )

    def __init__(
            self,
            taskid: str,
            clientid: str,
            platform: str,
            cmdstatus: ECommandStatus,
            scanrecvmsg: str,
            sequence: int,
            source: str,
            currtime: str = None,
            periodnum: int = None,
            progress: float = None,
            elapsed: float = None
    ):
        TaskBackBase.__init__(self, EStandardDataType.IscanTaskBack, platform,
                              cmdstatus, scanrecvmsg, currtime)
        if not isinstance(taskid, str):
            raise Exception("Invalid iscan taskid for IScanTaskBack")
        self._taskid = taskid
        self._clientid = clientid
        self.platform = platform

        self._sequence: int = None
        if isinstance(sequence, int):
            self._sequence = sequence
        elif isinstance(sequence, str):
            self._sequence = int(sequence)
        else:
            raise Exception("Invalid sequence for IScanTaskBack")

        self.progress: float = 0
        if not progress is None:
            self.progress = float(progress)

        self._source: str = source

        # 新增执行次数
        self.periodnum: int = None
        if isinstance(periodnum, int):
            self.periodnum = periodnum
        elif isinstance(periodnum, str):
            self.periodnum = int(periodnum)
        self.elapsed = None
        if elapsed is not None:
            self.elapsed = elapsed

    def get_output_segs(self) -> iter:
        """"""
        # 数据段索引，非sequence
        self.segindex = 1
        if self.owner_data is None:
            self.owner_data = self
        yield self

    def get_output_fields(self):
        self.append_to_fields('taskid', self._taskid)
        self.append_to_fields('clientid', self._clientid)
        self.append_to_fields('platform', self.platform)
        self.append_to_fields('state', self._cmdstatus.value)
        self.append_to_fields('periodnum', self.periodnum)
        self.append_to_fields('recvmsg', self._cmdrcvmsg)
        self.append_to_fields('time', self.time)
        self.append_to_fields('sequence', self._sequence)
        self.append_to_fields('source', self._source)
        self.append_to_fields('progress', self.progress)
        self.append_to_fields('elapsed', self.elapsed)
        return self._fields


class IscanBtaskBack(TaskBackBase):
    """
    这个暂时没用。
    采集端回传的子任务回馈，主要是采集端使用
    """

    @staticmethod
    def create_from_iscantask(iscantask: IscanTask,
                              cmdstatus: ECommandStatus,
                              scanrecvmsg,
                              currtime: str = None):
        """
        从iscantask创建任务体
        :param iscantask:
        :param cmdstatus:
        :param scanrecvmsg:
        :param currtime:
        :return:
        """
        return IscanBtaskBack(iscantask.taskid, iscantask.batchid,
                              iscantask.batchindex, iscantask.progress,
                              iscantask.time_now, iscantask.sequence,
                              iscantask.platform, cmdstatus, scanrecvmsg,
                              iscantask.source, currtime)

    def __init__(self,
                 taskid,
                 batchid,
                 batchindex,
                 progress,
                 time_now,
                 sequence,
                 platform,
                 cmdstatus: ECommandStatus,
                 scanrecvmsg,
                 source,
                 currtime: str = None):
        # self._iscantask = iscanbtask
        TaskBackBase.__init__(self, EStandardDataType.IscanTaskBack, platform,
                              cmdstatus, scanrecvmsg, currtime)
        # self.state: EscanStatus = cmdstatus
        # self.recvmsg = scanrecvmsg
        if taskid is None:
            raise Exception('Iscanfeedback taskid can not be None')
        if batchid is None:
            raise Exception('Iscanfeedback batchid can not be None')
        self.taskid = taskid
        self.batchid = batchid
        self.batchindex = batchindex
        self.progress = progress
        self.time_now = time_now
        self.sequence = sequence
        self.source = source

    def get_output_segs(self) -> iter:
        """"""
        # 数据段索引，非sequence
        self.segindex = 1
        yield self

    def get_output_fields(self):
        self.append_to_fields('taskid', self.taskid)
        self.append_to_fields('batchid', self.batchid)
        self.append_to_fields('batchindex', self.batchindex)
        self.append_to_fields('state', self._cmdstatus.value)
        self.append_to_fields('progress', self.progress)
        self.append_to_fields('recvmsg', self._cmdrcvmsg)
        self.append_to_fields('time', self.time_now)
        self.append_to_fields('sequence', self.sequence)
        self.append_to_fields('source', self.source)
        return self._fields
