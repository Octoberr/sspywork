"""采集端状态数据解析器配置"""

# -*- coding:utf-8 -*-

from datacontract import (ExtMatcher, StatusBasic, StatusTask, StatusTaskInfo,
                          TaskBack)

from .statusmantainer import StatusParseConfig

statusparseconfig = StatusParseConfig(
    exts={
        'idown_status_basic': StatusBasic,
        'idown_status_task': StatusTask,
        'idown_status_tasks': StatusTaskInfo,
    })
