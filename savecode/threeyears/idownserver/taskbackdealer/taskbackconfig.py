"""task feedback data dealer config"""

# -*- coding:utf-8 -*-

from .taskbackdealerbase import TaskBackDealerBase


class TaskBackConfig:
    """采集端任务回馈数据处理配置"""

    def __init__(self, dealers: dict):
        if dealers is None or len(dealers) < 1:
            raise Exception(
                "No any taskbackdealer configured in config_taskback.py")

        self._dealers: dict = {}
        for dealer in dealers.items():
            key: str = dealer[0]
            dealer: TaskBackDealerBase = dealer[1]
            if not isinstance(key, str):
                raise Exception("Invalid key for taskbackdealer")
            if not isinstance(dealer, TaskBackDealerBase):
                raise Exception("Invalid taskbackdealer object")
            self._dealers[key] = dealer
