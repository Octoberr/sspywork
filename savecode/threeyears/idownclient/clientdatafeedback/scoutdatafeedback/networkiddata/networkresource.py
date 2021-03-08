"""
各种资源数据，包括聊天附带的表情、图片
、音频资源由于多个用户的资源可能有同一个，
所以不以userid为关联字段
create by judy  2018/10/18
"""

import enum
import io

from commonbaby.helpers import helper_crypto, helper_str, helper_time

from datacontract.iscoutdataset import IscoutTask
from datacontract.outputdata import (EStandardDataType, OutputData,
                                     OutputDataSeg)


class EResourceType(enum.Enum):
    """标识资源类型\n
    0图片 1视频 2音频 3网站（分享链接） 4其他"""

    Picture = 0
    Audio = 1
    Video = 2
    Url = 3
    Other_Text = 4


class ESign(enum.Enum):
    """对RESOURCE预定义的sign标记枚举"""
    Null = 0
    PicUrl = 1  # 标记当前数据为一个头像图片


class Resource:
    """表示一个资源数据。\n
    url:当前资源的唯一标识\n
    rsctype:EResourceType资源类型"""
    @property
    def sign(self):
        '''当前Resource资源的特殊标记，统一使用resourcefeedback.ESign枚举值'''
        return self.__sign

    @sign.setter
    def sign(self, value):
        '''当前Resource资源的特殊标记，统一使用resourcefeedback.ESign枚举值'''
        if not isinstance(value,
                          ESign) or not self._sign_map.__contains__(value):
            raise Exception("Value must be Esign or value is invalid")
        self.__sign = value

    def __init__(self,
                 url: str,
                 rsctype: EResourceType = EResourceType.Other_Text):
        if url is None or url == "":
            raise Exception("Invalid param 'url' for Resource")
        if not isinstance(rsctype, EResourceType):
            raise Exception("Invalid param 'rsctype' for Resource")

        self._url: str = url
        self._resourcetype: EResourceType = rsctype

        self.__sign: ESign = ESign.Null
        self._sign_map: dict = {
            ESign.Null: None,
            ESign.PicUrl: "picurl",
        }


class NetworkResource(Resource, OutputData, OutputDataSeg):
    """
    tsk: datacontract.Task\n
    url: 资源的url链接，用作当前资源的唯一标识，不是用来访问的。
    resourcetype: 0图片 1视频 2音频 3网站（分享链接） 4其他
    """
    def __init__(self, task: IscoutTask, platform: str, url: str, source: str,
                 rsctp: EResourceType):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid IscoutTask")
        if not isinstance(platform, str):
            raise Exception("Invalid platform")
        if not isinstance(url, str):
            raise Exception("Invalid url")
        if not isinstance(source, str):
            raise Exception("Invalid source")

        Resource.__init__(self, url, rsctp)
        OutputData.__init__(self, platform,
                            EStandardDataType.IScoutNetworkResource)
        OutputDataSeg.__init__(self)

        self._task: IscoutTask = task
        self._source: str = source

        self.resourceid: str = None
        self.filename: str = None
        self.extension: str = None
        self.remark: str = None

        self.stream = None

    def get_output_segs(self) -> iter:
        """返回当前数据要输出的 数据段 集合的生成器iterable"""
        yield self

    def get_output_fields(self) -> dict:
        """返回当前输出的数据段的字段字典"""
        self.append_to_fields('taskid', self._task.taskid)
        self.append_to_fields('batchid', self._task.batchid)
        self.append_to_fields('source', self._source)
        # 新增字段
        if self._task.cmd.stratagyscout.relationfrom is not None:
            self.append_to_fields('relationfrom',
                                  self._task.cmd.stratagyscout.relationfrom)
        if not self.resourceid is None:
            self.append_to_fields('resourceid', self.resourceid)
        self.append_to_fields('url', self._url)
        if not self.filename is None:
            self.append_to_fields('filename', self.filename)
        if not self.extension is None:
            self.append_to_fields('extension', self.extension)
        if isinstance(self._resourcetype, EResourceType):
            self.append_to_fields('resourcetype', self._resourcetype.value)
        elif isinstance(self._resourcetype, int):
            self.append_to_fields('resourcetype', self._resourcetype)
        else:
            raise Exception("Invalid resourcetype: {}".format(
                self._resourcetype))
        if not self.sign is None:
            self.append_to_fields('sign', self._sign_map[self.sign])
        self.append_to_fields('time', helper_time.get_time_sec_tz())
        if isinstance(self.remark, str) and not self.remark == "":
            self.append_to_fields('remark',
                                  helper_str.base64format(self.remark))
        return self._fields

    def get_uniqueid(self):
        return helper_crypto.get_md5_from_str("{}{}{}".format(
            self.resourceid, self._task.platform, self._url))

    def get_display_name(self):
        res = ''
        if not helper_str.is_none_or_empty(self.filename):
            res += " {}".format(self.filename)
        if not helper_str.is_none_or_empty(self.sign):
            res += " {}".format(self.sign)
        return res

    def get_stream(self) -> io.RawIOBase:
        return self.stream

    def has_stream(self) -> bool:
        return self.stream is not None
