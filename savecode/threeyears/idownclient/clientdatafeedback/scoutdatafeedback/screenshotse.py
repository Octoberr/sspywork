"""represents a searchengine screenshot file"""

# -*- coding:utf-8 -*-

import io
from commonbaby.helpers import helper_crypto, helper_str, helper_time
from datacontract.iscoutdataset.iscouttask import IscoutTask, EObjectType
from datacontract.outputdata import EStandardDataType, OutputData, OutputDataSeg


class ScreenshotSE(OutputData, OutputDataSeg):
    """搜索引擎网页截图文件。必有keyword字段。
    此数据按标准键值对数据方式输出"""
    def __init__(self, task: IscoutTask, level: int, parentobj: str,
                 parentobjtype: EObjectType, url: str, keyword: str):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid iscouttask")
        # if not isinstance(level, int):
        #     raise Exception("Invalid level")
        if not isinstance(parentobjtype, EObjectType):
            raise Exception("Invalid parentobjtype")
        if not isinstance(url, str) or url == '':
            raise Exception("Invalid url")
        if not isinstance(keyword, str) or keyword == '':
            raise Exception("Invalid keyword")
        OutputData.__init__(self, task.platform,
                            EStandardDataType.IScoutScreenShotSE)
        OutputDataSeg.__init__(self)

        # OutputData.__init__(self, task._platform, EStandardDataType.IScoutScreenShotUrl)

        self._task: IscoutTask = task
        self._level: int = level
        self._parentobj: str = parentobj
        self.parentobjtype: EObjectType = parentobjtype
        self.url = url
        self.keyword: str = keyword
        # self.platform = platform
        # self.datatype: EStandardDataType = datatype

        self._stream: io.RawIOBase = None

    def get_output_segs(self) -> iter:
        """返回当前数据要输出的 数据段 集合的生成器iterable"""
        yield self

    def get_output_fields(self) -> dict:
        """返回当前数据要输出的 数据段 集合的生成器iterable"""
        self.append_to_fields('taskid', self._task.taskid)
        self.append_to_fields('batchid', self._task.batchid)
        self.append_to_fields('source', self._task.source)
        self.append_to_fields('periodnum', self._task.periodnum)
        self.append_to_fields('level', self._level)
        self.append_to_fields('parentobj', self._parentobj)
        self.append_to_fields('parentobjtype', self.parentobjtype.value)
        self.append_to_fields('url', self.url)
        self.append_to_fields('keyword', self.keyword)
        return self._fields

    def get_uniqueid(self):
        return helper_crypto.get_md5_from_str("{}{}{}".format(
            self._parentobj, self._task.platform, self.url))

    def get_display_name(self):
        res = ''
        if not helper_str.is_none_or_empty(self.url):
            res += " {}".format(self.url)
        return res

    @property
    def stream(self) -> io.RawIOBase:
        return self._stream

    @stream.setter
    def stream(self, value):
        self._stream = value

    def has_stream(self) -> bool:
        """返回bool值指示当前数据是否有二进制流"""
        # return self._stream is not None and self._stream.readable()
        return self._stream is not None

    def get_stream(self) -> io.RawIOBase:
        """如果当前数据有二进制数据流，返回此流对象，否则返回None"""
        return self._stream
