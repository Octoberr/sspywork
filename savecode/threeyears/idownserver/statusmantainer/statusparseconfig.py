"""client status parse config"""

# -*- coding:utf-8 -*-


class StatusParseConfig:
    """状态数据解析器配置\n
    datamatcher:数据匹配器"""

    def __init__(self, exts: dict):
        if not isinstance(exts, dict) or len(exts) < 1:
            raise Exception("Invalid param 'exts' for StatusParseConfig")
        self._exts: dict = {}
        for i in exts.items():
            e = i[0]
            t = i[1]
            if not isinstance(e, str) or e == "":
                continue
            if not isinstance(t, type):
                continue
            e = e.strip().lstrip('.')
            if not self._exts.__contains__(e):
                self._exts[e] = t
