"""parse ssl certificate by openssl"""

# -*- coding:utf-8 -*-

import uuid
from subprocess import PIPE, Popen
from pathlib import Path
import OpenSSL

# execute this need openssl installed:
# 'openssl s_client -showcerts -connect googleapis.com:443'

tmppath = Path('./_clienttmpdir/openssl')
if not tmppath.exists():
    tmppath.mkdir(exist_ok=True)


def parse_ssl_raw(sslraw: str):
    """
    这里获取ssl的详细信息，这里会去调命令行的信息，如果
    当前程序如果不是运行在docker容器里可能就会无法解析
    ssl信息，所以尽量让当前的程序运行在容器里
    :param ssldata:
    :return:
    """

    res = None
    proc = None
    tmpname = None
    outs = None
    # 1、将数据保存在当前的缓存文件夹下
    try:
        tmpname = tmppath / f'{uuid.uuid1()}.crt'
        while tmpname.exists():
            tmpname = tmppath / f'{uuid.uuid1()}.crt'
        tmpname.write_text(sslraw, encoding='utf-8')
        proc = Popen(f'openssl x509 -in {tmpname} -text -noout',
                     stdout=PIPE,
                     shell=True)
        outs, errs = proc.communicate(timeout=60)

        # if errs is not None and not errs == "":
        #     raise Exception(errs)

    except TimeoutError:
        # 数据量比较大就不设置超时了
        proc.kill()
        outs, errs = proc.communicate()

    except Exception as ex:
        raise Exception(ex)

    finally:
        if outs is not None:
            res = outs.decode('utf-8')

        # 回收数据，并且删除缓存
        if proc is not None:
            proc.kill()
        if tmpname is not None:
            tmpname.unlink()
    return res


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
            res = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1,
                                                  raw)
        except Exception:
            res = None

    return res