"""object ip"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.helpers import helper_time

from datacontract.iscoutdataset.iscouttask import EObjectType, IscoutTask

from .geoinfo import GeoInfo
from .ipwhois_data import IPWhoisData, IPWhoisEntityData
from .portinfo import PortInfo
from .rangechost import RangeCHost
from .scoutfeedbackbase import ScoutFeedBackBase
from .sidesite import SideSite


class IP(ScoutFeedBackBase):
    """scout object IP"""

    def __init__(
            self,
            task: IscoutTask,
            level: int,
            ip: str,
    ):
        ScoutFeedBackBase.__init__(self, task, level, EObjectType.Ip, ip,
                                   'iscout_ip')
        # 暂时不查错
        # try:
        #     IPy.IP(ip)
        # except Exception:
        #     return

        # current fields
        # 组织
        self.org = None
        # 运行商
        self.isp = None
        # 反动网站需求，新镇hostnames，用于保存当前端口的hostnames，这个字段不需要加，by judy 2020/06/19
        self.logtime: str = helper_time.get_time_sec_tz()

        # subitems

        self._bind_domain_histories: dict = {}
        self._bind_domain_histories_locker = threading.RLock()

        self._geoinfo: GeoInfo = None

        self._ipwhoises: dict = {}
        self._ipwhoises_locker = threading.RLock()

        self._portinfos: dict = {}
        self._portinfos_locker = threading.RLock()

        # ip反查domain
        self._ip_reverse: list = []
        self._ip_reverse_locker = threading.RLock()

        # C段探测
        self._rangec: dict = {}
        self._rangec_locker = threading.RLock()

        self._url: dict = {}
        self._url_locker = threading.RLock()

        self._side_sites: dict = {}
        self._side_sites_locker = threading.RLock()

    def _subitem_count(self) -> int:
        """子类实现 返回当前根节点的 子数据 总条数"""
        res = 0
        with self._bind_domain_histories_locker:
            res += len(self._bind_domain_histories)
        if isinstance(self._geoinfo, GeoInfo):
            res += 1
        with self._ipwhoises_locker:
            res += len(self._ipwhoises)
        with self._portinfos_locker:
            # res += len(self._portinfos)
            # 这个数据太大了，特殊计算长度
            for p in self._portinfos.values():
                res += len(p)
        with self._ip_reverse_locker:
            res += len(self._ip_reverse)
        with self._rangec_locker:
            res += len(self._rangec)
        with self._url_locker:
            res += len(self._url)
        with self._side_sites_locker:
            res += len(self._side_sites)
        return res

    # set items ###############################################
    def set_bind_domain_history(self, domain):
        """向当前IP根节点添加 历史绑定域名信息。\n
        domain: scoutdata.Domain 对象"""
        if domain is None:
            return

        with self._bind_domain_histories_locker:
            self._bind_domain_histories[domain.value] = domain
            self._set_parentobj(domain)

    def set_geolocation(self, geo: GeoInfo):
        """向当前IP根节点添加 归属地信息。\n
        geo: scoutdata.GeoInfo 对象"""
        if not isinstance(geo, GeoInfo):
            return
        self._geoinfo = geo

    def set_ipwhois(self, iw: IPWhoisData):
        """向当前IP根节点添加 归属地信息。\n
        iw: IPWhoisData 对象"""
        if not isinstance(iw, IPWhoisData):
            return
        key = iw._handle + iw._md5
        if self._ipwhoises.__contains__(key):
            return
        with self._ipwhoises_locker:
            if self._ipwhoises.__contains__(key):
                return
            self._ipwhoises[key] = iw

    def set_portinfo(self, portinfo: PortInfo):
        """向当前IP根节点添加 端口名信息\n
        portinfo: PortInfo 对象"""
        # 避免多线程同时添加时造成重复，需加锁
        if not isinstance(portinfo, PortInfo):
            return
        with self._portinfos_locker:
            self._portinfos[portinfo._port] = portinfo
            self._set_parentobj(portinfo)

    def set_ipreverse(self, reverse_domain: str):
        """
        向当前根节点添加ip反查到的域名
        :param reverse_domain:
        :return:
        """
        with self._ip_reverse_locker:
            self._ip_reverse.append({'domain': reverse_domain})

    def set_rangec(self, *hosts):
        """设置 C段探测到的存活主机"""
        if len(hosts) < 1:
            return
        with self._rangec_locker:
            for host in hosts:
                if not isinstance(host, RangeCHost):
                    continue
                # host: RangeCHost = host
                old: RangeCHost = self._rangec.get(host._ip)
                if old is None:
                    self._rangec[host._ip] = host
                else:
                    self._rangec[host._ip] = old.merge(host)

    def set_url(self, url):
        """向当前域名根节点添加 URL结果\n
        url: URL 对象"""
        if url is None:
            return

        with self._url_locker:
            self._url[url.value] = url

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

    # output dict ###############################################
    def _get_outputdict_sub(self, rootdict: dict):
        if not isinstance(rootdict, dict):
            raise Exception("Invalid rootdict")

        if self.org is not None:
            rootdict['org'] = self.org
        if self.isp is not None:
            rootdict['isp'] = self.isp

        # bind domain history
        self._outputdict_add_bind_domain_histories(rootdict)
        # geoinfo
        self._outputdict_add_geolocation(rootdict)
        # service providers
        self._outputdict_add_ipwhois(rootdict)
        # port service
        self._outputdict_add_port_service(rootdict)
        # reverse_domain
        self._outputdict_add_ip_reverse(rootdict)
        # range c detect
        self._outputdict_add_rangec(rootdict)
        # url
        self._outputdict_add_url(rootdict)
        # side site
        self._outputdict_add_sidesite(rootdict)

    def _outputdict_add_bind_domain_histories(self, rootdict: dict):
        if len(self._bind_domain_histories) < 1:
            return
        if not rootdict.__contains__("domainlog"):
            rootdict["domainlog"] = []

        for dl in self._bind_domain_histories.values():
            rootdict["domainlog"].append({
                "domain": dl.value,
                "logtime": dl.logtime,
            })

    def _outputdict_add_geolocation(self, rootdict: dict):
        if not isinstance(self._geoinfo, GeoInfo):
            return

        geodict: dict = self._geoinfo.get_outputdict()
        if not isinstance(geodict, dict) or len(geodict) < 1:
            return

        rootdict["geoinfo"] = geodict

    def _outputdict_add_ipwhois(self, rootdict: dict):
        if len(self._ipwhoises) < 1:
            return

        rootdict['ipwhois'] = []
        for iw in self._ipwhoises.values():
            iw: IPWhoisData = iw
            rootdict['ipwhois'].append(iw.get_outputdict())

    def _outputdict_add_port_service(self, rootdict: dict):
        if self._portinfos is None or len(self._portinfos) < 1:
            return
        if not rootdict.__contains__("portinfo"):
            rootdict["portinfo"] = []

        for pinfo in self._portinfos.values():
            if not isinstance(pinfo, PortInfo):
                continue
            pinfodict: dict = pinfo.get_outputdict()
            if not isinstance(pinfodict, dict) or len(pinfodict) < 1:
                continue
            rootdict["portinfo"].append(pinfodict)

    def _outputdict_add_ip_reverse(self, rootdict: dict):
        if len(self._ip_reverse) == 0:
            return
        rootdict['domains'] = self._ip_reverse

    def _outputdict_add_rangec(self, rootdict: dict):
        if len(self._rangec) < 1:
            return
        if not rootdict.__contains__('rangec'):
            rootdict['rangec'] = []

        for host in self._rangec.values():
            host: RangeCHost = host
            rootdict['rangec'].append(host.get_outputdict())

    def _outputdict_add_url(self, rootdict: dict):
        """"""
        if len(self._url) < 1:
            return
        if not rootdict.__contains__("urls"):
            rootdict['urls'] = []
        with self._url_locker:
            for u in self._url.values():
                rootdict['urls'].append({'url': u.value})

    def _outputdict_add_sidesite(self, rootdict: dict):
        if len(self._side_sites) < 1:
            return
        if not rootdict.__contains__("sidesites"):
            rootdict["sidesites"] = []

        for ssdata in self._side_sites.values():
            rootdict['sidesites'].append(ssdata.get_sidesite_output_dict())
