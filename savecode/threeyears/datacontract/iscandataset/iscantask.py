"""
Iscan的task
目前先不
by judy 2019/06/12
"""
import json
import threading
from datetime import datetime
from enum import Enum

import pytz

from ..ecommandstatus import ECommandStatus
from ..etaskstatus import ETaskStatus
from ..idowncmd import IdownCmd
from ..idowncmd.cmd_policy_default import cmd_dict
from ..outputdata import EStandardDataType, OutputData, OutputDataSeg


class EScanType(Enum):
    """
    标识扫描类型
    """
    # 扫描搜索
    ScanSearch = 1
    # 扫描
    Scan = 2


class IscanTask(OutputData, OutputDataSeg):
    """扫描任务"""

    @property
    def sequence(self):
        """
        文件顺序，每次调用自增1
        :return:
        """
        with self.__sequencelocker:
            self._sequence = self._sequence + 1

        return self._sequence

    @property
    def time_now(self):
        """
        当前东8区的时间
        :return:
        """
        return self._time

    @property
    def createtime(self) -> float:
        """当前任务的创建时间的时间戳，float"""
        if isinstance(self._createtime, str):
            return datetime.strptime(self._createtime,
                                     '%Y-%m-%d %H:%M:%S').timestamp()
        return self._createtime

    @property
    def createtimestr(self) -> str:
        """当前任务的创建时间的时间字符串"""
        if isinstance(self._createtime, float):
            return datetime.fromtimestamp(
                self._createtime,
                pytz.timezone('Asia/Shanghai')).strftime("%Y-%m-%d %H:%M:%S")
        return self._createtime

    @staticmethod
    def parse_from_dict(
            fields: dict,
            platform: str,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
            cmdrcvmsg: str = None,
            clientid: str = None,
    ):
        return IscanTask(fields, platform, cmdstatus, cmdrcvmsg, clientid)

    def __init__(self,
                 iscan_dict: dict,
                 platform: str = None,
                 cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
                 cmdrcvmsg: str = None,
                 clientid: str = None):

        # 这个时间不是我们自己拿到的，是任务给过来的
        self._createtime: str = iscan_dict.get('createtime')
        if self._createtime is None:
            raise Exception('Iscan createtime cant be None')

        self.taskid: str = iscan_dict.get('taskid')
        if self.taskid is None:
            raise Exception('Iscan taskid cant be None')

        # iscan现在没有batchid
        self.batchid = iscan_dict.get('batchid')
        # 循环次数,初始化的时候是0，每次执行的时候加1，并且结果会保存到数据库
        self.batchindex = 0

        self._clientid: str = iscan_dict.get('clientid')
        if not isinstance(self._clientid, str):
            self._clientid = clientid

        self.source = iscan_dict.get('source')
        if self.source is None:
            raise Exception('Iscan source cant be None')

        self.periodnum: int = iscan_dict.get('periodnum', 1)
        if not isinstance(self.periodnum, int):
            self.periodnum = int(self.periodnum)

        _scantype = iscan_dict.get('scantype')
        if _scantype is None:
            raise Exception('Iscan scantype cant be None')
        self.scantype: EScanType = EScanType(int(_scantype))

        self.platform = platform
        if not isinstance(self.platform, str):
            self.platform = iscan_dict.get('platform')

        self.cmdstatus: ECommandStatus = cmdstatus
        tmpstatus = iscan_dict.get('status')
        if not tmpstatus is None:
            self.cmdstatus = ECommandStatus(int(tmpstatus))

        self.cmdrcvmsg: str = cmdrcvmsg
        tmpmsg = iscan_dict.get('cmdrcvmsg')
        if not tmpmsg is None:
            self.cmdrcvmsg = tmpmsg

        self.laststarttime: str = self._judge(iscan_dict, "laststarttime")
        self.lastendtime: str = self._judge(iscan_dict, "lastendtime")

        OutputData.__init__(self, self.platform, EStandardDataType.IScanTask)
        OutputDataSeg.__init__(self)

        # 设置不是必要字段，会有默认的
        self.cmd_id = iscan_dict.get('cmdid')
        self.cmd: IdownCmd = None
        jscmd = json.dumps(cmd_dict)  # ["stratagy"]
        dftcmd = IdownCmd(jscmd, None, self._platform, self.source, None, self.cmdstatus)
        if self.cmd_id is not None:
            _cmd_str = iscan_dict.get('cmd')
            if _cmd_str is None:
                raise Exception('IscanTask get cmdid, but cmd is None')
            self.cmd = IdownCmd(_cmd_str, self.cmd_id, self.platform,
                                self.source, self._clientid,
                                ECommandStatus.WaitForSend)
            self.cmd.fill_defcmd(dftcmd)
        else:
            self.cmd = dftcmd

        self._is_period: bool = False
        if not self.cmd is None and not self.cmd.stratagy is None:
            if self.cmd.stratagy.circulation_mode == 2:
                self._is_period = True

        # 每次初始化的时候赋值，这个值会存入数据库，有外部保持增长
        self._sequence = iscan_dict.get('sequence', 0)
        self.__sequencelocker = threading.RLock()
        # 当次循环的扫描进度,每次刚开始执行的时候初始化为0.0，后面使用时自行赋值
        self.progress: float = 0.0

        self._time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        # 通用回调函数
        self.on_complete = self._on_complete
        # -----------------------------------新增可能会用到的循环任务字段
        self.taskstatus: ETaskStatus = ETaskStatus(int(iscan_dict.get('taskstatus', ETaskStatus.New.value)))
        # 会在cmd里面拿一个priority，默认为2
        self.priority = 2
        # self.lastexecutetime = None
        # self.failtimes = None
        # self.successtimes = None
        self.taskstarttime: float = iscan_dict.get('taskstarttime', datetime.now(pytz.timezone('Asia/Shanghai')).timestamp())
        # 新增两个字段，用于下载国家数据的时候记录下载地址使用
        self.query_date = iscan_dict.get('query_date')
        # 这个数据初始化可以为1
        self.query_page = iscan_dict.get('query_page', 1)
        if isinstance(self.query_page, str):
            self.query_page = int(self.query_page)

    # 对象之间按照优先级排序
    def __lt__(self, other):
        return int(self.priority) > int(other.priority)

    def _on_complete(self, task):
        """任务处理完毕的回调"""
        pass

    def has_stream(self) -> bool:
        return False

    def get_stream(self):
        return None

    def get_output_segs(self) -> iter:
        """"""
        self.segindex = 1
        if self.owner_data is None:
            self.owner_data = self
        yield self

    def get_output_fields(self) -> dict:
        self.append_to_fields("platform", self._platform)
        self.append_to_fields("taskid", self.taskid)
        self.append_to_fields("source", self.source)
        self.append_to_fields("scantype", self.scantype.value)
        self.append_to_fields('periodnum', self.periodnum)
        self.append_to_fields('createtime', self.createtimestr)
        if isinstance(self.cmd_id, str):
            self.append_to_fields("cmdid", self.cmd_id)
        if isinstance(self.cmd, IdownCmd):
            self.append_to_fields("cmd", self.cmd.cmd_str)
        if type(self.progress) in [int, float] and self.progress > 0:
            self.append_to_fields('progress', self.progress)
        return self._fields

    def __repr__(self):
        return "{}".format(self.cmd_id)
