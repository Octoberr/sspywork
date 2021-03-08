"""helper for str"""

# -*- coding:utf-8 -*-

import ast
import base64
import json
from ast import literal_eval


def is_none_or_empty(s: str) -> bool:
    """judge if a str is None or empty str ''.
    s: source str.
    return: True if it's None or empty str, otherwise False."""
    if not isinstance(s, str):
        if s is None or s == "":
            return True
        else:
            return False
    else:
        if s is None or s == "":
            return True
        else:
            return False


def is_none_or_white_space(s: str) -> bool:
    """judge if a str is None or only contains white space.
    s: source str.
    return: True if it's None or empty str, otherwise False."""
    if s is None:
        return True
    tmp = s.strip().rstrip()
    if tmp is None or tmp == '':
        return True
    return False


def base64bytes(bs, encoding: str = 'utf-8', encerrors='strict') -> str:
    """base64 encode a byte[]
    bs: the byte[] to be encoded
    encoding: default is 'utf-8'
    return: the result str"""
    enc = encoding
    if enc is None or enc == '':
        enc = 'utf-8'
    bsOut = base64.b64encode(bs)
    res = str(bsOut, enc, encerrors)
    return res


def base64str(s: str,
              encoding: str = 'utf-8',
              decoding='utf-8',
              encerrors='strict',
              decerrors='strict') -> str:
    """base64 encode a str and return the str form of result.
    s: src str
    encoding: default is 'utf-8'
    return: result str"""
    enc = encoding
    if enc is None or enc == '':
        enc = 'utf-8'
    dec = decoding
    if dec is None or dec == '':
        dec = 'utf-8'

    bsIn = bytes(s, enc, encerrors)
    bsOut = base64.b64encode(bsIn)
    res = str(bsOut, dec, decerrors)
    return res


def base64format(s: str, enc='utf-8', encerrors='strict',
                 decerrors='strict') -> str:
    """return standard base64 format: =?utf-8?B?xxxx"""
    try:
        # return "=?{}?b?{}".format(enc, base64.b64encode(s.encode(enc, encerrors)).decode(enc, decerrors))
        return "=?{}?b?{}".format(enc,
                                  base64str(s, enc, enc, encerrors, decerrors))
    except Exception as ex:
        s = repr(s)
        # return "=?{}?b?{}".format(enc, base64.b64encode(s.encode(enc, encerrors)).decode(enc, decerrors))
        return "=?{}?b?{}".format(enc,
                                  base64str(s, enc, enc, encerrors, decerrors))


def base64_decode_format(s: str,
                         enc='utf-8',
                         encerrors='strict',
                         decerrors='strict') -> str:
    """try decode base64 like: =?utf-8?B?xxx"""
    res = s
    try:
        if not s.startswith('=?'):
            return res
        q1 = s.find('?')
        if q1 is None or q1 == -1:
            return res
        q2 = s.find('?', q1 + 1)
        if q2 is None or q2 == -1:
            return res
        enc = s[q1 + 1:q2]
        q3 = s.find('?', q2 + 1)
        if q3 is None or q3 == -1:
            return res
        codetype = s[q2 + 1:q3]
        if codetype is None or (not codetype == 'b' and not codetype == 'B'):
            return res
        src = s[q3 + 1:]
        if src is None or src == '':
            return ''
        #src: str = src
        # res = base64.b64decode(src.encode(enc)).decode(enc)
        res = base64_decode(src, enc, encerrors, decerrors)
        return res
    except Exception as ex:
        raise Exception("Decode base64 failed: %s  %s" % (s, ex))


def base64_decode(s: str, enc='utf-8', encerrors='strict',
                  decerrors='strict') -> str:
    '''errors: Default is 'strict' meaning that encoding errors raise 
    a UnicodeEncodeError. Other possible values are 'ignore', 
    'replace' and 'xmlcharrefreplace' as well as any other name 
    registered with codecs.register_error that can handle UnicodeEncodeErrors.'''
    return base64.b64decode(s.encode(enc, encerrors)).decode(enc, decerrors)


def base64_decode_to_bytes(s: str) -> bytes:
    return base64.b64decode(s)


