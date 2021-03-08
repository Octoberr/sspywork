"""ripe"""

# -*- coding:utf-8 -*-

import json
import traceback

from proxymanagement.proxymngr import ProxyMngr
from .ipwhoisbase import IPWhoisBase
from ....clientdatafeedback.scoutdatafeedback import (IPWhoisData)


class Ripe(IPWhoisBase):
    """search ip-whois from arin.net"""

    def __init__(self):
        IPWhoisBase.__init__(self)
        self._api_host: str = "stat.ripe.net"

        self._api_ipwhois = "https://stat.ripe.net/data/whois/data.json?resource="
        # 目前 ripe 没找到查历史的
        self._api_ipwhois_history = "https://stat.ripe.net/data/whois/data.json?resource="

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

            jcontent = json.loads(html)
            res: IPWhoisData = self._parse_one_ipwhois(ip, jcontent, reason)
            self._logger.info("Got an IPWhois: ip={} handle={} name={}".format(
                ip, res._handle, res._netname))

        except Exception:
            self._logger.error("Get ipwhois error: ip:{}, error: {}".format(
                ip, traceback.format_exc()))
        return res
