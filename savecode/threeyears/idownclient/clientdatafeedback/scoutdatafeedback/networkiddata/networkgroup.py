"""represents a networkid profile"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.helpers import helper_str

from .networkprofile import NetworkProfile


class NetworkGroup(object):
    """represents a networkid profile.\n
    task: IScoutTask\n
    level: the recursion level\n
    networkid: str 与目标相关的（找到关联）的目标网络Id/昵称/账号等\n
    userid:str 账号在目标网站的唯一标识。"""

    def __init__(self, groupid: str, source: str):
        if groupid is None or groupid == '':
            raise Exception("Invalid groupid for networkid profile")
        if source is None or source == '':
            raise Exception("Invalid source for networkid profile")

        # ScoutJsonable.__init__(self)

        # current fields
        self._groupid: str = str(groupid)
        self._source: str = str(source)

        self.groupname: str = None
        self.grouptype: str = None
        self.url: str = None
        self.reason: str = None

        self.membercount: int = 0

        self._profile_pic: bytes = None

        self.details: str = None

        self._participants: dict = {}
        self._par_locker = threading.RLock()
        # 新加个字段phone,用来表示当前时哪个手机拿到的数据
        self.phone = None

    ###############################################
    # set items

    def set_profile_pic(self, profile_pic: bytes):
        if not isinstance(profile_pic, bytes):
            raise Exception("Invalid profile_pic, should be bytes")
        self._profile_pic = profile_pic

    def set_participant(self, profile: NetworkProfile):
        if not isinstance(profile, NetworkProfile):
            raise Exception("Invalid NetworkProfile")

        if self._participants.__contains__(profile._source + profile._userid):
            return
        with self._par_locker:
            if self._participants.__contains__(profile._source +
                                               profile._userid):
                return
            self._participants[profile._source + profile._userid] = profile

    ###############################################
    # outputdict

    def get_outputdict(self) -> dict:
        """返回当前对象的输出用的json对象"""
        res: dict = {}
        jgroup = res["group"] = {}
        self._get_outputdict_group(jgroup)

        jpar = res["participants"] = []
        self._get_outputdict_participants(jpar)

        return res

    def _get_outputdict_group(self, jgroup: dict):
        """搞group"""
        jgroup["groupid"] = self._groupid
        jgroup["source"] = self._source

        if not self.groupname is None:
            jgroup["groupname"] = self.groupname
        if not self.grouptype is None:
            jgroup["grouptype"] = self.grouptype
        if not self.url is None:
            jgroup["url"] = self.url
        if not self.reason is None:
            jgroup["reason"] = self.reason
        if not self.membercount is None:
            jgroup["membercount"] = self.membercount
        if isinstance(self._profile_pic, bytes):
            jgroup["profile_pic"] = "=?utf-8?B?{}".format(
                helper_str.base64bytes(self._profile_pic))
        if not self.details is None:
            jgroup["detail"] = self.details

    def _get_outputdict_participants(self, jpar: list):
        """搞 participants 字段"""

        with self._par_locker:
            for par in self._participants.values():
                par: NetworkProfile = par
                dpar = {
                    "userid": par._userid,
                    "nickname": par.nickname,
                    "source": par._source
                }
                jpar.append(dpar)
