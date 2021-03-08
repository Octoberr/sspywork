"""zgrab2 parser http"""

# -*- coding:utf-8 -*-

import json
import os
import re
import traceback

import OpenSSL
# from common.tools import sslparse
from commonbaby.helpers import helper_sslcert as sslparse
from commonbaby.helpers import helper_str
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask

from .....clientdatafeedback.scoutdatafeedback import (Certificate, CertIssuer,
                                                       CertSubject, PortInfo,
                                                       SiteInfo, SslCert)
from .zgrab2parserbase import Zgrab2ParserBase
from idownclient.scan.plugin.component.webalyzer import WebAlyzer


class Zgrab2ParserHttp(Zgrab2ParserBase):
    """zgrab2 parser"""

    # _logger: MsLogger = MsLogManager.get_logger("Zgrab2ParserHttp")

    _re_title = re.compile(r"<title>(.*?)</title>", re.S | re.M)
    # <meta content="17173,17173.com,17173游戏网,网络游戏" name="Keywords" />
    _re_meta = re.compile(r'<meta[^>]+?name="(keywords|description)"[^>]+?/>',
                          re.S | re.M | re.IGNORECASE)

    def __init__(self):
        Zgrab2ParserBase.__init__(self)
        self.ca = WebAlyzer('isouttask')
        # self._name = type(self).__name__

    def _parse_http(self, sj, portinfo: PortInfo) -> SiteInfo:
        """parse one json block and return a PortInfo, if failed retrn None"""
        res: SiteInfo = None
        try:
            if not sj.__contains__("data") or not sj["data"].__contains__(
                    "http"):
                return

            sjhttp = sj["data"]["http"]

            succ = sjhttp["status"]
            if succ != "success":
                return

            # ??? what ?
            protocol = sjhttp["protocol"]
            if protocol != "http":
                return
            if portinfo.service != protocol:
                portinfo.service = protocol
            if portinfo.ssl_flag:
                portinfo.service = 'https'

            host: str = None
            if sj.__contains__("ip"):
                host = sj["ip"]
            elif sj.__contains__("domain"):
                host = sj["domain"]
            else:
                return

            self._get_port_timestamp(sjhttp, portinfo)

            res = SiteInfo(host)
            # append ips from portinfo to current siteinfo
            # 将组件信息加入到site里面
            wapres = 0
            try:
                self._logger.info(f"Start scout zgrab2http wappalyzer: {host}")
                for com in self.ca.get_alyzer_res(level=1, url=host):
                    wapres += 1
                    res.set_components(com)
            except:
                self._logger.error(
                    f"Get scout zgrab2http components error,err:{traceback.format_exc()}")
            self._logger.info(f"Stop scout zgrab2http wappalyzer: {host} rescount:{wapres}")

            # append ips from portinfo to current siteinfo
            # should here use dnspy?
            res.set_ips(*[ip for ip in portinfo.ips])

            sjresult = sjhttp["result"]

            # location
            sjresp = sjresult["response"]
            if (sjresp.__contains__("request")
                    and sjresp["request"].__contains__("url")
                    and sjresp["request"]["url"].__contains__("path")):
                res.location = sjresp["request"]["url"]["path"]

            # redirects
            if sjhttp.__contains__("redirect_response_chain"):
                sjredirs = sjhttp["redirect_response_chain"]
                for sjredir in sjredirs:
                    scheme = sjredir["request"]["url"]["scheme"]
                    host = sjredir["request"]["url"]["host"]
                    path = sjredir["request"]["url"]["path"]
                    redir = "{}://{}{}".format(scheme, host, path)
                    res.set_redirect(redir)

            # httpdata request headers/joint
            reqheaders: str = ""
            protocolline = sjresp["protocol"]["name"]
            sjreq = sjresp["request"]
            method = sjreq["method"]
            reqheaders += "{} {}\n".format(method, protocolline)
            if sjreq.__contains__("host"):
                reqheaders += "host: {}\n".format(sjreq["host"])
            for k, values in sjreq["headers"].items():
                if k != "unknown":
                    for v in values:
                        reqheaders += "{}: {}\n".format(k, v)
                else:
                    for val in values:
                        k = val["key"]
                        for v in val:
                            reqheaders += "{}: {}\n".format(k, v)
            res.set_httpdata(reqheader=reqheaders)

            # httpdata request body/joint
            # http request body is None, due to "Method" is "GET"

            # httpdata response headers/joint
            respheaders: str = ""
            statusline = sjresp["status_line"]
            respheaders += "{} {}\n".format(protocolline, statusline)
            for k, values in sjresp["headers"].items():
                if k != "unknown":
                    for v in values:
                        respheaders += "{}: {}\n".format(k, v)
                else:
                    for val in values:
                        k = val["key"]
                        for v in val:
                            respheaders += "{}: {}\n".format(k, v)
            if sjresp.__contains__("transfer_encoding"):
                for v in sjresp["transfer_encoding"]:
                    respheaders += "transfer-encoding: {}\n".format(v)
            if sjresp.__contains__(
                    "content_length") and sjresp["content_length"] != -1:
                respheaders += "content-length: {}\n".format(
                    sjresp["content_length"])
            res.set_httpdata(respheader=respheaders)

            # httpdata response body
            respbody: str = None
            if sjresp.__contains__("body"):
                respbody = sjresp["body"]
                res.set_httpdata(respbody=respbody)

            # portinfo.banner/ reqheader+reqbody+respheader+respbody
            portinfo.banner += "{}\n\n{}\n\n{}\n\n{}".format(
                reqheaders.rstrip(), "", respheaders.rstrip(),
                respbody.rstrip())

            # title
            title: str = None
            if not respbody is None and respbody != "":
                m = Zgrab2ParserHttp._re_title.search(respbody)
                if not m is None:
                    title = m.group(1)
                    res.title = title

            # meta/this should be joint to json str
            meta: dict = {}
            if not respbody is None and respbody != "":
                # <meta content="17173,17173.com,17173游戏网,网络游戏" name="Keywords" />
                for m in Zgrab2ParserHttp._re_meta.finditer(respbody):
                    if not m is None:
                        k = m.group(1).lower()
                        succ, v = helper_str.substringif(
                            respbody[m.start():m.end()], 'content="', '"')
                        if succ:
                            meta[k] = v
                if len(meta) > 0:
                    meta = json.dumps(meta)
                    res.meta = meta

            # favicon/this requires extra http request
            # find out the url for favicon.ico
            # <link type="image/x-icon" rel="icon" href="//ue.17173cdn.com/images/lib/v1/favicon-hd.ico" />
            # <link type="image/x-icon" rel="shortcut icon" href="//ue.17173cdn.com/images/lib/v1/favicon.ico" />

            # web technologies recognize
            if not res is None:
                portinfo.set_siteinfo(res)

        except Exception:
            self._logger.error("Parse http json line error:{}".format(
                traceback.format_exc()))
