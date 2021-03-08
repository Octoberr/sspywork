"""represents a ssh info"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.helpers import helper_str


class SshInfo:
    """ssh info\n
    keep all same with iscan data"""

    def __init__(self, server_id: str, server_key: str, type_: str):
        if not isinstance(server_id, str) or server_id == "":
            raise Exception("Invalid ssh server_id")
        if not isinstance(server_key, str) or server_key == "":
            raise Exception("Invalid ssh server_key")
        if not isinstance(type_, str) or type_ == "":
            raise Exception("Invalid ssh type")

        self._server_id: str = server_id
        self._server_key: str = server_key
        self._type: str = type_

        self.fingerprint_md5: str = None
        self.fingerprint_sha256: str = None

        self.mac: str = None  # Message Authentication code algorithm
        self.cipher: str = None

        self._server_host_key_algorithms: list = []
        self._server_host_key_algorithms_locker = threading.RLock()

        self._encryption_algorithms: list = []
        self._encryption_algorithms_locker = threading.RLock()

        self.kex_follows: bool = False
        self.reserved: int = 0

        self._languages: list = []
        self._languages_locker = threading.RLock()

        self._kex_algorithms: list = []
        self._kex_algorithms_locker = threading.RLock()

        self._compression_algorithms: list = []
        self._compression_algorithms_locker = threading.RLock()

        self._mac_algorithms: list = []
        self._mac_algorithms_locker = threading.RLock()

    def set_server_host_key_algorithms(self, alg: str):
        """set server_host_key_algorithms"""
        if not isinstance(alg, str):
            return
        if alg in self._server_host_key_algorithms:
            return
        with self._server_host_key_algorithms_locker:
            if alg in self._server_host_key_algorithms:
                return
            self._server_host_key_algorithms.append(alg)

    def set_encryption_algorithms(self, alg: str):
        """set encryption_algorithms"""
        if not isinstance(alg, str):
            return
        if alg in self._encryption_algorithms:
            return
        with self._encryption_algorithms_locker:
            if alg in self._encryption_algorithms:
                return
            self._encryption_algorithms.append(alg)

    def set_languages(self, lang: str):
        """set languages"""
        if not isinstance(lang, str):
            return
        if lang in self._languages:
            return
        with self._languages_locker:
            if lang in self._languages:
                return
            self._languages.append(lang)

    def set_kex_algorithms(self, alg: str):
        """set kex_algorithms"""
        if not isinstance(alg, str):
            return
        if alg in self._kex_algorithms:
            return
        with self._kex_algorithms_locker:
            if alg in self._kex_algorithms:
                return
            self._kex_algorithms.append(alg)

    def set_compression_algorithms(self, alg: str):
        """set compression_algorithms"""
        if not isinstance(alg, str):
            return
        if alg in self._compression_algorithms:
            return
        with self._compression_algorithms_locker:
            if alg in self._compression_algorithms:
                return
            self._compression_algorithms.append(alg)

    def set_mac_algorithms(self, alg: str):
        """set mac_algorithms"""
        if not isinstance(alg, str):
            return
        if alg in self._mac_algorithms:
            return
        with self._mac_algorithms_locker:
            if alg in self._mac_algorithms:
                return
            self._mac_algorithms.append(alg)

    def build_banner(self) -> str:
        """build banner info on current ssh info"""
        res: str = ""

        # key
        res += self._server_id + "\n"
        res += "Key type: {}\n".format(self._type)
        res += "Key: {}\n".format(self._server_key)

        # fingerprint
        if not self.fingerprint_md5 is None and self.fingerprint_md5 != "":
            res += "Fingerprint MD5: {}\n".format(self.fingerprint_md5)
        if not self.fingerprint_sha256 is None and self.fingerprint_sha256 != "":
            res += "Fingerprint SHA256: {}\n".format(self.fingerprint_sha256)
        res = res.strip() + "\n\n"

        # kex algorithms
        if len(self._kex_algorithms) > 0:
            res += "Kex Algorithms:\n"
            for a in self._kex_algorithms:
                res += "\t{}\n".format(a)
            res = res.strip() + "\n\n"

        # server host key algorithms
        if len(self._server_host_key_algorithms) > 0:
            res += "Server Host Key Algorithms:\n"
            for a in self._server_host_key_algorithms:
                res += "\t{}\n".format(a)
            res = res.strip() + "\n\n"

        # encryption algorithms
        if len(self._encryption_algorithms) > 0:
            res += "Encryption Algorithms:\n"
            for a in self._encryption_algorithms:
                res += "\t{}\n".format(a)
            res = res.strip() + "\n\n"

        # mac algorithms
        if len(self._mac_algorithms) > 0:
            res += "MAC Algorithms:\n"
            for a in self._mac_algorithms:
                res += "\t{}\n".format(a)
            res = res.strip() + "\n\n"

        # compression algorithms
        if len(self._mac_algorithms) > 0:
            res += "Compression Algorithms:\n"
            for a in self._mac_algorithms:
                res += "\t{}\n".format(a)
            res = res.strip() + "\n\n"

        if not res is None and res != "":
            res = "SSH:\n" + res
        return res

    def get_outputdict(self) -> dict:
        res: dict = {}

        ##########################################
        # must keep all same with iscan data standard.
        # allow extra fields, but cannot modify original fields
        ##########################################
        res["server_id"] = self._server_id  # extra field
        res["type"] = self._type
        if not self.fingerprint_sha256 is None:
            res["fingerprint"] = self.fingerprint_sha256.replace(":", "")
        elif not self.fingerprint_md5 is None:
            res["fingerprint"] = self.fingerprint_md5.replace(":", "")
        if not self.mac is None:
            res["mac"] = self.mac
        if not self.cipher is None:
            res["cipher"] = self.cipher  # original iscan standard
        res["key"] = self._server_key

        if not res.__contains__("kex"):
            res["kex"] = {}
        kex = res["kex"]

        kex["key_follows"] = self.kex_follows
        # kex["reserved"] = self.reserved
        kex["unused"] = self.reserved  # original iscan standard

        if len(self._server_host_key_algorithms) > 0:
            kex["server_host_key_algorithms"] = []
            for a in self._server_host_key_algorithms:
                kex["server_host_key_algorithms"].append(a)

        if len(self._encryption_algorithms) > 0:
            kex["encryption_algorithms"] = []
            for a in self._encryption_algorithms:
                kex["encryption_algorithms"].append(a)

        if len(self._kex_algorithms) > 0:
            kex["kex_algorithms"] = []
            for a in self._kex_algorithms:
                kex["kex_algorithms"].append(a)

        if len(self._compression_algorithms) > 0:
            kex["compression_algorithms"] = []
            for a in self._compression_algorithms:
                kex["compression_algorithms"].append(a)

        if len(self._mac_algorithms) > 0:
            kex["mac_algorithms"] = []
            for a in self._mac_algorithms:
                kex["mac_algorithms"].append(a)

        return res
