"""represents a networkid profile"""

# -*- coding:utf-8 -*-

import json
import threading

from commonbaby.helpers import helper_str


# from ..scoutjsonable import ScoutJsonable


class NetworkProfile(object):
    """represents a networkid profile.\n
    task: IScoutTask\n
    level: the recursion level\n
    networkid: str 与目标相关的（找到关联）的目标网络Id/昵称/账号等\n
    userid:str 账号在目标网站的唯一标识。"""

    def __init__(self, networkid: str, userid: str, source: str):
        if networkid is None or networkid == "":
            raise Exception("Invalid networkid for networkid profile")
        if userid is None or userid == "":
            raise Exception("Invalid uniqueid for networkid profile")
        if source is None or source == "":
            raise Exception("Invalid source for networkid profile")

        # ScoutJsonable.__init__(self)

        # current fields
        self._networkid: str = str(networkid)
        try:
            if self._networkid.__contains__("\\u"):
                self._networkid = self._networkid.encode("utf-8").decode(
                    "unicode-escape"
                )
        except Exception:
            pass
        self._userid: str = str(userid)
        self._source: str = str(source)

        self.url: str = None
        self.reason: str = None

        self._emails: list = []
        self._emails_locker = threading.RLock()

        self._phones: list = []
        self._phones_locker = threading.RLock()

        self.nickname: str = (
            self._networkid
        )  # 这个是专门写在这的，要用其他值自行在外部赋值，不然就默认nickname=networkid
        self.gender: str = None
        self.birthday: str = None
        self.address: str = None

        self._profile_pic: str = None  # bas64后的二进制头像图片

        self._details: dict = {}
        self._details_locker = threading.RLock()

        self._contacts: dict = {}
        self._contacts_locker = threading.RLock()

    ###############################################
    # set items
    def set_email(self, *emails: str):
        """向当前节点设置 email"""
        if emails is None or len(emails) < 1:
            return
        with self._emails_locker:
            for e in emails:
                if e not in self._emails:
                    self._emails.append(e)

    def set_phone(self, *phones: str):
        """向当前节点设置 phone"""
        if phones is None or len(phones) < 1:
            return
        with self._phones_locker:
            for p in phones:
                if p not in self._phones:
                    self._phones.append(p)

    def set_profile_pic(self, profile_pic: bytes):
        if not isinstance(profile_pic, bytes):
            raise Exception("Invalid profile_pic, should be bytes")
        self._profile_pic = helper_str.base64bytes(profile_pic)

    def set_contacts(
        self,
        profile,
        isfollower: bool = False,
        isfollowing: bool = False,
        isfriend: bool = False,
    ):
        """设置好友"""
        if not isinstance(profile, NetworkProfile):
            raise Exception("Invalid NetworkProfile")
        # profile: NetworkProfile = profile
        if self._contacts.__contains__(profile._userid + profile._source):
            return
        with self._contacts_locker:
            if self._contacts.__contains__(profile._userid + profile._source):
                return
            self._contacts[profile._userid + profile._source] = (
                profile,
                isfollower,
                isfollowing,
                isfriend,
            )

    def set_details(self, **keyvalues):
        """把键值对 (key1=value1, key2=value2)设置到当前details。注意如果多次设置时，键相同的值会被覆盖"""
        if keyvalues is None or len(keyvalues) < 1:
            return
        with self._details_locker:
            for k, v in keyvalues.items():
                self._details[k] = v

    ###############################################
    # output
    def get_outputdict(self) -> dict:
        """返回当前对象的输出用的json对象"""
        res: dict = {}
        jprofile = res["profile"] = {}
        self._get_outputdict_profile(jprofile)
        jcontacts = res["contacts"] = []
        self._get_outputdict_contacts(jcontacts)
        return res

    def _get_outputdict_profile(self, jprofile: dict):
        """添加profile根节点"""
        jprofile["networkid"] = (
            self.nickname if self.nickname is not None else self._networkid
        )

        jprofile["userid"] = self._userid
        jprofile["source"] = self._source

        if self.url is not None:
            jprofile["url"] = self.url

        if self.reason is not None:
            jprofile["reason"] = self.reason

        if len(self._emails) > 0:
            jemail = jprofile["emails"] = []
            with self._emails_locker:
                for e in self._emails:
                    jemail.append({"email": e})

        if len(self._phones) > 0:
            jphone = jprofile["phones"] = []
            with self._phones_locker:
                for p in self._phones:
                    jphone.append({"phone": p})

        if self.nickname is not None:
            jprofile["nickname"] = self.nickname
        if self.gender is not None:
            jprofile["gender"] = self.gender
        if self.birthday is not None:
            jprofile["birthday"] = self.birthday
        if self.address is not None:
            jprofile["address"] = self.address
        if isinstance(self._profile_pic, bytes):
            jprofile["profile_pic"] = "=?utf-8?B?{}".format(
                helper_str.base64bytes(self._profile_pic)
            )
        elif isinstance(self._profile_pic, str) and self._profile_pic != "":
            jprofile["profile_pic"] = "=?utf-8?B?{}".format(self._profile_pic)
        if self._details is not None and len(self._details) > 0:
            jprofile["detail"] = json.dumps(self._details, ensure_ascii=False)

    def _get_outputdict_contacts(self, jprofile: list):
        """
        输出每个这个账号的联系人
        :param jprofile:
        :return:
        """
        for con in self._contacts.values():
            profile, isfollower, isfollowing, isfriend = con
            profile: NetworkProfile = profile
            jprofile.append(
                {
                    "contactid": profile._userid,
                    "source": profile._source,
                    "isfollower": isfollower,
                    "isfollowing": isfollowing,
                    "isfriend": isfriend,
                }
            )
