"""output config"""

# -*- coding:utf-8 -*-

from .outputerbase import OutputerBase


class OutputConfig:
    """表示输出器配置\n
    outputers: 配置输出器相关配置，此为一个以平台名称为键的输出器字典，例：
    {
        'xxx': OutputerFile(),
        'yyy': OutputerWeb()
    }"""

    def __init__(self, outputers: list):
        if not isinstance(outputers, list) or len(outputers) < 1:
            raise Exception("Invalid param 'outputers' for OutputConfig")

        self._outputers: dict = {}
        for o in outputers:
            if not isinstance(o, OutputerBase):
                raise Exception("Invalid Outputer object in OutputConfig")
            o: OutputerBase = o
            if not self._outputers.__contains__(o._platform):
                self._outputers[o._platform] = {}

            if self._outputers[o._platform].__contains__(o._description):
                raise Exception(
                    "Reduplicated description for outputer: {} {}".format(
                        o._platform, o._description
                    )
                )
            self._outputers[o._platform][o._description] = o
