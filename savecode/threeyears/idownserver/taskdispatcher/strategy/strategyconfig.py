"""task dispatch strategy config"""

# -*- coding:utf-8 -*-

from .stgunits import StrategyBase


class ExplicitFilters:
    """强制指定的任务分发策略，实例化后使用ExplicitFilters.xxx来使用\n
    目前就一个crosswall策略，后面要加显示策略加在这里即可"""

    @property
    def crosswall(self) -> bool:
        return self._crosswall

    @crosswall.setter
    def crosswall(self, value):
        if not isinstance(value, bool):
            raise Exception("Invalid strategy filter: {}".format(value))
        self._crosswall = value

    def __init__(self):
        self._crosswall: bool = None


class StrategyConfig:
    """任务分配策略单元配置。\n
    strategies: 对当前业务策略器(strategybuibase)启用的通用策略单元(strategybase)\n
    explicit_filters: dict,当前业务策略器(strategybuibase)需要强制采用的分配策略，
        例如{'crosswall':1}表示当前业务策略器仅将任务分配到crosswall=1的client"""

    def __init__(
            self,
            strategies: list,
    ):
        if not isinstance(strategies, list) or len(strategies) < 1:
            raise Exception("Task dispatch strategy config is invalid")

        for stra in strategies:
            if not issubclass(stra.__class__, StrategyBase):
                raise Exception(
                    "Task dispatch strategy config is invalid: %s" % stra[0])

        self._strategies = strategies
