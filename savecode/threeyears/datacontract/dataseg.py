"""data segment"""

# -*- coding:utf-8 -*-

import threading
from .inputdata import InputData


class DataSeg:
    """表示一个通用的，由多个数据行组成的数据段。包含多个字段<键，值>对"""

    @property
    def inputdata(self) -> InputData:
        """当前数据所属的原始数据"""
        return self._inputdata

    @inputdata.setter
    def inputdata(self, value):
        if not isinstance(value, InputData):
            raise Exception("Invalid InputData for DataSeg")
        self._inputdata = value

    @property
    def segindex(self) -> int:
        """当前数据段所在数据的段索引（第几段）
        """
        return self.__segindex

    @segindex.setter
    def segindex(self, value):
        """当前数据段所在数据的段索引（第几段）"""
        if not isinstance(value, int):
            raise Exception("Invalid segindex value")
        # 仅允许在self._segindex为-1时被赋值，
        # 因为若不为-1，说明是已经计算好了的索引，不允许二次变更
        if self.__segindex != -1:
            return
        with self.__segindex_locker:
            if self.__segindex == -1:
                self.__segindex = value

    @property
    def segline(self) -> int:
        """当前数据段所在数据中的行号"""
        return self.__segline

    @segline.setter
    def segline(self, value):
        """当前数据段所在数据中的行号"""
        # 仅允许在self._segline为-1时被赋值，
        # 因为若不为-1，说明是已经计算好了的行号，不允许二次变更
        if self.__segline != -1:
            return
        with self.__segline_locker:
            if self.__segline == -1:
                self.__segline = value

    def __init__(self):
        #
        self._inputdata: InputData = None

        # 属性字段，数据段所在数据中的索引
        self.__segindex: int = -1
        self.__segindex_locker = threading.RLock()

        # 属性字段，数据段所在数据中的行号
        self.__segline: int = -1
        self.__segline_locker = threading.RLock()

        self.__fields_locker = threading.RLock()
        self._fields: dict = {}

    def append_to_fields(self, key: str, val: str):
        '''将键值对 添加/更新 到当前数据段中'''
        if not isinstance(key, str) or key == "":
            raise Exception("Invalid key while appending to DataSeg fields")
        # 将所有字段无差别添加到字典中，输出时再判断是否可为空，需加密等
        with self.__fields_locker:
            self._fields[key] = val

    def contains_key(self, key: str):
        """判断当前 DataSeg 是否包含指定键"""
        if key is None:
            return False
        with self.__fields_locker:
            return self._fields.__contains__(key)

    def try_get_value(self, key: str) -> str:
        """尝试获取当前 DataSeg._fields 字段字典中的指定 key 对应的 value 值，
        若未找到，返回 None"""
        res: str = None
        if key is None or key == '':
            return res
        with self.__fields_locker:
            res = self._fields.get(key, None)
        return res

    def _judge(
            self,
            allfields: dict,
            key: str,
            dft=None,
            error: bool = False,
            excludefields: dict = None,
    ) -> str:
        """判断是否包含指定key字段。若包含则返回字段的值，若不包含时，若dft不为空，则返回dft(default值)，
        否则，当error为True时报错，为False时返回None"""
        return DataSeg._judge_static(allfields, key, dft, error, excludefields)

    @staticmethod
    def _judge_static(
            allfields: dict,
            key: str,
            dft=None,
            error: bool = False,
            excludefields: dict = None,
    ) -> str:
        """判断是否包含指定key字段。若包含则返回字段的值，若不包含时，若dft不为空，则返回dft(default值)，
        否则，当error为True时报错，为False时返回None"""
        if not isinstance(allfields, dict) or len(allfields) < 1:
            raise Exception("All fields is None when initial StatusBasic")
        if not isinstance(key, str) or key is None:
            raise Exception("Key cannot be None")

        res: str = None
        if allfields.__contains__(key):
            res = allfields[key]
            # 自动将已添加到Task结构体里的字段去掉
            if isinstance(excludefields, dict):
                excludefields.pop(key, None)
        elif dft is not None:
            res = dft
        elif not error:
            res = None
        else:
            raise Exception("Required key '%s' not found in allfields" % key)

        return res