def repr_str(s: str) -> str:
    '''将s字符串（可能为Unicode字符\\ud83d\\ude1d） 转换为正常显示的字符 😝, 失败返回 repr(s)'''
    res: str = s
    try:
        res = json.loads(repr(s).replace("'", '"'))
    except Exception:
        res = repr(s)
    return res


def repr_str_reverse(s: str) -> str:
    """repr的反向处理\n
    得到类似于:
    print(s) 后 在控制台输出的字符串的效果"""
    return literal_eval(s)


def convert_to_bytes(s: str, enc: str = 'utf-8', errors='strict') -> bytes:
    """将字符串转换为bytes，失败返回 bytes(repr(s),enc,errors) """
    res: bytes = None
    try:
        res = s.encode(enc)
    except UnicodeEncodeError:
        try:
            res = json.loads(repr(s).replace("'", '"'))
            if not isinstance(res, str):
                res = bytes(repr(s), enc, errors)
            else:
                res = res.encode(enc, errors)
        except Exception:
            res = bytes(repr(s), enc, errors)
    except Exception:
        res = bytes(repr(s), enc, errors)
    return res


def unicode_unescape(s: str) -> str:
    """do unicode unescape make '2007-2018\"\u003e' to '2007-2018">' """
    b = s.encode('utf-8')
    return b.decode('unicode_escape')


def get_kvp(s: str, splt: str) -> (str, str):
    """split s by splt, and return the key-value pairs.
    key is the str before the first 'splt' str, the rest is the value.
    return (None,None) if failed."""
    res = (None, None)
    if s is None or s == "":
        return res
    if splt is None or splt == "":
        return res
    idx: int = s.find(splt)
    if idx == -1:
        return (None, None)
    k: str = s[:idx]
    v: str = s[idx + 1:]
    res = (k, v)
    return res


def substringif(
        s: str,
        startStr: str,
        endStr: str,
        startIdx: int = 0,
) -> (bool, str):
    """get string after 'startStr' and before 'endStr', start to match 
    after 'startIdx, return (bool, str) which bool indicates if succeed 
    and str is the result when succeed."""
    retStr = substring(s, startStr, endStr, startIdx)
    if retStr is None or retStr == "" or retStr == "-1":
        return (False, None)

    return (True, retStr)


def substring(
        s: str,
        startStr: str,
        endStr: str,
        startIdx: int = 0,
) -> str:
    """get string after 'startStr' and before 'endStr', start to match 
    after 'startIdx, return str if succeed or None if failed."""
    res = None
    try:
        if s is None or s == "":
            return res
        if startIdx < 0:
            return res
        if len(s) < startIdx:
            return res
        stmp1: str = s[startIdx:len(s) - startIdx]

        index = 0
        if not startStr is None and not startIdx == "":
            index = stmp1.index(startStr)
        if index < 0:
            return res

        if not startStr is None and not startStr == "":
            index += len(startStr)

        #stmp1 = stmp1[index:len(stmp1) - index]
        stmp1 = stmp1[index:]
        length = stmp1.index(endStr)
        if length < 0:
            return res
        res = stmp1[0:length]
    except Exception as ex:
        res = None
    return res


if __name__ == "__main__":
    try:
        s = '\ud83d\ude02\ud83d\ude02\ud83d\ude02'
        ss = repr(s)
        sss = base64format(ss)
        a = 0
    except Exception as ex:
        pass


def parse_js(jsonstr):
    """
    解析非标准JSON的Javascript字符串，等同于json.loads(JSON str)\n
    jsonstr:非标准JSON的Javascript字符串\n
    返回Python字典对象
    """
    res = None
    try:
        m = ast.parse(jsonstr)
        a = m.body[0]
        res = __parse(a)
    except Exception:
        res = None
    return res


def __parse(node):
    if isinstance(node, ast.Expr):
        return __parse(node.value)
    elif isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Str):
        return node.s
    elif isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Dict):
        return dict(zip(map(__parse, node.keys), map(__parse, node.values)))
    elif isinstance(node, ast.List):
        return map(__parse, node.elts)
    elif isinstance(node, ast.UnaryOp):
        node: ast.UnaryOp = node
        return node.__repr__()
        # return  __parse(node)
    else:
        return node.__repr__()
        # raise NotImplementedError(node.__class__)
