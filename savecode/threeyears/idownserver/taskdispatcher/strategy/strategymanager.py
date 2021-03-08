"""manage all strategies"""

# -*- coding:utf-8 -*-

import random
import traceback
from typing import Tuple

from commonbaby.helpers import helper_str
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import Client

from ...config_strategy import stgconfig
from .strategyauto import StrategyAutoTask
from .strategybuibase import StrategyBuisinessBase
from .strategyidowntask import StrategyIDownTask
from .strategyiscan import StrategyIScanTask
from .strategyiscout import StrategyIScoutTask


class StrategyManager:
    """管理所有任务分配策略，并提供调用接口。"""
    def __init__(self):

        self._strategies: list = []

        StrategyBuisinessBase.static_init(stgconfig)
        self._stgidowntask: StrategyIDownTask = StrategyIDownTask()
        self._strategies.append(self._stgidowntask)

        self._stgiscantask: StrategyIScanTask = StrategyIScanTask()
        self._strategies.append(self._stgiscantask)

        self._stgiscouttask: StrategyIScoutTask = StrategyIScoutTask()
        self._strategies.append(self._stgiscouttask)

        self._stgautotask: StrategyAutoTask = StrategyAutoTask()
        self._strategies.append(self._stgautotask)

        # 其他
        self._logger: MsLogger = MsLogManager.get_logger("strategymanager")

    def dispatch(self, task, clients: dict) -> Tuple[bool, Client, str]:
        """按策略择最优采集端。\n
        task: 要分配的任务（必然为子任务对象，带有taskid和batchid）。\n
        clients: 要从中挑选出目标client的采集端 Client对象 列表。
        return:返回 唯一一个 选中的采集端对象 (bool是否成功,client,msg)"""
        succ: bool = False
        res: Client = None
        msg: str = None
        try:

            for stg in self._strategies:
                stg: StrategyBuisinessBase = stg
                if not stg.match(task):
                    continue

                succ, res, msg = stg.dispatch(task, clients)
                break

        except Exception:
            succ = False
            res = None
            self._logger.error("Dispatch task error:\ntaskid:%s\nerror:%s" %
                               (task.taskid, traceback.format_exc()))
        return (succ, res, msg)
