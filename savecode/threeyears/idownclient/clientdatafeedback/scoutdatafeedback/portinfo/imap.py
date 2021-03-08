"""
An port of imap info
"""


class Imap:
    def __init__(self):
        self.banner = None
        self.close = None
        self.starttls = None

    def build_banner(self) -> str:
        """
        build banner string
        """
        banner = ''
        if self.banner is not None:
            banner += self.banner
        if self.close is not None:
            banner += self.close
        if self.starttls is not None:
            banner += self.starttls

        if not banner is None and banner != "":
            banner = "IMAP:\n" + banner
        return banner

    def get_outputdict(self) -> dict:
        """return mongodb dict"""
        res: dict = {}
        if self.banner is not None:
            res['banner'] = self.banner
        if self.close is not None:
            res['close'] = self.close
        if self.starttls is not None:
            res['starttls'] = self.starttls

        return res
