"""standard convert manage"""

# -*- coding:utf-8 -*-

import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.idowndataset.task import Task
from inputmanagement.inputmanagement import InputData

from .convertconfig import ConvertConfig
from .converterbase import ConverterBase


class StandardConvertManagement:
    """数据标准转换，将各来源数据转换为统一的数据格式"""

    def __init__(self, cfg: ConvertConfig):
        if not isinstance(cfg, ConvertConfig) or cfg is None:
            raise Exception("Invalid standard converter config.")

        for cvtr in cfg._converters.values():
            if not issubclass(cvtr.__class__, ConverterBase):
                raise Exception("Specified convert is invalid.")

        self.converterconfig = cfg
        self._logger: MsLogger = MsLogManager.get_logger("stdconvertmanager")

    def convert(self, data: InputData) -> iter:
        """转换数据标准，返回标准Task结构体iterable"""
        try:
            cvtr = self._match_converter(data)
            if cvtr is None:
                self._logger.error("Converter not match:%s" % data._source)
                data.on_complete(False)
                return

            succ = False
            for tsk in cvtr.convert(data):
                if tsk is None:
                    self._logger.error(
                        "Convert data to task failed:%s" % data._source)
                    continue
                succ = True
                yield tsk

            if not succ:
                data.on_complete(False)

        except Exception:
            self._logger.error("Convert standard error:\ndata:%s\nerror:%s" %
                               (data._source, traceback.format_exc()))
            data.on_complete(False)

    def _match_converter(self, data: InputData) -> ConverterBase:
        """匹配转换器"""
        res: ConverterBase = None
        try:
            for cvtr in self.converterconfig._converters.values():
                cvtr: ConverterBase = cvtr
                if cvtr.match_data(data):
                    # data._srcmark
                    res = cvtr
                    break

        except Exception:
            self._logger.error(
                "Match standard converter error:\ndata:%s\nex:%s" %
                (data._source, traceback.format_exc()))
            res = None
        return res
