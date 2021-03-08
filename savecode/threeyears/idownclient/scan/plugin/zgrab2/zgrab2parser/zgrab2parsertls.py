"""zgrab2 parser tls"""

# -*- coding:utf-8 -*-

import json
import os
import re
import traceback

import OpenSSL
# from common.tools import sslparse
from commonbaby.helpers import helper_sslcert as sslparse
from commonbaby.helpers import helper_str
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscandataset.iscantask import IscanTask

from .....clientdatafeedback.scoutdatafeedback import (Certificate, CertIssuer,
                                                       CertSubject, PortInfo,
                                                       SiteInfo, SslCert)
from .zgrab2parserbase import Zgrab2ParserBase

openssl_pubkey_types = {
    OpenSSL.crypto.TYPE_DH: "dh",
    OpenSSL.crypto.TYPE_DSA: "dsa",
    OpenSSL.crypto.TYPE_EC: "ec",
    OpenSSL.crypto.TYPE_RSA: "rsa",
}


class Zgrab2ParserTls(Zgrab2ParserBase):
    """zgrab2 parser"""

    # _logger: MsLogger = MsLogManager.get_logger("Zgrab2ParserTls")

    _re_title = re.compile(r"<title>(.*?)</title>", re.S | re.M)
    # <meta content="17173,17173.com,17173游戏网,网络游戏" name="Keywords" />
    _re_meta = re.compile(r'<meta[^>]+?name="(keywords|description)"[^>]+?/>',
                          re.S | re.M | re.IGNORECASE)

    def __init__(self):
        # self._name = type(self).__name__
        Zgrab2ParserBase.__init__(self)

    def _parse_tls(self, sjtls: dict, portinfo):
        """from zgrab2 tls scan result json(not the tls json from other protocol scan result)"""
        try:
            if not isinstance(sjtls, dict) or len(sjtls) < 1:
                return

            if not sjtls.__contains__("result") or \
                not sjtls["result"].__contains__("handshake_log"):
                return

            self._get_port_timestamp(sjtls, portinfo)

            sjhandshake = sjtls["result"]["handshake_log"]
            return self._parse_cert(sjhandshake, portinfo)

        except Exception:
            self._logger.error("Parse one ssl json line error: {}".format(
                traceback.format_exc()))

    def _parse_cert(self, sjhandshakelog: dict, portinfo: PortInfo):
        """parse sslinfo from inner json"""
        try:

            if not isinstance(sjhandshakelog, dict) or len(sjhandshakelog) < 1:
                return

            # cert
            # certdict = ssldict["cert"] = {}
            sjcert = sjhandshakelog["server_certificates"]["certificate"]

            # parse x509
            orgiraw: str = sjcert["raw"]
            if not orgiraw.startswith("-----BEGIN CERTIFICATE-----"):
                orgiraw = "-----BEGIN CERTIFICATE-----\n" + orgiraw
            if not orgiraw.endswith("-----END CERTIFICATE-----"):
                orgiraw = orgiraw.rstrip() + "\n-----END CERTIFICATE-----"
            x509: OpenSSL.crypto.X509 = sslparse.get_sslcert(orgiraw)
            if x509 is None:
                return

            # cert serial number
            serialnum = str(x509.get_serial_number())
            if (serialnum is None or serialnum == ""
                    or portinfo.sslcert_contains_serialnum(serialnum)):
                return

            # construct certificate
            cert: Certificate = Certificate(serialnum)

            # cert fields
            cert.sig_alg = x509.get_signature_algorithm()
            cert.issued_time = x509.get_notBefore()
            cert.expires_time = x509.get_notAfter()
            cert.expired = x509.has_expired()
            pubkey: OpenSSL.crypto.PKey = x509.get_pubkey()
            cert.pubkey_bits = pubkey.bits()
            cert.pubkey_type = openssl_pubkey_types.get(pubkey.type())
            cert.version = x509.get_version()
            for i in range(0, x509.get_extension_count()):
                ext: OpenSSL.crypto.X509Extension = x509.get_extension(i)
                cert.set_extensions(
                    ext.get_short_name().decode(encoding="utf-8"),
                    ext.get_data(),
                )  # name?

            # fingerprints
            sha1 = sslparse.get_cert_sha1(orgiraw)
            cert.set_fingerprint("sha1", sha1)
            sha256 = sslparse.get_cert_sha256(orgiraw)
            cert.set_fingerprint("sha256", sha256)
            md5 = sslparse.get_cert_md5(orgiraw)
            cert.set_fingerprint("md5", md5)

            # issuer
            sissuer: OpenSSL.crypto.X509Name = x509.get_issuer()
            issuer: CertIssuer = CertIssuer()
            for bk, bv in sissuer.get_components():
                issuer.set_field(bk.decode(), bv.decode())
            cert.issuer = issuer

            # subject
            ssubject: OpenSSL.crypto.X509Name = x509.get_subject()
            subject: CertSubject = CertSubject()
            for bk, bv in ssubject.get_components():
                subject.set_field(bk.decode(), bv.decode())
            cert.subject = subject

            # construct sslcert
            sslcert: SslCert = SslCert(cert, orgiraw)

            # dhparams, from handshake
            # give up...for now, will do it later.
            # if sjtls["handshake_log"].__contains__("server_key_exchange") and sjtls[
            #     "handshake_log"
            # ]["server_key_exchange"].__contains__("ecdh_params"):
            #     sjdh = sjtls["handshake_log"]["server_key_exchange"]["ecdh_params"]
            #     pass

            # tls exts, from handshake
            # give up...for now, will do it later
            # the value is in server_hello

            # versions, from handshake
            # no API...

            # acceptable_cas, from handshake
            # no API

            # cipher
            if sjhandshakelog.__contains__("server_hello"):
                sjhello = sjhandshakelog["server_hello"]
                name: str = None
                version: str = None
                if sjhello.__contains__("cipher_suite") and sjhello[
                        "cipher_suite"].__contains__("name"):
                    name = sjhello["cipher_suite"]["name"]
                if sjhello.__contains__(
                        "version") and sjhello["version"].__contains__("name"):
                    version = sjhello["version"]["name"]
                if not name is None:
                    sslcert.set_cipher(name, version, None)

            # cert chain
            # sslparse.obtain_cert_chain()
            sjchain = sjhandshakelog["server_certificates"].get("chain")
            if isinstance(sjchain, list) and len(sjchain) > 0:
                for sjc in sjchain:
                    if (sjc is None or not isinstance(sjc, dict)
                            or not sjc.__contains__("raw")):
                        continue
                    chain_raw = sjc["raw"]
                    if not chain_raw.startswith("-----BEGIN CERTIFICATE-----"):
                        chain_raw = "-----BEGIN CERTIFICATE-----\n" + chain_raw
                    if not chain_raw.endswith("-----END CERTIFICATE-----"):
                        chain_raw = chain_raw.rstrip(
                        ) + "\n-----END CERTIFICATE-----"
                    sslcert.set_chain(chain_raw)

            # alpn
            # No API...
            portinfo.banner = sslcert.build_banner()
            portinfo.set_sslinfo(sslcert)

        except Exception:
            self._logger.error("Parse one ssl json line error: {}".format(
                traceback.format_exc()))
