"""data to outputer matcher"""

# -*- coding:utf-8 -*-

from abc import ABCMeta, abstractmethod


class DataMatcher:
    """匹配数据到处理器的匹配器\n
    默认匹配器在匹配时全部返回true，
    要实现匹配控制需要重载\n
    innermatchers:DataMatcher对象列表，用于构建匹配流，按顺序
    每一个innerDataMatcher都匹配成功时，才算匹配成功。"""

    __metaclass = ABCMeta

    def __init__(self, innermatchers: list = None):
        self._innermatchers: list = []
        if isinstance(innermatchers, DataMatcher) and len(innermatchers) > 0:
            for i in innermatchers:
                self.append_datamatcher(i)

    def append_datamatcher(self, datamatcher):
        """添加内部匹配器"""
        if not isinstance(datamatcher, DataMatcher):
            raise Exception("Invalid DataMatcher object for innermatcher")
        self._innermatchers.append(datamatcher)

    @abstractmethod
    def match_data(self, data) -> bool:
        """判断一个要数据是否满足当前匹配器的条件，返回bool
        指示True是/False否"""
        return True
