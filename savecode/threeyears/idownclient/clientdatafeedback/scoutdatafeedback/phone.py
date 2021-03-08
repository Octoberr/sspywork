"""object phone"""

# -*- coding:utf-8 -*-
import threading

from datacontract.iscoutdataset.iscouttask import EObjectType, IscoutTask
# from .networkid import NetworkId
from .networkiddata import NetworkGroup, NetworkProfile
from .scoutfeedbackbase import ScoutFeedBackBase
from .searchengine import SearchEngine
from .whoisr import Whoisr


class Phone(ScoutFeedBackBase):
    """scout object IP"""

    def __init__(
            self,
            task: IscoutTask,
            level: int,
            phone: str,
    ):
        ScoutFeedBackBase.__init__(self,
                                   task,
                                   level,
                                   EObjectType.PhoneNum,
                                   phone,
                                   'iscout_phone')

        # current fields
        self.source: str = None  # 数据获取到的网站/源地址/出处
        self.reason: str = None  # 数据由来

        # subitems
        self._whoisrs: dict = {}
        self._whoisrs_locker = threading.RLock()

        # self._networkid: dict = {}
        # self._networkid_locker = threading.RLock()
        self._networkid_profile: dict = {}
        self._networkid_profile_locker = threading.RLock()

        self._searchengine: dict = {}
        self._searchengine_locker = threading.RLock()

        self._networkid_groups: dict = {}
        self._networkid_groups_locker = threading.RLock()

        self._emails: dict = {}
        self._emails_locker = threading.RLock()

    def _subitem_count(self) -> int:
        res = 0
        with self._whoisrs_locker:
            res += len(self._whoisrs)
        # with self._networkid_locker:
        #     res += len(self._networkid)
        with self._networkid_profile_locker:
            res += len(self._networkid_profile)
        with self._searchengine_locker:
            res += len(self._searchengine)
        with self._networkid_groups_locker:
            res += len(self._networkid_groups)
        with self._emails_locker:
            res += len(self._emails)
        return res

    # subitems ###############################################

    def set_whoisr(self, whoisr: Whoisr):
        """向当前Email根节点设置 Whoisr对象"""
        if not isinstance(whoisr, Whoisr):
            return
        with self._whoisrs_locker:
            self._whoisrs[whoisr._domain] = whoisr

    # def set_networkid(self, networkid: NetworkId):
    #     """向当前Email根节点添加 网络Id\n
    #     networkid: NetworkId 对象"""
    #     if not isinstance(networkid, NetworkId):
    #         raise Exception("Invalid networkid for Email")
    #     if not isinstance(networkid.userid, str) or networkid.userid == "":
    #         raise Exception("Invalid networkid.userid for Email")
    #     if not isinstance(networkid.source, str) or networkid.source == "":
    #         raise Exception("Invalid networkid.source for Email")
    #     if not isinstance(networkid.reason, str) or networkid.reason == "":
    #         raise Exception("Invalid networkid.reason for Email")
    #     with self._networkid_locker:
    #         self._networkid[networkid.value] = networkid
    #         self._set_parentobj(networkid)
    def set_networkid_profile(self, np: NetworkProfile):
        """向当前NetworkId根节点添加 网络id用户信息\n
        np: NetworIdkProfile 对象"""
        if not isinstance(np, NetworkProfile):
            raise Exception("Invalid NetworkIdProfile for NetworkId")
        with self._networkid_profile_locker:
            self._networkid_profile[np._source + np._userid] = np

    def set_searchengine(self, searchengine: SearchEngine):
        """向当前域名根节点添加 搜索引擎结果\n
            searchengine: SearchEngine 对象"""
        if not isinstance(searchengine, SearchEngine):
            return

        with self._searchengine_locker:
            self._searchengine[searchengine._keyword +
                               searchengine._url] = searchengine

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
            raise Exception("Invalid email for relative email:{}".format(email))
        with self._emails_locker:
            self._emails[email.value] = email

    # output dict ###############################################

    def _get_outputdict_sub(self, rootdict: dict):
        if not isinstance(rootdict, dict):
            raise Exception("Invalid rootdict")

        self._outputdict_add_whosr(rootdict)
        # self._outputdict_add_networkid(rootdict)
        self._outputdict_add_profile(rootdict)
        self._outputdict_add_searchengine(rootdict)
        self._outputdict_add_groups(rootdict)
        self._outputdict_add_email(rootdict)

    def _outputdict_add_whosr(self, rootdict: dict):
        if len(self._whoisrs) < 1:
            return
        if not rootdict.__contains__("whoisr"):
            rootdict["whoisr"] = []

        for wr in self._whoisrs.values():
            wr: Whoisr = wr
            wrdict: dict = {}
            wrdict["domain"] = wr._domain
            if isinstance(wr.registrant, str) and not wr.registrant == "":
                wrdict["registrant"] = wr.registrant
            if isinstance(wr.registrar, str) and not wr.registrar == "":
                wrdict["registrar"] = wr.registrar
            if isinstance(wr.registtime, str) and not wr.registtime == "":
                wrdict["registtime"] = wr.registtime
            if isinstance(wr.expiretime, str) and not wr.expiretime == "":
                wrdict["expiretime"] = wr.expiretime
            if len(wr._dns_servers) > 0:
                wrdict["dns"] = [d for d in wr._dns_servers.keys()]

            rootdict["whoisr"].append(wrdict)

    # def _outputdict_add_networkid(self, rootdict: dict):
    #     if len(self._networkid) < 1:
    #         return
    #     if not rootdict.__contains__("networkids"):
    #         rootdict["networkids"] = []
    #
    #     for ni in self._networkid.values():
    #         ni: NetworkId = ni
    #         nidict: dict = {}
    #         nidict["networkid"] = ni.value
    #         nidict["userid"] = ni.userid
    #         if isinstance(ni.url, str) and not ni.url == "":
    #             nidict["url"] = ni.url
    #         nidict["source"] = ni.source
    #         nidict["reason"] = ni.reason
    #         rootdict["networkids"].append(nidict)
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

    # 待增加networkid_group
    def _outputdict_add_groups(self, rootdict: dict):
        """
        添加输出的group
        :param rootdict:
        :return:
        """
        if len(self._networkid_groups) == 0:
            return
        if not rootdict.__contains__("groups"):
            rootdict["groups"] = []
        ginfo_list = rootdict['groups']
        for gf in self._networkid_groups.values():
            # gf: NetworkGroup = gf
            g_dict = gf.get_outputdict()
            ginfo_list.append(g_dict)

    # 新增email
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
