"""
An port of ftp info
"""
import json


class FTP:

    def __init__(self):
        self.banner = None
        self.auth_tls = None

    def build_banner(self) -> str:
        """
        build banner string
        """
        banner = ''
        if self.banner is not None:
            banner += self.banner
        if self.auth_tls is not None:
            banner += self.auth_tls

        if not banner is None and banner != "":
            banner = "FTP:\n" + banner
        return banner

    def get_outputdict(self) -> dict:
        """return mongodb dict"""
        res: dict = {}
        if self.banner is not None:
            res['banner'] = self.banner
        if self.auth_tls is not None:
            res['auth_tls'] = self.auth_tls
        return res
