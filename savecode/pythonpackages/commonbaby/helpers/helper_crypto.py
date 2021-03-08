"""helper for cryptograph"""

# -*- coding:utf-8 -*-

import hashlib
import io

from Crypto.Cipher import AES
from Crypto.Hash import SHA1, SHA256

################################
# MD5


def get_md5_from_str(src: str) -> str:
    """calculate md5 for the src str and return the result str."""
    res: str = ""
    if not isinstance(src, str) or str == "":
        return res
    m: hashlib._hashlib.HASH = hashlib.md5()
    m.update(src.encode('utf-8'))
    res = m.hexdigest()
    return res


def get_md5_from_stream(src: io.IOBase) -> str:
    """calculate md5 of src stream. The stream could been 
    from a file(mode='rb')/network-stream/stringio or any other readable
    object in BINARY stream. This method will NOT close the stream! 
    Return the MD5 hex digest number."""
    if not isinstance(src, io.IOBase) or not src.readable():
        raise Exception("src is not stream or unreadable")
    m: hashlib._hashlib.HASH = hashlib.md5()
    while True:
        b = src.read(4096)
        if not b:
            break
        m.update(b)

    res = m.hexdigest()
    return res


################################
# AES


def aes_encrypt_bs(key: [str, bytes], bmessage: bytes) -> bytes:
    """aes encrypt.\n
    key: the aes key\n
    message: the str to be aes encrypted"""
    if not isinstance(key, bytes):
        key = key.encode('utf-8')
    if not isinstance(bmessage, bytes):
        raise Exception("")
    cipher = AES.new(key, AES.MODE_CBC, key)
    v1 = len(bmessage)
    v2 = v1 % 16
    if v2 == 0:
        v3 = 16
    else:
        v3 = 16 - v2
    for i in range(v3):
        bmessage.append(v3)
    mi_msg = cipher.encrypt(bmessage)
    return mi_msg


def aes_encrypt(key: str, message: str) -> bytes:
    """aes encrypt.\n
    key: the aes key\n
    message: the str to be aes encrypted"""
    if not isinstance(message, str):
        raise Exception("message cannot be None")
    bmessage = bytearray(message, encoding='utf-8')
    return aes_encrypt_bs(key, bmessage)


def aes_decrypt(key: str, message: bytes) -> str:
    if not isinstance(key, bytes):
        key = key.encode('utf-8')
    if not isinstance(message, bytes):
        raise Exception("Message must be bytes")
    cipher = AES.new(key, AES.MODE_CBC, key)
    result = cipher.decrypt(message)
    data: bytes = result[0:-result[-1]]
    return data.decode('utf-8')


################################
# SHA


def get_sha1(src: str) -> str:
    """get the sha1 of the src str, return hex str result"""
    if not isinstance(src, str) or src == "":
        raise Exception("Invalid src str")
    i = io.BytesIO(bytearray(src, encoding='utf-8'))
    return get_sha1_from_stream(i)


def get_sha1_from_stream(src: io.IOBase) -> str:
    """get the sha1 of the src bytes, return hex str result"""
    if not isinstance(src, io.IOBase) or not src.readable():
        raise Exception("src is not stream or unreadable")
    m: hashlib._hashlib.HASH = hashlib.sha1()
    return calc_hash(src, m)


def get_sha256(src: str) -> str:
    """get the sha256 of the src str, return hex str result"""
    if not isinstance(src, str) or src == "":
        raise Exception("Invalid src str")
    i = io.BytesIO(bytearray(src, encoding='utf-8'))
    return get_sha256_from_stream(i)


def get_sha256_from_stream(src: io.IOBase) -> str:
    """get the sha256 of the src bytes, return hex str result"""
    if not isinstance(src, io.IOBase) or not src.readable():
        raise Exception("src is not stream or unreadable")
    m: hashlib._hashlib.HASH = hashlib.sha256()
    return calc_hash(src, m)


def get_sha384(src: str) -> str:
    """get the sha384 of the src str, return hex str result"""
    if not isinstance(src, str) or src == "":
        raise Exception("Invalid src str")
    i = io.BytesIO(bytearray(src, encoding='utf-8'))
    return get_sha384_from_stream(i)


def get_sha384_from_stream(src: io.IOBase) -> str:
    """get the sha384 of the src bytes, return hex str result"""
    if not isinstance(src, io.IOBase) or not src.readable():
        raise Exception("src is not stream or unreadable")
    m = hashlib.sha384()
    return calc_hash(src, m)


def get_sha512(src: str) -> str:
    """get the sha512 of the src str, return hex str result"""
    if not isinstance(src, str) or src == "":
        raise Exception("Invalid src str")
    i = io.BytesIO(bytearray(src, encoding='utf-8'))
    return get_sha512_from_stream(i)


def get_sha512_from_stream(src: io.IOBase) -> str:
    """get the sha512 of the src bytes, return hex str result"""
    if not isinstance(src, io.IOBase) or not src.readable():
        raise Exception("src is not stream or unreadable")
    m = hashlib.sha512()
    return calc_hash(src, m)


def calc_hash(src: io.IOBase, m: hashlib._hashlib.HASH) -> str:
    """calc hash of the io-src and specified hash mode"""
    if src is None:
        raise Exception("Invalid src for hash calc")
    if m is None:
        raise Exception("Invalid hash m for hash calc")
    while True:
        b = src.read(4096)
        if not b:
            break
        m.update(b)
    res = m.hexdigest()
    return res


if __name__ == "__main__":
    try:
        print("ok")
    except Exception as ex:
        print(ex)
