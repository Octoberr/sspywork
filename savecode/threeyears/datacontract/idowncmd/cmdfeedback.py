"""
idowncmd的回馈文件
create by judy
2019/05/15
"""

from datacontract.outputdata import DataSeg
from datacontract.outputdata import EStandardDataType
from .idowncmd import IdownCmd
from ..ecommandstatus import ECommandStatus
from ..taskbackbase import TaskBackBase


class CmdFeedBack(TaskBackBase):
    """命令数据回馈"""

    @property
    def time(self):
        return self._time

    @staticmethod
    def create_from_dataseg(seg: DataSeg, platform: str):
        """从解析好的数据段结构初始化 TaskBatchBack 对象"""
        seg: DataSeg = seg
        res = CmdFeedBack.create_from_dict(seg._fields, platform)
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
            raise Exception("Invalid initial fields dict for TaskBatchBack")

        return CmdFeedBack(
            allfields.get('clientid'),
            allfields.get('cmdid'),
            platform,
            allfields.get('state'),
            allfields.get('time'),
            allfields.get('recvmsg'),
            allfields.get('sequence'),
            allfields.get('source'),
        )

    @staticmethod
    def create_from_cmd(cmd: IdownCmd, state: ECommandStatus, recvmsg):
        """
        :param cmd:
        :param state:
        :param recvmsg:
        :return:
        """
        return CmdFeedBack(
            cmd._clientid,
            cmd.cmd_id,
            cmd.platform,
            state,
            time_=None,
            recvmsg=recvmsg,
            sequence=cmd.sequence,
            source=cmd.source)

    def __init__(
            self,
            clientid: str,
            cmdid: str,
            platform: str,
            state: ECommandStatus,
            time_: str = None,
            recvmsg: str = None,
            sequence: int = None,
            source: str = None,
    ):

        TaskBackBase.__init__(self, EStandardDataType.TaskCmdBack, platform,
                              state, recvmsg, time_)
        # OutputData.__init__(self, platform, EStandardDataType.TaskCmdBack)
        # OutputDataSeg.__init__(self)

        if not isinstance(cmdid, str):
            raise Exception("Cmdid cannot be None for CmdFeedBack")
        self.cmd_id: str = cmdid

        # if not isinstance(clientid, str):
        #     raise Exception("Clientid is required for CmdFeedBack")
        self.clientid: str = clientid

        if isinstance(sequence, str):
            sequence = int(sequence)
        elif not isinstance(sequence, int):
            raise Exception("Invalid sequence for CmdFeedBack")
        self._sequence: int = sequence
        self._source: str = source

    def get_output_segs(self) -> iter:
        """"""
        # 数据段索引，非sequence
        self.segindex = 1
        if self.owner_data is None:
            self.owner_data = self
        yield self

    def get_output_fields(self) -> dict:
        self.append_to_fields('cmdid', self.cmd_id)
        self.append_to_fields('clientid', self.clientid)
        self.append_to_fields('platform', self._platform)
        self.append_to_fields('source', self._source)
        self.append_to_fields('state', self._cmdstatus.value)
        self.append_to_fields('recvmsg', self._cmdrcvmsg)
        self.append_to_fields('time', self.time)
        self.append_to_fields('sequence', self._sequence)
        return self._fields
