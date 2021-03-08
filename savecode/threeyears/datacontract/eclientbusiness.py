"""Client Buisiness"""

# -*- coding:utf-8 -*-

from enum import Enum


class EClientBusiness(Enum):
    """表示采集端启用的业务类型（任务类型），
    使用时直接将多个值相加表示多个业务"""

    # 未指定/启用所有业务
    ALL = 0
    # 启用 IDownTask任务
    IDownTask = 1
    # 启用 IScanTask任务
    IScanTask = 2
    # 启用 IScout任务
    IScoutTask = 4
    # 启用自动任务
    AutoTask = 5
