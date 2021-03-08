"""bcp data parser"""

# -*- coding:utf-8 -*-

import io
import traceback

from commonbaby.helpers import helper_str

from datacontract import DataSeg

from .dataparserbase import DataParserBase


class ParserBcp(DataParserBase):
    """解析bcp结构数据并返回 DataSeg 数据段迭代器"""

    def __init__(self):
        DataParserBase.__init__(self)

    def _parse_sub(self, stm: io.IOBase) -> iter:
        """从流中解析标准数据，并返回 DataSeg 数据段迭代器"""
        pass

    def __get_segs_from_stm(self, stm: io.IOBase) -> iter:
        """"""
        if stm is None or not stm.readable():
            raise Exception("Data stream is unreadable")

        segindex = 0
        segline = 1  # BCP一行就是一个数据段
        for line in stm:
            try:
                items: list = line.split('\t')
                if not isinstance(items, list) or len(items) < 1:
                    continue

                # bcp字段
                seg: DataSeg = DataSeg()
                self._append_item(seg, 'ispid', items, 0)
                self._append_item(seg, 'sip', items, 1)
                self._append_item(seg, 'dip', items, 2)
                self._append_item(seg, 'sport', items, 3)
                self._append_item(seg, 'dport', items, 4)
                self._append_item(seg, 'time', items, 5, int)
                self._append_item(seg, 'phone', items, 6)
                self._append_item(seg, 'imsi', items, 7)
                self._append_item(seg, 'equipmentid', items, 8)
                self._append_item(seg, 'longitude', items, 9)
                self._append_item(seg, 'latitude', items, 10)
                self._append_item(seg, 'maintype', items, 11)
                self._append_item(seg, 'osversion', items, 12)
                self._append_item(seg, 'dataid', items, 13)
                self._append_item(seg, 'msisdn', items, 14)
                self._append_item(seg, 'lac', items, 15)
                self._append_item(seg, 'ci', items, 16)
                self._append_item(seg, 'url', items, 17)
                self._append_item(seg, 'host', items, 18)
                self._append_item(seg, 'cookie', items, 19)

                seg.segindex = segindex
                seg.segline = segline
                segline += 1
                segindex += 1
                yield seg
            except Exception as ex:
                self._logger.error(
                    "Parse one line in bcp file error: {}".format(ex))

    def _append_item(self,
                     seg: DataSeg,
                     key: str,
                     items: list,
                     itemidx: int,
                     totype: type = None):
        """判断items[itemidx]的值不为空，则fields[key]=items[itemidx]"""
        if not isinstance(seg, DataSeg) or not isinstance(
                key, str) or key == "" or not isinstance(
                    items, list) or not isinstance(itemidx, int):
            return
        if len(items) - 1 < itemidx:
            return
        val = items[itemidx]
        if not isinstance(val, str) or val == "":
            return
        val = val.strip()
        if val == "":
            return

        if isinstance(totype, type):
            val = totype(val)

        seg.append_to_fields(key, val)
