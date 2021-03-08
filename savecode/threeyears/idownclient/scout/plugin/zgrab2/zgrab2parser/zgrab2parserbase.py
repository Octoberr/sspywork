"""zgrab2 parser base"""
import json
import os
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback.portinfo import PortInfo


class Zgrab2ParserBase:
    """zgrab2 parser base"""
    def __init__(self):
        self._name = type(self).__name__
        self._logger: MsLogger = MsLogManager.get_logger(self._name)

    def _get_port_timestamp(self, sj: dict, portinfo: PortInfo) -> str:
        """Get the timestamp field of current protocol json value, return str.
        :sj: the protocol json value"""
        if sj.__contains__("timestamp"):
            portinfo.timestamp = sj["timestamp"]