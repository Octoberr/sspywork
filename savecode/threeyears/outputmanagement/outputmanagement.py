"""output management"""

# -*- coding:utf-8 -*-

import queue
import threading
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.outputdata import OutputData

from .outputconfig import OutputConfig
from .outputerbase import OutputerBase
from .outputfile import Outputfile
from .outputstandardconfig import (
    OutputDataConfig,
    OutputPlatformConfig,
    OutputStandardConfig,
)

# __locker = threading.RLock()
# OutputManagement = None

# def __singleton_connmngr(cls):
#     """单例"""

#     # __singleton_connmngr.__doc__ = cls.__doc__

#     def _singleton(*args, **kwargs):
#         """"""

#         with __locker:
#             if OutputManagement._instance is None:
#                 OutputManagement._instance = cls(*args, **kwargs)
#             return OutputManagement._instance

#     _singleton.__doc__ = cls.__doc__
#     return _singleton

# @__singleton_connmngr


class OutputManagement_:
    """数据输出器\n
    outputconfig:输出默认路径等配置\n
    standardconfig:输出数据标准配置，每个数据来了会检查数据标准并自动构建输出数据\n"""

    _logger: MsLogger = MsLogManager.get_logger("Outputmanagement")
    _outputconfig: OutputConfig = None
    _standardconfig: OutputStandardConfig = None

    _outputers: dict = {}
    __outputers_locker = threading.RLock()

    _initialed: bool = False
    __initailed_locker = threading.RLock()

    def __init__(self):
        pass

    @classmethod
    def static_initial(
        cls, outputconfig: OutputConfig, standardconfig: OutputStandardConfig
    ):
        """初始化"""
        if cls._initialed:
            return
        with cls.__initailed_locker:
            if cls._initialed:
                return
            if not isinstance(outputconfig, OutputConfig):
                raise Exception("Invalid OutputConfig")
            if not isinstance(standardconfig, OutputStandardConfig):
                raise Exception("Invalid Ouptutstandard config")
            cls._outputconfig: OutputConfig = outputconfig
            cls._standardconfig = standardconfig
            # for o in cls._outputconfig._outputers.values():
            #     cls._append_outputer(o)
            cls._outputers = cls._outputconfig._outputers

            cls._initialed = True

    @classmethod
    def _append_outputer(cls, outputer: OutputerBase):
        """"""
        if not isinstance(outputer, OutputerBase):
            raise Exception("Invalid OutputerBase object")
        if cls._outputers.__contains__(outputer._description):
            raise Exception(
                "Reduplicated platform in outputers dictionary: {}".format(
                    outputer._description
                )
            )
        with cls.__outputers_locker:
            if cls._outputers.__contains__(outputer._description):
                raise Exception(
                    "Reduplicated platform in outputers dictionary: {}".format(
                        outputer._description
                    )
                )
            cls._outputers[outputer._description] = outputer

    @classmethod
    def _get_data_std(cls, data: OutputData) -> OutputDataConfig:
        """查找data对应的数据标准"""
        res: OutputDataConfig = None
        # 查找数据标准
        if not cls._standardconfig._output_platforms.__contains__(data._platform):
            cls._logger.error(
                "OutputData.plaform '{}' for Standard is not configured".format(
                    data._platform
                )
            )
            return res
        platformstd: OutputPlatformConfig = cls._standardconfig._output_platforms[
            data._platform
        ]
        if not platformstd._enabled:
            cls._logger.warn(
                "Platform data is disabled: {}".format(platformstd._platform)
            )
            return res
        if not platformstd._datas.__contains__(data._datatype):
            cls._logger.error(
                "OutputData.datatype '{}' in platform '{}' is not configured".format(
                    data._datatype.name, data._platform
                )
            )
            return res
        res: OutputDataConfig = platformstd._datas[data._datatype]
        return res

    @classmethod
    def output(cls, data: OutputData) -> bool:
        """查找平台映射，检查数据标准，并使用所有匹配的输出器实例
        输出数据到每个输出器实例的默认输出目录，返回bool指示是否输出成功"""
        res: bool = True
        try:

            if not isinstance(data, OutputData):
                cls._logger.error("Invalid OutputData object")
                res = False
                return res

            # 查找数据标准
            datastd: OutputDataConfig = cls._get_data_std(data)
            if not isinstance(datastd, OutputDataConfig):
                cls._logger.error(
                    "No data standard matches data:\nplatform:{}\ndatatype:{}\ndatasegidx:{}".format(
                        data._platform, data._datatype, data.segindex
                    )
                )
                res = False
                return res

            # 查找输出器
            if not cls._outputers.__contains__(data._platform):
                cls._logger.error(
                    "No outputer for specified platform matches data:\nplatform:{}\ndatatype:{}\ndatasegidx:{}".format(
                        data._platform, data._datatype, data.segindex
                    )
                )
                res = False
                return res

            # 遍历所有已配置的outputer，
            # 对每个符合条件的outputer都输出一次
            found: bool = False
            for o in cls._outputers[data._platform].values():
                outputer: OutputerBase = o
                if (
                    data._platform == o._platform
                    and o.match_data(data)
                    and isinstance(o, OutputerBase)
                ):
                    found = True
                    # 输出
                    if not outputer.output(data, datastd):
                        res = False

            if not found:
                cls._logger.error(
                    "No outputer matches data:\nplatform:{}\ndatatype:{}\ndatasegidx:{}".format(
                        data._platform, data._datatype, data.segindex
                    )
                )
                res = False
                return res

        except Exception:
            res = False
            cls._logger.error("output error: {}".format(traceback.format_exc()))
        return res

    @classmethod
    def output_to_file(cls, data: OutputData, targetdir: str) -> bool:
        """查找平台映射，检查数据标准，将数据输作为文件出到指定的目录\n
        data:数据\n
        targetdir:目标目录\n"""
        res: bool = True
        try:

            if not isinstance(data, OutputData):
                cls._logger.error("Invalid OutputData object")
                res = False
                return res

            # 查找数据标准
            datastd: OutputDataConfig = cls._get_data_std(data)
            if not isinstance(datastd, OutputDataConfig):
                cls._logger.error(
                    "No data standard matches data:\nplatform:{}\ndatatype:{}\ndatasegidx:{}".format(
                        data._platform, data._datatype, data.segindex
                    )
                )
                res = False
                return res

            # 直接调用文件输出器输出
            return Outputfile.output_to_file(data, datastd, targetdir)

        except Exception:
            res = False
            cls._logger.error("Output error: {}".format(traceback.format_exc()))
        return res

    @classmethod
    def output_move_file(cls, platform: str, srcfi: str) -> bool:
        """根据platform，把指定srcfi源文件移动到对应平台的回传目录中，
        返回是否移动成功True/False。\n
        若未找到指定平台的回传目录，则返回False。"""
        res: bool = False
        try:
            outputer: Outputfile = None
            for o in cls._outputers[platform].values():
                if not isinstance(o, Outputfile):
                    continue
                outputer: Outputfile = o

            if not isinstance(outputer, Outputfile):
                cls._logger.error(
                    "Target outputer not found for output move file:\nplatform:{}\ndata:{}".format(
                        platform, srcfi
                    )
                )
                return res

            res = outputer.output_move_file(platform, srcfi)

        except Exception:
            cls._logger.error(
                "Output move file error:\nplatform:{}\ndata:{}\nerror:{}".format(
                    platform, srcfi, traceback.format_exc()
                )
            )
        return res


OutputManagement = OutputManagement_
