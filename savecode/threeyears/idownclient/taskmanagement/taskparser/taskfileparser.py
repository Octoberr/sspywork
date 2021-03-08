"""Task file parser"""

# -*- coding:utf-8 -*-

import traceback

from commonbaby.helpers import helper_str

from datacontract import DataSeg, InputData, Task, IscanTask, IscoutTask
from datacontract.automateddataset import AutomatedTask
from datacontract.idowncmd import IdownCmd
from idownclient.config_client import basic_client_config
# from idownclient.dnsreq import DnsData
from .taskparser import TaskParser


class TaskFileParser(TaskParser):
    """文件解析成任务"""

    def __init__(self):
        super(TaskFileParser, self).__init__()

    def _taskparse(self, data: dict, file_suffix: str):
        """
        用于判断不同的任务类型
        目前有：idowntask
                idowncmd
        后面应该根据文件的后缀来判断文件类型
        所以后面这个方法要改
        add by judy 2019/06/11
        :param data:
        :return:
        """
        if file_suffix is None:
            raise Exception("To distinguish file types, file_suffix can not be None.")
        # 单独处理an_dns的数据 add by judy 2020/03/04
        # if file_suffix == 'an_dns_client':
        #     return DnsData(data)
        # 初始化数据要增加clientid,这样无论是task，和idowncmd就会有clientid了
        data['clientid'] = basic_client_config.clientid
        if file_suffix == 'idown_task':
            return Task(data)
        elif file_suffix == 'idown_cmd':
            return IdownCmd.parse_from_dict(data)
        elif file_suffix == 'iscan_task':
            return IscanTask(data)
        elif file_suffix == 'iscout_task':
            return IscoutTask(data)
        elif file_suffix == 'automated_task':
            return AutomatedTask.create_from_dict(data)
        # -------------------------------------这些东西目前改了，用后缀来判断任务类型，这样更准确些
        # if data.get('taskid') is not None:
        #     taskid 不为空目前一定是task
        # return Task(data)
        # elif data.get('taskid') is None and data.get('cmdid') is not None:
        #     没有taskid但是有cmdid
        # return IdownCmd.parse_from_dict(data)
        else:
            # 希望别走到这，走到这就说明这个任务解析错了
            self._logger.error('Unkown task type')

    def convert(self, data: InputData) -> iter:
        """解析InputData，返回Task生成器"""
        try:
            for dataseg in self._convert(data):
                try:
                    if not isinstance(dataseg, DataSeg) or not any(dataseg._fields):
                        continue
                    # 获取到的数据可能会有很多类型
                    get_data: dict = dataseg._fields
                    task = self._taskparse(get_data, data.extension)
                    yield task
                except Exception:
                    self._logger.error(
                        "Init Task object error:\ndata:%s\nerror:%s" %
                        (data._source, traceback.format_exc()))
                    if isinstance(data, InputData):
                        data.on_complete(False)
        except Exception:
            self._logger.error("Parse task error:\ndata:%s\nerror:%s" %
                               (data._source, traceback.format_exc()))
            if isinstance(data, InputData):
                data.on_complete(False)

    def _convert(self, data: InputData) -> iter:
        """读取数据，返回数据段的字典迭代器"""
        try:
            if data.stream is None or not data.stream.readable():
                self._logger.error(
                    "Data stream is None when trying to convert to standard Task: %s"
                    % data._source)
                return

            for dicseg in self._get_segments(data):
                if dicseg is None or len(dicseg._fields) < 1:
                    continue

                yield dicseg

        except Exception:
            self._logger.error("Convert data to Task error:\ndata:%s\nex:%s" %
                               (data._source, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)

    def _get_segments(self, data: InputData) -> iter:
        """读取数据流，返回数据段枚举"""
        try:

            if data.stream is None or not data.stream.readable():
                self._logger.error(
                    "Data stream is None when trying to convert to standard Task: %s"
                    % data._source)
                return

            segidx = 1
            seg: DataSeg = DataSeg()
            prevline: str = None
            for line in data.stream:
                if line is None or line == "":
                    break

                if (line == '\n' or line == '\r\n') and (prevline == '\n' or
                                                         prevline == '\r\n'):
                    seg.segindex = segidx
                    segidx += 1
                    yield seg
                    seg = DataSeg()

                k, v = helper_str.get_kvp(line, ':')
                if not k is None and not k == "":
                    # 这里若遇到键相同，容错处理只保留第一次读到的键值对
                    v = helper_str.base64_decode_format(v)
                    if not seg._fields.__contains__(k):
                        seg._fields[k] = v.strip()

                prevline = line

            if not seg is None and len(seg._fields) > 0:
                yield seg

        except Exception:
            self._logger.error("Read data segments error:\ndata:%s\nex:%s" %
                               (data._source, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)
