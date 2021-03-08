"""zgrab2 parser ssh"""

# -*- coding:utf-8 -*-

import io
import json
import os
import re
import traceback

from commonbaby.helpers import helper_crypto, helper_str
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask

from .....clientdatafeedback.scoutdatafeedback import PortInfo, SshInfo
from .zgrab2parserbase import Zgrab2ParserBase


class Zgrab2ParserSsh(Zgrab2ParserBase):
    """zgrab2 parser"""

    # _logger: MsLogger = MsLogManager.get_logger("Zgrab2ParserSSH")

    def __init__(self):
        # self._name = type(self).__name__
        Zgrab2ParserBase.__init__(self)

    def parse_ssh(self, sjssh: dict, portinfo: PortInfo):
        """parse one json block and return a PortInfo, if failed retrn None"""
        ssh: SshInfo = None
        try:
            if not isinstance(sjssh, dict):
                self._logger.error("Invalid sj for ssh parse")
                return ssh

            if not isinstance(portinfo, PortInfo):
                self._logger.error("Invalid portinfo for ssh parse")
                return ssh

            if (not sjssh.__contains__("data")
                    or not sjssh["data"].__contains__("ssh")
                    or not sjssh["data"]["ssh"].__contains__("status")
                    or not sjssh["data"]["ssh"].__contains__("result")):
                return ssh

            result = sjssh["data"]["ssh"]["status"]
            if result != "success":
                return ssh

            self._get_port_timestamp(sjssh["data"]["ssh"], portinfo)

            sjresult = sjssh["data"]["ssh"]["result"]
            if sjresult is None:
                return ssh

            # server_id
            if not sjresult.__contains__("server_id") or not sjresult[
                    "server_id"].__contains__("raw"):
                return
            server_id = sjresult["server_id"]["raw"]
            if not isinstance(server_id, str) or server_id == "":
                return ssh

            # server key
            if not sjresult.__contains__("key_exchange") or not sjresult[
                    "key_exchange"].__contains__("server_host_key"):
                return ssh
            sjkey_serverhostkey = sjresult["key_exchange"]["server_host_key"]
            if not sjkey_serverhostkey.__contains__(
                    "algorithm") or not sjkey_serverhostkey.__contains__(
                        "raw"):
                return ssh
            server_key_type = sjkey_serverhostkey["algorithm"]
            server_key_raw = sjkey_serverhostkey["raw"]
            if (not isinstance(server_key_type, str) or server_key_type == ""
                    or not isinstance(server_key_raw, str)
                    or server_key_raw == ""):
                return ssh
            ssh: SshInfo = SshInfo(server_id, server_key_raw, server_key_type)

            # fingerprint
            braw = io.BytesIO(
                helper_str.base64_decode_to_bytes(server_key_raw))
            ssh.fingerprint_md5 = helper_crypto.get_md5_from_stream(braw)
            braw.seek(0)
            ssh.fingerprint_sha256 = helper_crypto.get_sha256_from_stream(braw)

            # server alg type
            if sjresult.__contains__("algorithm_selection"):
                sjalg = sjresult["algorithm_selection"]
                if not sjalg is None and sjalg.__contains__(
                        "server_to_client_alg_group"):
                    sjalggroup = sjalg["server_to_client_alg_group"]
                    if not sjalggroup is None:
                        ssh.mac = sjalggroup.get("mac")
                        ssh.cipher = sjalggroup.get("cipher")

            # kex
            sj_kex = sjresult.get("server_key_exchange")
            if not sj_kex is None:
                # kex_follows
                ssh.kex_follows = sj_kex.get("first_kex_follows")
                # reserved
                ssh.reserved = sj_kex.get("reserved")
                # server_host_key_algorithms
                sjhost_key_alg = sj_kex.get("host_key_algorithms")
                if isinstance(sjhost_key_alg,
                              list) and len(sjhost_key_alg) > 0:
                    for a in sjhost_key_alg:
                        ssh.set_server_host_key_algorithms(a)
                # encryption_algorithms
                sjencry_alg = sj_kex.get("server_to_client_ciphers")
                if isinstance(sjencry_alg, list) and len(sjencry_alg) > 0:
                    for a in sjencry_alg:
                        ssh.set_encryption_algorithms(a)
                # languages(not found in zgrab2 result)
                # will research later...

                # kex_algorithms
                sjkex_alg = sj_kex.get("kex_algorithms")
                if isinstance(sjkex_alg, list) and len(sjkex_alg) > 0:
                    for a in sjkex_alg:
                        ssh.set_kex_algorithms(a)

                # compression_algorithms
                sjcomp = sj_kex.get("server_to_client_compression")
                if isinstance(sjcomp, list) and len(sjcomp) > 0:
                    for a in sjcomp:
                        ssh.set_compression_algorithms(a)

                # mac_algorithms
                sjmac_alg = sj_kex.get("server_to_client_macs")
                if isinstance(sjmac_alg, list) and len(sjmac_alg) > 0:
                    for a in sjmac_alg:
                        ssh.set_mac_algorithms(a)

                portinfo.banner = ssh.build_banner()
                portinfo.set_sshinfo(ssh)

        except Exception:
            self._logger.error("Parse one ssh json line error: {}".format(
                traceback.format_exc()))
