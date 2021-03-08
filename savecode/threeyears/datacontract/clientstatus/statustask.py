"""client task status"""

# -*- coding:utf-8 -*-

import time
from datetime import datetime

import pytz

from datacontract.idowndataset.datafeedback import EStandardDataType
from ..outputdata import OutputData, OutputDataSeg


class StatusTask(OutputData, OutputDataSeg):
    """表示采集端的任务状态统计信息"""

    @property
    def time(self):
        if not type(self._time) in [int, float]:
            self._time = datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
        return self._time

    def __init__(self, allfields: dict):
        # 采集端所属平台， 对于状态数据来说是非必要的
        self.platform: list = self._judge(
            allfields, 'platform', dft='none')  
        OutputData.__init__(self, self.platform, EStandardDataType.StatusTask)
        OutputDataSeg.__init__(self)

        if not isinstance(allfields, dict) or len(allfields) < 1:
            raise Exception("All fields is None when initial StatusBasic")

        self._clientid = self._judge(allfields, 'clientid', error=True)

        # 当前数据产生时间 必要 在生成文件时再赋值
        self._time = self._judge(allfields, 'time')
        if self._time is None:
            self._time = datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
        # 任务统计
        self.tasknewcnt: int = self._judge(
            allfields, 'tasknewcnt', error=True)  # 新任务总数 必要
        self.taskwaitingcnt: int = self._judge(
            allfields, 'taskwaitingcnt', error=True)  # 等待队列任务数 必要
        self.taskdownloadingcnt: int = self._judge(
            allfields, 'taskdownloadingcnt', error=True)  # 正在执行的任务数量 必要

        # 控制端独有
        self.updatetime: float = self._judge(
            allfields, 'updatetime',
            dft=0)  # 时间戳，用东8区的时间戳，当前采集端的此类状态数据更新时间

    def get_task_status_info_lines(self):
        lines = ''
        lines += 'time:{}\r\n'.format(self.time)
        lines += 'clientid:{}\r\n'.format(self._clientid)
        lines += 'tasknewcnt:{}\r\n'.format(self.tasknewcnt)
        lines += 'taskwaitingcnt:{}\r\n'.format(self.taskwaitingcnt)
        lines += 'taskdownloadingcnt:{}\r\n'.format(self.taskdownloadingcnt)
        return lines.encode('utf-8')

    def has_stream(self) -> bool:
        return False

    def get_stream(self):
        return None

    def get_output_segs(self) -> iter:
        """"""
        self.segindex = 1
        yield self

    def get_output_fields(self) -> iter:
        """"""
        self.append_to_fields('time', self.time)
        self.append_to_fields('clientid', self._clientid)
        self.append_to_fields('tasknewcnt', self.tasknewcnt)
        self.append_to_fields('taskwaitingcnt', self.taskwaitingcnt)
        self.append_to_fields('taskdownloadingcnt', self.taskdownloadingcnt)
        return self._fields
