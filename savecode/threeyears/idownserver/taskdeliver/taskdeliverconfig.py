"""task dispatcher config"""

# -*- coding:utf-8 -*-

import enum
import os

import IPy
from commonbaby.helpers import helper_str

class TaskDeliverConfig:
    """表示任务数据文件传输配置（只有走文件传输才需要此配置），
    后面走直连了可以不要这个配置了。\n
    ipdir: 采集端ip到目标目录的dict: <ip, dir>"""

    def __init__(self, ipdir: dict):
        if not isinstance(ipdir, dict) or len(ipdir) < 1:
            raise Exception("Invalid param 'ipdir' for TaskDeliverConfig")

        self._ipdir: dict = {}
        for i in ipdir.items():
            ip: str = i[0]
            di: str = i[1]
            if helper_str.is_none_or_empty(ip) or helper_str.is_none_or_empty(
                    di):
                raise Exception(
                    "Invalid ip->dir key value pair: {}->{}".format(ip, di))
            self._ipdir[ip] = di
