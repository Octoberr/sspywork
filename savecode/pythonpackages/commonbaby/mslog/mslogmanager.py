"""
Ms log manager
"""

# -*- coding:utf-8 -*-

import threading

from .consolelogprovider import ConsoleLogProvider
from .filelogprovider import FileLogProvider
from .mslogconfig import (MsConsoleLogConfig, MsFileLogConfig, MsLogConfig,
                          MsLogMessageConfig)
from .mslogfactory import MsLogFactroy
from .mslogger import MsLogger
from .msloglevel import MsLogLevel, MsLogLevels
from .mslogmsg import MsLogMessage
from .singlefilelogprovider import SingleFileLogProvider


class MsLogManager(object):
    """Ms log manager. If not specific any config when calling
    static_initial(), or just not call it. The default settings
    will be used. For more detail about the settings, see
    utility.mslog.basic.mslogconfig"""

    # the initial locker
    __locker = threading.RLock()
    __initialed: bool = False
    # the log factory
    __log_factory: MsLogFactroy = None

    __default_logger: MsLogger = None

    def __init__(self):
        pass

    @classmethod
    def static_initial(cls,
                       dft_lvl: MsLogLevel = MsLogLevels.DEBUG,
                       msmsgcfg: MsLogMessageConfig = None,
                       msficfg: MsFileLogConfig = None,
                       mscslogcfg: MsConsoleLogConfig = None,
                       write_to_file: bool = False
                       ):
        """To initial the settings.
        dft_lvl: specifieds the default level of a MsLogger.
        msmsgcfg: specifieds the config for the MsLogMessege(the formatter, etc.).
        msficfg: specifieds the config for how to write a log file(the file logger level, etc.).
        mscslogcfg: specifieds the config for how to write log on console(the console logger level, etc.)."""

        with cls.__locker:
            if cls.__initialed:
                return

            # init log message
            MsLogMessage.static_initial(msmsgcfg)

            # init log providers
            console_log_provider = ConsoleLogProvider(mscslogcfg)
            fi_log_provider = None
            if msficfg is None or not msficfg.separate_logfile:
                fi_log_provider = SingleFileLogProvider(msficfg)
            else:
                fi_log_provider = FileLogProvider(msficfg)

            # add providers to factory
            if cls.__log_factory is None:
                cls.__log_factory = MsLogFactroy(dft_lvl=dft_lvl)
            cls.__log_factory.add_provider(console_log_provider)
            if write_to_file:
                cls.__log_factory.add_provider(fi_log_provider)

            cls.__initialed = True

    @classmethod
    def get_logger(cls, name: str = None, cfg: MsLogConfig = None) -> MsLogger:
        """Get (or create if not exits) a logger with specific logger name,
        or if 'name' is None, will return a logger with name 'default'"""

        if not cls.__initialed:
            cls.static_initial()
        return cls.__log_factory.get_logger(name, cfg)
