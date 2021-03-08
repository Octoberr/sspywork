"""client tasks status"""

# -*- coding:utf-8 -*-

from datacontract.idowndataset.datafeedback import EStandardDataType
from ..outputdata import OutputData, OutputDataSeg
from datacontract.idowndataset.task import ETaskStatus, ETaskType


class StatusTaskInfo(OutputData, OutputDataSeg):
    """表示单个任务状态信息"""

    def __init__(self, allfields: dict):
        # 采集端所属平台， 对于任务信息来说是必要的
        self.platform: str = self._judge(
            allfields, 'platform', error=True)  # 当前任务所属平台
        OutputData.__init__(self, self.platform,
                            EStandardDataType.StatusTaskInfo)
        OutputDataSeg.__init__(self)

        if not isinstance(allfields, dict) or len(allfields) < 1:
            raise Exception("All fields is None when initial StatusBasic")

        self._clientid = self._judge(allfields, 'clientid', error=True)

        self.time: str = None  # 当前数据产生时间 必要 在生成文件时再赋值

        # 单个任务信息 必要
        self.taskid: str = self._judge(
            allfields, 'taskid', error=True)  # 单个任务的任务id

        self.tasktype: ETaskType = ETaskType(
            int(self._judge(allfields, 'tasktype', error=True)))  # 当前任务的任务类型
        self.status: ETaskStatus = ETaskStatus(
            self._judge(allfields, 'status', error=True))  # 当前任务执行状态
        # 当前任务的保活状态 0无效（无效的直接删除） 1有效 2失效（连续3次下载失效的任务删除）
        self.efficient: int = self._judge(allfields, 'efficient', error=True)

        # 非必要
        # 当前任务创建时间（时间字符串 yy-MM-dd HH:mm:ss）
        self.createtime: str = self._judge(allfields, 'createtime', error=True)
        self.lastexecutetime: str = self._judge(
            allfields, 'lastexecutetime', error=True)  # 当前任务最后访问时间（时间字符串）
        self.apptype: int = self._judge(allfields, 'apptype')  # 当前任务所属app网站类型
        self.datacount: int = self._judge(allfields,
                                          'datacount')  # 当前任务已下载数据个数
        self.datasize: float = self._judge(allfields,
                                           'datasize')  # 当前任务已下载数据量大小（单位Kb）

        # 控制端独有
        # 时间戳，直接用time.time()，当前采集端的此类状态数据更新时间
        self.updatetime: float = self._judge(allfields, 'updatetime')

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
