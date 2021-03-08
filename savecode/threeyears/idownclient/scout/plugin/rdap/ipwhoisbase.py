"""ip whois (history) search"""

# -*- coding:utf-8 -*-

import json
import traceback

import IPy
from commonbaby.helpers import helper_crypto
from commonbaby.httpaccess import HttpAccess

from ....clientdatafeedback.scoutdatafeedback import (GeoInfo, IPWhoisData,
                                                      IPWhoisEntityData)
from ..dbip import DbipMmdb
from ..scoutplugbase import ScoutPlugBase


class IPWhoisBase(ScoutPlugBase):
    """搜索目标IP地址的Whois（历史）信息"""

    # 就尼玛离谱，哪有人这样写的 2020/06/23
    # _dbip = DbipMmdb()
    # 就离谱，2020/06/23

    def __init__(self):
        ScoutPlugBase.__init__(self)
        self._dbip = DbipMmdb()
        self._rdap_apis = {
            # arin 加拿大、美国和一些加勒比海岛屿
            "arin": "https://rdap.arin.net/registry/ip/",
            # apnic 亚洲/太平洋地区
            "apnic": "https://rdap.apnic.net/history/ip/",
            # afrinic 非洲地区
            "afrinic": "https://rdap.afrinic.net/rdap/ip/",
            # ripe 欧洲、中东和中亚
            "ripe":
                "https://stat.ripe.net/data/whois/data.json?resource=192.0.20/23",
        }
        self._ha: HttpAccess = HttpAccess()

    def _parse_ipwhois_history(self, ip: str, html: str, reason) -> iter:
        """parse ipwhois history, yield return IPWhoisData"""
        try:
            if not isinstance(html, str) or html == "":
                return

            jwhois: dict = json.loads(html)

            if jwhois is None:
                return

            if not jwhois.__contains__("records"):
                return

            for jw in jwhois["records"]:
                iw = self._parse_one_ipwhois_history(ip, jw, reason)
                if iw is None:
                    continue
                yield iw

        except Exception:
            self._logger.error("Parse ipwhois error: ip:{}, error: {}".format(
                ip, traceback.format_exc()))

    def _parse_one_ipwhois_history(self, ip: str, jw: dict,
                                   reason) -> IPWhoisData:
        """parse one ipwhois history"""
        res: IPWhoisData = None
        try:
            if not isinstance(jw, dict):
                return res

            # required fields
            applicableFrom = jw.get('applicableFrom')
            applicableUntil = jw.get('applicableUntil')

            jcontent: dict = jw.get("content")
            if jcontent is None:
                self._logger.error(
                    "Parse one ipwhois filed not found: content, ip:{}".format(
                        ip))
                return res

            res = self._parse_one_ipwhois(ip, jcontent, reason)
            if res is None: return res
            if res.applicable_from is None and not applicableFrom is None:
                res.applicable_from = applicableFrom
            if res.applicable_until is None and not applicableUntil is None:
                res.applicable_until = applicableUntil

        except Exception:
            self._logger.debug(
                "Parse one ipwhois error: ip:{}, error: {}".format(
                    ip, traceback.format_exc()))
        return res

    def _parse_one_ipwhois(self, ip: str, jcontent: dict,
                           reason) -> IPWhoisData:
        """parse one ipwhois, same as ipwhois history.content"""
        res: IPWhoisData = None
        try:
            if not isinstance(jcontent, dict):
                return res

            handle = jcontent.get("handle")
            ip_ver = jcontent.get("ipVersion")
            allocate_type = jcontent.get("type")
            netname = jcontent.get("name")
            country_code = jcontent.get("country")
            if country_code is None:
                # 整理因为修改了mmdb的数据库，所以会返回组织和运营商
                geo, org, isp = self._dbip.get_ip_mmdbinfo(1, ip)
                country_code = geo._country_code

            raw: str = json.dumps(jcontent)
            md5 = helper_crypto.get_md5_from_str(raw)

            # construct obj
            res = IPWhoisData(reason, md5, raw, handle, allocate_type, netname,
                              country_code, ip_ver)

            # last_modified
            jevents = jcontent.get("events")
            if not jevents is None and len(jevents) > 0:
                for je in jevents:
                    if je.__contains__("eventAction") and \
                            je.__contains__("eventDate"):
                        jea = je["eventAction"]
                        jval = je["eventDate"]
                        if jea == "last changed":
                            res.last_modified = jval
                        elif jea == "registration":
                            res.applicable_from = jval
                        else:
                            self._logger.warn(
                                "Unknown eventAction for ipwhois: ip={}, action={}, val={}"
                                    .format(ip, jea, jval))

            # remarks
            jremarks = jcontent.get("remarks")
            if not jremarks is None and len(jremarks) > 0:
                remarks = ''
                for jr in jremarks:
                    jdes = jr.get("description")
                    if jdes is None or len(jdes) < 1:
                        continue
                    for jd in jdes:
                        remarks += (jd + "\r\n")
                if not remarks is None and remarks != "":
                    res.remarks = remarks

            # cidrs
            jcidrs = jcontent.get("cidr0_cidrs")
            if not jcidrs is None and len(jcidrs) > 0:
                for jc in jcidrs:
                    k = None
                    if jc.__contains__("v4prefix"):
                        k = jc['v4prefix']
                    elif jc.__contains__("v6prefix"):
                        k = jc['v6prefix']
                    v = jc.get("length")
                    if v is None:
                        continue
                    res.set_cidrs("{}/{}".format(k, v))

            # entities
            jentity = jcontent.get("entities")
            if not jentity is None and len(jentity) > 0:
                for jen in jentity:
                    en = self._parse_entity(ip, jen)
                    if en is None:
                        continue
                    res.set_entity(en)

        except Exception:
            self._logger.debug(
                "Parse one ipwhois error: ip:{}, error: {}".format(
                    ip, traceback.format_exc()))
        return res

    def _parse_entity(self, ip: str, jentity: dict) -> IPWhoisEntityData:
        """parse ipwhois entity"""
        res: IPWhoisEntityData = None
        try:
            if not isinstance(jentity, dict):
                return res

            # handle
            handle = jentity.get("handle")
            if handle is None or handle == "":
                return res

            # constuct obj
            res: IPWhoisEntityData = IPWhoisEntityData(handle)

            # roles
            jroles: list = jentity.get("roles")
            if jroles is None or len(jroles) < 1:
                return res
            for r in jroles:
                res.set_role(r)

            # last_modified
            jevents = jentity.get("events")
            if not jevents is None and len(jevents) > 0:
                for je in jevents:
                    if je.__contains__("eventAction") and \
                            je["eventAction"] == "last changed" and \
                            je.__contains__("eventDate"):
                        res.last_modified = je["eventDate"]
                        break

            # vcardArray
            jvcards = jentity.get("vcardArray")
            if jvcards is None or jvcards == "":
                return res

            for jvs in jvcards:
                if not isinstance(jvs, list) or len(jvs) < 1:
                    continue
                for jv in jvs:
                    try:
                        if not isinstance(jv, list) or len(jv) < 1:
                            continue
                        if "fn" in jv:
                            res.name = jv[3]
                        elif "adr" in jv:
                            res.address = jv[1].get("label") + "; " + ''.join(
                                jv[3])
                        elif "email" in jv:
                            res.email = jv[3]
                        elif "tel" in jv:
                            res.phone = jv[3]
                    except Exception:
                        self._logger.error(
                            "Parse one ipwhois entity vcard error: ip:{}, error: {}"
                                .format(ip, traceback.format_exc()))

        except Exception:
            self._logger.error(
                "Parse one ipwhois entity error: ip:{}, error: {}".format(
                    ip, traceback.format_exc()))
        return res
