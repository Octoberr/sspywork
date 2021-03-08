"""
聊天群组信息
create by judy 2018/10/18
"""

import json
import threading

from commonbaby.helpers import helper_crypto

from datacontract.idowndataset import Task
from datacontract.outputdata import EStandardDataType

from .feedbackbase import FeedDataBase, InnerDataBase, ResourceData


class ICHATGROUP_ONE(InnerDataBase, ResourceData):
    """表示一个(社交)群组"""

    @property
    def participants(self) -> iter:
        """当前群组内群成员的userid列表迭代器"""
        with self.__participants_locker:
            for i in self.__participants:
                yield i

    @property
    def participants_empty(self) -> bool:
        """指示当前群组的群成员列表是否为空，返回bool\n
        :return: True当前群组群成员列表为空，False不为空"""
        if any(self.__participants):
            return False
        return True

    def __init__(self, task: Task, apptype: int, userid, groupid):
        super(ICHATGROUP_ONE, self).__init__(task, apptype)
        ResourceData.__init__(self)
        if userid is None:
            raise Exception('userid cant be None')
        self._userid = userid
        if groupid is None:
            raise Exception('groupid cant be None')
        self._groupid = groupid
        self.__participants: list = []  # 此条消息参与人员的id列表
        self.__participants_locker = threading.RLock()
        self.groupname = None
        self.grouptype: str = None

    def append_participants(self, *items):
        """将若干个成员添加到当前ICHATGROUP_ONE的成员列表self._participants里"""
        if items is None or len(items) < 1:
            return
        with self.__participants_locker:
            for i in items:
                self.__participants.append(str(i))

    def _get_output_fields(self) -> dict:
        """"""
        self.append_to_fields('userid', self._userid)
        self.append_to_fields('groupid', self._groupid)
        self.append_to_fields(
            'participants', json.dumps(
                self.__participants, ensure_ascii=False))
        self.append_to_fields('groupname', self.groupname)
        self.append_to_fields('resources',
                              json.dumps(self._resources, ensure_ascii=False))
        self.append_to_fields('grouptype', self.grouptype)
        return self._fields

    # def _get_write_lines(self):
    #     lines = ''
    #     lines += 'userid:{}\r\n'.format(self._userid)
    #     lines += 'groupid:{}\r\n'.format(self._groupid)
    #     lines += 'participants:{}\r\n'.format(
    #         helper_str.base64format(
    #             json.dumps(self.__participants).encode().decode('unicode_escape')))
    #     if self.groupname is not None and self.groupname != '':
    #         if not self.groupname.startswith('=?utf-8?b?'):
    #             self.groupname = helper_str.base64format(self.groupname)
    #         lines += 'groupname:{}\r\n'.format(self.groupname)
    #     if isinstance(self._resources, list) and len(self._resources) > 0:
    #         lines += 'resources:{}\r\n'.format(
    #             helper_str.base64format(
    #                 json.dumps(self._resources).encode().decode('unicode_escape')))
    #     if self.grouptype is not None:
    #         lines += 'grouptype:{}\r\n'.format(
    #             helper_str.base64format(self.grouptype))
    #     return lines

    def get_uniqueid(self):
        return helper_crypto.get_md5_from_str("{}{}{}".format(
            self._userid, self._groupid, self._apptype))

    def get_display_name(self):
        return self.groupname


class ICHATGROUP(FeedDataBase):
    def __init__(self, clientid: str, tsk: Task, apptype: int):
        FeedDataBase.__init__(self, '.ichat_group',
                              EStandardDataType.ChatGroup, tsk, apptype,
                              clientid, True)
