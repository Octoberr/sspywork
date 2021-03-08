"""help for cpmpressing"""

# -*- coding:utf-8 -*-

import io
import zlib
from gzip import GzipFile
from io import StringIO
import zipfile


def gzip_decompress(data: bytes) -> str:
    """decompress gziped data and retrun str"""
    buf = io.BytesIO(data)
    f = GzipFile(fileobj=buf)
    return f.read()


def deflate_decompress(data: bytes) -> str:
    """decompress deflated data and return str"""
    try:
        return zlib.decompress(data, -zlib.MAX_WBITS)
    except zlib.error:
        return zlib.decompress(data)


def zip_decompress(fi: str, outdir: str, pwd: str):
    """decompress zip file to outdir"""
    f = zipfile.ZipFile(fi, 'r')
    for file in f.namelist():
        f.extract(file, outdir, pwd)
