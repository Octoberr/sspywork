"""status parser"""

# -*- coding:utf-8 -*-

import traceback

from commonbaby.helpers import helper_str
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import (DataSeg, InputData, StatusBasic, StatusTask,
                          StatusTaskInfo)
from dataparser import DataParser

from .statusparseconfig import StatusParseConfig


class StatusParser:
    """状态数据解析器"""

    def __init__(self, config: StatusParseConfig):
        if not isinstance(config, StatusParseConfig):
            raise Exception("Invalid param 'config' for StatusParser")
        self._config = config

        self._logger: MsLogger = MsLogManager.get_logger("status_parser")

    # def match_data(self, data: InputData) -> bool:
    #     for k in self._config._exts.keys():
    #         if data.extension.endswith(k):
    #             return True
    #     return False

    def is_status_basic(self, data: InputData) -> bool:
        """判断是不是Statusbasic数据"""
        return self._is_status_type(data, StatusBasic)

    def is_status_task(self, data: InputData) -> bool:
        """判断是不是StatusTask数据"""
        return self._is_status_type(data, StatusTask)

    def is_status_taskinfo(self, data: InputData) -> bool:
        """判断是不是StatusTaskInfo数据"""
        return self._is_status_type(data, StatusTaskInfo)

    def _is_status_type(self, data: InputData, tp: type) -> bool:
        """判断数据是否是指定数据类型"""
        configuredtype = self._get_data_type(data)
        if configuredtype is None:
            return False
        if not configuredtype is tp:
            return False
        return True

    def _get_data_type(self, data: InputData) -> type:
        """返回data是哪个类型的状态数据"""
        for i in self._config._exts.items():
            ext = i[0]
            if data.extension.endswith(ext):
                return i[1]
        return None

    def parse_status_basic(self, data: InputData) -> iter:
        """解析采集端基础状态数据，返回StatusBasic数据迭代器"""
        try:
            for dicseg in self._convert(data):
                dicseg: DataSeg = dicseg
                status: StatusBasic = StatusBasic(dicseg._fields)
                yield status

        except Exception:
            self._logger.error(
                "Parse status basic data error:\ndata:%s\nerror:%s" %
                (data._source, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)

    def parse_status_task(self, data: InputData) -> iter:
        """解析采集端任务状态数据，返回StatusTask数据迭代器"""
        try:
            for dicseg in self._convert(data):
                dicseg: DataSeg = dicseg
                status: StatusTask = StatusTask(dicseg._fields)
                yield status

        except Exception:
            self._logger.error(
                "Parse status task data error:\ndata:%s\nerror:%s" %
                (data._source, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)

    def parse_status_taskinfo(self, data: InputData) -> iter:
        """解析采集端单个任务详情数据，返回StatusTaskInfo迭代器"""
        try:
            for dicseg in self._convert(data):
                dicseg: DataSeg = dicseg
                status: StatusTaskInfo = StatusTaskInfo(dicseg._fields)
                yield status

        except Exception:
            self._logger.error(
                "Parse status task data error:\ndata:%s\nerror:%s" %
                (data._source, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)

    def _convert(self, data: InputData) -> iter:
        """读取数据，返回数据段的字典迭代器"""
        try:
            if data.stream is None or not data.stream.readable():
                self._logger.error(
                    "Data stream is None when trying to convert to standard Task: %s"
                    % data._source)
                return

            for dicseg in DataParser.parse_standard_data(data.stream):
                if dicseg is None or len(dicseg._fields) < 1:
                    continue
                yield dicseg

        except Exception:
            self._logger.error("Convert data to Task error:\ndata:%s\nex:%s" %
                               (data._source, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)
