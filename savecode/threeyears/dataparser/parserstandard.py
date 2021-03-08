"""standard data parser"""

# -*- coding:utf-8 -*-

import io
import traceback

from commonbaby.helpers import helper_str

from datacontract import DataSeg

from .dataparserbase import DataParserBase


class ParserStandard(DataParserBase):
    """标准数据解析器"""

    def __init__(self):
        DataParserBase.__init__(self)

    def _parse_sub(self, stm: io.IOBase) -> iter:
        """从流中解析标准数据，并返回 DataSeg 数据段迭代器"""
        return self.__get_segs_from_stream(stm)

    def __get_segs_from_stream(self, stm: io.IOBase,
                               targettype: type = None) -> iter:
        """从流中读取字段，返回 DataSeg 对象迭代器\n
        targettype: 目标类型，可以为任何 DataSeg 类型的子类，若为空，则返回 DataSeg 类型的对象"""
        try:

            if stm is None or stm.closed:
                raise Exception("Data stream is unreadable")

            segidx = 1
            segline = 0
            seg: DataSeg = DataSeg()
            prevline: str = ''
            for line in stm:
                if line is None or line == "":
                    break

                segline += 1

                if (line == '\n' or line == '\r\n') and \
                        (prevline.endswith('\n') or prevline.endswith('\r\n')):
                    seg.segindex = segidx
                    segidx += 1
                    seg.segline = segline
                    yield seg
                    seg = DataSeg()
                else:
                    k, v = helper_str.get_kvp(line, ':')
                    if not k is None and not k == "":
                        v = helper_str.base64_decode_format(v)
                        # 这里若遇到键相同，容错处理只保留第一次读到的键值对
                        if not seg._fields.__contains__(k):
                            seg._fields[k] = v.strip()

                prevline = line

            if not seg is None and len(seg._fields) > 0:
                seg.segindex = segidx
                seg.segline = segline
                yield seg

        except Exception as ex:
            raise ex
