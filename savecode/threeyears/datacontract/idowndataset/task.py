"""
universal Task structure
增加了一个强制下载的字段forcedownload
by judy 2019/03/22

update by judy 2019/05/14
增加一个中途被停止的任务状态，当启动时会重新开始下载
"""

import json
import threading
import uuid
from datetime import datetime
from enum import Enum

import pytz
from commonbaby.helpers import helper_str, helper_time

from ..ecommandstatus import ECommandStatus
from ..etaskstatus import ETaskStatus
from ..idowncmd import IdownCmd
from ..outputdata import EStandardDataType, OutputData, OutputDataSeg


class ETaskType(Enum):
    """任务类型枚举"""

    LoginOnly = 1  # 仅登陆
    LoginDownload = 2  # 登陆并使用指定的Token下载数据
    CheckOnline = 3  # 查询账号是否在线，结果带在TaskBack中返回
    CheckRegistration = 4  # 查询某个账号注册了哪些app
    LoginTest = 5  # 批量测试账号是否能登陆成功
    Logout = 6  # 退出登录
    Input = 10  # 交互（验证码）


class ETokenType(Enum):
    """登陆令牌/资源类型"""

    NotNeed = -1  # 不需要Token
    Unknown = 0  # 未指定
    Sms = 1  # 短信
    Pwd = 2  # 账密
    SmsPwd = 3  # 账密+短信
    Cookie = 4


