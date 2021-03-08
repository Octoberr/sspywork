"""
An port of mssql info
"""


class Mssql:
    def __init__(self):
        self.instance_name = None
        self.version = None
        self.banner = 'mssqlbanner'

    def build_banner(self) -> str:
        """
        build banner string
        """
        banner = ''
        banner += f'ServerName;ITASSET1;'
        if self.instance_name is not None and self.instance_name != '':
            banner += f'InstanceName;{self.instance_name};'
        else:
            banner += f'InstanceName;MSSQLSERVER;'
        banner += 'IsClustered;No;'
        if self.version is not None:
            banner += f'Version;{self.version};'

        if not banner is None and banner != "":
            banner = "MsSql:\n" + banner
        return banner

    def get_outputdict(self) -> dict:
        """return mssql dict"""
        res: dict = {}
        if self.banner is not None:
            res['banner'] = self.banner
        if self.instance_name is not None:
            res['instance_name'] = self.instance_name
        if self.version is not None:
            res['version'] = self.version

        return res
