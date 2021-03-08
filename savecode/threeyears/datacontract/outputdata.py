"""output data"""

# -*- coding:utf-8 -*-

import enum
import io
from abc import ABCMeta, abstractmethod

from .dataseg import DataSeg


class EStandardDataType(enum.Enum):
    """数据类型枚举"""
    # 采集端状态数据
    StatusBasic = 1  # 采集端基本状态
    StatusTask = 2  # 采集端任务统计
    StatusTaskInfo = 3  # 采集端单个任务信息
    # IDownTask相关
    Task = 4
    TaskBack = 5
    TaskBatchBack = 6
    Profile = 7
    Resource = 8
    LoginLog = 9
    Contact = 10
    ChatGroup = 11
    ChatLog = 12
    Email = 13
    NetDiskList = 14
    NetDiskFile = 15
    ShoppingOrder = 16
    TravelOrder = 17
    TripOrder = 18
    # IDownCmd相关
    IDownCmd = 19  # IDownCmdBack在上面19，
    TaskCmdBack = 20
    # 用户状态信息
    UserStatus = 21
    # 任务下载日志回馈
    Client_log = 22
    # IScanTask相关
    IScanTask = 23
    IscanTaskBack = 24
    IscanBtaskBack = 25
    # IScoutTask相关
    IScoutTask = 26
    IscoutTaskBack = 27
    IscoutBtaskBack = 28
    IScoutScreenShotUrl = 29
    IScoutScreenShotSE = 30
    IScoutSearchengineFile = 31
    IScoutNetworkResource = 32  # 特定目标侦查资源数据
    # 自动化任务
    Autotask = 33
    Autotaskback = 34
    AutoBatchTaskBack = 35


OutputData = None


class OutputDataSeg(DataSeg):
    """output data segment，表示一个数据段"""

    __metaclass = ABCMeta

    @property
    def owner_data(self) -> OutputData:
        """返回当前数据段所属数据"""
        return self._owner_data

    @owner_data.setter
    def owner_data(self, value):
        if not isinstance(value, OutputData):
            raise Exception(
                "Invalid Outputdata object for data-seg's owner: {}".format(
                    value))
        self._owner_data = value

    def __init__(self):
        DataSeg.__init__(self)
        self._owner_data: OutputData = None

    @abstractmethod
    def get_output_fields(self) -> dict:
        """子类实现时，调用self._append_to_fields将字段添加到self._fields中"""
        raise NotImplementedError()


class OutputData_(DataSeg):
    """表示一个输出数据"""

    __metaclass = ABCMeta

    @property
    def on_complete(self) -> callable:
        """当前 OutputData 处理完成的回调函数"""
        return self.__on_complete

    @on_complete.setter
    def on_complete(self, func: callable):
        """当前 OutputData 处理完成的回调函数"""
        if not callable(func):
            raise Exception(
                "Invalid function for OutputData.on_complete: {}".format(func))
        self.__on_complete = func

    def __init__(self, platform: str, datatype: EStandardDataType):
        DataSeg.__init__(self)
        if not isinstance(platform, str) or platform == "":
            raise Exception("Invalid param 'platform' for OutputData")
        if not isinstance(datatype, EStandardDataType):
            raise Exception("Invalid param 'datatype' for OutputData")

        self._platform: str = platform
        self._datatype: EStandardDataType = datatype
        self.__on_complete: callable = None

    @abstractmethod
    def get_output_segs(self) -> iter:
        """返回当前数据要输出的 数据段 集合的生成器iterable"""
        raise NotImplementedError()

    @abstractmethod
    def has_stream(self) -> bool:
        """返回bool值指示当前数据是否有二进制流"""
        raise NotImplementedError()

    @abstractmethod
    def get_stream(self) -> io.RawIOBase:
        """如果当前数据有二进制数据流，返回此流对象，否则返回None"""
        return None

    @abstractmethod
    def validate_file(self, fipath: str) -> bool:
        """自验证一个数据文件是否合法，暂时只在输出到文件中后被调用了。"""
        return True


OutputData = OutputData_
