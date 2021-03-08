"""
个人信息字段结构体
create by judy 2018/10/16
"""
import json

from commonbaby.helpers import helper_crypto, helper_str

from datacontract.idowndataset import Task
from datacontract.outputdata import EStandardDataType, OutputData, OutputDataSeg
from .feedbackbase import DetailedData, EGender, FeedDataBase, ResourceData


class PROFILE(FeedDataBase, ResourceData, DetailedData, OutputData,
              OutputDataSeg):
    """
    个人信息，下载文件中的个人信息,
    srcdata字典传入所有数据
    """

    @property
    def gender(self) -> EGender:
        """性别，使用统一的 feedbackbase.EGender枚举值"""
        return self._gender

    @gender.setter
    def gender(self, value):
        """性别，使用统一的 feedbackbase.EGender枚举值"""
        if not isinstance(value, EGender):
            raise Exception("Gender should be of type feedbackbase.EGender")
        self._gender = value

    def __init__(self, clientid: str, tsk: Task, apptype: int, userid):
        FeedDataBase.__init__(self, '.idown_profile',
                              EStandardDataType.Profile, tsk, apptype,
                              clientid, False)

        ResourceData.__init__(self)
        DetailedData.__init__(self)
        if userid is None:
            raise Exception('userid cant be None')
        self._userid = userid
        self.phone = None
        self.email = None
        # 任务的account
        self.account = tsk.account
        self.nickname = None
        self._gender: EGender = EGender.Unknown  # 性别
        self.birthday = None
        self.country = None
        self.region = None  # 地区
        self.address = None
        self.resoures: list = []  # 格式详情参见数据标准

    def _get_write_lines(self):
        lines = ''
        lines += 'userid:{}\r\n'.format(self._userid)
        if self.phone is not None and self.phone != '':
            lines += 'phone:{}\r\n'.format(self.phone)
        if self.email is not None and self.email != '':
            lines += 'email:{}\r\n'.format(self.email)
        if self.account is not None and self.account != '':
            if not self.account.startswith('=?utf-8?b?'):
                self.account = helper_str.base64format(self.account)
            lines += 'account:{}\r\n'.format(self.account)
        if self.nickname is not None and self.nickname != '':
            if not self.nickname.startswith('=?utf-8?b?'):
                self.nickname = helper_str.base64format(self.nickname)
            lines += 'nickname:{}\r\n'.format(self.nickname)
        if self.gender is not None and self.gender != '':
            lines += 'gender:{}\r\n'.format(self.gender.value)
        if self.birthday is not None and self.birthday != '':
            lines += 'birthday:{}\r\n'.format(
                helper_str.base64format(self.birthday))
        if self.country is not None and self.country != '':
            lines += 'country:{}\r\n'.format(
                helper_str.base64format(self.country))
        if self.region is not None and self.region != '':
            lines += 'region:{}\r\n'.format(
                helper_str.base64format(self.region))
        if self.address is not None and self.address != '':
            lines += 'address:{}\r\n'.format(
                helper_str.base64format(self.address))
        if isinstance(self._detail, dict) and len(self._detail) > 0:
            lines += 'detail:{}\r\n'.format(helper_str.base64format(
                    json.dumps(self._detail, ensure_ascii=False)))
        if isinstance(self._resources, list) and len(self._resources) > 0:
            lines += 'resources:{}\r\n'.format(helper_str.base64format(
                    json.dumps(self._resources, ensure_ascii=False)))
        return lines

    def _get_output_fields(self) -> dict:
        """返回当前输出的数据段的字段字典"""
        self.append_to_fields('userid', self._userid)
        self.append_to_fields('phone', self.phone)
        self.append_to_fields('email', self.email)
        self.append_to_fields('account', self.account)
        self.append_to_fields('nickname', self.nickname)
        self.append_to_fields('gender', self.gender.value)
        self.append_to_fields('birthday', self.birthday)
        self.append_to_fields('country', self.country)
        self.append_to_fields('region', self.region)
        self.append_to_fields('address', self.address)
        self.append_to_fields('detail', json.dumps(self._detail, ensure_ascii=False))
        self.append_to_fields('resources', json.dumps(self._resources, ensure_ascii=False))
        return self._fields

    def get_uniqueid(self):
        return helper_crypto.get_md5_from_str(self._get_write_lines())

    def get_display_name(self):
        return self.nickname
