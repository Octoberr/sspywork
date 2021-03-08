"""
An port of airos info
"""


class Ubiquiti:
    def __init__(self):
        self.ip = None
        self.mac = None
        self.alternate_ip = None
        self.alternate_mac = None
        self.hostname = None
        self.product = None
        self.version = None

    def build_banner(self) -> str:
        """
        build banner string
        """
        banner = ''
        if self.ip is not None:
            banner += f'ip: {self.ip}\n'
        if self.mac is not None:
            banner += f'mac: {self.mac}\n'
        if self.alternate_ip is not None:
            banner += f'alternate_ip: {self.alternate_ip}\n'
        if self.alternate_mac is not None:
            banner += f'alternate_mac: {self.alternate_mac}\n'
        if self.hostname is not None:
            banner += f'hostname: {self.hostname}\n'
        if self.product is not None:
            banner += f'product: {self.product}\n'
        if self.version is not None:
            banner += f'version: {self.version}\n'

        if banner is not None and banner != "":
            banner = "Ubiquiti Networks Device:\n" + banner
        return banner

    def get_outputdict(self) -> dict:
        """return ubiquiti dict"""
        res: dict = {}
        if self.ip is not None:
            res['ip'] = self.ip
        if self.mac is not None:
            res['mac'] = self.mac
        if self.alternate_ip is not None:
            res['alternate_ip'] = self.alternate_ip
        if self.alternate_mac is not None:
            res['alternate_mac'] = self.alternate_mac
        if self.hostname is not None:
            res['hostname'] = self.hostname
        if self.product is not None:
            res['product'] = self.product
        if self.version is not None:
            res['version'] = self.version

        return res