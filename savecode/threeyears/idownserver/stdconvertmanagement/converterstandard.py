"""convert cmd"""

# -*- coding:utf-8 -*-

import traceback
from abc import ABCMeta, abstractmethod
from datacontract.inputdata import InputData
from dataparser import DataParser

from .converterbase import ConverterBase, DataSeg


class ConverterStandard(ConverterBase):
    """
    标准数据类型解析器基类
    """

    __metaclass = ABCMeta

    def __init__(self, uniquename, fields: dict, extensions: list,
                 extendfields: dict):

        if not isinstance(extensions, list) or len(extensions) < 1:
            raise Exception("Specified ConverterScan extension is invalid")

        ConverterBase.__init__(self, uniquename, fields, extendfields)

        self._extensions: list = []
        if isinstance(extensions, list):
            self._extensions: list = [e.strip(".") for e in extensions]

    @abstractmethod
    def match_data(self, data: InputData) -> bool:
        """匹配数据"""
        res: bool = False
        try:
            if data is None:
                raise Exception("Data is None.")

            if isinstance(
                    data.extension,
                    str) and data.extension.strip('.') in self._extensions:
                res = True

        except Exception:
            self._logger.error(
                "Match data error:\ndata:%s\nex:%s" % data._source,
                traceback.format_exc())
        return res

    def _get_segments(self, data: InputData) -> iter:
        """以标准数据的格式，读取数据流，返回数据段枚举"""
        if data.stream is None or not data.stream.readable():
            self._logger.error(
                "Data stream is None when trying to convert to standard Task: %s"
                % data._source)
            return

        succ = True
        try:
            for seg in DataParser.parse_standard_data(data.stream):
                # 获取到一个数据段
                seg: DataSeg = seg

                self._add_required_fields(seg, data)

                # 验证字段有效性
                if not self._validation_fields(seg, data):
                    succ = False
                    continue

                yield seg

        finally:
            if not succ:
                data.on_complete(False)