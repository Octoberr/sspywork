"""automated task"""

# -*- coding:utf-8 -*-

from .taskdispatcher.autotaskdispatchconfig import AutoTaskConfig
from datacontract import EAutoType

autotaskconfigs: list = [
    AutoTaskConfig(
        enable=False,
        tasktype=EAutoType.DBIP,
        platform="zplus",
        source="zplus",
        interval=86400,
        seperatetask=False,
    ),
    AutoTaskConfig(
        enable=False,
        tasktype=EAutoType.EXPDB,
        platform="zplus",
        source="zplus",
        interval=10,
        seperatetask=False,
    ),
    AutoTaskConfig(
        enable=False,
        tasktype=EAutoType.GEONAME,
        platform="zplus",
        source="zplus",
        interval=30*24*3600,
        seperatetask=False,
    )
]
