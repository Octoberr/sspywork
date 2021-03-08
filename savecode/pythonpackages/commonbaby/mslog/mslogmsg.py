"""The log message object, represents a log message"""

# -*- coding:utf-8 -*-

import threading

from ..helpers import helper_time
from .mslogconfig import MsLogMessageConfig
from .msloglevel import MsLogLevel, MsLogLevels


class MsLogMessage(object):
    """The log message object, represents a log message"""

    __static_initialed: bool = False
    # locker for static initial
    __locker = threading.RLock()
    # the MsLogMessageConfig
    __config = None

    __formatter = None

    # the message that is already formatted after initialed the current MsLogMessage object
    message: str = None
    level = MsLogLevels.DEBUG

    def __init__(self,
                 loggername: str,
                 msg: str,
                 eventid: int = -1,
                 lvl: MsLogLevel = MsLogLevels.DEBUG,
                 exc: Exception = None):
        self.message = self.__default_format(loggername, msg, eventid, lvl,
                                             exc)
        self.level = lvl if lvl is not None else MsLogLevels.DEBUG

    @classmethod
    def static_initial(cls, msgcfg: MsLogMessageConfig = None):
        """To init the static settings for log message"""
        with cls.__locker:
            if cls.__static_initialed:
                return

            if (msgcfg is not None) and (msgcfg.formatter is not None):
                cls.__formatter = msgcfg.formatter
            else:
                cls.__formatter = cls.__default_format

            cls.__static_initialed = True

    @classmethod
    def __default_format(cls,
                         loggername: str,
                         msg: str,
                         eventid: int = -1,
                         lvl: MsLogLevel = MsLogLevels.DEBUG,
                         exc: Exception = None) -> str:
        """
        The default format delegate
        msg: The log message.
        exc: The Exception object(if exists)"""
        # [2018-01-22 10:59:46] [INFO] [592] [aaa] this is logger aaa
        if eventid == -1:
            eventid = threading.current_thread().ident

        # 精确到毫秒...
        time_stamp = helper_time.get_time_millionsec()
        new_msg = '[%s] [%s] [%d] [%s] %s' % (time_stamp, lvl, eventid,
                                              loggername, msg)
        if exc is not None:
            new_msg = new_msg + '\r\nex:%s' % exc.args
        return new_msg
