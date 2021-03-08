"""
An port of redis info
"""


class Redis:
    def __init__(self):
        self.info_response = None
        self.ping_response = None
        self.banner = 'redisbanner'

    def build_banner(self) -> str:
        """
        build banner string
        """
        banner = ""
        if self.info_response is not None:
            banner = self.info_response
        elif self.ping_response is not None:
            banner = self.ping_response

        if not banner is None and banner != "":
            banner = "Redis:\n" + banner
        return banner

    def get_outputdict(self) -> dict:
        """return mongodb dict"""
        res: dict = {}
        if self.banner is not None:
            res['banner'] = self.banner
        if self.info_response is not None:
            res['info_response'] = self.info_response
        if self.ping_response is not None:
            res['ping_response'] = self.ping_response

        return res
