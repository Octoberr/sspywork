"""tasklen strategy"""

# -*- coding:utf-8 -*-

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import Client, Task

from .strategybase import StrategyBase


class StgTaskLen(StrategyBase):
    """crosswall strategy。
    任务队列长度排序策略"""

    def __init__(self, name: str, weight: float = 1, isforced: bool = True):
        super(StgTaskLen, self).__init__(name, weight, isforced)

    def get_score(self, clients: list) -> dict:
        """给给与的采集端计算分数，返回<client, 分数>"""
        # 按队列长度降序排序
        sorted_cliens: list = [
            c for c in sorted(
                clients,
                key=lambda c: c._statustask.tasknewcnt is not None and c.
                _statustask.tasknewcnt)
        ]
        res: dict = {}
        # 采集端带宽占用分数最高分=列表长度，
        # 分数按带宽占用率降序依次减一 * 权重比
        currscore = len(sorted_cliens)
        for c in sorted_cliens:
            c: Client = c
            res[c] = currscore * self._weight
            currscore -= 1 * self._weight

        return res
