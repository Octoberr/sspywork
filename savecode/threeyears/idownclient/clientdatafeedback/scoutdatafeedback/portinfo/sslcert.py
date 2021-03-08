"""represents a sslcert"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.helpers import helper_str, helper_sslcert


class CertSubject:
    """a certificate subject, the cert owner info"""

    def __init__(self):
        self._kvs: dict = {}
        self._kvs_locker = threading.RLock()
        # self.UID: str = None  # userid
        # self.C: str = None  # country
        # self.ST: str = None  # state
        # self.L: str = None  # location
        # self.STREET: str = None  # street
        # self.DC: str = None  # domain component
        # self.CN: str = None  # common name
        # self.O: str = None  # organization
        # self.OU: str = None  # organization unit

    def set_field(self, k: str, v: str):
        if not isinstance(k, str) or k == "":
            return
        if not isinstance(v, str) or v == "":
            return
        # coverly update
        with self._kvs_locker:
            self._kvs[k] = v

    def get_outputdict(self) -> dict:
        res: dict = {}
        if len(self._kvs) > 0:
            for k, v in self._kvs.items():
                res[k] = v
        # if not self.UID is None:
        #     res["UID"] = self.UID
        # if not self.C is None:
        #     res["C"] = self.C
        # if not self.ST is None:
        #     res["ST"] = self.ST
        # if not self.L is None:
        #     res["L"] = self.L
        # if not self.STREET is None:
        #     res["STREET"] = self.STREET
        # if not self.DC is None:
        #     res["DC"] = self.DC
        # if not self.CN is None:
        #     res["CN"] = self.CN
        # if not self.O is None:
        #     res["O"] = self.O
        # if not self.OU is None:
        #     res["OU"] = self.OU
        return res


class CertIssuer:
    """a certificate issuer, the issuer info"""

    def __init__(self):
        self._kvs: dict = {}
        self._kvs_locker = threading.RLock()
        # self.UID: str = None  # userid
        # self.C: str = None  # country
        # self.ST: str = None  # state
        # self.L: str = None  # location
        # self.STREET: str = None  # street
        # self.DC: str = None  # domain component
        # self.CN: str = None  # common name
        # self.O: str = None  # organization
        # self.OU: str = None  # organization unit

    def set_field(self, k: str, v: str):
        if not isinstance(k, str) or k == "":
            return
        if not isinstance(v, str) or v == "":
            return
        # coverly update
        with self._kvs_locker:
            self._kvs[k] = v

    def get_outputdict(self) -> dict:
        res: dict = {}
        if len(self._kvs) > 0:
            for k, v in self._kvs.items():
                res[k] = v
        # if not self.UID is None:
        #     res["UID"] = self.UID
        # if not self.C is None:
        #     res["C"] = self.C
        # if not self.ST is None:
        #     res["ST"] = self.ST
        # if not self.L is None:
        #     res["L"] = self.L
        # if not self.STREET is None:
        #     res["STREET"] = self.STREET
        # if not self.DC is None:
        #     res["DC"] = self.DC
        # if not self.CN is None:
        #     res["CN"] = self.CN
        # if not self.O is None:
        #     res["O"] = self.O
        # if not self.OU is None:
        #     res["OU"] = self.OU
        return res


class Certificate:
    """a certificate in ssl"""

    @property
    def serialnum(self) -> str:
        """return the serial number"""
        return self._serialnum

    @property
    def issuer(self) -> CertIssuer:
        """the cert issuer"""
        return self._issuer

    @issuer.setter
    def issuer(self, value: CertIssuer):
        """the cert issuer"""
        if not isinstance(value, CertIssuer):
            raise Exception("Invalid cert issuer")
        self._issuer = value

    @property
    def subject(self) -> CertSubject:
        """the cert subject"""
        return self._subject

    @subject.setter
    def subject(self, value: CertSubject):
        """the cert issuer"""
        if not isinstance(value, CertSubject):
            raise Exception("Invalid cert subject")
        self._subject = value

    @property
    def sig_alg(self) -> str:
        return self._sig_alg

    @sig_alg.setter
    def sig_alg(self, value):
        if isinstance(value, bytes):
            value = value.decode()
        self._sig_alg = value

    @property
    def issued_time(self) -> str:
        return self._issued_time

    @issued_time.setter
    def issued_time(self, value):
        if isinstance(value, bytes):
            value = value.decode()
        self._issued_time = value

    @property
    def expires_time(self) -> str:
        return self._expires_time

    @expires_time.setter
    def expires_time(self, value):
        if isinstance(value, bytes):
            value = value.decode()
        self._expires_time = value

    def __init__(self, serialnum: str):
        if serialnum is None:
            raise Exception("Invalid serialnum for SslCert")

        self._serialnum: str = str(serialnum)

        self._sig_alg: str = None  # sig algorithm

        self._issued_time: str = None
        self._expires_time: str = None
        self.expired: bool = None

        self.pubkey_bits: int = None
        self.pubkey_type: str = None

        self.version: str = None

        self._extensions: dict = {}
        self._extensions_locker = threading.RLock()

        self._fingerprint: dict = {}
        self._fingerprint_locker = threading.RLock()

        self._issuer: CertIssuer = None
        self._subject: CertSubject = None

    def set_extensions(self, name: str, data: str):
        """set cert exts"""
        if not isinstance(name, str):
            return
        if self._extensions.__contains__(name):
            return
        with self._extensions_locker:
            if self._extensions.__contains__(name):
                return
            if isinstance(data, bytes):
                data = data.hex()
            self._extensions[name] = data

    def set_fingerprint(self, key: str, val: str):
        if (
            not isinstance(key, str)
            or key == ""
            or not isinstance(val, str)
            or val == ""
        ):
            return
        if self._fingerprint.__contains__(key):
            return
        with self._fingerprint_locker:
            if self._fingerprint.__contains__(key):
                return
            self._fingerprint[key] = val

    def get_outputdict(self) -> dict:
        res: dict = {}

        res["serial"] = self._serialnum

        if not self.sig_alg is None:
            res["sig_alg"] = self.sig_alg
        if not self.issued_time is None:
            res["issued"] = self.issued_time
        if not self.expires_time is None:
            res["expires"] = self.expires_time
        if not self.expired is None:
            res["expired"] = self.expired

        res["pubkey"] = {}
        if not self.pubkey_bits is None:
            res["pubkey"]["bits"] = self.pubkey_bits
        if not self.pubkey_type is None:
            res["pubkey"]["type"] = self.pubkey_type

        if not self.version is None:
            res["version"] = self.version

        res["extensions"] = []
        if len(self._extensions) > 0:
            for n, d in self._extensions.items():
                res["extensions"].append({"name": n, "data": d})

        res["fingerprint"] = {}
        if len(self._fingerprint) > 0:
            for k, v in self._fingerprint.items():
                res["fingerprint"][k] = v

        if not self._issuer is None:
            res["issuer"] = self._issuer.get_outputdict()
        if not self._subject is None:
            res["subject"] = self.subject.get_outputdict()

        return res


class SslCert:
    """ssl certificate\n
    raw: the certificate raw like:\n
        -----BEGIN CERTIFICATE-----\n
        xxx\n
        -----END CERTIFICATE-----\n
    """

    def __init__(self, cert: Certificate, raw: str):
        if not isinstance(cert, Certificate):
            raise Exception("Invalid cert for SslCert")
        if not isinstance(raw, str) or raw == "":
            raise Exception("Invalid raw for SslCert")

        self._cert: Certificate = cert
        self._raw: str = raw

        self.dhparams_prime: str = None
        self.dhparams_public_key: str = None
        self.dhparams_bits: int = None
        self.dhparams_generator: str = None

        self._tlsexts: dict = {}
        self._tlsexts_locker = threading.RLock()

        self._versions: list = []
        self._versions_locker = threading.RLock()

        self._acceptable_cas: list = []
        self._acceptable_cas_locker = threading.RLock()

        self._cipher_version: str = None
        self._cipher_bits: int = None
        self._cipher_name: str = None

        self._chain: list = []
        self._chain_locker = threading.RLock()

        self._alpn: list = []  # application level protocal
        self._alpn_locker = threading.RLock()

    def set_dhparams(
        self,
        prime: str = None,
        pubkey: str = None,
        bits: int = None,
        generator: str = None,
    ):
        """set dehalfman params"""
        if not prime is None:
            self.dhparams_prime = prime
        if not pubkey is None:
            self.dhparams_public_key = pubkey
        if not bits is None:
            self.dhparams_bits = bits
        if not generator is None:
            self.dhparams_generator = generator

    def set_tlsexts(self, id_: str, name: str):
        """set tls extensions"""
        if not isinstance(id_, str) or id_ == "":
            return
        if self._tlsexts.__contains__(id_):
            return
        with self._tlsexts_locker:
            if self._tlsexts.__contains__(id_):
                return
            self._tlsexts[id_] = name

    def set_versions(self, version: str):
        """set server supported ssl/tls versions"""
        if not isinstance(version, str) or version == "":
            return
        with self._versions_locker:
            if version in self._versions:
                return
            self._versions.append(version)

    def set_acceptable_cas(self, ca: str):
        """set server acceptable Certificate authority"""
        if not isinstance(ca, str):
            return
        with self._acceptable_cas_locker:
            if ca in self._acceptable_cas:
                return
            self._acceptable_cas.append(ca)

    def set_cipher(self, name: str, version: str, bits: int):
        """set cipher"""
        if isinstance(name, str) and name != "":
            self._cipher_name = name
        if isinstance(version, str) and version != "":
            self._cipher_version = version
        if isinstance(bits, int) and bits >= 0:
            self._cipher_bits = bits

    def set_chain(self, chain: str):
        """append a chain to the cert"""
        if not isinstance(chain, str) or chain == "":
            return
        with self._chain_locker:
            self._chain.append(chain)

    def set_alpn(self, alpn: str):
        """set application level protocal to cert"""
        if not isinstance(alpn, str) or alpn == "":
            return
        if alpn in self._alpn:
            return
        with self._alpn_locker:
            if alpn in self._alpn:
                return
            self._alpn.append(alpn)

    def build_banner(self) -> str:
        res = ""
        # raw
        res = helper_sslcert.format_ssl_raw(self._raw)
        if not res is None and res != "":
            res = "TLS:\n" + res
        return res

    def get_outputdict(self) -> dict:
        res: dict = {}

        res["dhparams"] = {}
        if not self.dhparams_prime is None:
            res["dhparams"]["prime"] = self.dhparams_prime
        if not self.dhparams_public_key is None:
            res["dhparams"]["public_key"] = self.dhparams_public_key
        if not self.dhparams_bits is None:
            res["dhparams"]["bits"] = int(self.dhparams_bits)
        if not self.dhparams_generator is None:
            res["dhparams"]["generator"] = self.dhparams_generator

        res["tlsext"] = []
        if len(self._tlsexts) > 0:
            for i, n in self._tlsexts.items():
                res["tlsext"].append({"id": i, "name": n})

        res["versions"] = []
        if len(self._versions) > 0:
            for v in self._versions:
                res["versions"].append(v)

        res["acceptable_cas"] = []
        if len(self._acceptable_cas) > 0:
            for c in self._acceptable_cas:
                res["acceptable_cas"].append(c)

        if not self._cert is None:
            res["cert"] = self._cert.get_outputdict()

        res["cipher"] = {}
        if not self._cipher_name is None:
            res["cipher"]["name"] = self._cipher_name
        if not self._cipher_bits is None:
            res["cipher"]["bit"] = self._cipher_bits
        if not self._cipher_version is None:
            res["cipher"]["version"] = self._cipher_version

        res["chain"] = []
        if len(self._chain) > 0:
            for c in self._chain:
                res["chain"].append(c)

        res["alpn"] = []
        if len(self._alpn) > 0:
            for a in self._alpn:
                res["alpn"].append(a)

        return res
