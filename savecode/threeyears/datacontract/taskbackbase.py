"""
子类插件下载的数据类型
create by judy 2018/10/12
modify by judy 2018/10/15
"""
from datetime import datetime
import threading
import time

from abc import ABCMeta, abstractmethod

import pytz

from datacontract.outputdata import DataSeg, EStandardDataType, OutputData, OutputDataSeg
from .ecommandstatus import ECommandStatus


class EBackResult:
    Registerd = '#@11'

    UnRegisterd = '#@12'

    CheckRegisterdFail = '#@13'

    LoginSucess = '#@32'

    LoginFailed = '#@33'

    Online = '#@21'

    Offline = '#@22'

    Unknownline = '#@23'


class TaskBackBase(OutputData, OutputDataSeg):
    """TaskBackBase"""

    __metaclass = ABCMeta

    @property
    def time(self) -> str:
        """直接用self.time会报错，，封装成属性"""
        return self._time

    @time.setter
    def time(self, value):
        if not isinstance(value, str):
            return
        self._time = value

    @property
    def cmdstatus(self) -> ECommandStatus:
        """CmdFeedBack的命令处理状态，可set"""
        return self._cmdstatus

    @cmdstatus.setter
    def cmdstatus(self, value):
        """CmdFeedBack的命令处理状态，可set"""
        if not isinstance(value, ECommandStatus):
            return
        self._cmdstatus = value

    @property
    def cmdrcvmsg(self) -> str:
        """CmdFeedBack的描述信息，可set"""
        return self._cmdrcvmsg

    @cmdrcvmsg.setter
    def cmdrcvmsg(self, value):
        """CmdFeedBack的描述信息，可set"""
        if not isinstance(value, str):
            return
        self._cmdrcvmsg = value

    def __init__(
            self,
            stddatatype: EStandardDataType,
            platform: str,
            cmdstatus: ECommandStatus,
            cmdrcvmsg: str = None,
            currenttime: str = None,
    ):

        OutputData.__init__(self, platform, stddatatype)
        OutputDataSeg.__init__(self)

        self._cmdstatus: ECommandStatus = None
        if isinstance(cmdstatus, ECommandStatus):
            self._cmdstatus = cmdstatus
        else:
            try:
                self._cmdstatus = ECommandStatus(int(cmdstatus))
            except Exception:
                pass

        self._cmdrcvmsg: str = None
        if isinstance(cmdrcvmsg, str) and cmdrcvmsg != '':
            self._cmdrcvmsg = cmdrcvmsg
        # 当前时间, 字符串的datetime
        self._time: str = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        if currenttime is not None and currenttime != '':
            self._time = currenttime
