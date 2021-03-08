"""ssl certificate helper over openssl"""

# -*- coding:utf-8 -*-

import io
import re
import uuid
from pathlib import Path
from subprocess import PIPE, Popen

import OpenSSL

from . import helper_crypto, helper_str

# execute this need openssl installed:
# 'openssl s_client -showcerts -connect googleapis.com:443'

tmppath = Path("./")
if not tmppath.exists():
    tmppath.mkdir(exist_ok=True)

_re_cert_raw = re.compile(
    r"-----BEGIN CERTIFICATE-----([^-]+?)-----END CERTIFICATE-----", re.S
)


def get_sslcert(raw: str) -> OpenSSL.crypto.X509:
    """parse ssl cert by pyOpenSSL\n
    return the cert object.\n
    return None if parse failed.\n
    
    raw example:\n
    -----BEGIN CERTIFICATE-----
    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
    -----END CERTIFICATE-----"""
    res: OpenSSL.crypto.X509 = None
    try:
        res = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, raw)
    except Exception:
        try:
            res = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, raw)
        except Exception:
            res = None

    return res


def format_ssl_raw(certraw: str) -> str:
    """parse ssl certificate raw data(without the \n
    '-----BEGIN CERTIFICATE-----' and -----END CERTIFICATE-----), \n
    and output the formatted result str"""
    res = None
    tmpname = None
    try:
        tmpname = tmppath / f"{uuid.uuid1()}.crt"
        while tmpname.exists():
            tmpname = tmppath / f"{uuid.uuid1()}.crt"
        tmpname.write_text(certraw, encoding="utf-8")

        res = exec_openssl(
            f"openssl x509 -in {tmpname} -text -noout", shell=True, raise_err=True
        )

    except Exception as ex:
        raise Exception(f"Parse ssl data error, may be it not in docker, err:{ex}")
    finally:
        # 删除缓存
        if tmpname is not None:
            tmpname.unlink()
    return res


def truncate_out_cert_raw(origin_raw_str: str):
    """truncate the original ssl certificate raw str like:\n
    -----BEGIN CERTIFICATE-----
    raw_str_data...
    -----END CERTIFICATE-----\n
    and split out the raw_str_data"""
    if not isinstance(origin_raw_str, str) or origin_raw_str == "":
        raise Exception("Invalid certificate origin_raw_str")
    if origin_raw_str.startswith("-----BEGIN CERTIFICATE-----"):
        origin_raw_str = origin_raw_str.replace("-----BEGIN CERTIFICATE-----", "")
    if origin_raw_str.endswith("-----END CERTIFICATE-----"):
        origin_raw_str = origin_raw_str.replace("-----END CERTIFICATE-----", "")
    origin_raw_str.strip()
    return origin_raw_str


def exec_openssl(
    cmd: str,
    input_: str = None,
    shell: bool = True,
    timeout: float = 15,
    raise_err: bool = False,
) -> str:
    """execute cmd on openssl and return the output str"""
    res: bytes = None
    proc = None
    # 1、将数据保存在当前的缓存文件夹下
    try:
        # if not isinstance(input_, bytes):
        #     input_ = input_.encode('utf-8')
        proc = Popen(
            cmd,
            stdin=PIPE,
            stdout=PIPE,
            stderr=PIPE,
            shell=shell,
            universal_newlines=True,
            encoding="utf-8",
            text=True,
        )
        if not input_ is None:
            proc.stdin.write(input_)
            proc.stdin.flush()
        outs, errs = proc.communicate(timeout=timeout)
        if raise_err and not errs is None and not errs == "":
            raise Exception(errs)

        res = outs

    except Exception as ex:
        if raise_err:
            raise ex
    finally:
        # 回收数据，并且删除缓存
        if proc is not None:
            proc.kill()
    return res


def get_cert_md5(certraw: str) -> str:
    """calc the md5 of a certificate, return hex str"""
    if not isinstance(certraw, str) or certraw == "":
        raise Exception("Invalid certificate raw str")
    certraw = truncate_out_cert_raw(certraw)
    bs = helper_str.base64_decode_to_bytes(certraw)
    bio = io.BytesIO(bs)
    return helper_crypto.get_md5_from_stream(bio)


def get_cert_sha1(certraw: str) -> str:
    """calc the sha1 of a certificate, return hex str"""
    if not isinstance(certraw, str) or certraw == "":
        raise Exception("Invalid certificate raw str")
    certraw = truncate_out_cert_raw(certraw)
    bs = helper_str.base64_decode_to_bytes(certraw)
    bio = io.BytesIO(bs)
    return helper_crypto.get_sha1_from_stream(bio)


def get_cert_sha1_by_openssl(certraw: str) -> str:
    """calc the sha1 of a certificate, return openssl result str"""
    res: str = None
    tmpname = None
    try:
        tmpname = tmppath / f"{uuid.uuid1()}.crt"
        while tmpname.exists():
            tmpname = tmppath / f"{uuid.uuid1()}.crt"
        tmpname.write_text(certraw, encoding="utf-8")

        cmd = f"openssl x509 -in {tmpname} -fingerprint -noout -sha1"
        res = exec_openssl(cmd)

    except Exception as ex:
        raise Exception(f"Parse ssl data error, err:{ex}")
    finally:
        if tmpname is not None:
            tmpname.unlink()
    return res


def get_cert_sha256(certraw: str) -> str:
    """calc the sha256 of a certificate, return hex str"""
    if not isinstance(certraw, str) or certraw == "":
        raise Exception("Invalid certificate raw str")
    certraw = truncate_out_cert_raw(certraw)
    bs = helper_str.base64_decode_to_bytes(certraw)
    bio = io.BytesIO(bs)
    return helper_crypto.get_sha256_from_stream(bio)


def get_cert_sha256_by_openssl(certraw: str) -> str:
    """calc the sha1 of a certificate, return openssl result str"""
    res: str = None
    tmpname = None
    try:
        tmpname = tmppath / f"{uuid.uuid1()}.crt"
        while tmpname.exists():
            tmpname = tmppath / f"{uuid.uuid1()}.crt"
        tmpname.write_text(certraw, encoding="utf-8")

        cmd = f"openssl x509 -in {tmpname} -fingerprint -noout -sha256"
        res = exec_openssl(cmd)

    except Exception as ex:
        raise Exception(f"Parse ssl data error, err:{ex}")
    finally:
        if tmpname is not None:
            tmpname.unlink()
    return res


def obtain_cert_chain(domain: str, https: bool = True, raise_err: bool = False) -> list:
    """obtain or retrive the completely ssl certificate chain \n
    of specified domain, return each certificate raw data str.\n
    This function causes network data."""
    res: list = []
    try:
        port = 443
        if not https:
            port = 80
        # cmd = 'openssl s_client -host {} -port {} -prexit -showcerts'.format(
        #     domain, port)
        cmd = "openssl s_client -showcerts -connect {}:{}".format(domain, port)

        # openssl这个奇怪，需要手动输入一个字符并输入换行才会结束
        outstr = exec_openssl(cmd, " \r\n", timeout=5)
        if outstr is None or outstr == "":
            return res

        # parse chain
        for seg in _re_cert_raw.finditer(outstr):
            if seg is None:
                continue
            raw = seg.group(1)
            if raw is None or raw == "":
                continue
            res.append(raw.strip())

    except Exception as ex:
        if not raise_err:
            return
        else:
            raise ex
    return res
