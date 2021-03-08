"""EProxyAnonymity"""

# -*- coding:utf-8 -*-

from enum import Enum


class EProxyAnonymity(Enum):
    """代理匿名类型"""

    Unknow = 0  # 不晓得的
    Transparent = 1  # 普通/透明代理
    Anonymous = 2  # 匿名
    Elite = 3  # 高匿
