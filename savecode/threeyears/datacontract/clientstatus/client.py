"""client status wrapper"""

# -*- coding:utf-8 -*-

from .statusbasic import StatusBasic
from .statustask import StatusTask


class Client:
    """表示采集端总体状态，就是把各种状态包装一下，仅服务端使用"""

    def __init__(self,
                 sbasic: StatusBasic,
                 stask: StatusTask,
                 staskinfo: list = None):
        if not isinstance(sbasic, StatusBasic) or sbasic is None:
            raise Exception("Status basic cannot be None when init")
        if not isinstance(stask, StatusTask):
            raise Exception("Status task cannot be None when init")

        self._statusbasic = sbasic
        self._statustask = stask
        self._statustaskinfo = staskinfo
