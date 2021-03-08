"""
iscouttask的任务回馈文件生成
create by judy 2019/06/12
"""

from .iscouttask import IscoutTask
from ..ecommandstatus import ECommandStatus
from ..outputdata import DataSeg, EStandardDataType
from ..taskbackbase import TaskBackBase


class IscoutTaskBack(TaskBackBase):
    """
    这个也应该是控制端使用的，先写在这里后面有变化就控制端来修改
    """
    @staticmethod
    def create_from_task(
            iscouttask: IscoutTask,
            cmdstatus: ECommandStatus,
            recvmsg: str,
            currtime: str = None,
            batchcompletecount: int = -1,
            periodnum: int = None,
    ):
        iscouttask: IscoutTask = iscouttask
        return IscoutTaskBack(
            taskid=iscouttask.taskid,
            platform=iscouttask.platform,
            cmdstatus=cmdstatus,
            scanrecvmsg=recvmsg,
            sequence=iscouttask.sequence,
            source=iscouttask.source,
            currtime=currtime,
            batchcompletecount=batchcompletecount,
            progress=iscouttask._progress,
            periodnum=periodnum,
            elapsed=iscouttask.elapsed,
        )

    @staticmethod
    def create_from_dataseg(
            seg: DataSeg,
            platform: str,
            batchcompletecount: int = -1,
    ):
        """从解析好的数据段结构初始化 IscoutTaskBack 对象"""
        seg: DataSeg = seg
        res = IscoutTaskBack.create_from_dict(seg._fields, platform,
                                              batchcompletecount)
        res.segindex = seg.segindex
        res.segline = seg.segline
        return res

    @staticmethod
    def create_from_dict(
            allfields: dict,
            platform: str = None,
            batchcompletecount: int = -1,
    ):
        """从键值对字典创建 IscoutTaskBack 对象，
        此情况一般是从数据中读出来 键值对 字典时使用。"""
        if not isinstance(allfields, dict) or len(allfields) < 1:
            raise Exception("Invalid initial fields dict for IScanTask")

        state = allfields.get('state')
        if state is None:
            state = allfields.get('status')
        if not state is None:
            state = ECommandStatus(int(state))

        return IscoutTaskBack(
            taskid=allfields.get('taskid'),
            platform=platform,
            cmdstatus=state,
            scanrecvmsg=allfields.get('recvmsg'),
            sequence=allfields.get('sequence'),
            source=allfields.get('source'),
            currtime=allfields.get('time'),
            batchcompletecount=batchcompletecount,
            progress=allfields.get('progress'),
            periodnum=allfields.get('periodnum'),
            elapsed=allfields.get('elapsed'),
        )

    def __init__(
            self,
            taskid: str,
            platform: str,
            cmdstatus: ECommandStatus,
            scanrecvmsg: str,
            sequence: int,
            source: str,
            currtime: str = None,
            batchcompletecount: int = -1,
            progress: float = 0,
            periodnum: int = None,
            elapsed: float = 0,
    ):

        TaskBackBase.__init__(self, EStandardDataType.IscoutTaskBack, platform,
                              cmdstatus, scanrecvmsg, currtime)
        if not isinstance(taskid, str):
            raise Exception("Invalid iscan taskid for IScanTaskBack")
        self._taskid = taskid

        self._sequence: int = None
        if isinstance(sequence, int):
            self._sequence = sequence
        elif isinstance(sequence, str):
            self._sequence = int(sequence)
        else:
            raise Exception("Invalid sequence for IScanTaskBack")

        self._source: str = source
        # 批处理任务的子任务已完成数量
        self.batchcompletecount: int = 0
        if isinstance(batchcompletecount, int) and batchcompletecount > 0:
            self.batchcompletecount = batchcompletecount

        self._progress: float = 0
        if type(progress) in [int, float]:
            self._progres = progress

        self.periodnum = 1
        if isinstance(periodnum, int):
            self.periodnum = periodnum  # 控制端不知道succeedtime和failedtimes
        elif isinstance(periodnum, str):
            self.periodnum = int(periodnum)

        self.elapsed: float = 0
        if not elapsed is None and type(elapsed) in [int, float
                                                     ] and elapsed > 0:
            self.elapsed = elapsed
        elif isinstance(elapsed, str):
            try:
                tmp = float(elapsed)
                self.elapsed = float(tmp)
            except Exception:
                pass

    def get_output_segs(self) -> iter:
        """"""
        # 数据段索引，非sequence
        self.segindex = 1
        if self.owner_data is None:
            self.owner_data = self
        yield self

    def get_output_fields(self):
        self.append_to_fields('taskid', self._taskid)
        self.append_to_fields('state', self._cmdstatus.value)
        self.append_to_fields('progress', self._progress)
        self.append_to_fields('recvmsg', self._cmdrcvmsg)
        self.append_to_fields('time', self.time)
        self.append_to_fields('sequence', self._sequence)
        self.append_to_fields('periodnum', self.periodnum)
        if not self.elapsed is None:
            self.append_to_fields('elapsed', self.elapsed)

        # 这个字段暂时不用
        # self.append_to_fields('batchcompletecount',self.batchcompletecount)
        return self._fields


