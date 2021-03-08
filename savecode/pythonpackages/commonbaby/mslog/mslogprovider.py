"""Ms log provider base"""

# -*- coding:utf-8 -*-

from abc import ABCMeta, abstractmethod

from .mslogconfig import MsLogConfig
from .msloglevel import MsLogLevels
from .mslogwriter import MsLogWriter


class MsLogProvider(object):
    """log provider base"""

    __metaclass__ = ABCMeta

    # the config object
    _config: MsLogConfig = None

    def __init__(self, cfg: MsLogConfig):
        if cfg is None:
            self._config = MsLogConfig(MsLogLevels.DEBUG)
        else:
            self._config = cfg

    @abstractmethod
    def get_writer(self, name: str, cfg: MsLogConfig = None) -> MsLogWriter:
        """Returns a MsLogWriter with specific name
        name: the writer's name"""
        pass
