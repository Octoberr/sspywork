"""Task parser"""

# -*- coding:utf-8 -*-

from abc import ABCMeta, abstractclassmethod

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import InputData, Task


class TaskParser:
    """任务解析接口"""

    def __init__(self):
        self._logger: MsLogger = MsLogManager.get_logger(__name__)

    @abstractclassmethod
    def convert(self, data: InputData)->iter:
        """解析InputData，返回Task生成器"""
        pass
