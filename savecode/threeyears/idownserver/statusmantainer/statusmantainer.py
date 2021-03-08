"""client status mantainance"""

# -*- coding:utf-8 -*-

import queue
import threading
import time
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import DataMatcher, InputData
from datacontract.clientstatus import (Client, StatusBasic, StatusTask,
                                       StatusTaskInfo)

from ..config_statusparse import statusparseconfig
from ..dbmanager.dbmanager import DbManager
from ..servicemanager import DealerBase
from .statusparser import StatusParser


class StatusMantainer(DealerBase):
    """采集端状态维护器\n
    datamatcher: 当前处理器的数据匹配器\n
    heartbeat: 查询心跳
    """

    _static_initialed: bool = False
    _static_initialed_locker = threading.RLock()

    _clientstatus_ip_sorted: dict = {}  # 采集端状态存储队列
    _clientstatus_locker_ip_sorted = threading.RLock()

    _clientstatus_id_sorted: dict = {}  # 采集端状态存储队列
    _clientstatus_locker_id_sorted = threading.RLock()

    def __init__(
            self,
            datamatcher: DataMatcher,
            heartbeat: float = 15,
    ):
        DealerBase.__init__(self, datamatcher)

        self._statusparser: StatusParser = StatusParser(statusparseconfig)

        # 心跳包单位秒
        self._heartbeat: float = 15
        if type(heartbeat) in [float, int] and heartbeat >= 2:
            self._heartbeat = heartbeat

        # 此处用一个实例开监控线程，监控到的client数据写入
        # classmethod静态字段即可
        self._t_status_monitor = threading.Thread(
            target=self._task_status_monitor,
            name="taskstatusmonitor",
            daemon=True)

    def _start(self):
        if StatusMantainer._static_initialed:
            return
        with StatusMantainer._static_initialed_locker:
            if StatusMantainer._static_initialed:
                return
            if not self._t_status_monitor._started._flag:
                self._t_status_monitor.start()
            StatusMantainer._static_initialed = True

    def _deal_data(self, data: InputData) -> bool:
        """处理状态数据，并存入数据库，返回bool指示是否成功"""
        res: bool = False
        try:
            if self._statusparser.is_status_basic(data):
                res = self.deal_status_basic(data)
            elif self._statusparser.is_status_task(data):
                res = self.deal_status_task(data)
            else:
                self._logger.error("Unrecognized status data: {}".format(
                    data.fullname))

        except Exception:
            self._logger.error("Deal status data error:\ndata:%s\nerror:%s" %
                               (data._source, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)
        return res

    def deal_status_basic(self, data: InputData) -> bool:
        """解析基础状态数据，存入数据库"""
        res: bool = False
        try:
            for status in self._statusparser.parse_status_basic(data):
                status: StatusBasic = status
                if not self._dbmanager.save_client_status_basic(status):
                    return res

            res = True
        except Exception:
            self._logger.error(
                "Deal status basic data error:\ndata:%s\nerror:%s" %
                (data._source, traceback.format_exc()))
        return res

    def deal_status_task(self, data: InputData) -> bool:
        """处理任务状态数据，存入数据库"""
        res: bool = False
        try:
            for status in self._statusparser.parse_status_task(data):
                status: StatusTask = status
                if not self._dbmanager.save_client_status_task(status):
                    return res

            res = True
        except Exception:
            self._logger.error(
                "Deal status task data error:\ndata:%s\nerror:%s" %
                (data._source, traceback.format_exc()))
        return res

    def _task_status_monitor(self):
        """采集端状态监视器，用于从数据库提取和维护采集端状态"""
        cnt = 0
        while True:
            try:
                statuses = DbManager.get_client_status_all(self._heartbeat)
                items = [s for s in statuses]

                with StatusMantainer._clientstatus_locker_ip_sorted:
                    # 清空重新添加，只添加在线的client
                    StatusMantainer._clientstatus_ip_sorted.clear()
                    for status in items:
                        StatusMantainer._clientstatus_ip_sorted[
                            status._statusbasic.ip] = status

                with StatusMantainer._clientstatus_locker_id_sorted:
                    # 清空重新添加，只添加在线的client
                    StatusMantainer._clientstatus_id_sorted.clear()
                    for status in items:
                        StatusMantainer._clientstatus_id_sorted[
                            status._statusbasic._clientid] = status

                cnt += 1
                if cnt >= 60:
                    self._logger.info(
                        f"Active clients: {[c for c in StatusMantainer._clientstatus_ip_sorted.keys()]}"
                    )
                    cnt = 0

            except Exception:
                self._logger.error("Task status monitor thread error: %s" %
                                   traceback.format_exc())
            finally:
                # 暂定为有一个硬性的查询间隔
                time.sleep(1)

    @classmethod
    def get_clientstatus_ip_sorted(cls) -> dict:
        """返回调用此属性时的最新采集端集合（字典<ip,client>）"""
        with StatusMantainer._clientstatus_locker_ip_sorted:
            return StatusMantainer._clientstatus_ip_sorted

    @classmethod
    def get_clientstatus_id_sorted(cls) -> dict:
        """返回调用此属性时的最新采集端集合（字典<ip,client>）"""
        with StatusMantainer._clientstatus_locker_id_sorted:
            return StatusMantainer._clientstatus_id_sorted