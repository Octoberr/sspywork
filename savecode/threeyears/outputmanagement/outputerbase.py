"""outputer basic class"""

# -*- coding:utf-8 -*-

import io
import queue
import threading
import time
import traceback
import uuid
from abc import ABCMeta, abstractmethod

from commonbaby import charsets
from commonbaby.helpers import helper_str
from commonbaby.mslog import MsLogger, MsLogManager
from datacontract.datamatcher import DataMatcher
from datacontract.outputdata import OutputData, OutputDataSeg

from .outputstandardconfig import (ECrypto, EDataName, OutputDataConfig,
                                   OutputFieldConfig)


class OutputerBase:
    """represents an outputer, provides output interface\n
    description:当前输出器描述，必填，且每个输出器唯一\n
    platform:当前输出器所属平台\n
    datamathcer:数据匹配器，匹配输出数据是否应由当前输出器处理，默认为None则默认匹配\n
    maxsegcount:一次性最大输出数据段数量，默认为1000\n
    enc:输出时使用的字符集\n"""

    __metaclass = ABCMeta

    _logger: MsLogger = MsLogManager.get_logger("Outputer")

    def __init__(
            self,
            description: str,
            platform: str,
            datamatcher: DataMatcher = None,
            maxsegcount: int = 1000,
            enc: str = "utf-8",
    ):
        if not isinstance(description, str) or description == "":
            raise Exception("Invalid description for outputer")
        if not isinstance(platform, str) or platform == "":
            raise Exception("Invalid platform for outputer")

        self._description: str = description  # 当前输出器唯一描述信息
        self._platform: str = platform  # 当前输出器所属平台
        self._maxsegcount: int = 1000  # 单次发送数据的最大数据段数量
        if isinstance(maxsegcount, int) and maxsegcount > 0:
            self._maxsegcount = maxsegcount

        self._datamacher: DataMatcher = DataMatcher()
        if isinstance(datamatcher, DataMatcher):
            self._datamacher = datamatcher

        if not isinstance(
                enc, str) or enc == "" or not charsets.contains_charset(enc):
            raise Exception("Invalid charset param 'enc' for OutputerBase")
        self._enc: str = enc

        self._logger: MsLogger = MsLogManager.get_logger("Output_{}".format(
            self._platform))

    def match_data(self, data: OutputData) -> bool:
        """匹配数据，返回数据是否应由当前输出器处理True是/False否"""
        return self._datamacher.match_data(data)

    def output(self, data: OutputData, datastd: OutputDataConfig) -> bool:
        """异步输出。
        根据标准检验数据字段是否符合规范，并输出数据，返回bool指示是否输出成功\n
        data: 要输出的数据对象\n
        datastd: 此数据对应的数据标准"""
        res: bool = False
        try:
            if not isinstance(data, OutputData):
                self._logger.error(
                    "Invalid OutputData object: {}".format(data))
                return res

            if not isinstance(datastd, OutputDataConfig):
                self._logger.error(
                    "Invalid OutputDataStandard: {}".format(datastd))
                return res

            stm = data.get_stream()

            if not issubclass(type(stm), io.IOBase) or not stm.readable():
                succ: bool = True
                for b in self._get_mutiple_bs(data, datastd):
                    if not self._output_sub(data, b, datastd):
                        succ = False
                res = succ
            else:
                b: bytes = self._get_single_bs(data, datastd, stm)
                res = self._output_sub(data, b, datastd, stm)

            if callable(data.on_complete):
                data.on_complete(res, data)

        except Exception:
            self._logger.error("Output data error: {} {}\n{}".format(
                data._platform, datastd._uniquename, traceback.format_exc()))
        return res

    @classmethod
    def _get_mutiple_bs(
            cls,
            data: OutputData,
            datastd: OutputDataConfig,
            enc: str = "utf-8",
            maxsegcount: int = 1000,
    ) -> iter:
        """输出多段类型数据，返回bytes迭代器"""
        res: bool = True
        segcount = 0
        segbs: bytes = bytes()
        try:
            if not datastd._enable:
                cls._logger.debug(
                    "Data standard '{}' in platform '{}' is not enabled, data won't output"
                    .format(datastd._datatype.name, datastd.owner._platform))
                return res
            for seg in data.get_output_segs():
                try:
                    # 构建输出bytes
                    try:
                        if not isinstance(seg, OutputDataSeg):
                            cls._logger.error(
                                "Invalid OutputDataSeg object: {}".format(seg))
                            res = False
                            return res
                        seg: OutputDataSeg = seg
                        # 检查输出数据字段有效性
                        fields = cls._parse_fields(seg, datastd)
                        if not isinstance(fields, dict) or len(fields) < 1:
                            continue
                        bs = cls._fields_to_bytes(fields, enc)
                        if bs is None or not any(bs):
                            continue

                        segbs += bs
                        segcount += 1
                    except Exception:
                        res = False
                        cls._logger.error(
                            "Check segment fields validation failed:\nplatform:{}\ndatatype:{}\nerror:{}"
                            .format(
                                data._platform,
                                data._datatype.name,
                                traceback.format_exc(),
                            ))

                    if segcount < maxsegcount:
                        continue

                    # 达到segment段落数量上限输出
                    try:
                        yield segbs
                    except Exception:
                        cls._logger.error(
                            "Output mutiple segments error: {}".format(
                                traceback.format_exc()))
                    finally:
                        segbs = bytes()
                        segcount = 0

                except Exception:
                    res = False
                    cls._logger.error(
                        "Check output data segment failed:\nplatform:{}\ndatatype:{}\nerror:{}"
                        .format(data._platform, data._datatype.name,
                                traceback.format_exc()))

            # 或者遍历所有seg完成时输出
            if not segbs is None and any(segbs):
                yield segbs

        except Exception:
            res = False
            cls._logger.error(
                "Output mutiple data segment error:\nplatform:{}\ndatatype:{}\nerror:{}"
                .format(data._platform, data._datatype.name,
                        traceback.format_exc()))

    @classmethod
    def _get_single_bs(
            cls,
            data: OutputData,
            datastd: OutputDataConfig,
            stm: io.RawIOBase,
            enc: str = "utf-8",
    ) -> bytes:
        """输出带文件体的数据类型"""
        res: bytes = None
        try:
            if not isinstance(data,
                              OutputData) or stm is None or not stm.readable():
                cls._logger.error(
                    "Invalid OutputData object or stream for output single")
                return res

            for seg in data.get_output_segs():
                # seg: OutputDataSeg = data.get_output_segs()
                fields: dict = cls._parse_fields(seg, datastd)
                if not isinstance(fields, dict) or len(fields) < 1:
                    cls._logger.error(
                        "Invalid fields after check output segment fields:\nplatform:{}\ndatatype:{}"
                        .format(data._platform, data._datatype.name))
                    return res
                bs: bytes = cls._fields_to_bytes(fields, enc)
                if bs is None or not any(bs):
                    return res

                res = bs
                return res

        except Exception:
            res = None
            cls._logger.error(
                "Output single data segment error:\nplatform:{}\ndatatype:{}\nerror:{}"
                .format(data._platform, data._datatype.name,
                        traceback.format_exc()))

    @abstractmethod
    def _output_sub(self,
                    data: OutputData,
                    bs: bytes,
                    datastd: OutputDataConfig,
                    stm: io.RawIOBase = None) -> bool:
        """子类实现将数据输出，并返回是否输出成功"""
        raise NotImplementedError()

    @classmethod
    def _parse_fields(cls, seg: OutputDataSeg,
                      datastd: OutputDataConfig) -> dict:
        """检查数据段的字段有效性，返回构建好的即将输出的字段字典"""
        res: dict = {}
        try:
            tmp: dict = {}
            srckey = ''
            fields = seg.get_output_fields()
            for fstd in datastd._fields.values():
                fstd: OutputFieldConfig = fstd
                if not fields.__contains__(
                        fstd._srcfield
                ) and fstd._isrequired and fstd._dftval is None:
                    cls._log_error_field(fstd._destfield, seg,
                                         "missing the field")
                    return res

            for f in fields.items():
                # 检查每个字段
                srckey = f[0]
                val = f[1]
                # 当前字段不在标准中，看值是否为空，不为空则输出，为空则继续
                if not datastd._fields.__contains__(srckey):
                    if val is None:
                        continue
                    else:
                        # 没配的，直接用srckey为输出键
                        tmp[srckey] = val
                # 当前字段在标准中配了的
                else:
                    f = None
                    fstd: OutputFieldConfig = datastd._fields[srckey]

                    # 被过滤的字段
                    if fstd._isfiltered:
                        continue
                    # 如果值为None，检查是否必要和默认值
                    if val is None or val == "":
                        # 如果非必要字段，则直接跳过
                        if not fstd._isrequired:
                            continue
                        # 如果为必要字段，则看有没有配默认值
                        else:
                            if not fstd._dftval is None:
                                val = fstd._dftval
                            # 如果没有配默认值，则报错返回
                            else:
                                cls._log_error_field(srckey, seg,
                                                     "missing the field")
                                return res

                    # 检查值类型
                    if not fstd._typecheck is None:
                        if not isinstance(val, fstd._typecheck):
                            if not fstd._isrequired:
                                continue
                            else:
                                cls._log_error_field(
                                    srckey,
                                    seg,
                                    "Wrong value type: key={} value={}".format(
                                        fstd._destfield, val),
                                )
                                return res

                    # 最后来编码等
                    if fstd._crypto != ECrypto.Null:
                        val = cls._crypto(val, fstd)

                    # 为空或None则不输出（再判断一次）
                    if val is None or val == '':
                        continue

                    # 赋值
                    tmp[fstd._destfield] = val

            res = tmp
        except Exception:
            cls._log_error_field(srckey, seg, "error occured")
            res = None
        return res

    @classmethod
    def _crypto(cls, val, fstd: OutputFieldConfig) -> str:
        """
        对val进行crypto编码，返回编码后的字符串
        val 可以是字符串,可以是bytes
        """
        res: str = None
        if val == "":
            res = val
            return res
        if not isinstance(fstd, OutputFieldConfig):
            raise Exception("Invalid OutputFieldConfig: {}".format(fstd))

        crypto: ECrypto = fstd._crypto
        if not isinstance(crypto, ECrypto):
            raise Exception("Unknow cryptograph method: {}".format(crypto))

        enc: str = fstd._cryptoenc
        if not charsets.contains_charset(enc):
            raise Exception("Unknow charset for encoding: {}".format(enc))
        # 有些数据不得不先加密
        if crypto == ECrypto.Null or not isinstance(
                val, str) or val.startswith('=?utf-8?b?'):
            res = val
        elif crypto == ECrypto.Base64:
            res = cls._base64_encrypt(val, enc)
        else:
            raise Exception("Unknow cryptograph method: {}".format(crypto))

        return res

    @classmethod
    def _base64_encrypt(cls, val, enc) -> str:
        # =?utf-8?b?xxxxx
        # 上面的代码已经判断完了，下面的代码就判断是否直接bytes加密或是str加密
        res = None
        if isinstance(val, str):
            try:
                res = "=?{}?b?{}".format(enc, helper_str.base64str(val, enc))
            except Exception:
                tmp = helper_str.repr_str(val)
                if not isinstance(val, str):
                    raise Exception(
                        "Invalid val for encryption: {}".format(val))
                res = "=?{}?b?{}".format(enc, helper_str.base64str(tmp, enc))
        elif isinstance(val, bytes):
            res = "=?{}?b?{}".format(enc, helper_str.base64bytes(val, enc))
        else:
            raise Exception("Invalid val for encryption: {}".format(val))
        return res

    @classmethod
    def _fields_to_bytes(cls, fields: dict, enc: str = "utf-8") -> bytes:
        """字段搞成bytes"""
        enc_ = "utf-8"
        if isinstance(enc, str) and charsets.contains_charset(enc):
            enc_ = enc
        res: bytes = bytes()
        for f in fields.items():
            try:
                s = "{}:{}\r\n".format(f[0], f[1])
                res += s.encode(enc_)
            except Exception as ex:
                # 此处不应报错或做任何处理，过来的字段必须为
                # 正常可转换为bytes的，如果不能，则应修改配置，将需要
                # base64的字段给编码了再过来
                # s = "{}:{}\r\n".format(f[0], helper_str.repr_str(f[1]))
                # res += s.encode(enc_)
                raise ex
        res += "\r\n".encode(enc_)
        return res

    @classmethod
    def _get_dataname(cls, datastd: OutputDataConfig) -> str:
        """构建数据名称"""
        res: str = None
        # 数据名称

        if datastd._dataname == EDataName.Guid:
            res = str(uuid.uuid1())
        else:
            raise Exception("Unknown EDataName config: {}".format(
                datastd._dataname))

        # 数据后缀
        if isinstance(datastd._suffix, str) and datastd._suffix != "":
            res = "{}.{}".format(res.rstrip("."), datastd._suffix.lstrip("."))

        return res

    @classmethod
    def _log_error_field(cls,
                         key: str,
                         seg: OutputDataSeg,
                         msg: str = None,
                         logger: MsLogger = None):
        lgr = cls._logger
        if isinstance(logger, MsLogger):
            lgr = logger
        lgr.error(
            "Check data field error:\nfield:{}\ndata:{}\nplatform:{}\nmsg:{}\nerror:{}"
            .format(
                key,
                seg.owner_data._datatype.name
                if not seg.owner_data is None else "",
                seg.owner_data._platform if not seg.owner_data is None else "",
                msg,
                traceback.format_exc(),
            ))
