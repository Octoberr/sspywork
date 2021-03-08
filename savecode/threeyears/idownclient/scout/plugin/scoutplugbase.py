"""
scout插件的一些公用数据和方法
可能每个子类需要的流程不太一样
所以子类有可能都是独立的
create by judy 2019/07/10
"""


import json
from datacontract.idowncmd.iscoutcmd import SendCode
import threading
import time
import traceback

from commonbaby.mslog import MsLogger, MsLogManager
from jsonoutputer import Outputjtf
from idownclient.config_task import clienttaskconfig
from datacontract import (
    ECommandStatus,
    IscoutBtaskBack,
    IscoutTask,
    PrglogBase,
)
from outputmanagement import OutputManagement
from idownclient.clientdbmanager import DbManager


class ScoutPlugBase(object):
    """每个具体scouter插件的实现类base"""

    def __init__(self, loggername: str = None):
        # 插件名字
        self._name = type(self).__name__
        if isinstance(loggername, str) and loggername != "":
            self._name = loggername
        self._logger: MsLogger = MsLogManager.get_logger(f"{self._name}")
        # 验证码的有效时间，一般为3分钟
        self._effective_time = 60
        self._sqlfunc = DbManager
        # reason
        # self.d_tools = dtools

    def _outprglog(self, log):
        """
        新增日志输出功能，modify by judy 2020/08/10
        """
        log = PrglogBase("IdownClient", "1.0", log, self.task)
        self.outputdata(log.output_dict(), "prg_log")
        return

    def outputdata(self, resdata: dict, suffix):
        """
        输出字典，json结果
        """
        # if suffix != self._log_suffix:
        #     self.output_count += 1
        try:
            outname = Outputjtf.output_json_to_file(
                resdata, clienttaskconfig.tmppath, clienttaskconfig.outputpath, suffix
            )
            self._logger.info(f"Output a data success, filename:{outname}")
        except:
            self._logger.error(f"Output json data error, err:{traceback.format_exc()}")
        return

    def write_iscouttaskback(
        self,
        iscouttask: IscoutTask,
        cmdstatus: ECommandStatus,
        scoutrecvmsg: str,
        currtime: str = None,
        elapsed: float = None,
    ):
        """
        通用方法编写iscantask的回馈
        update by judy 20201110
        编写这个任务的回馈因为需要登陆的插件需要这个回馈
        :param iscouttask:
        :param cmdstatus:
        :param scanrecvmsg:
        :param currtime:
        :param elapsed:
        :return:
        """
        if iscouttask is None:
            raise Exception("Write iscantaskback iscantask cannot be None")
        scanback = IscoutBtaskBack.create_from_task(
            iscouttask, cmdstatus, scoutrecvmsg, currtime, elapsed
        )
        OutputManagement.output(scanback)
        return

    def process_cmd(self, iscouttask: IscoutTask):
        """
        根据cmdid查询出来的cmd把验证码提取出来
        """
        vercode_dict = self._sqlfunc.query_cmd_by_cmdid(iscouttask.cmd_id)
        cmd_json = vercode_dict.get("cmd")
        if cmd_json is None or cmd_json == "":
            return
        cmd_dict = json.loads(cmd_json)
        if not isinstance(vercode_dict, dict):
            return
        try:
            vercode = cmd_dict.get("stratagyscout").get("sendcode").get("code")
            return vercode
        except:
            return

    def get_verifi_code(self, iscouttask: IscoutTask, account) -> str:
        """
        统一获取验证码的方法
        适用于三种登陆方式
        :param self:
        :return:
        """
        self.write_iscouttaskback(iscouttask, ECommandStatus.NeedSmsCode, "需要短信登陆验证码")
        log = f"Wait for sms verify code, account={account}"
        self._logger.info(log)
        self._outprglog(log)
        vercode: str = ""
        for i in range(self._effective_time // 1):
            vercode = self.process_cmd(iscouttask)
            if vercode is None or vercode == "":
                time.sleep(3)
                continue
            else:
                break
        if not isinstance(vercode, str) or vercode == "":
            log = "等待输入验证码超过了15分钟，验证码已失效"
            self._write_task_back(ECommandStatus.Failed, log)
            self._outprglog(log)
            raise Exception("Wait sms verify code timeout")
        else:
            log = "Got verify code: {}".format(vercode)
            self._logger.info(log)
            self._outprglog(log)
            self._write_task_back(ECommandStatus.Dealing, "输入验证码: {}".format(vercode))
        return vercode


# 新建一个线程类，用于获取线程的值
class MyThread(threading.Thread):
    def __init__(self, func, args=()):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.result = self.func(*self.args)  # 在执行函数的同时，把结果赋值给result,
        # 然后通过get_result函数获取返回的结果

    def get_result(self):
        try:
            return self.result
        except Exception as e:
            return None
