"""logical banner grabber"""

# -*- coding:utf-8 -*-

from abc import ABCMeta, abstractmethod
from operator import truediv

from commonbaby.mslog import MsLogger, MsLogManager

from idownclient.clientdatafeedback.scandatafeedback.search import PortInfo


class LogicalGrabberBase:

    __metaclass = ABCMeta

    def __init__(self, servicetype: str) -> None:
        if not isinstance(servicetype, str) or servicetype == "":
            raise Exception(
                "Invalid service type for initialing Logic Banner Grabber.")

        self._servicetype: str = servicetype
        self._name: str = f"LD_{self._servicetype}"

        self._logger: MsLogger = MsLogManager.get_logger(self._name)

    @abstractmethod
    def match_service(self, target_service: str) -> str:
        """return if the target service is matched by current grabber"""
        if target_service != self._servicetype:
            return False
        return True

    @abstractmethod
    def run_logic_grabber(self, host: str, portinfo: PortInfo, **kwargs):
        pass
