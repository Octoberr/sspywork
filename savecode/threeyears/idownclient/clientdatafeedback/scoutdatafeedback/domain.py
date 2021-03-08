"""object domain"""

# -*- coding:utf-8 -*-

import json
import threading

from commonbaby.helpers import helper_time

from datacontract.iscoutdataset.iscouttask import EObjectType, IscoutTask
from .mailserver import MailServer
from .portinfo import PortInfo
from .scoutfeedbackbase import ScoutFeedBackBase
from .searchengine import SearchEngine
from .sidesite import SideSite
from .url import URL
from .whois import Whois


class Domain(ScoutFeedBackBase):
    """scout object Domain"""

    def __init__(self, task: IscoutTask, level: int, domain: str):
        ScoutFeedBackBase.__init__(self, task, level, EObjectType.Domain,
                                   domain, 'iscout_domain')

        # if not helper_domain.is_valid_domain(domain):
        #     raise Exception("Invalid domain value")

        # current fields
        self.logtime: str = helper_time.get_time_sec_tz()

        # subitems
        self._subdomains: dict = {}
        self._subdomains_locker = threading.RLock()

        self._iplogs: dict = {}
        self._iplogs_locker = threading.RLock()

        self._whois: dict = {}
        self._whois_locker = threading.RLock()

        self._emails: dict = {}
        self._emails_locker = threading.RLock()

        self._phones: dict = {}
        self._phones_locker = threading.RLock()

        self._searchengine: dict = {}
        self._searchengine_locker = threading.RLock()

        self._url: dict = {}
        self._url_locker = threading.RLock()

        self._portinfos: dict = {}
        self._portinfo_locker = threading.RLock()

        self._realip: dict = {}
        self._realip_locker = threading.RLock()

        self._side_sites: dict = {}
        self._side_sites_locker = threading.RLock()

        self._wafs: dict = {}
        self._wafs_locker = threading.RLock()

        self._mailservers: dict = {}
        self._mailservers_locker = threading.RLock()

    def _subitem_count(self) -> int:
        res = 0
        with self._subdomains_locker:
            res += len(self._subdomains)
        with self._iplogs_locker:
            res += len(self._iplogs)
        with self._whois_locker:
            res += len(self._whois)
        with self._emails_locker:
            res += len(self._emails)
        with self._phones_locker:
            res += len(self._phones)
        with self._searchengine_locker:
            res += len(self._searchengine)
        with self._url_locker:
            res += len(self._url)
        with self._portinfo_locker:
            res += len(self._portinfos)
        with self._realip_locker:
            res += len(self._realip)
        with self._side_sites_locker:
            res += len(self._side_sites)
        with self._wafs_locker:
            res += len(self._wafs)
        with self._mailservers_locker:
            res += len(self._mailservers)
        return res

    # set items #######################################################
    def set_subdomain(self, subdomain):
        """向当前域名根节点添加 子域名\n
            domain: Domain对象"""
        if not isinstance(subdomain, Domain):
            return

        # 避免多线程同时添加时造成重复，需加锁
        with self._subdomains_locker:
            self._subdomains[subdomain.value] = subdomain
            self._set_parentobj(subdomain)

    def set_iplog(self, ip):
        """向当前域名根节点添加 历史解析IP记录\n
            ip: IP对象"""
        with self._iplogs_locker:
            self._iplogs[ip.value] = ip
            self._set_parentobj(ip)

    def set_whois(self, whois: Whois):
        """赋值当前域名根节点的 whois信息，覆盖更新原值\n
            whois: Whois对象"""
        if not isinstance(whois, Whois):
            return

        key = json.dumps(whois.get_whois_outputdict())  # 去重条件(直接字典的全部内容,后续视情况再改!)
        with self._whois_locker:
            if self._whois.__contains__(key):
                return
            self._whois[key] = whois

    def set_email(self, email):
        """向当前域名根节点添加 邮箱地址\n
            email: Email对象"""
        with self._emails_locker:
            self._emails[email.value] = email
            self._set_parentobj(email)

    def set_phone(self, phone):
        """向当前域名根节点添加 电话号码\n
            phone: Phone 对象"""
        with self._phones_locker:
            self._phones[phone.value] = phone
            self._set_parentobj(phone)

    def set_searchengine(self, searchengine: SearchEngine):
        """向当前域名根节点添加 搜索引擎结果\n
            searchengine: SearchEngine 对象"""
        if not isinstance(searchengine, SearchEngine):
            return

        with self._searchengine_locker:
            self._searchengine[searchengine._keyword +
                               searchengine._url] = searchengine

    def set_url(self, url: URL):
        """向当前域名根节点添加 URL结果\n
        url: URL 对象"""
        if not isinstance(url, URL):
            return

        with self._url_locker:
            self._url[url.value] = url

    def set_portinfo(self, portinfo: PortInfo):
        """向当前域名根节点添加 PortInfo端口服务信息\n
        portinfo: PortInfo 对象"""
        if not isinstance(portinfo, PortInfo):
            return

        with self._portinfo_locker:
            self._portinfos[portinfo._port] = portinfo

    def set_realip(self, realip: str):
        """向当前域名根节点添加 Realip真实ip信息
        realip: Realip 对象"""
        if not isinstance(realip, str):
            return

        with self._realip_locker:
            if self._realip.__contains__(realip):
                return
            self._realip[realip] = None

    def set_side_site(self, ssite: SideSite):
        """
        向当前域名对象中设置site
        :param ssite:
        :return:
        """
        if not isinstance(ssite, SideSite):
            return
        with self._side_sites_locker:
            self._side_sites[ssite.host + ssite.ip + str(ssite.port)] = ssite  # 1204 add port  --tms

    def set_waf(self, waf: str):
        """向当前域名对象中设置waf字段"""
        if not isinstance(waf, str):
            return

        with self._wafs_locker:
            if self._wafs.__contains__(waf):
                return
            self._wafs[waf] = None

    def set_mailserver(self, mailserver: MailServer):
        """向当前Email根节点添加 邮服地址\n
            emailserver: EmailServer对象"""
        if not isinstance(mailserver, MailServer):
            raise Exception(
                "Invalid MailServer for Email: {}".format(mailserver))
        with self._mailservers_locker:
            self._mailservers[mailserver._host] = mailserver
            # self._set_parentobj(mailserver)

    # output #######################################################
    def _get_outputdict_sub(self, rootdict: dict):
        if not isinstance(rootdict, dict):
            raise Exception("Invalid rootdict")

        # 添加子域名节点
        self._outputdict_add_subdomain(rootdict)
        # 添加域名历史解析ip记录
        self._outputdict_add_iplog(rootdict)
        # 添加whois记录
        self._outputdict_add_whois(rootdict)
        # 添加邮箱节点
        self._outputdict_add_email(rootdict)
        # 添加电话节点
        self._outputdict_add_phone(rootdict)
        # searchengine
        self._outputdict_add_searchengine(rootdict)
        # url
        self._outputdict_add_url(rootdict)
        # portinfo
        self._outputdict_add_portinfo(rootdict)
        # 添加real_ip节点
        self._outputdict_add_realip(rootdict)
        # 添加side site 节点
        self._outputdict_add_sidesite(rootdict)
        # 添加waf节点
        self._outputdict_add_waf(rootdict)
        # mailserver
        self._outputdict_add_email_server(rootdict)

    def _outputdict_add_subdomain(self, rootdict: dict):
        if len(self._subdomains) < 1:
            return
        if not rootdict.__contains__("subdomain"):
            rootdict["subdomain"] = []

        for subdomain in self._subdomains.keys():
            # sd = {}
            # sd['name'] = subdomain
            rootdict['subdomain'].append({'name': subdomain})

    def _outputdict_add_iplog(self, rootdict: dict):
        if len(self._iplogs) < 1:
            return
        if not rootdict.__contains__("iplog"):
            rootdict["iplog"] = []

        for ip in self._iplogs.values():
            rootdict["iplog"].append({"ip": ip.value, "logtime": ip.logtime})

    def _outputdict_add_whois(self, rootdict: dict):
        if not isinstance(self._whois, dict) or len(self._whois) < 1:
            return
        if not rootdict.__contains__("whois"):
            rootdict["whois"] = []

        with self._whois_locker:
            for whois in self._whois.values():
                wdict: dict = whois.get_whois_outputdict()
                if not isinstance(wdict, dict):
                    continue
                rootdict["whois"].append(wdict)

    def _outputdict_add_email(self, rootdict: dict):
        if len(self._emails) < 1:
            return
        if not rootdict.__contains__("emails"):
            rootdict["emails"] = []

        for email in self._emails.values():
            rootdict["emails"].append({
                "email": email.value,
                "source": email.source,
                "reason": email.reason,
            })

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

    def _outputdict_add_url(self, rootdict: dict):
        """"""
        if len(self._url) < 1:
            return
        if not rootdict.__contains__("urls"):
            rootdict['urls'] = []
        with self._url_locker:
            for u in self._url.values():
                u: URL = u
                rootdict['urls'].append({'url': u.value})

    def _outputdict_add_portinfo(self, rootdict: dict):
        """portinfo"""
        if len(self._portinfos) < 1:
            return
        if not rootdict.__contains__("portinfo"):
            rootdict["portinfo"] = []

        for portinfo in self._portinfos.values():
            if not isinstance(portinfo, PortInfo):
                continue
            # portinfo: PortInfo = portinfo
            portdictone: dict = portinfo.get_outputdict()
            if not isinstance(portdictone, dict) or len(portdictone) < 1:
                continue
            rootdict["portinfo"].append(portdictone)

    def _outputdict_add_realip(self, rootdict: dict):
        """real_ip"""
        if len(self._realip) < 1:
            return
        if not rootdict.__contains__("realip"):
            rootdict["realip"] = []

        with self._realip_locker:
            for rp in self._realip.keys():
                rootdict["realip"].append({"ip": rp})

    def _outputdict_add_sidesite(self, rootdict: dict):
        if len(self._side_sites) < 1:
            return
        if not rootdict.__contains__("sidesites"):
            rootdict["sidesites"] = []

        for ssdata in self._side_sites.values():
            rootdict['sidesites'].append(ssdata.get_sidesite_output_dict())

    def _outputdict_add_waf(self, rootdict: dict):
        if len(self._wafs) < 1:
            return
        if not rootdict.__contains__("waf"):
            rootdict["waf"] = {}

        # 暂时只取第一个，后面测试下是否有网站能探测到2个或以上的再改标准
        for waf in self._wafs.keys():
            rootdict["waf"]["name"] = waf
            break

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
