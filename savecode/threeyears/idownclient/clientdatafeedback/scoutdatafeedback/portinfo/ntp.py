"""
An port of ntp info
"""


class Ntp:

    def __init__(self):
        self.version = None
        self.stratum = None
        self.leap_indicator = None
        self.precision = None
        self.root_delay = {}
        self.root_dispersion = {}
        self.reference_id = None
        self.reference_timestamp = None
        self.poll = None

    def build_banner(self) -> str:
        """
        build banner string
        """
        banner = ''
        if self.version is not None:
            banner += f'protocolversion: {self.version}\n'
        if self.stratum is not None:
            banner += f'stratum: {self.stratum}\n'
        if self.leap_indicator is not None:
            banner += f'leap: {self.leap_indicator}\n'
        if self.precision is not None:
            banner += f'precision: {self.precision}\n'
        seconds = self.root_delay.get('seconds')
        if seconds is not None:
            banner += f'rootdelay: {seconds}\n'
        seconds = self.root_dispersion.get('seconds')
        if seconds is not None:
            banner += f'rootdisp: {seconds}\n'
        if self.reference_id is not None:
            banner += f'refid: {self.reference_id}\n'
        if self.reference_timestamp is not None:
            banner += f'reftime: {self.reference_timestamp}\n'
        if self.poll is not None:
            banner += f'pool: {self.poll}\n'

        if not banner is None and banner != "":
            banner = "NTP:\n" + banner
        return banner

    def get_outputdict(self) -> dict:
        """return mongodb dict"""
        res: dict = {}
        if self.version is not None:
            res['version'] = self.version
        if self.stratum is not None:
            res['straum'] = self.stratum
        if self.leap_indicator is not None:
            res['leap_indicator'] = self.leap_indicator
        if self.precision is not None:
            res['precision'] = self.precision
        if len(self.root_delay) > 0:
            res['root_delay'] = [{'key': k, 'value': v} for k, v in self.root_delay.items()]
        if len(self.root_dispersion) > 0:
            res['root_dispersion'] = [{'key': k, 'value': v} for k, v in self.root_dispersion.items()]
        if self.reference_id is not None:
            res['reference_id'] = self.reference_id
        if self.reference_timestamp is not None:
            res['reference_timestamp'] = self.reference_timestamp
        if self.poll is not None:
            res['poll'] = self.poll
        return res
