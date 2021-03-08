"""
An port of pop3 info
"""


class POP3:

    def __init__(self):
        self.banner = None
        self.noop = None
        self.help = None
        self.starttls = None
        self.quit = None

    def build_banner(self) -> str:
        """
        build banner string
        """
        banner = ''
        if self.banner is not None:
            banner += self.banner
        if self.noop is not None:
            banner += self.noop
        if self.help is not None:
            banner += self.help
        if self.starttls is not None:
            banner += self.starttls
        if self.quit is not None:
            banner += self.quit

        if not banner is None and banner != "":
            banner = "POP3:\n" + banner
        return banner

    def get_outputdict(self) -> dict:
        """return mongodb dict"""
        res: dict = {}
        if self.banner is not None:
            res['banner'] = self.banner
        if self.noop is not None:
            res['noop'] = self.noop
        if self.help is not None:
            res['help'] = self.help
        if self.starttls is not None:
            res['starttls'] = self.starttls
        if self.quit is not None:
            res['quit'] = self.quit

        return res
