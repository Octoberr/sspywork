"""proxy spiders"""

# -*- coding:utf-8 -*-

import re
import time
import traceback

from commonbaby.countrycodes import ALL_COUNTRIES, CountryCode
from commonbaby.httpaccess import HttpAccess
from commonbaby.mslog import MsLogger, MsLogLevel, MsLogLevels, MsLogManager
from commonbaby.proxy import (EProxyAnonymity, EProxyType, ProxyItem,
                              ProxySetting, ProxySpiderbase)
from lxml import etree


class WWW89IP(ProxySpiderbase):
    """www.goubanjia.com"""

    def __init__(self):
        ProxySpiderbase.__init__(self, False)

        self._logger: MsLogger = MsLogManager.get_logger(
            self.__class__.__name__)

        self._reproxy = re.compile(r'([\d.]+?):(\d+)<br>', re.S)
        # 慢点，1秒一次请求
        self._ha: HttpAccess = HttpAccess(interval=1)
        self._ha.getstring(
            "http://www.89ip.cn",
            headers='''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Accept-Encoding: gzip, deflate
            Accept-Language: en,zh-CN;q=0.9,zh;q=0.8
            Cache-Control: no-cache
            Connection: keep-alive
            Host: www.89ip.cn
            Pragma: no-cache
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'''
        )

    def _get_proxy_sub(
            self,
            setting: ProxySetting,
    ) -> iter:
        """
        proxysetting: 指定代理要抓取的代理IP的相关参数配置\n
        return ProxyItem\n
        返回 ProxyItem"""
        try:
            for item in self._get_proxy_free(setting):
                if not isinstance(item, ProxyItem):
                    continue
                yield item

            for item in self._get_proxy_paid(setting):
                if not isinstance(item, ProxyItem):
                    continue
                yield item

        except Exception:
            self._logger.error("Get proxyitem error: {}".format(
                traceback.format_exc()))

    def _get_proxy_free(self, setting: ProxySetting) -> iter:
        """free proxies"""
        try:
            # http://www.89ip.cn/tqdl.html?api=1&num=9999&port=&address=&isp=
            url = 'http://www.89ip.cn/tqdl.html?api=1&num=30&port=&address=&isp='
            html = self._ha.getstring(
                url,
                headers='''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Accept-Encoding: gzip, deflate
            Accept-Language: en,zh-CN;q=0.9,zh;q=0.8
            Cache-Control: no-cache
            Connection: keep-alive
            Host: www.89ip.cn
            Pragma: no-cache
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'''
            )

            ms = self._reproxy.finditer(html)
            for m in ms:
                try:
                    if m is None:
                        continue

                    ip = m.group(1)
                    port = m.group(2)
                    if not port.isnumeric():
                        continue

                    if not setting.compare(port=port):
                        continue

                    proxyitem: ProxyItem = ProxyItem(
                        ip,
                        int(port),
                        proxy_type=EProxyType.HTTP,
                        is_ssl=False,
                        countrycode='CN',  #这个网站拿的都是中国的
                    )

                    yield proxyitem

                except Exception as ex:
                    self._logger.error(
                        "Parse one Proxy IP error: {}".format(ex))

        except Exception:
            self._logger.error("Get proxyitem error: {}".format(
                traceback.format_exc()))

    def _get_proxy_paid(self, setting: ProxySetting) -> iter:
        """free proxies"""
        try:
            yield None
        except Exception:
            self._logger.error("Get proxyitem error: {}".format(
                traceback.format_exc()))
