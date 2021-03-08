"""data platform matcher"""

# -*- coding:utf-8 -*-

from ..outputdata import OutputData
from .datamatcher import DataMatcher


class PlatformMatcher(DataMatcher):
    """平台匹配"""

    def __init__(self, targetplatform: str):
        DataMatcher.__init__(self)

        if not isinstance(targetplatform, str) or targetplatform == "":
            raise Exception(
                "Invalid param 'targetplatform' for PlatformMatcher")
        self._targetplatform = targetplatform

    def match_data(self, data) -> bool:
        """返回给予的data是否是当前匹配器匹配的platform过来的"""
        if hasattr(data,
                   '_platform') and data._platform == self._targetplatform:
            return True
        elif hasattr(data,
                     'platform') and data.platform == self._targetplatform:
            return True
        return False
