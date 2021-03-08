"""
An port of telenet info
因为telnet兼容了scan的数据结构，所以虽然zgrab2在这扫出来只有一个banner
但是还是要将这些字段加进来，万一以后实现了呢
"""


class Telnet:
    def __init__(self):
        self.banner = None

    def build_banner(self) -> str:
        """
        build banner string
        """
        banner = ""
        if self.banner is not None:
            banner = self.banner

        if not banner is None and banner != "":
            banner = "Telnet:\n" + banner
        return banner

    def get_outputdict(self) -> dict:
        """return mongodb dict"""
        res: dict = {}
        if self.banner is not None:
            res['banner'] = self.banner

        return res
