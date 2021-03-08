"""data extension matcher"""

# -*- coding:utf-8 -*-

from .datamatcher import DataMatcher


class ExtMatcher(DataMatcher):
    """数据后缀匹配\n
    exts:当前匹配器要匹配的数据后缀（前面不带点.）"""

    def __init__(self, exts: list):
        DataMatcher.__init__(self)

        if not isinstance(exts, list) or len(exts) < 1:
            raise Exception("Invalid param 'exts' for ExtMatcher")

        self._exts: dict = {}
        for e in exts:
            if not isinstance(e, str) or e == "":
                continue
            e = e.strip().lstrip('.')
            if not self._exts.__contains__(e):
                self._exts[e] = e

    def match_data(self, data) -> bool:
        """返回给予的data是否是当前匹配器匹配的platform过来的"""
        # InputData数据结构里的extension字段
        if hasattr(data, 'extension') and self._exts.__contains__(
                data.extension):
            return True
        elif hasattr(data, '_extension') and self._exts.__contains__(
                data._extension):
            return True
        return False
