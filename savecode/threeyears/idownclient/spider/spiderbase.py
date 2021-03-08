"""
爬虫基类
create by judy 2018/10/08

fix till now by judy 2019/03/13

所有数据将唯一标识存入数据库，存入前会自动去除已经存在的数据
fix by judy 2019/03/25
"""
import threading
import time
import traceback
from datetime import datetime
import pytz

from datacontract.idowndataset import Task, ETokenType, EBackResult, task
from datacontract.etaskstatus import ETaskStatus
from datacontract.ecommandstatus import ECommandStatus
from idownclient.clientdatafeedback import (
    FeedDataBase,
    IdownLoginLog,
    IdownLoginLog_ONE,
    PROFILE,
)
from outputmanagement import OutputManagement
from .appcfg import AppCfg
from .spiderinnerdata import SpiderInnerData


class SpiderBase(SpiderInnerData):
    # __metaclass = ABCMeta

    def __init__(
        self, task: Task, appcfg: AppCfg, clientid: str, logger_name_ext: str = ""
    ):
        # 继承了父类的参数处理，然后给子类继承，子类的代码也就多了
        SpiderInnerData.__init__(self, task, appcfg, clientid, logger_name_ext)

    def login_test(self) -> bool:
        """
        测试cookie登陆，和账密登陆的有效性
        :return:
        """
        res = False
        if self.task.tokentype == ETokenType.Pwd:
            loginfunc = self._pwd_login
            # 登陆测试
        elif self.task.tokentype == ETokenType.Cookie:
            loginfunc = self._cookie_login
            # cookie登陆测试,判断cookie是否有效
        elif self.task.tokentype == ETokenType.Sms:
            loginfunc = self._sms_login
        elif self.task.tokentype == ETokenType.Unknown:
            if self.task.cookie is not None and self.task.cookie != "":
                loginfunc = self._cookie_login
            else:
                raise Exception("Unknown tokentype, unknown login way")
        else:
            raise Exception("Wrong login tasktype to test login")
        try:
            res = loginfunc()
            if res:
                self._restore_resources()
            elif self.task.tokentype == ETokenType.Pwd:
                data = PROFILE(
                    self._clientid, self.task, self.task.apptype, self.task.account
                )
                self._output_data_and_log_output_data(data)

        except Exception:
            self._logger.error(
                "Login test error, err:{}".format(traceback.format_exc())
            )
        return res

    def keep_cookie_live(self) -> bool:
        """
        目前先调用cookie登陆，保持cookie有效
        :return:
        """
        res = False
        try:
            succ = self._cookie_login()
            res = succ
        except:
            self._logger.error(f"Keep cookie alive error, err:{traceback.format_exc()}")
        return res

    def login_only(self) -> bool:
        """
        用于只是登陆的任务
        获取子类的登陆方法然后登陆即可
        :return:
        """
        res = False
        login_function = self._get_login_method()
        if login_function is None or not callable(login_function):
            self._logger.error(
                f"Login method is None or not callable: {self.task.tasktype}"
            )
            return res
        succ = login_function()
        if not succ:
            self._write_task_back(
                ECommandStatus.Failed, "登陆失败", result=EBackResult.LoginFailed
            )
            self._logger.info("Login failed")
        else:
            self._write_task_back(
                ECommandStatus.Succeed, "登陆成功", result=EBackResult.LoginSucess
            )
            self._restore_resources()
            self._logger.info("Login succed")
            res = True
        return res

    def online_check(self) -> bool:
        """
        返回btaskback数据标准参照datafeedback
        查询目标账号是否在线
        目前telegram的使用需要先登陆内置账号
        :return:
        """
        res = False
        try:
            res = self._online_check()
            if isinstance(res, bool):
                if res:
                    self._write_task_back(
                        ECommandStatus.Succeed, "目标账号在线", result=EBackResult.Online
                    )
                else:
                    self._write_task_back(
                        ECommandStatus.Succeed, "目标账号离线", result=EBackResult.Offline
                    )
            res = True
        except Exception:
            self._logger.error(traceback.format_exc())
        return res

    def logout(self):
        """
        退出登录
        :return:
        """
        res = False
        try:
            res = self._logout()
            if res:
                self.task.taskstatus = ETaskStatus.Logout
                # 这个东西以前用的是parentbatchid，我靠明显是有问题的，现在改了，以后出问题再改回来吧
                self._sqlfunc.update_status_by_taskid(
                    "taskstatus",
                    self.task.taskstatus.value,
                    self.task.batchid,
                    self.task.taskid,
                )
                self._write_task_back(ECommandStatus.Succeed, "退出登录成功")
            else:
                self._write_task_back(ECommandStatus.Failed, "退出登录失败")
            res = True
        except Exception:
            self._logger.error(traceback.format_exc())
        return res

    def check_registration(self):
        """
        tasktype为账号应用注册查询必须实现此方法
        :return:返回bool值指示账号是否注册当前app
        """
        # 像个办法统一==，想什么办法呢
        try:
            res = self._check_registration()
            if res is not None:
                for data in res:
                    # 统一日志输出
                    self._log_for_data(data)
                    # 每一个data获取到在输出之前需要做的事
                    # 输出
                    OutputManagement.output(data)
        except Exception:
            self._logger.error(
                "Check registration failed: {}".format(traceback.format_exc())
            )
        return

    def download_all_data(self) -> bool:
        """这是基类对外接口"""
        res: bool = False
        try:
            # 判断登陆接口用哪个
            loginfunc: callable = None  # 用于记录登陆接口方法
            if isinstance(self.task.cookie, str) and not self.task.cookie == "":
                loginfunc = self._cookie_login
            else:
                loginfunc = self._get_login_method()

            if loginfunc is None or not callable(loginfunc):
                self._logger.error(
                    f"Login method is None or not callable: {self.task.tasktype}"
                )
                return res

            # 登陆
            log_info = (
                f"开始登陆: {self.task.batchid} {self.task.tasktype.name} {self.uname_str}"
            )
            self._logger.info(
                f"login start: {self.task.batchid} {self.task.tasktype.name} {self.uname_str}"
            )
            self._write_log_back(log_info)
            self._update_task_status(ETaskStatus.Logining.value)
            self._write_task_back(ECommandStatus.Dealing, "登陆中-----")

            succ = loginfunc()
            # 如果登陆失败，且是cookie登陆，且tasktype不是cookie登陆，说明是走cookie登陆尝试
            # 需要再走实际登陆接口
            if (
                not succ
                and loginfunc == self._cookie_login
                and self.task.tokentype != ETokenType.Cookie
            ):
                loginfunc = self._get_login_method()
                succ = loginfunc()

            if not succ:
                self._write_task_back(
                    ECommandStatus.Failed, "登陆失败", result=EBackResult.LoginFailed
                )
                log_info = "登陆失败"
                self._logger.info("Login failed")
                self._write_log_back(log_info)
                self._update_task_status(ETaskStatus.LoginFailed.value)
                return res
            else:
                self._write_task_back(
                    ECommandStatus.Dealing, "登陆成功，正在下载", result=EBackResult.LoginSucess
                )
                # self._update_task_resource()
                self._update_task_status(ETaskStatus.LoginSucceed.value)
                log_info = f"登陆成功: username={self.uname_str}, userid={self._userid}"
                self._logger.info(
                    f"login succeed: username={self.uname_str}, userid={self._userid}"
                )
                self._write_log_back(log_info)

            # 单独开启一个线程，去查询外界改变下载状态，下载完成结束这个线程
            t = threading.Thread(target=self._get_stop_sign, name="stop_singn_scan")
            t.start()

            # 下载
            log_info = f"开始下载: {self.uname_str} {self._userid}"
            self._logger.info(f"Download started: {self.uname_str} {self._userid}")
            self._write_log_back(log_info)
            self._update_task_status(ETaskStatus.Downloading.value)
            succ = self.__download_process()
            if not succ:
                self._write_task_back(ECommandStatus.Failed, "下载出错")
                self._update_task_status(ETaskStatus.DownloadFailed.value)
                if self._userid is not None:
                    self._write_userstatus_back(self._userid)
                log_info = "下载失败"
                self._logger.info("Download failed")
                self._write_log_back(log_info)
                self.task.failtimes += 1
                return res
            elif self._errorcount > 0:
                self._write_task_back(ECommandStatus.Succeed, "下载完成，部分数据下载出错，请通知开发寻找原因")
                self._update_task_status(ETaskStatus.DownloadCompleted.value)
                log_info = "下载完成"
                self._logger.info(
                    "Download complete, but some data is wrong to download"
                )
                self._write_log_back(log_info)
                self.task.successtimes += 1
            else:
                self._write_task_back(ECommandStatus.Succeed, "下载成功")
                self._update_task_status(ETaskStatus.DownloadSucceed.value)
                if self._userid is not None:
                    self._write_userstatus_back(self._userid)
                log_info = "下载成功"
                self._logger.info(
                    "Download succeed: {} {}".format(self._userid, self._username)
                )
                self._write_log_back(log_info)
                self.task.successtimes += 1
                if self.task.cookie is not None and self.task.cookie != "":
                    # 更新cookie的状态用于cookie保活
                    self._update_cookie_status(
                        1,
                        int(datetime.now(pytz.timezone("Asia/Shanghai")).timestamp()),
                        self.task.batchid,
                    )
            res = succ
            # 数据下载完成，或者下载中断结束这个线程
            # 主线程结束那么这个线程也会销毁，所以不用等待
            self._terminate()

            if self._stop_sign:
                # 如果停止了要把中途暂停的状态存入数据库
                self._update_task_status(ETaskStatus.TemporarilyStop.value)

        except Exception as ex:
            log_info = f"下载出错:{ex.args}"
            self._write_log_back(log_info)
            self._logger.error(f"Download error:{traceback.format_exc()}")
        finally:
            # 更新数据库最后一次的下载信息
            self._update_download_complete_tskinfo()
            # 检查下是否是中途被停止的，如果是被停止的那么就会更新状态
            return res

    def __download_process(self) -> bool:
        """
        基类统一子类的下载流程
        """
        # 测试阶段，直接返回true
        # return True
        res: bool = False
        log_info = "开始下载"
        self._write_log_back(log_info)
        try:
            for data in self.__download_data():
                try:
                    data: FeedDataBase = data
                    if data is None:
                        continue
                    if not issubclass(data.__class__, FeedDataBase):
                        self._logger.error("Retruned data is invalid: {}".format(data))

                    # 每个profile都要输出
                    if isinstance(data, PROFILE):
                        log_info = (
                            f"获取到用户信息, username={data.account} userid={data._userid}"
                        )
                        self._write_log_back(log_info)
                        self._output_data_and_log_output_data(data)
                        # 根据profile输出userstatus
                        self._write_userstatus_back(data._userid)
                        continue

                    # 数据库查询并去重
                    # 如果强制性输出所有数据那么不去重
                    if not self.task.forcedownload and self._is_reduplicate(data):
                        continue

                    # 所有数据都需要存入本地数据库
                    # 数据唯一标识存入数据库, 数据插入前会自动查询数据是否已经存在于数据库
                    self._save_data_uniqueid(data)

                    # 输出数据,打印日志
                    self._output_data_and_log_output_data(data)

                except Exception as ex:
                    log_info = f"下载数据出错:{ex.args}"
                    self._logger.error(
                        "Download data error: {}".format(traceback.format_exc())
                    )
                    self._write_log_back(log_info)
                    self._errorcount += 1
                    if self._errorcount >= 10:
                        self._logger.error(
                            "The number of failures exceeded the limit，exit the download"
                        )
                        res = False
                        break
                finally:
                    # 数据流需要释放
                    if data is not None and data.io_stream is not None:
                        data.io_stream.close()

                    # 当前数据输出后判断是否停止下载，如果停止下载后面的数据就不要了
                    if self._stop_sign:
                        log_info = "下载已暂停"
                        self._logger.info(
                            "Download paused: {} {}".format(
                                self._userid, self._username
                            )
                        )
                        self._write_log_back(log_info)
                        break
            # 数据下载完成
            if self._errorcount > 0:
                log_info = "下载完成"
                self._logger.info(
                    "Download complete: {} {}".format(self._userid, self._username)
                )
                self._write_log_back(log_info)
            res = True

        except Exception as ex:
            log_info = f"下载出错:\nbatchid={self.task.batchid}\nerror:{ex.args}"
            self._logger.info("Download error: {}".format(traceback.format_exc()))
            self._write_log_back(log_info)
        finally:
            time.sleep(1)
        return res

    def __download_data(self):
        """
        所有插件都可能要下载的数据
        """
        try:
            self._logger.info("Start getting profile")
            for profile in self._get_profile():
                yield profile

            self._logger.info("Start getting loginlog")
            logs: IdownLoginLog = IdownLoginLog(
                self._clientid, self.task, self.task.apptype
            )
            for log in self._get_loginlog():
                if isinstance(log, IdownLoginLog_ONE):
                    logs.append_innerdata(log)
                else:
                    yield log
            if logs.innerdata_len > 0:
                yield logs

            for data in self._download():
                yield data

        except Exception:
            self._logger.error(f"Download error:{traceback.format_exc()}")

    def _get_vercode(self) -> str:
        """
        短信登陆用于获取验证码
        对外提供
        :param self:
        :return:
        """
        self._write_task_back(ECommandStatus.NeedSmsCode, "需要短信登陆验证码")
        self._logger.info(f"Wait for sms verify code, account={self.uname_str}")
        vercode: str = ""
        for i in range(self._effective_time // 1):
            vercode = self._sqlfunc.query_input(self.task)
            if vercode is None or vercode == "":
                time.sleep(3)
                continue
            else:
                break

        if not isinstance(vercode, str) or vercode == "":
            self._write_task_back(ECommandStatus.Failed, "等待输入验证码超过了15分钟，验证码已失效")
            raise Exception("Wait sms verify code timeout")
        else:
            self._logger.info("Got verify code: {}".format(vercode))
            self._write_task_back(ECommandStatus.Dealing, "输入验证码: {}".format(vercode))
        return vercode
