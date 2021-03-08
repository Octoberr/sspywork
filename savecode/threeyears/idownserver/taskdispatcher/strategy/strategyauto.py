"""strategybase for diff tasktypes"""

# -*- coding:utf-8 -*-

import traceback

from datacontract import AutomatedTask, Client

from .strategybuibase import StrategyBuisinessBase


class StrategyAutoTask(StrategyBuisinessBase):
    """"""

    def __init__(self):
        StrategyBuisinessBase.__init__(self)

    def match(self, task) -> bool:
        """"""
        if isinstance(task, AutomatedTask):
            return True
        return False

    def _dispatch(self, task: AutomatedTask,
                  clients: dict) -> (bool, Client, str):
        """按策略择最优采集端。\n
        task: 要分配的任务（必然为子任务对象，带有taskid和batchid）。\n
        clients: 要从中挑选出目标client的采集端 Client对象 列表。
        return:返回 唯一一个 选中的采集端对象 (bool是否成功,client,msg)"""
        succ: bool = False
        res: Client = None
        msg: str = None
        try:
            if not isinstance(task, AutomatedTask):
                raise Exception("Invalid IScanTask: {}".format(task))

            # 这里过来的就是按 buisiness 过滤好的clients集合，
            # 直接取最高分分配即可。
            res = self._get_highest_score(clients)
            succ = True
        except Exception:
            succ = False
            res = None
            self._logger.error(
                "Dispatch task error:\ntaskid:{}\nbatchid:{}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()))
        return (succ, res, msg)
