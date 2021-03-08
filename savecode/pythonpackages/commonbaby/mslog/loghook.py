"""log hook"""

# -*- coding:utf-8 -*-

import traceback

from ..mslog.msloglevel import MsLogLevel, MsLogLevels


class LogHook:
    """日志钩子..."""

    def __init__(self, logger_hook: callable):
        self.__logger_hook: callable = logger_hook

    def trace(self, msg):
        self.log(msg, MsLogLevels.TRACE)

    def debug(self, msg):
        self.log(msg, MsLogLevels.DEBUG)

    def info(self, msg):
        self.log(msg, MsLogLevels.INFO)

    def warn(self, msg):
        self.log(msg, MsLogLevels.WARN)

    def error(self, msg):
        self.log(msg, MsLogLevels.ERROR)

    def critical(self, msg):
        self.log(msg, MsLogLevels.CRITICAL)

    def log(self, msg: str, level: MsLogLevel):
        if callable(self.__logger_hook):
            try:
                self.__logger_hook(msg, level)
            except Exception:
                print("Logger_hook write log error: {}".format(
                    traceback.format_exc()))
                print(msg)
        else:
            print(msg)
