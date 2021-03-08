"""zmap parser"""

# -*- coding:utf-8 -*-

import os
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask
from ....clientdatafeedback.scoutdatafeedback import PortInfo


class ZmapParser:
    """zmap parser"""

    _logger: MsLogger = MsLogManager.get_logger("ZmapParser")

    def __init__(self):
        self._name = type(self).__name__

    @classmethod
    def parse_open_ports(cls,
                         task: IscoutTask,
                         level: int,
                         outfi: str,
                         port: str,
                         transprotocol: str = 'tcp') -> iter:
        """yield Port"""
        try:
            if not os.path.isfile(outfi):
                return

            with open(outfi, mode='r', encoding='utf-8') as fs:
                while True:
                    line = fs.readline().strip()
                    if not isinstance(line, str) or line == '':
                        break

                    ip = line.strip()
                    p: PortInfo = PortInfo(task, level, ip, str(port),
                                           transprotocol)
                    yield p

        except Exception:
            cls._logger.error("Parse zmap scan result error: {}".format(
                traceback.format_exc()))
