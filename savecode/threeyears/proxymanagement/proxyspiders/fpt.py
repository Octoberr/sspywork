"""
国外
https代理池
用于访问google,twitter,ipwhois等http访问
"""
import re
import traceback

import requests
from commonbaby.httpaccess import HttpAccess
from commonbaby.mslog import MsLogger, MsLogManager
from commonbaby.proxy import (
    EProxyAnonymity,
    EProxyType,
    ProxyItem,
    ProxySetting,
    ProxySpiderbase,
)
from commonbaby.countrycodes import ALL_COUNTRIES


class FPT(ProxySpiderbase):
    def __init__(self):
        ProxySpiderbase.__init__(self, False)

        self._logger: MsLogger = MsLogManager.get_logger(self.__class__.__name__)

        self._reproxy = re.compile(r"([\d.]+?):(\d+)", re.S)

        # 用于验证HTTP代理的,http访问器;interval两个HTTP请求之间的间隔时间(秒)
        self._ha: HttpAccess = HttpAccess(interval=1)

    def _get_proxy_sub(self, setting: ProxySetting) -> iter:
        """
        proxysetting: 指定代理要抓取的代理IP的相关参数配置
        return ProxyItem: 返回 ProxyItem
        """
        for item in self.get_foreign_highanoymous_https1(setting):
            if not isinstance(item, ProxyItem):
                continue
            yield item

        for item2 in self.get_foreign_highanoymous_https2(setting):
            if not isinstance(item2, ProxyItem):
                continue
            yield item2

        for item3 in self.get_foreign_highanoymous_https3(setting):
            if not isinstance(item3, ProxyItem):
                continue
            yield item3

    def get_foreign_highanoymous_https1(self, setting: ProxySetting) -> iter:
        """foreign proxies"""
        try:
            num = 10
            if setting is not None and setting.count is not None:
                num = setting.count
            url = "https://api.proxyscrape.com/?request=displayproxies&proxytype=socks4&country=all"
            for p in self._get_proxy(
                url,
                setting,
            ):
                yield p

        except Exception:
            self._logger.error(
                "Get foreign1 proxies error: {}".format(traceback.format_exc())
            )

    def get_foreign_highanoymous_https2(self, setting: ProxySetting) -> iter:
        """foreign proxies"""
        try:
            num = 10
            if setting is not None and setting.count is not None:
                num = setting.count
            url = "https://www.proxyscan.io/download?type=socks4"
            for p in self._get_proxy(
                url,
                setting,
            ):
                yield p

        except Exception:
            self._logger.error(
                "Get foreign2 proxies error: {}".format(traceback.format_exc())
            )

    def get_foreign_highanoymous_https3(self, setting: ProxySetting) -> iter:
        """foreign proxies"""
        try:
            num = 10
            if setting is not None and setting.count is not None:
                num = setting.count
            url = "https://top-proxies.ru/free_proxy/fre_proxy_api.php"
            for p in self._get_proxy(
                url,
                setting,
            ):
                yield p

        except Exception:
            self._logger.error(
                "Get foreign2 proxies error: {}".format(traceback.format_exc())
            )

    def _get_proxy(self, apiurl: str, setting: ProxySetting) -> iter:
        """"""
        try:
            if apiurl is None or apiurl == "":
                self._logger.debug("Invalid apiurl for parsing proxy")
                return

            html = self._ha.getstring(apiurl, timeout=10)

            for fp in self._reproxy.finditer(html):
                try:
                    if fp is None:
                        continue
                    ip = fp.group(1)
                    port = fp.group(2)
                    if not port.isnumeric():
                        continue
                    # if not setting.compare(
                    #         port=port,
                    #         proxy_type=proxy_type,
                    #         proxy_anonymous=EProxyAnonymity.Elite,
                    #         is_ssl=is_ssl,
                    #         countrycode=countrycode,
                    # ):
                    #     continue

                    proxyitem: ProxyItem = ProxyItem(ip, int(port))

                    yield proxyitem

                except Exception as ex:
                    self._logger.error("Parse one Proxy IP error: {}".format(ex))

        except Exception as error:
            self._logger.trace("Connecting proxy server")
