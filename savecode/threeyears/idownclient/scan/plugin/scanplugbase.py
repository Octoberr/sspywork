"""
现在scan需要自己去扫描走一个扫描流程
插件的一些公用数据和方法
可能每个子类需要的流程不太一样
所以子类有可能都是独立的
create by judy 2019/07/10
"""

# -*- coding:utf-8 -*-

from commonbaby.mslog import MsLogger, MsLogManager
# from idownclient.config_detectiontools import dtools


class ScanPlugBase(object):
    """每个具体scouter插件的实现类base"""

    def __init__(self, loggername: str = None):
        # 插件名字
        self._name = type(self).__name__
        if isinstance(loggername, str) and loggername != "":
            self._name = loggername
        self._logger: MsLogger = MsLogManager.get_logger(f"{self._name}")
        # reason
        # self.d_tools = dtools
