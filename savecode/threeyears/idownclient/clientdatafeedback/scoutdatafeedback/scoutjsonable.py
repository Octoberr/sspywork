"""可以输出dict的数据结构"""

# -*- coding:utf-8 -*-

from abc import ABCMeta, abstractmethod


class ScoutJsonable(object):
    """预留接口，暂时没用。
    可以输出dict的数据结构。"""

    __metaclass = ABCMeta

    def __init__(self, suffix: str = None):
        # 这里过来的不一定有suffix，因为可能就是为了继承一下
        # get_outputdict这个接口，并不需要直接输出
        self._suffix: str = suffix

    @abstractmethod
    def get_outputdict(self) -> dict:
        """返回输出数据字段字典，用于构造json数据体"""
        raise NotImplementedError()