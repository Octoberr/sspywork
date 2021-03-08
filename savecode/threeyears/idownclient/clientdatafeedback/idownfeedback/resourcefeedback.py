"""
各种资源数据，包括聊天附带的表情、图片
、音频资源由于多个用户的资源可能有同一个，
所以不以userid为关联字段
create by judy  2018/10/18
"""

from commonbaby.helpers import helper_crypto, helper_str
from datacontract.idowndataset import Task
from datacontract.outputdata import EStandardDataType
from .feedbackbase import EResourceType, FeedDataBase, Resource


class RESOURCES(FeedDataBase, Resource):
    """
    tsk: datacontract.Task\n
    url: 资源的url链接，用作当前资源的唯一标识，不是用来访问的。
    resourcetype: 0图片 1视频 2音频 3网站（分享链接） 4其他
    """

    def __init__(self, clientid: str, tsk: Task, url: str,
                 resourcetype: EResourceType, apptype: int):
        FeedDataBase.__init__(self, '.idown_resource',
                              EStandardDataType.Resource, tsk, apptype,
                              clientid, False)
        Resource.__init__(self, url, resourcetype)

        self.resourceid: str = None
        self.extension: str = None

    def _get_output_fields(self) -> dict:
        """返回当前输出的数据段的字段字典"""
        self.append_to_fields('url', self._url)
        self.append_to_fields('resourceid', self.resourceid)
        self.append_to_fields('filename', self.filename)
        self.append_to_fields('sign', self._sign_map[self.sign])
        self.append_to_fields('extension', self.extension)
        self.append_to_fields('resourcetype', self._resourcetype.value)
        return self._fields

    # def _get_write_lines(self):
    #     lines = ''
    #     lines += 'url:{}\r\n'.format(helper_str.base64format(self._url))
    #     if self.resourceid is not None and self.resourceid != '':
    #         lines += 'resourceid:{}\r\n'.format(
    #             helper_str.base64format(self.resourceid))
    #     if self.filename is not None and self.filename != '':
    #         lines += 'filename:{}\r\n'.format(
    #             helper_str.base64format(self.filename))
    #     if self.sign is not None and self.sign != ESign.Null:
    #         lines += 'sign:{}\r\n'.format(
    #             helper_str.base64format(self._sign_map[self.sign]))
    #     if self.extension is not None and self.extension != '':
    #         lines += 'extension:{}\r\n'.format(
    #             helper_str.base64format(self.extension))
    #     lines += 'resourcetype:{}\r\n'.format(self._resourcetype)
    #     lines += '\r\n'
    #     return lines

    def get_uniqueid(self):
        return helper_crypto.get_md5_from_str("{}{}{}".format(self.resourceid, self._task.apptype, self._url))

    def get_display_name(self):
        res = ''
        if not helper_str.is_none_or_empty(self.filename):
            res += " {}".format(self.filename)
        if not helper_str.is_none_or_empty(self.sign):
            res += " {}".format(self.sign)
        return res