class IscoutBtaskBack(TaskBackBase):
    """
    采集端使用的任务回馈，主要是采集端使用
    """
    @property
    def progress(self) -> float:
        """进度"""
        return self._progress

    @progress.setter
    def progress(self, value):
        """进度"""
        self._progress = float(value)

    @staticmethod
    def create_from_task(iscouttask: IscoutTask,
                         cmdstatus: ECommandStatus,
                         recvmsg: str,
                         currtime: str = None,
                         elapsed: float = None):
        return IscoutBtaskBack(taskid=iscouttask.taskid,
                               batchid=iscouttask.batchid,
                               progress=iscouttask.progress,
                               sequence=iscouttask.sequence,
                               platform=iscouttask._platform,
                               cmdstatus=cmdstatus,
                               recvmsg=recvmsg,
                               source=iscouttask.source,
                               currtime=currtime,
                               successedtimes=iscouttask.successtimes,
                               failedtimes=iscouttask.failtimes,
                               periodnum=iscouttask.periodnum,
                               elapsed=elapsed)

    @staticmethod
    def create_from_dataseg(seg: DataSeg, platform: str):
        """从解析好的数据段结构初始化 IScoutBTaskBack 对象"""
        seg: DataSeg = seg
        res = IscoutBtaskBack.create_from_dict(seg._fields, platform)
        res.segindex = seg.segindex
        res.segline = seg.segline
        return res

    @staticmethod
    def create_from_dict(
            allfields: dict,
            platform: str = None,
    ):
        """从键值对字典创建 IScoutBTaskBack 对象，
        此情况一般是从数据中读出来 键值对 字典时使用。"""
        if not isinstance(allfields, dict) or len(allfields) < 1:
            raise Exception("Invalid initial fields dict for IScanTask")

        state = allfields.get('state')
        if state is None:
            state = allfields.get('status')
        if not state is None:
            state = ECommandStatus(int(state))

        return IscoutBtaskBack(
            taskid=allfields.get('taskid'),
            batchid=allfields.get('batchid'),
            progress=allfields.get('progress'),
            sequence=allfields.get('sequence'),
            platform=platform,
            cmdstatus=state,
            recvmsg=allfields.get('recvmsg'),
            source=allfields.get('source'),
            currtime=allfields.get('time'),
            periodnum=allfields.get('periodnum'),
            elapsed=allfields.get('elapsed', 0),
        )

    def __init__(
            self,
            taskid: str,
            batchid: str,
            progress: float = 0,
            sequence=1,
            platform: str = None,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
            recvmsg: str = None,
            source: str = None,
            currtime=None,
            successedtimes: int = 0,
            failedtimes: int = 0,
            periodnum: int = None,
            elapsed: int = 0,
    ):
        TaskBackBase.__init__(self, EStandardDataType.IscoutBtaskBack,
                              platform, cmdstatus, recvmsg, currtime)
        if not isinstance(taskid, str) or taskid == '':
            raise Exception("Invalid param 'taskid' for IScoutBTaskBack")
        self._taskid = taskid

        if not isinstance(batchid, str) or batchid == '':
            raise Exception("Invalid param 'batchid' for IScoutBTaskBack")
        self._batchid = batchid

        self._progress: float = 0
        if isinstance(progress, str) and not progress == "":
            try:
                progress = float(progress)
            except Exception:
                pass
        if isinstance(progress, float) and progress > 0:
            self._progress = progress

        self._sequence: int = 1
        if isinstance(sequence, int):
            self._sequence: int = sequence
        else:
            self._sequence = int(sequence)

        self._cmdrcvmsg: str = None
        if isinstance(recvmsg, str) and recvmsg != '':
            self._cmdrcvmsg = recvmsg

        self.source: str = source

        # 新增执行次数
        self.successedtimes = successedtimes
        self.failedtimes = failedtimes
        self.periodnum = self.successedtimes + self.failedtimes + 1
        if isinstance(periodnum, int):
            self.periodnum = periodnum  # 控制端不知道succeedtime和failedtimes
        elif isinstance(periodnum, str):
            self.periodnum = int(periodnum)
        # 任务成功完成后增加字段elapsed
        self.elapsed: float = 0
        if not elapsed is None and type(elapsed) in [int, float
                                                     ] and elapsed > 0:
            self.elapsed = elapsed
        elif isinstance(elapsed, str):
            try:
                tmp = float(elapsed)
                self.elapsed = float(tmp)
            except Exception:
                pass

    def get_output_segs(self) -> iter:
        """"""
        # 数据段索引，非sequence
        self.segindex = 1
        yield self

    def get_output_fields(self):
        self.append_to_fields('taskid', self._taskid)
        self.append_to_fields('batchid', self._batchid)
        self.append_to_fields('state', self._cmdstatus.value)
        self.append_to_fields('progress', self._progress)
        self.append_to_fields('recvmsg', self.cmdrcvmsg)
        self.append_to_fields('time', self.time)
        self.append_to_fields('sequence', self._sequence)
        self.append_to_fields('source', self.source)
        # 新增执行次数的字段,没有在输出中配置那么就会直接输出
        self.append_to_fields('successedtimes', self.successedtimes)
        self.append_to_fields('failedtimes', self.failedtimes)
        self.append_to_fields('periodnum', self.periodnum)
        if self.elapsed is not None:
            self.append_to_fields('elapsed', self.elapsed)
        return self._fields
