"""
程序扫描日志的标准格式
create by judy 2020/08/10
"""
from datetime import datetime

import pytz

from idownclient.config_client import basic_client_config
from ..idowndataset import Task
from ..iscandataset import IscanTask
from ..iscoutdataset import IscoutTask


class PrglogBase(object):
    def __init__(self, name, version, log, task, loglevel=1):
        # client或者server的名字
        # 这个task可能是idowntask，iscantask, iscouttask
        if name is None:
            raise Exception('Prglog name cant be None')
        if version is None:
            raise Exception('Prglog version cant be None')
        if log is None:
            raise Exception('Prglog log cant be None')
        if task is None:
            raise Exception('Prglog task cant be None')
        self.task = task
        self.name = name
        self.version = version
        self.log = log
        # 每次时间实时获取
        self.logtime = datetime.now(
            pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S.%f')
        self.sequence = self.task.sequence
        self.host = basic_client_config.ip
        self.loglevel = loglevel  # 1正常日志2调试日志3错误日志
        self.taskid = self.task.taskid
        # ----------------------------非必要字段
        self.tasktype = None
        self.other = []
        # 添加模块标识
        self._module = None
        if isinstance(self.task, IscanTask):
            self._module = "iscan"
        elif isinstance(self.task, IscoutTask):
            self._module = "iscout"
        elif isinstance(self.task, Task):
            self._module = "idown"

    def output_dict(self):
        """
        输出还是手动写一下
        """
        res = {}
        res['name'] = self.name
        res['version'] = self.version
        res['log'] = self.log
        res['logtime'] = self.logtime
        res['sequence'] = self.sequence
        # if self.host is not None:
        res['host'] = self.host
        res['loglevel'] = self.loglevel
        res['taskid'] = self.taskid
        res['module'] = self._module
        if self.tasktype is not None:
            res['tasktype'] = self.tasktype
        if len(self.other) > 0:
            res['other'] = self.other
        return res
