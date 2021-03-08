"""zmap config"""

# -*- coding:utf-8 -*-


class ZmapConfig:
    """zmap config"""

    def __init__(
        self,
        interface_card: str,
        maxthread: int = 5,
        timeout: float = 300,
        sudo: bool = False,
        zmappath=[
            "zmap",
            "/usr/bin/zmap",
            "/usr/local/bin/zmap",
            "/sw/bin/zmap",
            "/opt/local/bin/zmap",
        ],
    ):
        if not isinstance(interface_card, str) or interface_card == "":
            raise Exception("Invalid Interface card for zmap config")

        self._interface_card: str = interface_card

        # self.scanargs: list = [
        #     '--max-sendto-failures -1',
        #     '-i %s' % interface_card, '-b .'
        # ]
        # if isinstance(scanargs, list) and len(scanargs) > 0:
        #     self.scanargs = scanargs

        self.maxthread: int = 5
        if isinstance(maxthread, int):
            self.maxthread = maxthread

        self.timeout: float = 300  # 600秒
        if type(timeout) in [int, float]:
            self.timeout = timeout

        self.sudo: bool = False
        if isinstance(sudo, bool):
            self.sudo = sudo

        self.zmappath: list = [
            "zmap",
            "/usr/bin/zmap",
            "/usr/local/bin/zmap",
            "/sw/bin/zmap",
            "/opt/local/bin/zmap",
        ]
        if isinstance(zmappath, list) and len(zmappath) > 0:
            self.zmappath = zmappath
