"""apnic"""

# -*- coding:utf-8 -*-

import json
import traceback

from proxymanagement.proxymngr import ProxyMngr
from .ipwhoisbase import IPWhoisBase
from ....clientdatafeedback.scoutdatafeedback import (IPWhoisData)


class Apnic(IPWhoisBase):
    """搜索目标IP地址的Whois信息"""

    def __init__(self):
        IPWhoisBase.__init__(self)
        self._api_host: str = "rdap.apnic.net"

        self._api_ipwhois_history = "https://rdap.apnic.net/history/ip/"
        self._api_ipwhois = "https://rdap.apnic.net/ip/"

    def get_ipwhois(self, ip: str, reason: str) -> IPWhoisData:
        """get ip whois"""
        res: IPWhoisData = None
        try:
            url = '{}{}'.format(self._api_ipwhois, ip)

            html = self._ha.getstring(url,
                                      headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Accept-Encoding: gzip, deflate
            Accept-Language: en-US,en;q=0.9,zh;q=0.8
            Cache-Control: no-cache
            Host: {}
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"""
                                      .format(self._api_host),
                                      proxies=ProxyMngr.get_static_proxy(),
                                      verify=False)

            if html is None or html == '':
                return res

            if html.__contains__('errorCode'):
                self._logger.info('Need ip proxy, url:{}'.format(url))
                return res

            jcontent = json.loads(html)
            res: IPWhoisData = self._parse_one_ipwhois(ip, jcontent, reason)
            self._logger.info("Got an IPWhois: ip={} handle={} name={}".format(
                ip, res._handle, res._netname))

        except Exception:
            self._logger.debug(
                "Get ipwhois history error: ip:{}, error: {}".format(
                    ip, traceback.format_exc()))
        return res

    def get_ipwhois_history(self, ip: str, reason: str) -> iter:
        """get ip whois"""
        try:

            url = '{}{}'.format(self._api_ipwhois_history, ip)

            html = self._ha.getstring(url,
                                      headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Accept-Encoding: gzip, deflate
            Accept-Language: en-US,en;q=0.9,zh;q=0.8
            Cache-Control: no-cache
            Host: {}
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"""
                                      .format(self._api_host),
                                      proxies=ProxyMngr.get_static_proxy(),
                                      verify=False)

            if html is None or html == '':
                return

            for iw in self._parse_ipwhois_history(ip, html, reason):
                if not isinstance(iw, IPWhoisData):
                    continue
                self._logger.info(
                    "Got an IPWhois: ip={} handle={} name={}".format(
                        ip, iw._handle, iw._netname))
                yield iw

        except Exception:
            self._logger.debug(
                "Get ipwhois history error: ip:{}, error: {}".format(
                    ip, traceback.format_exc()))