class Task(OutputData, OutputDataSeg):
    """统一的'任务'数据结构，表示一个任务。\n
    allfields: 用于初始化当前Task的所有字段的集合（需要把键全部转成小写的）\n
    """

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        if type(value) is str:
            self._time: float = datetime.now(pytz.timezone("Asia/Shanghai")).timestamp()
        elif not type(value) in [float, int]:
            raise Exception("Invalid time when initial %s" % self.__class__)

    @property
    def other_fields_json(self) -> str:
        """返回其他字段字典json，若无其他字段则返回None"""
        if isinstance(self._other_fields, dict) and len(self._other_fields) > 0:
            return json.dumps(self._other_fields)
        return None

    @property
    def cmdstatus(self) -> ECommandStatus:
        """当前任务的命令状态"""
        return self._cmdstatus

    @cmdstatus.setter
    def cmdstatus(self, value):
        """当前任务的命令状态"""
        if not isinstance(value, ECommandStatus):
            raise Exception("Invalid value for {}".format(type(self._cmdstatus)))
        self._cmdstatus = value

    @property
    def cmdrcvmsg(self) -> str:
        """当前任务的命令回馈描述信息"""
        return self._cmdrcvmsg

    @cmdrcvmsg.setter
    def cmdrcvmsg(self, value):
        """当前任务的命令回馈描述信息"""
        self._cmdrcvmsg = value

    @property
    def progress(self) -> float:
        """当前总/子任务的进度"""
        return self._progress
        # if not self._progress is None and self._progress > 0:
        #     return self._progress
        # if self.batchtotalcount == 0:
        #     return 0
        # else:
        #     return self.batchcompletecount / self.batchtotalcount

    @progress.setter
    def progress(self, value):
        """当前总/子任务的进度"""
        if value is None:
            return
        self._progress = value

    @property
    def forcedownload(self):
        """指示是否强制下载所有数据"""
        # 这里与数据确定了是True 191219
        if (
            self._forcedownload is True
            or self._forcedownload == "True"
            or self._forcedownload == "1"
            or self._forcedownload == 1
        ):
            return True
        else:
            return False

    def __init__(self, allfields: dict):
        """使用必要值实例化一个Task任务对象"""
        if not isinstance(allfields, dict) or len(allfields) < 1:
            raise Exception("Task initial fields is invalid")

        # 所有字段集合(包括数据中带过来的其他需要回传的字段)
        # 输出数据时根据所属平台，需要输出的额外字段，都在这里面来找
        # 比如：有一个邮件数据EMail，输出到某个标准时需要一个casenode字段
        # 这个字段直接在 EMail.Task._allfields.get("casenode")里找
        # 统一使用self._judge()，不使用allfields.get()
        self._allfields: dict = allfields

        # 若allfields是从数据库读出来，则含有otherfields的json字符串，需要
        # 解析并添加到allfields中，方便下面解析字段
        # 指示是否强制使用指定的tokentype进行登陆。
        tmpotherstr = self._judge(allfields, "otherfields")
        self._parse_otherfields(tmpotherstr)
        # self._other_fields.pop("otherfields", None)

        # 其他字段，用于存储除以下标准字段以外的，带在数据文件里的其他字段
        # 在 self._judge()方法中会自动剔除标准字段
        self._other_fields: dict = allfields.copy()

        # 当前数据产生时间，必要，默认的时间都改成东8区
        self._time: float = datetime.now(pytz.timezone("Asia/Shanghai")).timestamp()

        # 这个platform不知道哪些地方在用，先留着
        self.platform: str = self._judge(
            allfields, "platform", error=True, excludefields=self._other_fields
        )
        self._source: str = self._judge(
            allfields, "source", error=False, excludefields=self._other_fields
        )

        OutputData.__init__(self, self.platform, EStandardDataType.Task)
        OutputDataSeg.__init__(self)

        # 必要字段(数据标准字段)
        self.taskid: str = self._judge(
            allfields, "taskid", error=True, excludefields=self._other_fields
        )
        # 子任务id，对控制端为非必要，对采集端为必要
        self.batchid: str = self._judge(
            allfields, "batchid", dft="", error=False, excludefields=self._other_fields
        )
        # 登陆令牌tokenid，需要与界面同步。也方便后面做单机版
        self.tokenid: str = self._judge(
            allfields,
            "tokenid",
            # 这个字段没有的，说明不是中心下发的任务，就要随机一个tokenid
            # 且在解析时就判断了如果是中心下发的任务，若无此字段，就会报错
            dft=str(uuid.uuid1()),
            error=False,
            excludefields=self._other_fields,
        )
        # 非必要字段(数据标准字段)
        # 关联任务的taskid
        self.parenttaskid: str = self._judge(
            allfields, "parenttaskid", excludefields=self._other_fields
        )
        # 关联的父子任务
        self.parentbatchid: str = self._judge(
            allfields, "parentbatchid", excludefields=self._other_fields
        )
        # 状态字段 (非数据标准字段)
        self.taskstatus: ETaskStatus = ETaskStatus(
            int(
                self._judge(
                    allfields,
                    "taskstatus",
                    ETaskStatus.New.value,
                    excludefields=self._other_fields,
                )
            )
        )  # 任务当前状态
        # 批量任务的子任务总数
        self.batchtotalcount: int = self._judge(
            allfields, "batchtotalcount", 0, excludefields=self._other_fields
        )
        # 批量任务的已完成的任务数
        self.batchcompletecount: int = self._judge(
            allfields, "batchcompletecount", 0, excludefields=self._other_fields
        )
        self.isbatchcompletecountincreased: bool = self._judge(
            allfields,
            "isbatchcompletecountincreased",
            False,
            excludefields=self._other_fields,
        )
        # 任务类型
        self.tasktype: ETaskType = ETaskType(
            int(
                self._judge(
                    allfields, "tasktype", error=True, excludefields=self._other_fields
                )
            )
        )
        # 登陆资源/令牌类型
        self.tokentype: ETokenType = ETokenType(
            int(
                self._judge(
                    allfields,
                    "tokentype",
                    dft=ETokenType.Unknown.value,
                    error=False,
                    excludefields=self._other_fields,
                )
            )
        )
        # 必须有apptype，因为任务文件在server解出来，
        # 就是一个一个的子任务了
        self.apptype: int = int(
            self._judge(
                allfields,
                "apptype",
                dft=0,
                error=False,
                excludefields=self._other_fields,
            )
        )
        # 交互输入（验证码等）
        self.input: str = self._judge(
            allfields, "input", excludefields=self._other_fields
        )
        # 内部预置国际号码标识
        self.preglobaltelcode: str = self._judge(
            allfields, "preglobaltelcode", excludefields=self._other_fields
        )
        # 内部预置账号
        self.preaccount: str = self._judge(
            allfields, "preaccount", excludefields=self._other_fields
        )
        # 资源字段(数据标准字段)
        self.globaltelcode: str = self._judge(
            allfields, "globaltelcode", excludefields=self._other_fields
        )
        self.phone: str = self._judge(
            allfields, "phone", excludefields=self._other_fields
        )
        self.account: str = self._judge(
            allfields, "account", excludefields=self._other_fields
        )
        self.password: str = self._judge(
            allfields, "password", excludefields=self._other_fields
        )
        self.url: str = self._judge(allfields, "url", excludefields=self._other_fields)
        self.host: str = self._judge(
            allfields, "host", excludefields=self._other_fields
        )
        self.cookie: str = self._judge(
            allfields, "cookie", excludefields=self._other_fields
        )

        # 新加字段，是否强制下载
        self._forcedownload: str = self._judge(
            allfields, "forcedownload", dft=False, excludefields=self._other_fields
        )

        # 任务文件过来时的时间，时间戳转化一下
        self.timestr: str = None  # 日期时间格式字符串
        if self.time is not None and type(self.time) in [int, float]:
            self.timestr = datetime.fromtimestamp(
                self.time, pytz.timezone("Asia/Shanghai")
            ).strftime("%Y-%m-%d %H:%M:%S")
        if self.timestr is None:
            self.timestr = helper_time.get_time_sec_tz()
        # 这里新任务来了应该是没有time字段的
        if self._allfields.__contains__("time"):
            self._allfields["time"] = self.timestr

        # 任务回馈相关字段，在TaskBack类型中实现
        # 这两个时间，应该是写入数据库当时，获取的当前时间，而不是从任务文件里来的
        self.createtime = self._judge(
            allfields,
            "createtime",
            dft=int(self._time),
            excludefields=self._other_fields,
        )
        self.updatetime = self._judge(
            allfields, "updatetime", excludefields=self._other_fields
        )

        # 任务进度信息
        # 当Task作为子任务时，有progress字段
        # 当Task作为总任务时，progress通过计算得到
        self._progress: float = self._judge(
            allfields, "progress", dft=0, error=False, excludefields=self._other_fields
        )

        self.forcetokentype: bool = False

        # 控制端独有
        self.deal_succeed: bool = None  # 标记当前任务是否分配完成

        # 采集端独有
        self.lastexecutetime = self._judge(
            allfields, "lastexecutetime", excludefields=self._other_fields
        )  # 最后访问时间, unxitime需要什么类型自己转
        self.failtimes = self._judge(
            allfields, "failtimes", 0, excludefields=self._other_fields
        )
        self.successtimes = self._judge(
            allfields, "successtimes", 0, excludefields=self._other_fields
        )

        # 当任务从数据库中读出来时，会带有TaskBack数据的部分字段，需要读取出来，以免被
        # 算入self._other_fields里
        self._clientid: str = self._judge(
            allfields, "clientid", excludefields=self._other_fields
        )
        self._cmdstatus: ECommandStatus = ECommandStatus(
            int(
                self._judge(
                    allfields,
                    "cmdstatus",
                    dft=ECommandStatus.WaitForSend.value,
                    error=False,
                    excludefields=self._other_fields,
                )
            )
        )
        self._cmdrcvmsg: str = self._judge(
            allfields, "cmdrcvmsg", excludefields=self._other_fields
        )
        self._result: str = self._judge(
            allfields, "result", excludefields=self._other_fields
        )
        # tgback文件sequence, 用于回馈数据的文件顺序，要存入数据库
        self._sequence: int = self._judge(
            allfields, "sequence", 0, excludefields=self._other_fields
        )
        self._sequence_locker = threading.RLock()

        # 通用回调函数
        self.on_complete = self._on_complete
        # 新增source, 任务来源，需要带回去
        self.source = self._judge(
            allfields, "source", self._platform, excludefields=self._other_fields
        )
        self.casenode: str = self._judge(
            allfields, "casenode", error=False, excludefields=self._other_fields
        )
        # cmd_id会带在task里
        self.cmd_id = self._judge(
            allfields, "cmdid", None, excludefields=self._other_fields
        )
        self.cmd: IdownCmd = None
        # 会在cmd里面拿一个优先级，这里先定义着
        self.priority = 2
        self.cmdstr = self._judge(
            allfields, "cmd", None, excludefields=self._other_fields
        )
        if self.cmdstr is not None:
            # 任务的命令设置，如果有cmd的话那么会直接补齐使用，如果没有的话那么会使用默认的
            self.cmd = IdownCmd(
                self.cmdstr, self.cmd_id, self.platform, self._source, self._clientid
            )
        # 新增cookie保活状态和上次cookie保活时间
        # 0为失效，1为有效
        self.cookie_alive = self._judge(
            allfields, "cookiealive", None, excludefields=self._other_fields
        )
        self.cookie_last_keep_alive_time = self._judge(
            allfields, "cookielastkeeptime", None, excludefields=self._other_fields
        )

    # 对象之间按照优先级排序
    def __lt__(self, other):
        return int(self.priority) > int(other.priority)

    @property
    def sequence(self):
        with self._sequence_locker:
            self._sequence += 1
        return self._sequence

    def sequence_reset(self):
        """将当前Task的sequence重试为0"""
        with self._sequence_locker:
            self._sequence = 0

    def _on_complete(self, task):
        """任务处理完毕的回调"""
        pass

    def _parse_otherfields(self, ojs):
        if helper_str.is_none_or_empty(ojs):
            return
        try:
            js = json.loads(ojs)
            if js is None:
                return
            for key in js:
                # self._other_fields[key] = js[key]
                self._allfields[key] = js[key]

        except Exception as ex:
            print(ex)

    def get_real_tokentype(self) -> ETokenType:
        """根据tasktype,tokentype,forcetokentype，以及
        各资源字段url,host,cookie,account,password等判断真实的
        tokentype并返回。若是不需要token的任务类型，则返回
        ETokenType.NoNeed，若未能查询到任何可用token，则返回
        ETokenType.Unknown，若成功找到token，则返回对应的
        ETokenType值。"""
        res: ETokenType = ETokenType.NotNeed

        # 不需要令牌的任务类型
        if (
            self.tasktype == ETaskType.CheckOnline
            or self.tasktype == ETaskType.CheckRegistration
            or self.tasktype == ETaskType.Input
            or self.tasktype == ETaskType.Logout
        ):
            return res
        # 剩下的都是需要令牌的任务类型
        elif (
            self.tasktype == ETaskType.LoginOnly
            or self.tasktype == ETaskType.LoginDownload
            or self.tasktype == ETaskType.LoginTest
        ):

            res = self.__check_real_token()
            # 更新原有tokentype
            if (
                not res == ETokenType.Unknown
                and self.tokentype == ETokenType.Unknown
                and not self.forcetokentype
            ):
                self.tokentype = res
            self._allfields["tokentype"] = self.tokentype.value

        # 不认识的任务类型
        else:
            res = ETokenType.Unknown

        return res

    def __check_real_token(self) -> ETokenType:
        """检查真实tokentype并返回，找不到则返回ETokenType.Unknown"""
        if (
            self.tokentype != ETokenType.Unknown
            and self.tokentype != ETokenType.NotNeed
            and self.forcetokentype
        ):
            return self.tokentype

        res: ETokenType = ETokenType.Unknown
        # 从上到下按优先级排列任务资源

        # Cookie
        if not helper_str.is_none_or_empty(self.cookie):
            res = ETokenType.Cookie
        # 账密登陆
        elif not helper_str.is_none_or_empty(
            self.account
        ) and not helper_str.is_none_or_empty(self.password):
            if helper_str.is_none_or_empty(self.globaltelcode):
                res = ETokenType.Pwd
            else:
                res = ETokenType.SmsPwd
        # 短信
        elif not helper_str.is_none_or_empty(
            self.globaltelcode
        ) and not helper_str.is_none_or_empty(self.phone):
            res = ETokenType.Sms
        return res

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

    def get_output_fields(self) -> iter:
        """"""
        self.append_to_fields("platform", self._platform)
        self.append_to_fields("taskid", self.taskid)
        self.append_to_fields("tokenid", self.tokenid)
        self.append_to_fields("parenttaskid", self.parenttaskid)
        self.append_to_fields("batchid", self.batchid)
        self.append_to_fields("parentbatchid", self.parentbatchid)
        self.append_to_fields("progress", self.progress)
        self.append_to_fields("tasktype", self.tasktype.value)
        self.append_to_fields("tokentype", self.tokentype.value)
        self.append_to_fields("apptype", self.apptype)
        self.append_to_fields("forcedownload", self.forcedownload)
        self.append_to_fields("input", self.input)
        self.append_to_fields("preaccount", self.preaccount)
        self.append_to_fields("preglobaltelcode", self.preglobaltelcode)
        self.append_to_fields("globaltelcode", self.globaltelcode)
        self.append_to_fields("phone", self.phone)
        # 不是短信登陆才输出account
        if self.tokentype != ETokenType.Sms and self.tokentype != ETokenType.SmsPwd:
            self.append_to_fields("account", self.account)
        self.append_to_fields("password", self.password)
        self.append_to_fields("url", self.url)
        self.append_to_fields("host", self.host)
        self.append_to_fields("cookie", self.cookie)
        # 新增source
        self.append_to_fields("source", self.source)
        if not self.cmd_id is None:
            self.append_to_fields("cmdid", self.cmd_id)
        if not self.cmd is None:
            self.append_to_fields("cmd", self.cmd.cmd_str)
        return self._fields

    def __repr__(self):
        return "{} {}".format(self.taskid, self.tasktype.name)
