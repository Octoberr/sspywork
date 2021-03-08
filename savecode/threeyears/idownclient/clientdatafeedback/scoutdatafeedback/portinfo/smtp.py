"""represents a smtp info"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.helpers import helper_str


class SMTP:
    """represents SMTP"""

    def __init__(self, banner: str):
        if not isinstance(banner, str):
            raise Exception("Invalid banner for smtp")
        self._banner: str = banner.strip()
        self.ehlo: str = None
        self.starttls: str = None

    def build_banner(self) -> str:
        """build banner string"""
        res: str = ""
        if not self._banner is None:
            res += "{}\n".format(self._banner.strip())
        if not self.ehlo is None:
            res += "{}\n".format(self.ehlo.strip())
        if not self.starttls is None:
            res == "{}\n".format(self.starttls)

        if not res is None and res != "":
            res = "SMTP:\n" + res
        return res

    def get_outputdict(self) -> dict:
        """return smtp dict"""
        res: dict = {}
        res["banner"] = self._banner
        res["ehlo"] = self.ehlo
        res["starttls"] = self.starttls
        return res
