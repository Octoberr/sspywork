"""data parser base"""

# -*- coding:utf-8 -*-

import io

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import DataSeg
from abc import ABCMeta, abstractmethod


class DataParserBase:
    """数据解析器接口"""

    __metaclass = ABCMeta

    def __init__(self):
        self._logger: MsLogger = MsLogManager.get_logger(
            self.__class__.__name__)

    def parse(self, stm: io.IOBase) -> iter:
        """当前解析器解析接口"""
        return self._parse_sub(stm)

    @abstractmethod
    def _parse_sub(self, stm: io.IOBase) -> iter:
        """子类解析数据据体实现"""
        pass
