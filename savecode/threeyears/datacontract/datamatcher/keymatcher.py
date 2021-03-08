"""data to key matcher"""

# -*- coding:utf-8 -*-

from .datamatcher import DataMatcher


class KeyMatcher(DataMatcher):
    """按传入的文本关键字匹配"""

    def __init__(self, vals: list):
        DataMatcher.__init__(self)

        if not isinstance(vals, list) or len(vals) < 1:
            raise Exception("Invalid param 'vals' for KeyMatcher")
        self._vals: list = vals

    def match_data(self, val) -> bool:
        """返回val是否匹配当前KeyMatcher设置的值"""
        if val in self._vals:
            return True
        return False
