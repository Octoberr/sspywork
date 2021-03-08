"""The log factory for creating new loggers using the logger providers."""

# -*- coding:utf-8 -*-

import threading

from .mslogconfig import MsLogConfig
from .mslogger import MsLogger
from .msloglevel import MsLogLevel, MsLogLevels
from .mslogprovider import MsLogProvider


class MsLogFactroy(object):
    """The log factory for creating new loggers using the logger providers."""

    # the default logger create locker
    __dft_lgr_locker = threading.Lock()

    # the initial locker
    __locker = threading.Lock()
    __initialed: bool = False

    # all logger providers on using
    providers: list = []

    __dft_level = MsLogLevels.DEBUG

    # all loggers that published
    __all_loggers: dict = {}
    __all_loggers_locker = threading.RLock()

    __default_logger: MsLogger = None

    def __init__(self, *providers, dft_lvl: MsLogLevel = MsLogLevels.DEBUG):
        self.__dft_level = dft_lvl
        if len(providers) < 1:
            # no provider provided
            return
        # add providers
        for provider in providers:
            if provider is None:
                continue
            self.add_provider(provider)
        # create default logger
        self.__create_default_logger(self.__dft_level)

    def __create_default_logger(self, lvl: MsLogLevel):
        """to check and create the default logger"""
        if not self.__default_logger is None:
            return
        self.__dft_lgr_locker.acquire()
        if not self.__default_logger is None:
            return
        if not lvl is None:
            lgr = MsLogger("default", lvl)
        else:
            lgr = MsLogger("default", self.__dft_level)
        for pvd in self.providers:
            wtr = pvd.get_writer("default")
            lgr.add_writer(wtr)
        self.__default_logger = lgr
        self.__dft_lgr_locker.release()

    def add_provider(self, provider: MsLogProvider):
        """add a provider, after that, it will be used for creating
        loggers. (The loggers that are already created won't be influenced)"""
        with self.__locker:
            if provider in self.providers:
                return
            self.providers.append(provider)

    def get_logger(self, name: str = None,
                   cfg: MsLogConfig = None) -> MsLogger:
        """Get (or create if not exits) a logger with specific logger name,
        or if 'name' is None, will return a logger with name 'default'"""
        if (name is None) or (name == 'default'):
            self.__create_default_logger(self.__dft_level)
            return self.__default_logger

        lgr = None
        with self.__all_loggers_locker:
            if self.__all_loggers.__contains__(name):
                lgr = self.__all_loggers[name]
            else:
                lgr = MsLogger(name, cfg.level
                               if cfg is not None else self.__dft_level)
                for pvd in self.providers:
                    wtr = pvd.get_writer(name, cfg)
                    lgr.add_writer(wtr)
                if self.__all_loggers.__contains__(lgr.name):
                    lgr = self.__all_loggers[lgr.name]
                else:
                    self.__all_loggers[lgr.name] = lgr
        return lgr
