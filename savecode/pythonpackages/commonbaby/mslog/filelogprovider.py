"""File log provider that provides separated log file write"""

# -*- coding:utf-8 -*-

from .filelogwriter import MsFileLogWriter
from .mslogconfig import MsFileLogConfig, MsLogConfig
from .msloglevel import MsLogLevels
from .mslogprovider import MsLogProvider


class FileLogProvider(MsLogProvider):
    """File log provider that provides separated log file write"""

    def __init__(self, ficfg: MsFileLogConfig = None):

        if ficfg is None:
            ficfg = MsFileLogConfig(MsLogLevels.DEBUG, True)

        MsLogProvider.__init__(self, ficfg)

    def get_writer(self, name: str,
                   cfg: MsLogConfig = None) -> MsFileLogWriter:
        """Returns a MsLogWriter with specific name
        name: the writer's name"""
        if name is None:
            name = 'default'
        wtr = MsFileLogWriter(name, cfg if cfg is not None else self._config)
        return wtr
