"""object networkid"""

# -*- coding:utf-8 -*-

import threading

from datacontract.iscoutdataset.iscouttask import EObjectType, IscoutTask
from .networkiddata import NetworkGroup, NetworkProfile
from .scoutfeedbackbase import ScoutFeedBackBase
from .searchengine import SearchEngine
from .whoisr import Whoisr


class NetworkId(ScoutFeedBackBase):
    """scout object IP"""

    def __init__(
            self,
            task: IscoutTask,
            level: int,
            networkid: str,
    ):
        ScoutFeedBackBase.__init__(self,
                                   task,
                                   level,
                                   EObjectType.NetworkId,
                                   networkid,
                                   'iscout_networkid')

        # current fields
        self.userid: str = None  # 必要
        self.url: str = None
        self.source: str = None  # 必要
        self.reason: str = None  # 必要

        # subitems
        self._whoisrs: dict = {}
        self._whoisrs_locker = threading.RLock()

        self._networkid_profile: dict = {}
        self._networkid_profile_locker = threading.RLock()

        self._networkid_groups: dict = {}
        self._networkid_groups_locker = threading.RLock()

        self._emails: dict = {}
        self._emails_locker = threading.RLock()

        self._phones: dict = {}
        self._phones_locker = threading.RLock()

        self._searchengine: dict = {}
        self._searchengine_locker = threading.RLock()

    def _subitem_count(self) -> int:
        """子类实现 返回当前根节点的 子数据 总条数"""
        res = 0
        with self._whoisrs_locker:
            res += len(self._whoisrs)
        with self._networkid_profile_locker:
            res += len(self._networkid_profile)
        with self._networkid_groups_locker:
            res += len(self._networkid_groups)
        with self._emails_locker:
            res += len(self._emails)
        with self._phones_locker:
            res += len(self._phones)
        with self._searchengine_locker:
            res += len(self._searchengine)
        return res

    ###############################################
    # set items
    def set_whoisr(self, whoisr: Whoisr):
        """向当前NetworkId根节点设置 Whoisr对象"""
        if not isinstance(whoisr, Whoisr):
            return
        with self._whoisrs_locker:
            self._whoisrs[whoisr._domain] = whoisr

    def set_networkid_profile(self, np: NetworkProfile):
        """向当前NetworkId根节点添加 网络id用户信息\n
        np: NetworIdkProfile 对象"""
        if not isinstance(np, NetworkProfile):
            raise Exception("Invalid NetworkIdProfile for NetworkId")
        with self._networkid_profile_locker:
            self._networkid_profile[np._source + np._userid] = np

    def set_networkid_group(self, group: NetworkGroup):
        """向当前NetworkId根节点添加 网络id用户信息\n
        np: NetworIdkProfile 对象"""
        if not isinstance(group, NetworkGroup):
            raise Exception("Invalid NetworkIdProfile for NetworkId")
        with self._networkid_groups_locker:
            self._networkid_groups[group._source + group._groupid] = group

    def set_email(self, email):
        """向当前NetworkId根节点添加 邮箱信息\n
        email: Email对象"""
        if email is None:
            raise Exception(
                "Invalid email for relative email:{}".format(email))

        with self._emails_locker:
            self._emails[email.value] = email
            self._set_parentobj(email)

    def set_phone(self, phone):
        """向当前NetworkId根节点添加 邮箱信息\n
        phone: Phone 对象"""
        if phone is None:
            raise Exception(
                "Invalid phone for relative phone:{}".format(phone))

        with self._phones_locker:
            self._phones[phone.value] = phone
            self._set_parentobj(phone)

    def set_searchengine(self, searchengine: SearchEngine):
        """向当前NetworkId根节点添加 搜索引擎结果\n
            searchengine: SearchEngine 对象"""
        if not isinstance(searchengine, SearchEngine):
            return

        with self._searchengine_locker:
            self._searchengine[searchengine._keyword +
                               searchengine._url] = searchengine

    ###############################################
    # output dict
    def _get_outputdict_sub(self, rootdict: dict):
        if not isinstance(rootdict, dict):
            raise Exception("Invalid rootdict")
        self._outputdict_add_email(rootdict)
        self._outputdict_add_phone(rootdict)
        # 添加账号信息
        self._outputdict_add_profile(rootdict)
        self._outputdict_add_whoisr(rootdict)
        # 添加serachengine
        self._outputdict_add_searchengine(rootdict)

    def _outputdict_add_email(self, rootdict: dict):
        if len(self._emails) < 1:
            return
        if not rootdict.__contains__("emails"):
            rootdict["emails"] = []

        with self._emails_locker:
            for p in self._emails.values():
                edict: dict = {
                    "email": p.value,
                    "source": p.source,
                    "reason": p.reason
                }
                rootdict["emails"].append(edict)

    def _outputdict_add_phone(self, rootdict: dict):
        if len(self._phones) < 1:
            return
        if not rootdict.__contains__("phones"):
            rootdict["phones"] = []

        with self._phones_locker:
            for p in self._phones.values():
                pdict: dict = {
                    "phone": p.value,
                    "source": p.source,
                    "reason": p.reason
                }
                rootdict["phones"].append(pdict)

    def _outputdict_add_profile(self, rootdict: dict):
        """
        添加输出的profile
        :param rootdict:
        :return:
        """
        if len(self._networkid_profile) == 0:
            return
        if not rootdict.__contains__("networkids"):
            rootdict["networkids"] = []

        for pf in self._networkid_profile.values():
            pf: NetworkProfile = pf
            dpf = pf.get_outputdict()
            rootdict["networkids"].append(dpf)

    def _outputdict_add_whoisr(self, rootdict: dict):
        """
        这里增加输出whoisr
        :param rootdict:
        :return:
        """
        if len(self._whoisrs) == 0:
            return
        if not rootdict.__contains__("whoisr"):
            rootdict['whoisr'] = []

        for wf in self._whoisrs.values():
            wf: Whoisr = wf
            rootdict['whoisr'].append(wf.get_outputdict())

    def _outputdict_add_searchengine(self, rootdict: dict):
        """目前就域名、邮箱、电话有搜索引擎数据，后面多了就提出来封装下"""
        if len(self._searchengine) < 1:
            return
        if not rootdict.__contains__("searchengine"):
            rootdict["searchengine"] = []
        sglist = rootdict["searchengine"]

        for sg in self._searchengine.values():
            sg: SearchEngine = sg
            sglist.append(sg.get_output_dict())
