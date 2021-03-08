"""zgrab2 config"""

# -*- coding:utf-8 -*-

import os


class Zgrab2Config:
    """zgrab2 config"""

    def __init__(
            self,
            maxthread: int = 5,
            timeout: float = 600,
            sudo: bool = False,
            zgrab2path=[
                'zgrab2', '/usr/bin/zgrab2', '/usr/local/bin/zgrab2',
                '/sw/bin/zgrab2', '/opt/local/bin/zgrab2'
            ],
    ):
        self.maxthread: int = 5
        if isinstance(maxthread, int):
            self.maxthread = maxthread

        self.timeout: float = 600  # 600秒
        if type(timeout) in [int, float]:
            self.timeout = timeout

        self.sudo: bool = False
        if isinstance(sudo, bool):
            self.sudo = sudo

        self.zgrab2path: list = [
            'zgrab2',
            '/usr/bin/zgrab2',
            '/usr/local/bin/zgrab2',
            '/sw/bin/zgrab2',
            '/opt/local/bin/zgrab2',
        ]
        if isinstance(zgrab2path, list) and len(zgrab2path) > 0:
            self.zgrab2path = zgrab2path
