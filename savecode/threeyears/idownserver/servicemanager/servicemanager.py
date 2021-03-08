"""service manager"""

# -*- coding:utf-8 -*-

import os
import queue
import threading
import traceback

from commonbaby.helpers import helper_file
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import InputData

from ..config_dealer import dealerconfig
from ..taskdeliver.taskdelivermanager import TaskDeliverManager
from .dealerbase import DealerBase


class ServiceManager:
    """Dispatch data to different dealers,
    like client_status data, new task data,
    task feedback data, result data and so on."""

    # 所有处理器
    _dealers: list = []

    def __init__(self):
        self._logger: MsLogger = MsLogManager.get_logger("ServiceManager")

        # 所有处理器集合
        # 采集端状态管理器
        # 新任务分配器
        # 任务回馈数据处理器
        # 结果数据处理器
        ServiceManager._dealers = dealerconfig._dealers

        # 任务发送器（这个处理器不接收任何文件，是处理本地数据库消息的处理器，所以单独出来）
        self._delivermanager = TaskDeliverManager()

    def start(self):
        """处理器总开关"""
        for dealer in ServiceManager._dealers:
            if not dealer._started:
                dealer.start()
        self._delivermanager.start()

    def on_data_in(self, data: InputData):
        """data deal interface"""
        try:
            # status data
            # new task
            # taskback
            # feedbackdata

            ok: bool = False
            # 传给所有符合条件的dealer
            for d in ServiceManager._dealers:
                d: DealerBase = d
                if d._datamatcher.match_data(data):
                    d.on_data_in(data)
                    ok = True

            if not ok:
                self._logger.error("No dealer matches data: {}".format(
                    data.name))
                data.on_complete(False)

        except Exception:
            self._logger.error("On data in error:\ndata:%s\nerror:%s" %
                               (data, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)
