"""Console log provider which creates new logger log on console"""

# -*- coding:utf-8 -*-

from .consolelogwriter import MsConsoleLogWriter
from .mslogconfig import MsConsoleLogConfig, MsLogConfig
from .msloglevel import MsLogLevels
from .mslogprovider import MsLogProvider


class ConsoleLogProvider(MsLogProvider):
    """Console log provider which creates new logger log on console"""

    def __init__(self, cfg: MsConsoleLogConfig):
        if cfg is None:
            cfg = MsConsoleLogConfig(MsLogLevels.DEBUG)
        MsLogProvider.__init__(self, cfg)

    def get_writer(self, name: str,
                   cfg: MsLogConfig = None) -> MsConsoleLogWriter:
        """Returns a MsLogWriter with specific name
        name: the writer's name"""
        if name is None:
            name = 'default'
        wtr = MsConsoleLogWriter(name, cfg
                                 if cfg is not None else self._config)
        return wtr
