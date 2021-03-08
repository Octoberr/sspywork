"""File log provider that provides single log file write"""

# -*- coding:utf-8 -*-

from .mslogconfig import MsFileLogConfig, MsLogConfig
from .mslogprovider import MsLogProvider
from .mslogwriter import MsLogWriter
from .singlefilewriter import MsSingleFileLogWriter


class SingleFileLogProvider(MsLogProvider):
    """File log provider that provides single log file write"""

    def __init__(self, ficfg: MsFileLogConfig = None):
        if ficfg is None:
            ficfg = MsFileLogConfig()
        MsLogProvider.__init__(self, ficfg)

    def get_writer(self, name: str, cfg: MsLogConfig = None) -> MsLogWriter:
        """Returns a MsLogWriter with specific name
        name: the writer's name"""
        if name is None:
            name = 'default'
        wtr = MsSingleFileLogWriter(name, cfg
                                    if cfg is not None else self._config)
        return wtr
