"""task deliver manager"""

# -*- coding:utf-8 -*-

import inspect
import sys
import threading
import traceback

from datacontract import DataMatcher, InputData

from ..config_taskdeliver import taskdeliverconfig
from ..servicemanager import MicroService
# from .cmddeliver import CmdDeliver
# from .iscantaskdeliver import IScanTaskDeliver
# from .taskdeliver import TaskDeliver
# from .iscouttaskdeliver import IScoutTaskDeliver
from .taskdeliverbase import TaskDeliverBase


class TaskDeliverManager(MicroService):
    """"""

    def __init__(self):
        MicroService.__init__(self)
        self._delivers: dict = {}
        self.__init_delivers()

        self._istarted: bool = False
        self._startlocker = threading.RLock()

        TaskDeliverBase.static_init(taskdeliverconfig)

    def __init_delivers(self):
        # self._delivers: dict = {
        #     "taskdeliver": TaskDeliver(),
        #     "cmddeliver": CmdDeliver(),
        #     "iscantaskdeliver": IScanTaskDeliver(),
        #     "iscouttaskdeliver": IScoutTaskDeliver(),
        # }
        clsmembers = inspect.getmembers(
            sys.modules[__package__],
            lambda o: inspect.isclass(o) and not o is TaskDeliverBase and
            issubclass(o, TaskDeliverBase),
        )
        for clsname in clsmembers:
            dlvr: TaskDeliverBase = clsname[1]()
            self._delivers[dlvr.__class__.__name__] = dlvr

    def start(self):
        """start service"""
        if self._istarted:
            return
        with self._startlocker:
            if self._istarted:
                return
            for deliver in self._delivers.values():
                deliver: TaskDeliverBase = deliver
                deliver.start()
            self._istarted = True

    def stop(self):
        """stop service"""
        raise NotImplementedError()

    def reload(self):
        """reload service"""
        raise NotImplementedError()
