"""standard data parser"""

# -*- coding:utf-8 -*-

import io

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import DataSeg

from .parserbcp import ParserBcp
from .parserstandard import ParserStandard


class DataParser:
    """数据读取器\n
    解析各种格式化数据转换为内存数据结构 datacontract.DataSeg 对象
    """

    _logger: MsLogger = MsLogManager.get_logger('DataParser')

    _std_parser: ParserStandard = ParserStandard()
    _bcp_parser: ParserBcp = ParserBcp()

    def __init__(self):
        pass

    @staticmethod
    def parse_standard_data(stm: io.IOBase) -> iter:
        """从流中读取标准数据结构，返回多个 datacontract.DataSeg 数据段"""
        return DataParser._std_parser.parse(stm)

    @staticmethod
    def parse_bcp_data(stm: io.IOBase) -> iter:
        """从流中读取BCP结构，返回多个 datacontract.DataSeg 数据段"""
        return DataParser._bcp_parser.parse(stm)
