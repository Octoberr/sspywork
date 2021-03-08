"""EProxyType"""

# -*- coding:utf-8 -*-

from enum import Enum


class EProxyType(Enum):
    """代理类型"""

    Unknow = 0
    HTTP = 1
    Socks = 2
