"""standard converter"""

# -*- coding:utf-8 -*-

import time
import traceback
from abc import ABCMeta, abstractmethod

from commonbaby.helpers import helper_str, helper_time
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import ALL_APPS, AppConfig, DataSeg, InputData


class ConverterField:
    """表示一个需要转换的字段.\n
    key: 字段名\n
    required: 是否为必要字段，默认为True\n
    ignorecase: 读取时是否忽略大小写，默认为True\n
    """

    def __init__(self,
                 key: str,
                 required: bool = True,
                 ignorecase: bool = True):
        if not isinstance(key, str) or key == "":
            raise Exception("Converter field param 'key' cannot be empty")
        if not isinstance(required, bool):
            raise Exception("Converter field param 'required' is invalid.")
        if not isinstance(ignorecase, bool):
            raise Exception("Converter field param 'ignorecase' is invalid.")

        self._key: str = key
        self._required: bool = required
        self._ignorecase: bool = ignorecase


class ConverterBase:
    """数据标准转换器基类.\n
    uniquename:当前转换器的唯一标识\n
    fields: 一个字典，包含当前转换器需要转换的字段，以字段名为键，ConverterField为值<key,ConverterField>。\n
    extendfields: 需要额外添加的字段字典集合<key, value>，若原始数据中无指定字段才添加"""

    __metaclass = ABCMeta

    def __init__(self,
                 uniquename: str,
                 fields: dict,
                 extendfields: dict = None):
        if not isinstance(uniquename, str) or uniquename == "":
            raise Exception("Specified converter unique name is invalid.")
        if not isinstance(fields, dict) or len(fields) < 1:
            raise Exception(
                "Specified converter fields is not a dict or no field specified: %s"
                % uniquename)

        for field in fields.values():
            if not isinstance(field, ConverterField):
                raise Exception(
                    "Specified converter filed is not a ConverterField")

        self._uniquename: str = uniquename
        self._fields: dict = fields

        self._extendfields: dict = {}
        if isinstance(extendfields, dict) and len(extendfields) > 0:
            for ext in extendfields.items():
                if not isinstance(ext[0], str) or ext[0] == "":
                    continue
                self._extendfields[ext[0]] = ext[1]

        self._logger: MsLogger = MsLogManager.get_logger(self._uniquename)

    @abstractmethod
    def match_data(self, data: InputData) -> bool:
        """匹配数据"""
        pass

    def convert(self, data: InputData) -> iter:
        """convert standard and return Tasks.
        If failed, return None"""
        for seg in self._convert(data):
            seg: DataSeg = seg
            seg.inputdata = data
            yield seg

    @abstractmethod
    def _convert(self, data: InputData) -> iter:
        """子类实现数据解析功能"""
        raise NotImplementedError()

    def _validation_fields(self, seg: DataSeg, data: InputData) -> bool:
        """根据配置验证输入数据的字段是否符合要求，返回验证后的字段集合（键为小写）"""
        res: bool = False
        try:
            for field in self._fields.values():
                field: ConverterField = field
                if field._ignorecase:
                    succ: bool = False
                    for f in seg._fields.items():
                        lowkey = f[0].lower()
                        if lowkey == field._key.lower():
                            # 如果原键不是小写，给转成小写的
                            if lowkey != f[0]:
                                seg._fields.pop(f[0], None)
                                seg._fields[lowkey] = f[1]
                            succ = True
                            break
                    if not succ and field._required:
                        self._logger.error(
                            "Invalid field '{}' in data:\nsegindex:{}\nsegline:{}\ndata:{}"
                            .format(field._key, seg.segindex, seg.segline,
                                    data.name))
                        return res
                else:
                    if not seg._fields.__contains__(
                            field._key) and field._required:
                        return res

            res = True
        except Exception:
            self._logger.error(
                "Validation fields failed:%s" % traceback.format_exc())
        return res

    def _add_required_fields(self, seg: DataSeg, data: InputData):
        """向DataSeg中添加当前转换器配置的必要字段"""
        # 添加额外字段
        if not self._extendfields is None:
            for ef in self._extendfields.items():
                if not seg.contains_key(ef[0]):
                    if not callable(ef[1]):
                        seg.append_to_fields(ef[0], ef[1])
                    else:
                        seg.append_to_fields(ef[0], ef[1]())

        # 添加额外必要字段
        if not seg.contains_key("platform"):
            seg.append_to_fields("platform", data._platform)
        # 新任务过来，要加一个time
        if not seg.contains_key("time"):
            seg.append_to_fields("time", helper_time.ts_since_1970_tz())

    def _get_apptype(self, fields: dict, data: InputData) -> int:
        """从cookie文件中的host字段判断apptype，并返回 int apptype"""
        res: str = None
        try:

            if not fields.__contains__("host"):
                self._logger.error(
                    "Get apptype of data by '%s' failed, no 'host' find in cookie: %s"
                    % (self._uniquename, data._source))
                return res

            host: str = fields["host"]

            for cfg in ALL_APPS.values():
                cfg: AppConfig = cfg
                if any(
                        host.__contains__(h) or h.__contains__(host)
                        for h in cfg._apphosts):
                    res = cfg._apptype
                    break

        except Exception:
            res = None
            self._logger.error(
                "Get apptype of data by '{}' error:\ndata:{}\nerror:{}".format(
                    self._uniquename, data._source, traceback.format_exc()))
        return res
