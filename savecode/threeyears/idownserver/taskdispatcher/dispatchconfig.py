"""task dispatcher config"""

# -*- coding:utf-8 -*-

import os

from ..config_output import outputdir
from .dispatcherbase import DispatcherBase


class DispatchConfig:
    """表示任务分发相关配置\n
    taskdispatchers: 实例化任务分配器\n
    maxwaitcount: 等待任务数据达到一定数量后一次性分配（也就是这一坨数据最终都分配给同一个采集端），默认为1条。\n
    maxwaittime: 等待任务数据时长，单位秒。当等待时长达到指定限制，不管有多少任务数据在等待分配，都直接分配一次，默认为3秒。\n"""

    def __init__(
            self,
            taskdispatchers: dict,
            maxwaitcount: int = 1,
            maxwaittime: float = 3,
    ):

        if not isinstance(taskdispatchers, dict):
            raise Exception("Specified taskdispatchers is invalid")
        if len(taskdispatchers) < 1:
            raise Exception("No taskdispatcher specified")
        for disp in taskdispatchers.items():
            if not issubclass(disp[1].__class__, DispatcherBase):
                raise Exception(
                    "Specified taskdispatcher is invalid: %s" % disp[0])
        self._taskdispatchers = taskdispatchers

        self._maxwaitcount: int = 1
        if isinstance(maxwaitcount, int) and maxwaitcount > 0:
            self._maxwaitcount = maxwaitcount

        self._maxwaittime: float = 3
        if type(maxwaittime) in [int, float] and maxwaittime > 0:
            self._maxwaittime = maxwaittime
