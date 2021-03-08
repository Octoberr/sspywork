"""data to clientid matcher"""

# -*- coding:utf-8 -*-

from .datamatcher import DataMatcher


class ClientidMatcher(DataMatcher):
    """匹配数据是否与指定clientid关联"""

    def __init__(self, clientid: str):
        DataMatcher.__init__(self)

        if not isinstance(clientid, str) or clientid == "":
            raise Exception("Invalid param 'clientid' for ClientidMatcher")
        self._clientid = clientid

    def match_data(self, data) -> bool:
        """返回data是否匹配指定clientid"""
        if hasattr(data, '_clientid') and data._clientid == self._clientid:
            return True
        elif hasattr(data, 'clientid') and data.clientid == self._clientid:
            return True
        return False
