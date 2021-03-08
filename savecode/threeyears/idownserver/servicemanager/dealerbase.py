"""data dealer interfaces"""

# -*- coding:utf-8 -*-

import queue
import threading
import traceback
from abc import ABCMeta, abstractmethod

from datacontract import DataMatcher, InputData

from ..dbmanager.dbmanager import DbManager
from .microservice import MicroService


class DealerBase(MicroService):
    """declares interfaces of data dealers\n
    datamatcher: 数据匹配器，用于匹配当前处理器应处理的数据"""

    __metaclass = ABCMeta

    ## 各处理器
    # 数据库
    __dbmanager: DbManager = DbManager()

    @property
    def _dbmanager(self) -> DbManager:
        """数据库"""
        return DealerBase.__dbmanager

    def __init__(self, datamatcher: DataMatcher):
        MicroService.__init__(self)

        if not isinstance(datamatcher, DataMatcher):
            raise Exception(
                "Invalid DataMatcher object: {}".format(datamatcher))

        self._datamatcher: DataMatcher = datamatcher
        # queue and thread for dealing.
        # in order to manage deal pipe.
        self._queue: queue.Queue = queue.Queue()
        self._tdeal = threading.Thread(
            target=self.__dealdata, name=self.__class__.__name__)
        self._started: bool = False
        self.__startlocker = threading.Lock()

    def start(self):
        """开始处理"""
        if self._started:
            return
        with self.__startlocker:
            if self._started:
                return
            self._tdeal.start()
            self._start()
            self._started = True

    @abstractmethod
    def _start(self):
        """子类实现时，启动以开始处理"""
        pass

    def on_data_in(self, data: InputData):
        """当前处理器的数据输入接口"""
        try:
            if data is None:
                self._logger.error("Data is None")
                return

            self._queue.put(data)

        except Exception:
            self._logger.error("Deal data error: {} {}".format(
                data.name, traceback.format_exc()))

    def __dealdata(self):
        """Private dealing thread for each dealer"""
        got: bool = False
        res: bool = False
        while True:
            try:
                res = False

                got = False
                data: InputData = self._queue.get(block=True, timeout=3)
                got = True

                if data is None or not isinstance(data, InputData):
                    continue

                self._logger.debug("Deal data: %s" % data.name)

                res = self._deal_data(data)

            except queue.Empty:
                continue
            except Exception:
                self._logger.error("Dealing thread error: {}".format(
                    traceback.format_exc()))
                if not data is None:
                    data.on_complete(False)
            finally:
                if got:
                    self._queue.task_done()
                # res 为 None 的情况为 子类自行处理 data 的完成状态
                if got and not data is None and not res is None:
                    data.on_complete(res)
                    # if res:
                    #     self._logger.info("Data OK: {}".format(data.name))
                    # else:
                    #     self._logger.error("Data Failed: {}".format(data.name))

    @abstractmethod
    def _deal_data(self, data: InputData) -> bool:
        """子类实现时，根据功能划分处理相应的数据，并返回bool值指示是否成功"""
        self._logger.error(
            "Not implement for dealing, check method reload: {}".format(
                data.name))
        if not data is None:
            data.on_complete(False)
        return False
