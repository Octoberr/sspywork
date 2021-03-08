"""logical http"""

# -*- coding:utf-8 -*-

from abc import ABCMeta, abstractmethod

from .logicalgrabberbase import LogicalGrabberBase
from commonbaby.httpaccess import HttpAccess


class LogicalHttp(LogicalGrabberBase):
    """logical http banner grabber base class"""

    __metaclass = ABCMeta

    def __init__(self, servicetype: str) -> None:
        LogicalGrabberBase.__init__(self, servicetype)

        self._ha: HttpAccess = HttpAccess()

    def match_service(self, target_service: str) -> bool:
        """return if the target service is matched by current grabber"""
        if target_service is not None and target_service.__contains__("http"):
            return True
        else:
            self._logger.debug(f"Target protocol {target_service} not match http protocol")
            return False

