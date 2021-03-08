"""
automated task
由server控制下载
create by judy 2019/07/27
"""
import json
import math
import threading
from datetime import datetime
from enum import Enum

import pytz
from commonbaby.helpers import helper_time

from ..ecommandstatus import ECommandStatus
from ..etaskstatus import ETaskStatus
from ..idowncmd import IdownCmd
from ..idowncmd.cmd_policy_default import cmd_dict
from ..outputdata import EStandardDataType, OutputData, OutputDataSeg


class EAutoType(Enum):
    """
    EXPDB=1
    DBIP=2
    """

    EXPDB = 1
    DBIP = 2
    GEONAME = 3


class AutomatedTask(OutputData, OutputDataSeg):
    """"""

    @property
    def progress(self) -> float:
        """当前总/子任务的进度"""
        return self._progress

    @progress.setter
    def progress(self, value):
        """当前总/子任务的进度"""
        if value is None:
            return
        self._progress = value

    @property
    def sequence(self):
        """
        文件顺序，每次调用自增1
        :return:
        """
        with self.__sequencelocker:
            self._sequence = self._sequence + 1

        return self._sequence

    def sequence_set(self, seq: int):
        """用于当需要从数据库中取出总任务的sequence时使用"""
        if not isinstance(seq, int) or seq < 0:
            return
        with self.__sequencelocker:
            self._sequence = seq

    def sequence_reset(self):
        """将当前Task的sequence重试为0"""
        with self.__sequencelocker:
            self._sequence = 0

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
            return datetime.strptime(self._createtime, '%Y-%m-%d %H:%M:%S').timestamp()
        return self._createtime

    @property
    def createtimestr(self) -> str:
        """当前任务的创建时间的时间字符串"""
        if isinstance(self._createtime, float):
            return datetime.fromtimestamp(
                self._createtime).strftime("%Y-%m-%d %H:%M:%S")
        return self._createtime

    @staticmethod
    def create_from_dict(fieldsdict: dict, platform: str = None):
        """从字典初始化任务"""
        return AutomatedTask(
            fieldsdict,
            int(fieldsdict.get('autotasktype')),
            platform,
            fieldsdict.get('status'),
            fieldsdict.get('cmdrcvmsg'),
            fieldsdict.get('clientid'),
            fieldsdict.get('taskstatus'),
        )

    def __init__(
            self,
            auto_dict: dict,
            autotasktype: EAutoType,
            platform: str = None,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
            cmdrcvmsg: str = None,
            clientid: str = None,
            taskstatus: ETaskStatus = ETaskStatus.New,
    ):
        """
        auto task 的数据结构体
        :param auto_dict:
        :param platform:
        :param cmdstatus:
        :param cmdrcvmsg:
        :param clientid:
        :param taskstatus:
        """
        self._auto_dict: dict = auto_dict  # 这个字段字典存一下
        self._createtime: str = auto_dict.get('createtime')
        if self._createtime is None:
            self._createtime = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

        self.taskid: str = auto_dict.get('taskid', None)
        if not isinstance(self.taskid, str):
            raise Exception('Automatedtask taskid can not be None')

        self.batchid: str = auto_dict.get('batchid', None)
        if not isinstance(self.batchid, str):
            raise Exception('Automatedtask batchid can not be None')

        self._clientid: str = auto_dict.get('clientid')
        if not isinstance(self._clientid, str):
            self._clientid = clientid

        self.source: str = auto_dict.get('source', None)
        if not isinstance(self.source, str):
            raise Exception('Automatedtask source can not be None')

        self.periodnum: int = auto_dict.get('periodnum', 1)
        if not isinstance(self.periodnum, int):
            self.periodnum = int(self.periodnum)

        self.autotasktype: EAutoType = autotasktype
        if isinstance(self.autotasktype, int):
            self.autotasktype = EAutoType(self.autotasktype)

        self.platform: str = platform
        if not isinstance(self.platform, str):
            self.platform = auto_dict.get('platform')
        if not isinstance(self.platform, str):
            raise Exception('Automatedtask platform can not be None')

        self.taskstatus: ETaskStatus = taskstatus
        if isinstance(self.taskstatus, int):
            self.taskstatus = ETaskStatus(self.taskstatus)
        if not isinstance(self.taskstatus, ETaskStatus):
            self.taskstatus = ETaskStatus.New

        self.cmdstatus: ECommandStatus = cmdstatus
        if auto_dict.__contains__('status'):
            self.cmdstatus = ECommandStatus(int(auto_dict.get('status', 2)))
        if not isinstance(self.cmdstatus, ECommandStatus):
            self.cmdstatus = ECommandStatus.WaitForSend

        self.cmdrcvmsg: str = cmdrcvmsg

        # 批量任务的子任务总数
        self.batchtotalcount: int = self._judge(auto_dict, "batchtotalcount",
                                                0)
        # 批量任务的已完成的任务数
        self.batchcompletecount: int = self._judge(auto_dict,
                                                   "batchcompletecount", 0)
        self.isbatchcompletecountincreased: bool = self._judge(
            auto_dict, "isbatchcompletecountincreased", False)

        self.lastendtime: str = self._judge(auto_dict, "lastendtime")
        self.laststarttime: str = self._judge(auto_dict, 'laststarttime')

        OutputData.__init__(self, self.platform, EStandardDataType.Autotask)
        OutputDataSeg.__init__(self)

        # 设置不是必要字段，会有默认的
        self.cmd_id = auto_dict.get('cmdid')
        self.cmd: IdownCmd = None
        jscmd = json.dumps(cmd_dict)  #["stratagy"]
        dftcmd = IdownCmd(jscmd, None, self._platform, self.source, None,
                          self.cmdstatus)
        if self.cmd_id is not None:
            _cmd_str = auto_dict.get('cmd')
            if _cmd_str is None:
                raise Exception('Automated get cmdid,but cmd is None')
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
        self._sequence = auto_dict.get('sequence', 0)
        self.__sequencelocker = threading.RLock()
        # 当次循环的扫描进度,每次刚开始执行的时候初始化为0.0，后面使用时自行赋值
        # 任务进度信息
        # 当Task作为子任务时，有progress字段
        # 当Task作为总任务时，progress通过计算得到
        self._progress: float = self._judge(
            auto_dict, 'progress', dft=0, error=False)

        self._time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

        # 通用回调函数
        self.on_complete = self._on_complete

        # ------------------------------------------新增可能会用到的参数
        # client下载会在cmd里面拿一个priority，默认为2，初始化的时候用初始化的值即可
        self.priority = 2

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
        if isinstance(self.source, str) and not self.source == "":
            self.append_to_fields("source", self.source)
        self.append_to_fields('periodnum', self.periodnum)
        self.append_to_fields("taskid", self.taskid)
        self.append_to_fields("batchid", self.batchid)
        self.append_to_fields("autotasktype", self.autotasktype.value)
        self.append_to_fields('createtime', self.createtimestr)
        if isinstance(self.cmd_id, str):
            self.append_to_fields("cmdid", self.cmd_id)
        if isinstance(self.cmd, IdownCmd):
            self.append_to_fields("cmd", self.cmd.cmd_str)
        return self._fields
