"""represents a mysql info"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.helpers import helper_str


class MySql:
    """represents MySql"""
    def __init__(self):
        self.protocol_version: str = None
        self.server_version: str = None

        self._status_flags: dict = {}
        self._status_flags_locker = threading.RLock()

        self._capability_flags: dict = {}
        self._capability_flags_locker = threading.RLock()

        self._errormsg: str = None

    def set_status_flag(self, key: str, value):
        if not isinstance(key, str) or key == "":
            return
        if self._status_flags.__contains__(key):
            return
        with self._status_flags_locker:
            if self._status_flags.__contains__(key):
                return
            self._status_flags[key] = value

    def set_capability_flag(self, key: str, value):
        if not isinstance(key, str) or key == "":
            return
        if self._capability_flags.__contains__(key):
            return
        with self._capability_flags_locker:
            if self._capability_flags.__contains__(key):
                return
            self._capability_flags[key] = value

    def build_banner(self) -> str:
        """build banner string"""
        res: str = ""
        if not self.protocol_version is None:
            res += "protocol_version:{}\n".format(self.protocol_version)
        if not self.server_version is None:
            res += "server_version:{}\n".format(self.server_version)
        if not self._errormsg is None:
            res += "error_msg:{}\n".format(self._errormsg)
        if len(self._status_flags) > 0:
            res += "status_flags:\n"
            for k, v in self._status_flags.items():
                res += "\t{}:{}\n".format(k, v)
        if len(self._capability_flags) > 0:
            res += "capability_flags:\n"
            for k, v in self._capability_flags.items():
                res += "\t{}:{}\n".format(k, v)

        if not res is None and res != "":
            res = "MySql:\n" + res
        return res

    def get_outputdict(self) -> dict:
        """return mysql dict"""
        res: dict = {}

        if not self.protocol_version is None:
            res["protocol_version"] = self.protocol_version
        if not self.server_version is None:
            res["server_version"] = self.server_version
        if not self._errormsg is None:
            res["banner"] = self._errormsg
        if len(self._status_flags) > 0:
            res["status_flags"] = []
            for k, v in self._status_flags.items():
                res["status_flags"].append({"key": k, "value": v})
        if len(self._capability_flags) > 0:
            res["capability_flags"] = []
            for k, v in self._capability_flags.items():
                res["capability_flags"].append({"key": k, "value": v})

        return res
