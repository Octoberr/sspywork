"""配置命令数据分发策略"""

# -*- coding:utf-8 -*-

from datacontract import (AutomatedTask, EClientBusiness, IscanTask,
                          IscoutTask, Task)

from .taskdispatcher.strategy import StgBandWidth, StgTaskLen
from .taskdispatcher.strategy.strategyconfig import (ExplicitFilters,
                                                     StrategyConfig)

stgconfig: StrategyConfig = StrategyConfig(strategies=[
    StgBandWidth("bandwidth", 1, False),
    StgTaskLen("tasklen", 1, False),
])

# EClientBusiness
clientbusiness_mapping: dict = {
    Task: EClientBusiness.IDownTask,
    IscanTask: EClientBusiness.IScanTask,
    IscoutTask: EClientBusiness.IScoutTask,
    AutomatedTask: EClientBusiness.AutoTask,
}

# iscan filters
iscanfilters: ExplicitFilters = ExplicitFilters()
iscanfilters.crosswall = True

# iscout filters
iscoutfilters: ExplicitFilters = ExplicitFilters()
iscoutfilters.crosswall = True
