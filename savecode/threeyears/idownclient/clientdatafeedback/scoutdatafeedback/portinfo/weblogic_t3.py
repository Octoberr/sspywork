"""
7001 weblogic-t3 info 
"""


class WeblogicT3:
    def __init__(self):
        self.banner = None

    def build_banner(self) -> str:
        """
        build banner string
        """
        banner = ''
        if self.banner is not None:
            banner += f'banner: {self.banner}\n'

        if banner is not None and banner != "":
            banner = "Weblogic T3:\n" + banner
        return banner

    def get_outputdict(self) -> dict:
        """return weblogic t3 dict"""
        res: dict = {}
        if self.banner is not None:
            res['banner'] = self.banner

        return res