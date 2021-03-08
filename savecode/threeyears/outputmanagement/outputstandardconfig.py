"""output standard config"""

# -*- coding:utf-8 -*-

import enum

from datacontract.outputdata import EStandardDataType


class ECrypto(enum.Enum):
    """指定加密方式"""

    Null = 0
    Base64 = 1


OutputFieldConfig = None
OutputDataConfig = None
OutputPlatformConfig = None
OutputStandardConfig = None


class EDataName(enum.Enum):
    """指定数据名称构建方式"""

    # 使用Guid
    Guid = 1


class OutputFieldConfig_:
    """"表示一个输出数据标准中的一个字段\n
    fieldname:输出时的字段\n
    srcfield:源字段名（数据对象出来的）\n
    isrequired:bool，是否为必要字段\n
    crypto: ECrypto, 指定编码方式，默认为ECrypto.Null不编码\n
    cryptoenc: 指定编码所用的字符集，默认为utf-8\n
    dftval: 默认值，默认为None，无默认值\n
    typecheck: type类型，将检查字段值是否为此指定类型\n
    isfiltered: bool，指示当前字段是否在输出时被过滤（不输出），默认为False\n
    """

    @property
    def owner(self):
        """当前OutputFieldConfig的所属OutputDataConfig对象"""
        return self._owner

    @owner.setter
    def owner(self, value):
        """当前OutputFieldConfig的所属OutputDataConfig对象"""
        if not isinstance(value, OutputDataConfig):
            raise Exception("Invalid owner object: {}".format(value))
        self._owner = value

    def __init__(
            self,
            destfield: str,
            srcfield: str,
            isrequired: bool = False,
            crypto: ECrypto = ECrypto.Null,
            cryptoenc: str = "utf-8",
            dftval=None,
            typecheck: type = None,
            isfiltered: bool = False,
    ):
        if not isinstance(destfield, str) or destfield == "":
            raise Exception(
                "Invalid param 'outfield' in OutputFieldConfig, cannot be None or empty"
            )
        if not isinstance(srcfield, str) or srcfield == "":
            raise Exception(
                "Invalid param 'srcfield' in OutputFieldConfig, cannot be None or empty"
            )
        self._owner: OutputDataConfig = None
        self._destfield: str = destfield
        self._srcfield: str = srcfield
        self._isrequired: bool = False
        if isinstance(isrequired, bool):
            self._isrequired = isrequired
        self._crypto: ECrypto = ECrypto.Null
        if isinstance(crypto, ECrypto):
            self._crypto: ECrypto = crypto
        self._cryptoenc: str = "utf-8"
        if isinstance(cryptoenc, str) and not cryptoenc == "":
            self._cryptoenc = cryptoenc
        self._dftval = None
        if not dftval is None:
            self._dftval = dftval

        self._typecheck: type = typecheck

        self._isfiltered: bool = False
        if isinstance(isfiltered, bool):
            self._isfiltered = isfiltered


class OutputDataConfig_:
    """表示一个输出数据标准\n
    datatype: 数据类型唯一标识枚举\n
    suffix: 数据指定后缀，必须指定后缀\n
    fields: 当前数据类型的所有字段列表\n
    finame: 指示数据名的构建策略，默认为随机guid\n
    enable: 当前数据类型是否启用\n"""

    @property
    def owner(self):
        """当前OutputFieldConfig的所属OutputDataConfig对象"""
        return self._owner

    @owner.setter
    def owner(self, value):
        """当前OutputFieldConfig的所属OutputDataConfig对象"""
        if not isinstance(value, OutputPlatformConfig):
            raise Exception("Invalid owner object: {}".format(value))
        self._owner = value

    def __init__(
            self,
            datatype: EStandardDataType,
            suffix: str,
            fields: list,
            dataname: EDataName = EDataName.Guid,
            enable: bool = True,
    ):
        if not isinstance(datatype, EStandardDataType):
            raise Exception(
                "Invalid param 'datatype' in OutputDataConfig, cannot be None or empty"
            )
        if not isinstance(fields, list) or len(fields) < 1:
            raise Exception("Invalid param 'fields' for OutputDataConfig")
        if not isinstance(suffix, str) or suffix == "":
            raise Exception("Invalid param 'suffix' for OutputDataConfig")
        if not isinstance(dataname, EDataName):
            raise Exception("Invalid param 'datanme' for OutputDataConfig")

        self._owner: OutputPlatformConfig = None
        self._datatype: str = datatype
        self._suffix: str = suffix
        self._dataname: EDataName = dataname

        self._enable: bool = True
        if isinstance(enable, bool):
            self._enable = enable

        # 全部使用_srcfield，数据对象的键为键，便于字典查找
        self._fields: dict = {}
        for f in fields:
            f: OutputFieldConfig = f
            if self._fields.__contains__(f._srcfield):
                raise Exception(
                    "Reduplicate fieldname in OutputDataConfig: {} {}".format(
                        1, self._datatype))
            f.owner = self
            self._fields[f._srcfield] = f


class OutputPlatformConfig_:
    """表示一个平台的输出标准\n
    platform: 当前输出标准所属平台\n
    enabled: 当前平台的输出标准是否启用\n"""

    def __init__(self, platform: str, datas: list, enabled: bool = True):
        if not isinstance(platform, str) or platform == "":
            raise Exception("param 'platform' cannot be None or empty")
        if not isinstance(datas, list) or len(datas) < 1:
            raise Exception("param 'datas' is Invalid")

        self._platform: str = platform
        self._enabled: bool = True
        if isinstance(enabled, bool):
            self._enabled = enabled

        self._datas: dict = {}
        for data in datas:
            data: OutputDataConfig = data
            if not isinstance(data, OutputDataConfig):
                raise Exception("Invalid OutputDataConfig object")
            if self._datas.__contains__(data._datatype):
                raise Exception("Reduplicate OutputDataConfig: {} {}".format(
                    self._platform, data._datatype))
            data.owner = self
            self._datas[data._datatype] = data


class OutputStandardConfig_:
    """表示所有的输出标准\n
    规范性： 输出时，根据不同平台，检查输出数据的有效性，避免输出无效数据/错误数据。\n 
    扩展性： 按平台调整配置则可以同时适配不同平台。\n
    output_platform_configs: 各平台输出标准\n
    例：\n
    {
        "aaa": OutputPlatformConfig(aaa_params),
        "bbb": OutputPlatformConfig(bbb_params),
    }"""

    def __init__(self, platforms: list):
        if not isinstance(platforms, list) or len(platforms) < 1:
            raise Exception(
                "No output config configured in outputmanagement.outputconfig")

        self._output_platforms: dict = {}
        for item in platforms:
            p: OutputPlatformConfig = item
            if not isinstance(p, OutputPlatformConfig):
                raise Exception(f"Invalid {OutputPlatformConfig} : {p}")
            if self._output_platforms.__contains__(p._platform):
                raise Exception(
                    "Reduplicate platform in OutputConfig: {}".format(
                        p._platform))
            self._output_platforms[p._platform] = p


OutputStandardConfig = OutputStandardConfig_
OutputPlatformConfig = OutputPlatformConfig_
OutputDataConfig = OutputDataConfig_
OutputFieldConfig = OutputFieldConfig_
