"""Ms log. For 100 logs per seconds is ok. More is not that ok..."""

# -*- coding:utf-8 -*-

from .loghook import LogHook
from .mslogconfig import (MsConsoleLogConfig, MsFileLogConfig, MsLogConfig,
                          MsLogMessageConfig)
from .mslogger import MsLogger
from .msloglevel import MsLogLevel, MsLogLevels
from .mslogmanager import MsLogManager
from .mslogmsg import MsLogMessage

__all__ = [
    'mslogconfig',
    'mslogfactory',
    'mslogger',
    'msloglevel',
    'mslogmanager',
    'mslogmsg',
    'mslogprovider',
    'mslogmsg',
]
