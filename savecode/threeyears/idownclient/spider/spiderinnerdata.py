"""
这个文件存在的理由是因为spiderbase太大了
spiderbase既有对内的接口也有对外的接口
这里存放spiderbase一些对内的东西，
然后对外的流程就放在spiderbase
create by judy 2019/04/23
"""
import time
import traceback
from abc import ABCMeta, abstractmethod

from commonbaby.httpaccess.httpaccess import HttpAccess
from commonbaby.mslog import MsLogger, MsLogManager

# from datacontract import ETaskStatus, ETokenType, TaskBatchBack  # Task,
from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowncmd import IdownCmd
from datacontract.idowndataset.datafeedback import TaskBatchBack
from datacontract.idowndataset.task import ETaskStatus, ETokenType, Task
from idownclient.clientdatafeedback import ClientLog, FeedDataBase, UserStatus
from idownclient.clientdbmanager import DbManager
from outputmanagement import OutputManagement

from .appcfg import AppCfg


class SpiderInnerData(object):
    __metaclass = ABCMeta

    @property
    def phone_combined(self) -> str:
        """返回 国际区号（若有）+电话号码"""
        if not isinstance(self._phone, str) or self._phone == "":
            return self._phone
        res = self._phone
        if isinstance(self._globaltelcode, str) and self._globaltelcode != "":
            res = self._globaltelcode + self._phone
        return res

    @property
    def uname_str(self):
        """返回当前task对应的 phone/account/username
        的其中一个（哪个有反哪个），或返回 None"""
        # 为了尽量避免出现在使用不同令牌资源进行登陆后获取到的用户账号不一致的情况，
        # 设定使用的账号优先级为
        # phone > userid > account > username
        if isinstance(self.phone_combined, str) and not self.phone_combined == "":
            return self.phone_combined
        elif isinstance(self._userid, str) and not self._userid == "":
            return self._userid
        elif isinstance(self._account, str) and not self._account == "":
            return self._account
        elif isinstance(self._username, str) and not self._username == "":
            return self._username
        else:
            return None

    def __init__(
        self, task: Task, appcfg: AppCfg, clientid: str, logger_name_ext: str = ""
    ):
        if not isinstance(task, Task):
            raise Exception("Task is invalid.")
        if not isinstance(appcfg, AppCfg):
            raise Exception("AppConfig is invalid.")
        if not isinstance(clientid, str) or clientid == "":
            raise Exception("Invalid clientid")

        self.task = task
        self._clientid: str = clientid
        self._appcfg = appcfg

        # logger和插件名
        self._name = type(self).__name__
        loggername = f"{self._name}_{self.task.batchid}"
        if not logger_name_ext is None and not logger_name_ext == "":
            loggername += "_{}".format(logger_name_ext)
        self._logger: MsLogger = MsLogManager.get_logger(loggername)

        # Http库对象
        self._ha: HttpAccess = HttpAccess()

        # 一些通用字段，用于存放当前插件登陆的账号的一些到处都要用的信息
        self._userid: str = None  # 网站对用户的唯一识别标识
        self._account: str = self.task.account  # 可以用于登陆的账号名
        self._username: str = None  # 用户昵称
        self._globaltelcode: str = self.task.globaltelcode  # 国际区号
        self._phone: str = self.task.phone  # 电话
        self._url: str = self.task.url
        self._host: str = self.task.host
        self._cookie: str = self.task.cookie

        # 一些状态对象
        self._errorcount: int = 0
        self.is_running: bool = False
        self.running_task = []
        # 验证码有效时间定为900秒, 15分钟足够了，一般验证码的有效时间最高也就10分钟
        self._effective_time = 900
        # self._outputtgfile = OutputManage()
        self._sqlfunc = DbManager
        # 线程运行
        self._running = True
        # 停止标志,默认不停止, 1表示继续下载不停False，0表示停止True
        self._stop_sign = False

    def _terminate(self):
        self._running = False

    def _get_stop_sign(self):
        """
        单个线程不断在数据库中查询停止标志
        改变停止的状态
        :return:
        """
        sql = """
        SELECT cmdid, cmd FROM task 
        LEFT OUTER JOIN idowncmd USING (cmdid)
        WHERE batchid=? and taskid=?
        """
        pars = (self.task.batchid, self.task.taskid)
        while self._running:
            try:
                res = self._sqlfunc.query_task_by_sql(sql, pars)
                if len(res) == 0 or res[0].get("cmd") is None:
                    continue
                cmd = IdownCmd(res[0].get("cmd"))
                if (
                    cmd.switch_control is not None
                    and cmd.switch_control.download_switch is not None
                ):
                    self._stop_sign = int(cmd.switch_control.download_switch) == 0
            except:
                self._logger.error(
                    f"Something wrong when get stopsign,err:{traceback.format_exc()}"
                )
                continue
            finally:
                # 以防万一不要频繁的访问数据库,
                # 这个设置的时间可以等长一点，也许整个任务都不会有停止下载的设置
                time.sleep(2)

    def _get_login_method(self) -> callable:
        """
        根据task.tasktype找到实际需调用的登陆接口
        spiderbase内部使用
        """
        loginfunc = None
        if self.task.tokentype == ETokenType.Sms:
            loginfunc = self._sms_login
        elif self.task.tokentype == ETokenType.SmsPwd:
            loginfunc = self._pwd_sms_login
        elif self.task.tokentype == ETokenType.Pwd:
            loginfunc = self._pwd_login
        elif self.task.tokentype == ETokenType.Cookie:
            loginfunc = self._cookie_login
        elif (
            self.task.tokentype == ETokenType.NotNeed
            or self.task.tokentype == ETokenType.Unknown
        ):
            self._write_task_back(ECommandStatus.Failed, "内部错误，错误的接口调用")
            self._logger.error(
                f"Wrong interface call: tokentype:{self.task.tokentype.value}"
            )
        else:
            self._write_task_back(ECommandStatus.Failed, "登陆出错，未知的任务类型")
            self._logger.error(
                f"Unknown task type: tokentype:{self.task.tokentype.value}"
            )
        if not callable(loginfunc):
            self._write_task_back(ECommandStatus.Failed, "内部错误，登陆接口不可调用")
            self._logger.error(f"Login function is not callable, loginfunc:{loginfunc}")
        return loginfunc

    def _log_for_data(self, data: FeedDataBase):
        """
        统一日志输出数据信息，
        这是输出下载数据的日志信息，
        这样就会避免到处去写
        """
        # 单条数据
        if not data._is_muti_seg:
            login_info = f"Get {data._datatype.name} {data.get_uniqueid()} {data.get_display_name()}"
            self._logger.info(login_info)
            self._write_log_back(login_info)
        elif data.innerdata_len > 0:
            inner = data.first_innerdata()
            if inner is None:
                raise Exception(
                    "Get one inner data of {} is None".format(data._datatype.name)
                )
            login_info = (
                f"Get {data._datatype.name} with {data.innerdata_len} {type(inner).__name__} "
                f"inner segments {self.uname_str}"
            )
            self._logger.info(login_info)
            self._write_log_back(login_info)
        else:
            login_info = (
                f"Skip empty data: {data.get_uniqueid()} {data.get_display_name()}"
            )
            self._logger.info(login_info)
            self._write_log_back(login_info)
        return

    def _output_data_and_log_output_data(self, data):
        """
        输出日志然后输出文件
        :param data:
        :return:
        """
        # 统一日志输出
        self._log_for_data(data)
        # 这里会出现一个bug就是先输出日志然后输出数据会导致数据可能会混淆到一个文件里面去了目前还是会存在这样的，
        # 或者是生成的字符串导致hash一样传输程序将两个文件之间的东西混淆了, by judy 2020/01/7
        # time.sleep(0.5)
        OutputManagement.output(data)
        return

    def _write_task_back(
        self, taskstatus: ECommandStatus, description, currenttime=None, result=None
    ):
        """
        子类使用这个方法写回馈文件
        :param taskstatus: EcommandStatus
        :param description: 本次任务描述，必要
        :return:
        """
        if not isinstance(taskstatus, ECommandStatus):
            raise Exception("Unknown taskstatus type!")
        tginfo = TaskBatchBack.create_from_task(
            self.task,
            cmdstatus=taskstatus,
            cmdrcvmsg=description,
            result=result,
            currenttime=currenttime,
        )
        OutputManagement.output(tginfo)
        return

    def _update_task_status(self, statusvalue: int):
        """
        将最新的下载令牌/状态更新到数据库
        等于直接使用sql更新数据库的taskstatus状态
        """
        # 更新到数据库
        if not isinstance(statusvalue, int):
            raise Exception("Unknown statusvalue type!")
        self.task.taskstatus = ETaskStatus(statusvalue)
        self._sqlfunc.update_status_by_taskid(
            "taskstatus", statusvalue, self.task.batchid, self.task.taskid
        )
        return

    def _update_download_complete_tskinfo(self):
        """
        登陆成功后更新这些数据
        更新最新的下载令牌
        """
        self._restore_resources()
        self._sqlfunc.update_task_resource(self.task)
        return

    def _is_reduplicate(self, data: FeedDataBase) -> bool:
        """
        根据多段类型数据和单体数据不同，去重方式不同。
        是重复数据返回True，若不是返回False
        """
        # 单段数据
        res: bool = False
        if not data._is_muti_seg:
            res = self._sqlfunc.is_data_exists(data, data._datatype)
            if res:
                self._logger.info(
                    "Reduplicate data: {} {}".format(
                        data._datatype.name, data.get_uniqueid()
                    )
                )
        # 多段类型数据，去除重复的数据段
        else:
            totalcount = data.innerdata_len
            dup: list = []
            for inner in data:
                if self._sqlfunc.is_data_exists(inner, data._datatype):
                    dup.append(inner)
            dupcount = len(dup)
            for d in dup:
                data.remove_innerdata(d)
            if data.innerdata_len < 1:
                # 如果一条都不剩了，就是全部都是重复数据
                self._logger.info(
                    f"Reduplicate datas: {data._datatype.name} {data.get_display_name()}"
                )
                res = True
            else:
                # 否则就写入剩下的数据
                if dupcount > 0:
                    self._logger.info(
                        "Reduplicate data: {} {} {}(Reduplicate) of {}(total)".format(
                            data._datatype.name,
                            data.get_display_name(),
                            dupcount,
                            totalcount,
                        )
                    )
        return res

    def _save_data_uniqueid(self, data: FeedDataBase):
        """数据唯一标识存入数据库。多段和单段数据类型存入方式不同"""
        self._sqlfunc.insert_uniquely_identifies(data)
        return

    def _update_cookie_status(self, cookiealive: int, cookielastkeeptime, batchid):
        """
        更新cookie信息用于cookie保活
        :param cookiealive:
        :param cookielastkeeptime:
        :param batchid:
        :return:
        """
        sql = """
        update task set
        cookiealive=?,
        cookielastkeeptime=?
        where batchid=?
        """
        pars = (cookiealive, cookielastkeeptime, batchid)
        self._sqlfunc.update_task_by_sql(sql, pars)
        return

    def _write_userstatus_back(self, userid):
        """
        userstatus的回馈
        modify by judy 20201118
        输出每个userstatus的时候将user信息和task信息保存，后面cookie失活后需要更新这个表
        :param userid:
        :return:
        """
        if userid is None:
            raise Exception("Userid cant be None")
        uinfo = UserStatus(self.task, self._clientid, userid, self.task.apptype)
        OutputManagement.output(uinfo)
        # 保存userinfo
        self._sqlfunc.save_idown_userinfo(
            self.task.taskid, self.task.batchid, userid, self._clientid
        )
        return

    def _write_log_back(self, log):
        """
        log 的回馈
        :param log:
        :return:
        """
        if log == "" or log is None:
            raise Exception("Log can not be None")
        linfo = ClientLog(self.task, self._clientid, self.task.apptype, log)
        # 添加这个的原因是因为不知道为什么明明log都没有调用数据流这个字段，但是日志里却出现了文件体，这里相当于上了一个保险
        # if linfo.io_stream is not None:
        #     self._logger.error('Now get a clientlog data stream is not None')
        #     linfo.io_stream = None
        OutputManagement.output(linfo)
        return

    # ---------------------------------------------------------
    # 这下面全是子类需要实现的方法

    @abstractmethod
    def _check_registration(self) -> iter:
        """
        返回btaskback，数据参照datafeedback
        有个人信息则返回个人信息
        :return:
        """
        return []

    @abstractmethod
    def _online_check(self) -> bool:
        """
        返回btaskback,数据参照datefeedback
        查询账号目标是否在线
        :return:
        """
        return False

    @abstractmethod
    def _pwd_login(self) -> bool:
        """
        账号密码登陆
        :return:
        """
        return ""

    @abstractmethod
    def _sms_login(self) -> bool:
        """
        短信登陆，验证码通过getvertificode取
        :param self:
        :return:
        """
        return ""

    @abstractmethod
    def _cookie_login(self) -> bool:
        """
        cookie登陆
        :return:
        """
        return False

    @abstractmethod
    def _pwd_sms_login(self) -> bool:
        """
        账号密码+短信验证码登陆
        :return:
        """
        return False

    @abstractmethod
    def account_pwd_login(self) -> bool:
        """
        tasktype为账密批量测试必须实现此方法
        :return:
        """
        return False

    @abstractmethod
    def _download(self) -> iter:
        """
        每个类型的Spider基类需要实现的函数
        :return:
        """
        return []

    @abstractmethod
    def _get_profile(self) -> iter:
        """获取个人信息和头像（如果有），不要把异常抛出来"""
        return []

    @abstractmethod
    def _get_loginlog(self) -> iter:
        """获取登陆历史记录"""
        return []

    @abstractmethod
    def _get_contacts(self) -> iter:
        """获取联系人"""
        return []

    @abstractmethod
    def _after_down(self, data) -> bool:
        return False

    @abstractmethod
    def _restore_resources(self):
        """保存各种登陆令牌到self.task.cookies等等"""
        if not self._ha is None:
            ck = self._ha._managedCookie.get_all_cookie()
            if isinstance(ck, str) and not ck == "":
                self.task.cookie = ck

        # self.task.account = self.uname_str
        # if not isinstance(self.task.account, str) or self.task.account == "":
        #     self.task.account = self.uname_str
        if isinstance(self._host, str) and not self._host == "":
            self.task.host = self._host
        if isinstance(self._url, str) and not self._url == "":
            self.task.url = self._url
        return

    @abstractmethod
    def _logout(self) -> bool:
        """退出登录的方法"""
        return False
