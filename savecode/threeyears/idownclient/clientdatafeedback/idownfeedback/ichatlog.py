"""
社交聊天记录
create by judy 2018/10/18
"""
import json

from commonbaby.helpers import helper_crypto

from datacontract.idowndataset import Task
from datacontract.outputdata import EStandardDataType
from .feedbackbase import FeedDataBase, InnerDataBase, ResourceData


class ICHATLOG_ONE(InnerDataBase, ResourceData):
    """
    userid:\n
    messagetype: 0图片 1视频 2音频 3网址 4其他（包括文本信息）\n
    sessionid: 当前消息所属会话id，一个会话id相当于一个新的聊天框框，群聊用群groupid，私聊用好友id\n
    chattype: 0私聊 1 群聊\n
    messageid: 当前消息的唯一id\n
    senderid: 发送者的userid"""

    def __init__(self, task: Task, apptype: int, userid: str, messagetype: int,
                 sessionid: str, chattype: int, messageid: str, senderid,
                 sendtime):
        super(ICHATLOG_ONE, self).__init__(task, apptype)
        ResourceData.__init__(self)
        if userid is None:
            raise Exception('userid cant be None')
        self._userid = userid
        if messagetype is None:
            raise Exception('messagetype cant be None')
        self._messagetype = messagetype  # 0图片 1视频 2音频 3网址 4其他
        if sessionid is None:
            raise Exception('sessionid cant be None')
        self._sessionid = sessionid
        if chattype is None:
            raise Exception('chattype cant be None')
        self._chattype = chattype  # 0私聊 1群聊
        if messageid is None:
            raise Exception('messageid cant be None')
        self._messageid = messageid
        if senderid is None:
            raise Exception('senderid cant be None')
        self._senderid = senderid
        self.sendername = None
        if sendtime is None:
            raise Exception('sendtime cant be None')
        self.sendtime: str = sendtime  # 时间字符串 yyyy-MM-dd HH:mm:ss
        self.isread: int = 0  # 0未读 1已读
        self.answered: int = 0  # 接收者是否响应 0未响应 1已响应
        self.content = ''  # 信息文本内容，初始为空字符串，外面用的时候好直接+=操作...

    def _get_output_fields(self) -> dict:
        """"""
        self.append_to_fields('userid', self._userid)
        self.append_to_fields('messagetype', self._messagetype)
        self.append_to_fields('sessionid', self._sessionid)
        self.append_to_fields('chattype', self._chattype)
        self.append_to_fields('messageid', self._messageid)
        self.append_to_fields('senderid', self._senderid)
        self.append_to_fields('sendername', self.sendername)
        self.append_to_fields('sendtime', self.sendtime)
        self.append_to_fields('isread', self.isread)
        self.append_to_fields('answered', self.answered)
        if len(self._resources) > 0:
            self.append_to_fields('resources', json.dumps(self._resources, ensure_ascii=False))
        self.append_to_fields('content', self.content)
        return self._fields

    # def _get_write_lines(self):
    #     lines = ''
    #     lines += 'userid:{}\r\n'.format(self._userid)
    #     lines += 'messagetype:{}\r\n'.format(self._messagetype)
    #     lines += 'sessionid:{}\r\n'.format(self._sessionid)
    #     lines += 'chattype:{}\r\n'.format(self._chattype)
    #     lines += 'messageid:{}\r\n'.format(
    #         helper_str.base64format(self._messageid))
    #     lines += 'senderid:{}\r\n'.format(self._senderid)
    #     if self.sendername is not None and self.sendername != '':
    #         lines += 'sendername:{}\r\n'.format(
    #             helper_str.base64format(self.sendername))
    #     lines += 'sendtime:{}\r\n'.format(self.sendtime)
    #     # 这个字段回传是一个bool值
    #     if isinstance(self.isread, int) and 0 <= int(self.isread) <= 1:
    #         lines += 'isread:{}\r\n'.format(self.isread)
    #     # 这个字段回传是一个bool值
    #     if isinstance(self.answered, int) and 0 <= self.answered <= 1:
    #         lines += 'answered:{}\r\n'.format(str(self.answered))
    #     if isinstance(self._resources, list) and len(self._resources) > 0:
    #         lines += 'resources:{}\r\n'.format(
    #             helper_str.base64format(
    #                 json.dumps(
    #                     self._resources).encode().decode('unicode_escape')))
    #     if not helper_str.is_none_or_empty(self.content):
    #         if not self.content.startswith('=?utf-8?b?'):
    #             self.content = helper_str.base64format(self.content)
    #         lines += 'content:{}\r\n'.format(self.content)
    #     return lines

    def get_uniqueid(self):
        return helper_crypto.get_md5_from_str("{}{}".format(
            self._userid, self._messageid))

    def get_display_name(self):
        return self._messageid


class ICHATLOG(FeedDataBase):
    def __init__(self, clientid: str, tsk: Task, apptype: int):
        FeedDataBase.__init__(self, '.ichat_log', EStandardDataType.ChatLog,
                              tsk, apptype, clientid, True)
