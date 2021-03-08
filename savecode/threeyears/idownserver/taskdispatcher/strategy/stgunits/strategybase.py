"""task dispatch strategy"""

# -*- coding:utf-8 -*-

from abc import ABCMeta, abstractclassmethod

from commonbaby.mslog import MsLogger, MsLogManager


class StrategyBase:
    """表示一个任务分配策略。\n
    name: 策略唯一标识。\n
    weight: 当前策略所占分数权重比，默认为1，例如如果未1.2，则当前策略分数结果会乘以1.2。\n
    isforced: 当前策略是否为硬性策略，即只有符合当前策略的采集端才能最终被选定。"""

    __metaclass = ABCMeta

    def __init__(self, name: str, weight: float = 1, isforced: bool = True):
        if not isinstance(name, str) or name == "":
            raise Exception("Strategy param name is invalid.")
        if not type(weight) in [int, float] or weight < 0:
            raise Exception("Strategy param weight is invalid: %s" % name)
        if not isinstance(isforced, bool):
            raise Exception("Strategy param isforced is invalid: %s" % name)

        self._name = name
        self._weight = weight
        self._isforced = isforced

        self._logger: MsLogger = MsLogManager.get_logger("strategy_%s" % name)

    @abstractclassmethod
    def get_score(self, clients: list) -> dict:
        """给给与的采集端计算分数，返回<client, 分数>"""
        pass
