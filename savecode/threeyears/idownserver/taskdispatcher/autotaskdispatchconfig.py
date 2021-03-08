"""automatedtask dispatch config"""

# -*- coding:utf-8 -*-

from datacontract.automateddataset.automatedtask import EAutoType


class AutoTaskConfig:
    """自动化任务的配置\n
        tasktype: 当前自动化任务配置的任务类型\n
        platform:平台\n
        source:source\n
        interval:两次任务之间的时间间隔，单位秒，默认为1天\n
        enable:是否启用/开启当前自动化任务\n
        seperatetask:是否分割任务到多个采集端同时执行（暂不支持分割）"""

    _AUTO_TASK_CONF: dict = {}

    def __init__(
            self,
            tasktype: EAutoType,
            enable: bool = True,
            platform: str = "zplus",
            source: str = "zplus",
            interval: int = 86400,
            seperatetask: bool = False,
    ):
        if not isinstance(tasktype, EAutoType):
            raise Exception("Invalid AutoTaskType: {}".format(tasktype))
        if not isinstance(platform, str) or platform == "":
            raise Exception(
                "Invalid platform for AutoTaskType: {}".format(platform))
        if not isinstance(source, str) or source == "":
            raise Exception(
                "Invalid source for AutoTaskType: {}".format(source))
        if not isinstance(interval, int):
            raise Exception(
                "Invalid interval for AutoTaskType: {}".format(interval))
        if not isinstance(enable, bool):
            raise Exception(
                "Invalid enable for AutoTaskType: {}".format(enable))
        if not isinstance(seperatetask, bool):
            raise Exception("Invalid seperatetask for AutoTaskType: {}".format(
                seperatetask))

        if not AutoTaskConfig._AUTO_TASK_CONF.__contains__(tasktype):
            AutoTaskConfig._AUTO_TASK_CONF[tasktype] = {}

        if AutoTaskConfig._AUTO_TASK_CONF[tasktype].__contains__(platform):
            raise Exception("Duplicated AutoTaskConfig for: {} : {}".format(
                tasktype.name, platform))

        AutoTaskConfig._AUTO_TASK_CONF[tasktype][platform] = self

        self._tasktype: EAutoType = tasktype
        self._platform: str = platform
        self._source: str = source
        self._interval: int = interval
        self._enable: bool = enable
        self._seperatetask: bool = seperatetask
