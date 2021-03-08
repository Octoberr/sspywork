"""
侦查任务的字段定义
先把数据标准字段定义了
create by judy 2019/06/10
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


class EObjectType(Enum):
    """
    目标类型
    """

    # 域名
    Domain = 1
    # IP
    Ip = 2
    # 端口
    Port = 3
    # URL
    Url = 4
    # EMail
    EMail = 5
    # phone number
    PhoneNum = 6
    # 网络id
    NetworkId = 7
    # 未知99
    Unknown = 99


class IscoutTask(OutputData, OutputDataSeg):
    """IScoutTask"""

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
            return datetime.strptime(self._createtime, "%Y-%m-%d %H:%M:%S").timestamp()
        return self._createtime

    @property
    def createtimestr(self) -> str:
        """当前任务的创建时间的时间字符串"""
        if isinstance(self._createtime, float):
            return datetime.fromtimestamp(
                self._createtime, pytz.timezone("Asia/Shanghai")
            ).strftime("%Y-%m-%d %H:%M:%S")
        return self._createtime

    @staticmethod
    def create_from_dict(fieldsdict: dict, platform: str = None):
        """从字典初始化任务"""
        return IscoutTask(
            fieldsdict,
            platform,
            fieldsdict.get("status"),
            fieldsdict.get("cmdrcvmsg"),
            fieldsdict.get("clientid"),
            fieldsdict.get("taskstatus"),
            fieldsdict.get("elapsed"),
        )

    def __init__(
        self,
        iscout_dict: dict,
        platform: str = None,
        cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
        cmdrcvmsg: str = None,
        clientid: str = None,
        taskstatus: ETaskStatus = ETaskStatus.New,
        elapsed: float = 0,
    ):
        """
        iscout task 的数据结构体
        :param iscout_dict:
        :param platform:
        :param cmdstatus:
        :param cmdrcvmsg:
        :param clientid:
        :param taskstatus:
        """
        self._iscout_dict: dict = iscout_dict  # 这个字段字典存一下
        self._createtime: str = iscout_dict.get("createtime")
        if self._createtime is None:
            self._createtime = datetime.now(pytz.timezone("Asia/Shanghai")).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        self.taskid: str = iscout_dict.get("taskid", None)
        if not isinstance(self.taskid, str):
            raise Exception("IScoutTask taskid can not be None")

        # scout是有batchid的
        self.batchid: str = iscout_dict.get("batchid", None)
        if not isinstance(self.batchid, str):
            raise Exception("IScoutTask batchid can not be None")

        self._clientid: str = iscout_dict.get("clientid")
        if not isinstance(self._clientid, str):
            self._clientid = clientid

        self.source: str = iscout_dict.get("source", None)
        if not isinstance(self.source, str):
            raise Exception("IScoutTask source can not be None")

        self.periodnum: int = iscout_dict.get("periodnum", 1)
        if not isinstance(self.periodnum, int):
            self.periodnum = int(self.periodnum)

        self._objecttype: EObjectType = iscout_dict.get("objecttype", None)
        if isinstance(self._objecttype, int):
            self._objecttype = EObjectType(self._objecttype)
        else:
            self._objecttype = EObjectType(int(self._objecttype))

        # 本次查询目标
        self._object: str = iscout_dict.get("object", 99)
        if not isinstance(self._object, str):
            raise Exception("IScoutTask object can not be None")

        self.platform: str = platform
        if not isinstance(self.platform, str):
            self.platform = iscout_dict.get("platform")
        if not isinstance(self.platform, str):
            raise Exception("IScoutTask platform can not be None")

        self.taskstatus: ETaskStatus = taskstatus
        if isinstance(self.taskstatus, int):
            self.taskstatus = ETaskStatus(self.taskstatus)
        if not isinstance(self.taskstatus, ETaskStatus):
            self.taskstatus = ETaskStatus.New

        self.cmdstatus: ECommandStatus = cmdstatus
        if iscout_dict.__contains__("status"):
            self.cmdstatus = ECommandStatus(int(iscout_dict.get("status", 2)))
        if not isinstance(self.cmdstatus, ECommandStatus):
            self.cmdstatus = ECommandStatus.WaitForSend

        self.cmdrcvmsg: str = cmdrcvmsg
        tmpmsg = iscout_dict.get("cmdrcvmsg")
        if not tmpmsg is None:
            self.cmdrcvmsg = tmpmsg

        # 批量任务的子任务总数
        self.batchtotalcount: int = self._judge(iscout_dict, "batchtotalcount", 0)
        # 批量任务的已完成的任务数
        self.batchcompletecount: int = self._judge(iscout_dict, "batchcompletecount", 0)
        self.isbatchcompletecountincreased: bool = self._judge(
            iscout_dict, "isbatchcompletecountincreased", False
        )

        self.laststarttime: float = self._judge(iscout_dict, "laststarttime")
        self.lastendtime: float = self._judge(iscout_dict, "lastendtime")

        OutputData.__init__(self, self.platform, EStandardDataType.IScoutTask)
        OutputDataSeg.__init__(self)

        # 设置不是必要字段，会有默认的
        self.cmd_id = iscout_dict.get("cmdid")
        self.cmd: IdownCmd = None
        jscmd = json.dumps(cmd_dict)
        dftcmd = IdownCmd(
            jscmd, None, self._platform, self.source, None, self.cmdstatus
        )
        if self.cmd_id is not None:
            _cmd_str = iscout_dict.get("cmd")
            if _cmd_str is None:
                raise Exception("IscanTask get cmdid,but cmd is None")
            self.cmd = IdownCmd(
                _cmd_str,
                self.cmd_id,
                self.platform,
                self.source,
                self._clientid,
                ECommandStatus.WaitForSend,
            )
            self.cmd.fill_defcmd(dftcmd)
        else:
            self.cmd = dftcmd

        self._is_period: bool = False
        if not self.cmd is None and not self.cmd.stratagy is None:
            if self.cmd.stratagy.circulation_mode == 2:
                self._is_period = True

        # 每次初始化的时候赋值，这个值会存入数据库，有外部保持增长
        self._sequence = iscout_dict.get("sequence", 0)
        self.__sequencelocker = threading.RLock()
        # 当次循环的扫描进度,每次刚开始执行的时候初始化为0.0，后面使用时自行赋值
        # 任务进度信息
        # 当Task作为子任务时，有progress字段
        # 当Task作为总任务时，progress通过计算得到
        self._progress: float = self._judge(iscout_dict, "progress", dft=0, error=False)

        self._time = datetime.now(pytz.timezone("Asia/Shanghai")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # 通用回调函数
        self.on_complete = self._on_complete

        # ------------------------------------------新增可能会用到的参数
        # client下载会在cmd里面拿一个priority，默认为2，初始化的时候用初始化的值即可
        self.priority = 2
        # 新增循环下载需要的字段，初始化
        self.lastexecutetime = iscout_dict.get("lastexecutetime")

        # 新增查询层数,所有的任务第一次都是1， 从1开始，便于阅读
        # modify by swm 2019/09/29，由任务提供start_level，由任务指定当前的级数
        self.rec_level = self.cmd.stratagyscout.start_level
        # 新增一个字段，需要用来计算任务消耗了多少时间
        self.taskstarttime: float = iscout_dict.get(
            "taskstarttime", datetime.now(pytz.timezone("Asia/Shanghai")).timestamp()
        )

        # server端需要合并统计所有子任务的总计耗时
        self.elapsed: float = 0
        if elapsed == 0:
            elapsed = iscout_dict.get("elapsed")
        if not elapsed is None and type(elapsed) in [int, float] and elapsed > 0:
            self.elapsed = elapsed
        elif isinstance(elapsed, str):
            try:
                tmp = float(elapsed)
                self.elapsed = float(tmp)
            except Exception:
                pass
        # 新增任务失败状态
        # 新增成功次数和失败次数的统计
        self.failtimes = iscout_dict.get("failtimes", 0)
        self.successtimes = iscout_dict.get("successtimes", 0)
        # 两个字典，用于记录某插件成功和失败次数是否已在本次任务中添加
        # tag: 表示某个插件的唯一标识
        # 数据结构为： <tag+level, True/False>
        self._success_tags: dict = {}
        self._success_tags_locker = threading.RLock()
        self._failed_tags: dict = {}
        self._failed_tags_locker = threading.RLock()

    # 对象之间按照优先级排序
    def __lt__(self, other):
        return int(self.priority) > int(other.priority)

    def success_count(self, tag: str = None, level: int = -1):
        """一个插件的成功数量加1\n
        由于整个task要看它是否成功，需要具体到每个插件是否有成功执行的，\n
        成功执行不代表一定有数据产生，\n
        但成功执行则表示整个任务都算作成功（只要有成功的就算成功）\n
        填了tag就必须填level，为了保证区分每个递归级数的成功失败次数，\n
        且在同一level下一个tag的成功失败次数只能被增加一次"""
        # 没填tag的情况
        if tag is None or tag == "":
            self.successtimes += 1
            return
        # 填了tag的情况
        if level < 0:
            raise Exception(
                "Invalid level for increasing successtimes statistics: tag={}".format(
                    tag
                )
            )
        key: str = "{}{}".format(tag, level)
        if self._success_tags.__contains__(key) and self._success_tags[key] == True:
            return
        with self._success_tags_locker:
            if self._success_tags.__contains__(key) and self._success_tags[key] == True:
                return
            self.successtimes += 1
            self._success_tags[key] = True

    def fail_count(self, tag: str = None, level: int = -1):
        """一个插件的失败数量加1\n
        由于整个task要看它是否成功，需要具体到每个插件是否有成功执行的，\n
        成功执行不代表一定有数据产生，\n
        但成功执行则表示整个任务都算作成功（只要有成功的就算成功）\n
        填了tag就必须填level，为了保证区分每个递归级数的成功失败次数，\n
        且在同一level下一个tag的成功失败次数只能被增加一次"""
        # 没填tag的情况
        if tag is None or tag == "":
            self.failtimes += 1
            return
        # 填了tag的情况
        if level < 0:
            raise Exception(
                "Invalid level for increasing failtimes statistics: tag={}".format(tag)
            )
        key: str = "{}{}".format(tag, level)
        if self._failed_tags.__contains__(key) and self._failed_tags[key] == True:
            return
        with self._failed_tags_locker:
            if self._failed_tags.__contains__(key) and self._failed_tags[key] == True:
                return
            self.failtimes += 1
            self._failed_tags[key] = True

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
        self.append_to_fields("createtime", self.createtimestr)
        self.append_to_fields("taskid", self.taskid)
        self.append_to_fields("batchid", self.batchid)
        self.append_to_fields("periodnum", self.periodnum)
        self.append_to_fields("source", self.source)
        self.append_to_fields("objecttype", self._objecttype.value)
        self.append_to_fields("object", self._object)
        if isinstance(self.cmd_id, str):
            self.append_to_fields("cmdid", self.cmd_id)
        if isinstance(self.cmd, IdownCmd):
            self.append_to_fields("cmd", self.cmd.cmd_str)
        return self._fields
