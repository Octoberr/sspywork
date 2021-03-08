"""oracle"""

import os
import socket
import traceback

from commonbaby.helpers import helper_str

from datacontract.iscoutdataset import IscoutTask

from .....clientdatafeedback.scoutdatafeedback import PortInfo
from .zgrab2scannerbase import Zgrab2ScannerBase


class Zgrab2ScannerOracle(Zgrab2ScannerBase):
    """zgrab2 http scanner"""

    def __init__(self, zgrab_path: str):
        Zgrab2ScannerBase.__init__(self, "zgrab2oracle")

    def get_banner_oracle(
        self,
        task: IscoutTask,
        level,
        portinfo: PortInfo,
        *args,
        zgrab2path: str = "zgrab2",
        sudo: bool = False,
        timeout: float = 600,
    ) -> iter:
        """scan oracle services and get the banner"""
        so: socket.socket = None
        try:
            port: int = portinfo._port
            if not isinstance(port, int) or port < 0 or port > 65535:
                raise Exception("Invalid port: {}".format(port))

            # oracle 就直接用socket 去连一下，收完了就关了

            so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            so.settimeout(10)  # 30s timeout
            so.connect((portinfo._host, portinfo._port))
            bss: bytes = bytes()
            while True:
                bs: bytes = so.recv(1024)
                if bs is None or len(bs) < 1:
                    break
                bss += bs
                if len(bs) >= 1048576:  # receive over size
                    self._logger.warn(
                        "Oracle banner grab received over 1MB data, terminating the connection: {}:{}".format(
                            portinfo._host, portinfo._port
                        )
                    )
                    break

            banner = helper_str.base64bytes(bss)
            if not banner is None and banner != "":
                portinfo.set_oracle(banner)
                portinfo.banner = "Oracle:\n" + banner

        except Exception:
            self._logger.error(
                "Scan oracle error: {}:{} {}".format(
                    portinfo._host, portinfo._port, traceback.format_exc()
                )
            )
        finally:
            if not so is None and not so._closed:
                so.close()
