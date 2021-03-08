"""standard convert config"""

# -*- coding:utf-8 -*-

from .converterbase import ConverterBase


class ConvertConfig:
    """标准转换配置，直接使用此配置实例化各转换器.\n
    dicconverters:实例化好的转换器字典，以键为唯一标识区分"""

    def __init__(self, dicconverters: dict):
        if not isinstance(dicconverters, dict) or len(dicconverters) < 1:
            raise Exception("No standard converter specified.")

        for converter in dicconverters.values():
            if not issubclass(converter.__class__, ConverterBase):
                raise Exception("Specified standard converter is invalid")

        self._converters = dicconverters
