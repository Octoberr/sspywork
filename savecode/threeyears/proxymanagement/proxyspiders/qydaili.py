"""proxy spiders"""

# -*- coding:utf-8 -*-
import re
import traceback

import requests
from commonbaby.httpaccess import HttpAccess
from commonbaby.mslog import MsLogger, MsLogManager
from commonbaby.proxy import (EProxyAnonymity, EProxyType, ProxyItem, ProxySetting, ProxySpiderbase)
from commonbaby.countrycodes import ALL_COUNTRIES


class QiYunProxy(ProxySpiderbase):
    """www.qydaili.com"""

    def __init__(self):
        ProxySpiderbase.__init__(self, False)

        self._logger: MsLogger = MsLogManager.get_logger(self.__class__.__name__)

        self._reproxy = re.compile(r'"([\d.]+?):(\d+)"', re.S)

        # 用于验证HTTP代理的,http访问器;interval两个HTTP请求之间的间隔时间(秒)
        self._ha: HttpAccess = HttpAccess(interval=1)
        # 付费齐云代理的key
        self.key = 'dd0b192e8199af0b47faf005aac4483b1efff860'

    def _get_proxy_sub(self, setting: ProxySetting) -> iter:
        """
        proxysetting: 指定代理要抓取的代理IP的相关参数配置
        return ProxyItem: 返回 ProxyItem
        """
        try:
            # 国内-->
            if setting is None or setting.countrycode == 'CN':
                for item in self.get_internal_highanoymous_https(setting):
                    if not isinstance(item, ProxyItem):
                        continue
                    yield item
                for item in self.get_internal_highanoymous_http(setting):
                    if not isinstance(item, ProxyItem):
                        continue
                    yield item

            # 国外-->
            if setting is None or setting.countrycode != 'CN':
                for item in self.get_foreign_highanoymous_https(setting):
                    if not isinstance(item, ProxyItem):
                        continue
                    yield item
                for item in self.get_foreign_highanoymous_http(setting):
                    if not isinstance(item, ProxyItem):
                        continue
                    yield item

        except Exception:
            self._logger.error("Get proxyitem error: {}".format(traceback.format_exc()))

    # 国内+高匿+HTTPS的api
    def get_internal_highanoymous_https(self, setting: ProxySetting) -> iter:
        """internal proxies"""
        try:
            num = 10
            if setting is not None and setting.count is not None:
                num = setting.count
            url = "http://dev.qydailiip.com/api/?apikey={}&num={}&type=json&line=win&proxy_type=putong&sort=rand&model=all&protocol=https&address=&kill_address=&port=&kill_port=&today=true&abroad=1&isp=&anonymity=" \
                .format(self.key, num)
            for p in self._get_proxy(
                    url,
                    setting,
                    proxy_type=EProxyType.HTTP,
                    is_ssl=True,
                    countrycode='CN',  # 拿的国内的
            ):
                yield p

        except Exception:
            self._logger.error("Get internal proxies error: {}".format(traceback.format_exc()))

    # 国内+高匿+HTTP的api
    def get_internal_highanoymous_http(self, setting: ProxySetting) -> iter:
        """internal proxies"""
        try:
            num = 50
            if setting is not None and setting.count is not None:
                num = setting.count
            url = "http://dev.qydailiip.com/api/?apikey={}&num={}&type=json&line=win&proxy_type=putong&sort=rand&model=all&protocol=http&address=&kill_address=&port=&kill_port=&today=true&abroad=1&isp=&anonymity=2" \
                .format(self.key, num)
            for p in self._get_proxy(
                    url,
                    setting,
                    proxy_type=EProxyType.HTTP,
                    is_ssl=False,
                    countrycode='CN',  # 拿的国内的
            ):
                yield p

        except Exception:
            self._logger.error("Get internal proxies error: {}".format(traceback.format_exc()))

    # 国外+高匿+HTTPS的api
    def get_foreign_highanoymous_https(self, setting: ProxySetting) -> iter:
        """foreign proxies"""
        try:
            num = 10
            if setting is not None and setting.count is not None:
                num = setting.count
            url = "http://dev.qydailiip.com/api/?apikey={}&num={}&type=json&line=win&proxy_type=putong&sort=rand&model=all&protocol=https&address=&kill_address=&port=&kill_port=&today=true&abroad=2&isp=&anonymity=2" \
                .format(self.key, num)
            for p in self._get_proxy(
                    url,
                    setting,
                    proxy_type=EProxyType.HTTP,
                    is_ssl=True,
                    countrycode='US',  # 对我们而言,国外的代理,简单粗暴写死为美国
            ):
                # res = self.check_https(p.ip + ':' + str(p.port))
                # if not res:
                #     continue
                yield p

        except Exception:
            self._logger.error("Get foreign proxies error: {}".format(traceback.format_exc()))

    # 国外+高匿+HTTP的api
    def get_foreign_highanoymous_http(self, setting: ProxySetting) -> iter:
        """foreign proxies"""
        try:
            num = 50
            if setting is not None and setting.count is not None:
                num = setting.count
            url = "http://dev.qydailiip.com/api/?apikey={}&num={}&type=json&line=win&proxy_type=putong&sort=rand&model=all&protocol=http&address=&kill_address=&port=&kill_port=&today=true&abroad=2&isp=&anonymity=2" \
                .format(self.key, num)

            for p in self._get_proxy(
                    url,
                    setting,
                    proxy_type=EProxyType.HTTP,
                    is_ssl=False,
                    countrycode='US',  # 对我们而言,国外的代理,简单粗暴写死为美国
            ):
                # res = self.check_http(p.ip + ':' + str(p.port))
                # if not res:
                #     continue
                yield p

        except Exception:
            self._logger.error("Get foreign proxies error: {}".format(traceback.format_exc()))

    def _get_proxy(
            self,
            apiurl: str,
            setting: ProxySetting,
            proxy_type: EProxyType,
            is_ssl: bool,
            countrycode: str, ) -> iter:
        """"""
        try:
            if apiurl is None or apiurl == '':
                self._logger.debug("Invalid apiurl for parsing proxy")
                return
            if not isinstance(proxy_type, EProxyType):
                self._logger.debug("Invalid proxytype for parsing proxy")
                return
            if not isinstance(is_ssl, bool):
                self._logger.debug("Invalid is_ssl for parsing proxy")
                return
            if not isinstance(countrycode, str) or not ALL_COUNTRIES.__contains__(countrycode):
                self._logger.debug("Invalid countrycode for parsing proxy")
                return

            html = self._ha.getstring(apiurl,
                                      headers="""
                                      Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                                      Accept-Encoding: gzip, deflate
                                      Accept-Language: zh-CN,zh;q=0.9
                                      Connection: keep-alive
                                      Host: bet.energy67.top
                                      Upgrade-Insecure-Requests: 1
                                      User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36
                                      """,
                                      timeout=10,
                                      )

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

                    proxyitem: ProxyItem = ProxyItem(
                        ip,
                        int(port),
                        proxy_type=proxy_type,
                        is_ssl=is_ssl,
                        countrycode=countrycode,
                    )

                    yield proxyitem

                except Exception as ex:
                    self._logger.error("Parse one Proxy IP error: {}".format(ex))

        except Exception as error:
            self._logger.trace("Connecting proxy server")

    # def check_https(self, proxy):
    #     url = 'https://www.baidu.com/'
    #     try:
    #         html = requests.get(url, proxies={'https': f'https://{proxy}'}, timeout=3)
    #         if html.status_code == 200:
    #             return True
    #         else:
    #             return False
    #     except:
    #         return False
    #
    # def check_http(self, proxy):
    #     url = 'http://www.21cn.com/'
    #     try:
    #         html = requests.get(url, proxies={'http': f'http://{proxy}', 'https': f'https://{proxy}'}, timeout=10)
    #         if html.status_code == 200:
    #             return True
    #         else:
    #             return False
    #     except:
    #         return False
