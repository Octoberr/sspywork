"""
联系人数据结构体
create by judy 2018/10/16
"""

import json

from commonbaby.helpers import helper_crypto

from datacontract.idowndataset import Task
from datacontract.outputdata import EStandardDataType
from .feedbackbase import (DetailedData, EGender, FeedDataBase, InnerDataBase,
                           ResourceData)


class CONTACT_ONE(InnerDataBase, ResourceData, DetailedData):
    """表示一个联系人"""

    @property
    def gender(self) -> EGender:
        """性别，使用统一的 feedbackbase.EGender枚举值"""
        return self._gender

    @gender.setter
    def gender(self, value):
        """性别，使用统一的 feedbackbase.EGender枚举值"""
        if not isinstance(value, EGender):
            raise Exception("Gender should be of type contactfeedback.EGender")
        self._gender = value

    def __init__(self, userid, contactid, task: Task, apptype: int):
        super(CONTACT_ONE, self).__init__(task, apptype)
        # super(ResourceData, self).__init__()
        ResourceData.__init__(self)
        DetailedData.__init__(self)
        if userid is None:
            raise Exception("Userid cant be None.")
        self._userid = userid
        if contactid is None:
            raise Exception("contactid cant be None")
        self._contactid = contactid
        self.nickname = None
        self.phone = None
        self.group = None
        self.email = None
        self.birthday = None
        self._gender: EGender = EGender.Unknown  # 性别： 统一
        self.isfriend: int = 1  # 是否是好友，0不是，1是，默认为1
        self.bothfriend: int = 1  # 是否互为好友，0不是，1是，默认为1
        self.isdeleted: int = 0  # 是否为已删除的好友，0不是，1是，默认为1
        self.contact_type: str = None  # 联系人类型 好友/陌生人/xxx

    def _get_output_fields(self) -> dict:
        """返回个人信息应输出的所有字段字典"""
        self.append_to_fields('userid', self._userid)
        self.append_to_fields('contactid', self._contactid)
        self.append_to_fields('nickname', self.nickname)
        self.append_to_fields('phone', self.phone)
        self.append_to_fields('group', self.group)
        self.append_to_fields('gender', self.gender.value)
        self.append_to_fields('isfriend', self.isfriend)
        self.append_to_fields('bothfriend', self.bothfriend)
        self.append_to_fields('isdeleted', self.isdeleted)
        self.append_to_fields('resources', json.dumps(self._resources, ensure_ascii=False))
        self.append_to_fields('detail', json.dumps(self._detail, ensure_ascii=False))
        self.append_to_fields('email', self.email)
        self.append_to_fields('birthday', self.birthday)
        return self._fields

    # def _get_write_lines(self) -> str:
    #     lines: str = ''
    #     lines += 'userid:{}\r\n'.format(self._userid)
    #     lines += 'contactid:{}\r\n'.format(self._contactid)
    #     if self.nickname is not None and self.nickname != '':
    #         # 后面这个判断要搞成属性来写
    #         if not self.nickname.startswith('=?utf-8?b?'):
    #             self.nickname = helper_str.base64format(self.nickname)
    #         lines += 'nickname:{}\r\n'.format(self.nickname)
    #     if self.phone is not None and self.phone != '':
    #         lines += 'phone:{}\r\n'.format(self.phone)
    #     if self.group is not None and self.group != '':
    #         lines += 'group:{}\r\n'.format(self.group)
    #     if self.gender is not None and self.gender != '':
    #         lines += 'gender:{}\r\n'.format(self.gender.value)
    #     # 这三个字段只有当不为默认值时才输出，减少输出数据量
    #     if isinstance(self.isfriend, int) and self.isfriend != 1:
    #         lines += 'isfriend:{}\r\n'.format(self.isfriend)
    #     if isinstance(self.bothfriend, int) and self.bothfriend != 1:
    #         lines += 'bothfriend:{}\r\n'.format(self.bothfriend)
    #     if isinstance(self.isdeleted, int) and self.isdeleted != 0:
    #         lines += 'isdeleted:{}\r\n'.format(self.isdeleted)
    #
    #     if isinstance(self._resources, list) and len(self._resources) > 0:
    #         lines += 'resources:{}\r\n'.format(
    #             helper_str.base64format(
    #                 json.dumps(self._resources).encode().decode('unicode_escape')))
    #     if isinstance(self._detail, dict) and len(self._detail) > 0:
    #         lines += 'detail:{}\r\n'.format(
    #             helper_str.base64format(
    #                 json.dumps(self._detail).encode().decode('unicode_escape')))
    #     if self.email is not None:
    #         lines += 'email:{}\r\n'.format(self.email)
    #     if self.birthday is not None:
    #         lines += 'birthday:{}\r\n'.format(self.birthday)
    #     return lines

    def get_uniqueid(self) -> str:
        return helper_crypto.get_md5_from_str("{}{}{}".format(
            self._userid, self._contactid, self._apptype))

    def get_display_name(self):
        """返回当前数据的显示名称"""
        return self.nickname


class CONTACT(FeedDataBase):
    """表示一组联系人"""

    def __init__(self, clientid: str, tsk: Task, apptype: int):
        FeedDataBase.__init__(self, '.idown_contact',
                              EStandardDataType.Contact, tsk, apptype,
                              clientid, True)
