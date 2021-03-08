"""object email"""

# -*- coding:utf-8 -*-

import threading

from datacontract.iscoutdataset.iscouttask import EObjectType, IscoutTask

from .mailserver import MailServer
from .networkid import NetworkId
from .scoutfeedbackbase import ScoutFeedBackBase
from .searchengine import SearchEngine
from .whoisr import Whoisr
from .phone import Phone


class Email(ScoutFeedBackBase):
    """scout object email"""

    def __init__(self, task: IscoutTask, level: int, email: str):
        ScoutFeedBackBase.__init__(self, task, level, EObjectType.EMail, email, 'iscout_email')

        # TODO:check email validation

        # subitems
        self.source: str = None
        self.reason: str = None

        self._email = email
        self._mailservers: dict = {}
        self._mailservers_locker = threading.RLock()

        self._whoisrs: dict = {}
        self._whoisrs_locker = threading.RLock()

        # self._relative_emails: dict = {}
        # self._relative_emails_locker = threading.RLock()

        self._networkid: dict = {}
        self._networkid_locker = threading.RLock()

        self._searchengine: dict = {}
        self._searchengine_locker = threading.RLock()

        self._phones: dict = {}
        self._phones_locker = threading.RLock()

    def _subitem_count(self) -> int:
        res = 0
        with self._mailservers_locker:
            res += len(self._mailservers)
        with self._whoisrs_locker:
            res += len(self._whoisrs)
        # with self._relative_emails_locker:
        #     res += len(self._relative_emails)
        with self._networkid_locker:
            res += len(self._networkid)
        with self._searchengine_locker:
            res += len(self._searchengine)
        with self._phones_locker:
            res += len(self._phones)

        return res

    # subitems ###############################################

    def set_mailserver(self, mailserver: MailServer):
        """向当前Email根节点添加 邮服地址\n
            emailserver: EmailServer对象"""
        if not isinstance(mailserver, MailServer):
            raise Exception(
                "Invalid MailServer for Email: {}".format(mailserver))
        with self._mailservers_locker:
            self._mailservers[mailserver._host] = mailserver
            self._set_parentobj(mailserver)

    def set_whoisr(self, whoisr: Whoisr):
        """向当前Email根节点设置 Whoisr对象"""
        if not isinstance(whoisr, Whoisr):
            return
        with self._whoisrs_locker:
            self._whoisrs[whoisr._domain] = whoisr

    # def set_relative_email(self, email):
    #     """向当前Email根节点添加 相关邮箱\n
    #     email: Email对象"""
    #     if not isinstance(email, Email):
    #         raise Exception("Invalid email ro relative email:{}".format(email))
    #
    #     with self._relative_emails_locker:
    #         self._relative_emails[email.value] = email
    #         self._set_parentobj(email)

    def set_networkid(self, networkid: NetworkId):
        """向当前Email根节点添加 网络Id\n
        networkid: NetworkId 对象"""
        if not isinstance(networkid, NetworkId):
            raise Exception("Invalid networkid for Email")
        if not isinstance(networkid.userid, str) or networkid.userid == "":
            raise Exception("Invalid networkid.userid for Email")
        if not isinstance(networkid.source, str) or networkid.source == "":
            raise Exception("Invalid networkid.source for Email")
        if not isinstance(networkid.reason, str) or networkid.reason == "":
            raise Exception("Invalid networkid.reason for Email")
        with self._networkid_locker:
            self._networkid[networkid.value] = networkid
            self._set_parentobj(networkid)

    def set_searchengine(self, searchengine: SearchEngine):
        """向当前域名根节点添加 搜索引擎结果\n
            searchengine: SearchEngine 对象"""
        if not isinstance(searchengine, SearchEngine):
            return

        with self._searchengine_locker:
            self._searchengine[searchengine._keyword +
                               searchengine._url] = searchengine

    def set_phone(self, phone: Phone):
        """
        向当前根节点添加phone
        :param phone:
        :return:
        """
        if not isinstance(phone, Phone):
            return
        with self._phones_locker:
            self._phones[phone.value] = phone

    # output dict ###############################################

    def _get_outputdict_sub(self, rootdict: dict):
        """outputsub"""
        if not isinstance(rootdict, dict):
            raise Exception("Invalid rootdict")

        # source和reason不用在这里输出
        # 因为如果source和reason有值，则说明
        # 当前Email是作为子节点的，子节点的输出
        # 是在其父节点里控制的
        # 其他类型同理

        # 输出其他字段
        # mailserver
        self._outputdict_add_email_server(rootdict)
        self._outputdict_add_whosr(rootdict)
        # self._outputdict_add_relativeemail(rootdict)
        self._outputdict_add_networkid(rootdict)
        self._outputdict_add_searchengine(rootdict)
        self._outputdict_add_phone(rootdict)

    def _outputdict_add_email_server(self, rootdict: dict):
        if len(self._mailservers) < 1:
            return
        if not rootdict.__contains__("mailserver"):
            rootdict["mailserver"] = []

        for ms in self._mailservers.values():
            ms: MailServer = ms
            msdict: dict = {}
            msdict["type"] = ms._servertype
            msdict["host"] = ms._host
            if len(ms._ips) > 0:
                msdict["ip"] = [{'addr': ip} for ip in ms._ips.keys()]
            rootdict["mailserver"].append(msdict)

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

    # def _outputdict_add_relativeemail(self, rootdict: dict):
    #     if len(self._relative_emails) < 1:
    #         return
    #     if not rootdict.__contains__("emails"):
    #         rootdict["emails"] = []
    #
    #     for em in self._relative_emails.values():
    #         em: Email = em
    #         rootdict["emails"].append({
    #             "email": em.value,
    #             "source": em._source,
    #             "reason": em._reason,
    #         })

    def _outputdict_add_networkid(self, rootdict: dict):
        if len(self._networkid) < 1:
            return
        if not rootdict.__contains__("networkids"):
            rootdict["networkids"] = []

        for ni in self._networkid.values():
            ni: NetworkId = ni
            nidict: dict = {}
            nidict["networkid"] = ni.value
            nidict["userid"] = ni.userid
            if isinstance(ni.url, str) and not ni.url == "":
                nidict["url"] = ni.url
            nidict["source"] = ni.source
            nidict["reason"] = ni.reason
            rootdict["networkids"].append(nidict)

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

    def _outputdict_add_phone(self, rootdict: dict):
        if len(self._phones) < 1:
            return
        if not rootdict.__contains__("phones"):
            rootdict["phones"] = []

        for phone in self._phones.values():
            rootdict["phones"].append({
                "phone": phone.value,
                "source": phone.source,
                "reason": phone.reason,
            })
