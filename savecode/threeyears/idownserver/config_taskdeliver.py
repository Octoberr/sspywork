"""配置输出器"""

# -*- coding:utf-8 -*-

from .taskdeliver.taskdeliverconfig import TaskDeliverConfig

taskdeliverconfig = TaskDeliverConfig(
    # <ip, 目录> 的字典
    ipdir={
        "192.168.90.61": r"./_toclient/192.168.90.61",
        "192.168.90.62": r"./_toclient/192.168.90.62",
        "192.168.90.63": r"./_toclient/192.168.90.63",
        "192.168.90.64": r"./_toclient/192.168.90.64",
        "59.188.69.241": r"./_toclient/59.188.69.241",
    }
)
