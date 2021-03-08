"""services"""

# -*- coding:utf-8 -*-

from abc import ABCMeta, abstractmethod

from commonbaby.mslog import MsLogger, MsLogManager
import threading


class MicroService:
    """represents a background service"""

    __metaclass = ABCMeta

    def __init__(self):
        self._logger: MsLogger = MsLogManager.get_logger('{}'.format(
            self.__class__.__name__))

    @abstractmethod
    def start(self):
        """start service"""
        raise NotImplementedError()

    @abstractmethod
    def stop(self):
        """stop service"""
        raise NotImplementedError()

    @abstractmethod
    def reload(self):
        """reload service"""
        raise NotImplementedError()
