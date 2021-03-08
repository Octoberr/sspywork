"""proxy spiders"""

# -*- coding:utf-8 -*-

import time
from datetime import datetime
import pytz
import traceback

from commonbaby.countrycodes import ALL_COUNTRIES, CountryCode
from commonbaby.httpaccess import HttpAccess
from commonbaby.mslog import MsLogger, MsLogLevel, MsLogLevels, MsLogManager
from commonbaby.proxy import (EProxyAnonymity, EProxyType, ProxyItem,
                              ProxySetting, ProxySpiderbase)
from lxml import etree


class Goubanjia(ProxySpiderbase):
    """www.goubanjia.com"""

    def __init__(self):
        ProxySpiderbase.__init__(self, False)

        self._logger: MsLogger = MsLogManager.get_logger(
            self.__class__.__name__)
        # 慢点，1秒一次请求
        self._ha: HttpAccess = HttpAccess(interval=1)

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
            html = self._ha.getstring(
                "http://www.goubanjia.com",
                headers='''
                Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
                Accept-Encoding: gzip, deflate
                Accept-Language: en,zh-CN;q=0.9,zh;q=0.8
                Cache-Control: no-cache
                Host: www.goubanjia.com
                Pragma: no-cache
                Proxy-Connection: keep-alive
                Upgrade-Insecure-Requests: 1
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'''
            )
            if not isinstance(html, str) or html == "":
                return
            hdoc: etree._Element = etree.HTML(html, etree.HTMLParser())

            if hdoc is None:
                return

            # <table class="table table-hover">
            xtrs: list = hdoc.xpath(
                './/table[@class="table table-hover"]/tbody/tr')
            if xtrs is None or len(xtrs) < 1:
                return

            for xtr in xtrs:
                if xtr is None:
                    continue
                try:
                    xtds = xtr.xpath('./td')
                    if xtds is None or len(xtds) < 8:
                        continue

                    ip, port = self._parse_ip(xtds[0])
                    if not isinstance(ip, str) or ip == "" or not isinstance(
                            port, int) or port < 0 or port > 65535:
                        continue

                    anon: EProxyAnonymity = self._parse_anonymous(xtds[1])
                    ptype, isssl = self._parse_proxytype(xtds[2])
                    countrycode, location = self._parse_location(xtds[3])
                    isp: str = self._parse_isp(xtds[4])
                    respsec: float = self._parse_response_sec(xtds[5])
                    lastvf: float = self._parse_lastverifytime(xtds[6])

                    if not setting.compare(
                            port=port,
                            proxy_type=ptype,
                            is_ssl=isssl,
                            proxy_anonymous=anon,
                            countrycode=countrycode,
                            alive_sec=None,
                            iptype=1,
                            isp=isp,
                            location=location,
                            lastverifytime=lastvf,
                            response_sec=respsec,
                    ):
                        continue

                    proxyitem: ProxyItem = ProxyItem(
                        ip,
                        port,
                        ptype,
                        isssl,
                        anon,
                        countrycode,
                        None,
                        1,
                        isp,
                        location,
                        lastvf,
                        respsec,
                    )

                    yield proxyitem

                except Exception:
                    self._logger.error(
                        "Parse one Proxy IP error: {}".format(traceback.format_exc()))

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

    # #####################################################
    # Parse each
    def _parse_ip(self, xip: etree._Element) -> (str, int):
        """解析出 (IP,PORT) """
        if xip is None:
            return (None, None)

        items: list = xip.getchildren()
        # print(items)
        if items is None or len(items) < 1:
            return (None, None)

        txt: str = ''
        for item in items:
            if item is None:
                continue
            item: etree._Element = item
            if item.attrib.__contains__(
                    'style') and item.attrib['style'].replace(
                ' ', '') == 'display:none;':
                continue
            txt += ''.join(item.xpath('./text()'))
            if not item.tail is None:
                txt += item.tail

        txt: str = txt.strip()
        if not isinstance(txt, str) or not txt.__contains__(":"):
            return (None, None)

        tmp = txt.split(':')
        if tmp is None or len(tmp) != 2:
            return (None, None)

        ip = tmp[0].strip()
        port = int(tmp[1].strip())
        # print(ip, port)
        return (ip, port)

    def _parse_anonymous(self, xanony: etree._Element) -> EProxyAnonymity:
        """解析匿名程度"""
        if xanony is None:
            return EProxyAnonymity.Unknow

        items: list = xanony.xpath('.//text()')
        if items is None or len(items) < 1:
            return (None, None)

        txt: str = ''.join(items).strip()
        if not isinstance(txt, str) or txt == "":
            return EProxyAnonymity.Unknow

        if txt == "透明":
            return EProxyAnonymity.Transparent
        elif txt == "高匿":
            return EProxyAnonymity.Elite
        elif txt == "匿名":
            return EProxyAnonymity.Anonymous
        else:
            return EProxyAnonymity.Unknow

    def _parse_proxytype(self, xptype: etree._Element) -> (EProxyType, bool):
        """返回 (EProxyType,is_ssl)"""
        if xptype is None:
            return (None, None)

        items: list = xptype.xpath('.//text()')
        if items is None or len(items) < 1:
            return (None, None)

        txt: str = ''.join(items).strip()
        if not isinstance(txt, str) or txt == "":
            return (None, None)

        if txt == "http":
            return (EProxyType.HTTP, False)
        if txt == "https":
            return (EProxyType.HTTP, True)
        if txt.__contains__("socks"):
            return (EProxyType.Socks, True)
        else:
            return (EProxyType.Unknow, False)

    def _parse_location(self, xctry: etree._Element) -> (str, str):
        """返回 (2位国家码CountryCode,其他地理位置信息)，
        不知道则返回None"""
        if xctry is None:
            return (None, None)
        xas = xctry.xpath('./a')
        if xas is None or len(xas) < 1:
            return (None, None)

        # 国家码
        countrycode: str = None
        strctry: str = xas[0].text.strip()
        for ctcode in ALL_COUNTRIES.values():
            ctcode: CountryCode = ctcode
            if ctcode.country_names["CN"] == strctry:
                countrycode = ctcode.iso2
                break

        # 地理位置
        locations: list = []
        for xa in xas:
            locations.append(xa.text.strip())
        location = None

        if len(locations) > 0:
            location = ' '.join(locations)

        return (countrycode, location)

    def _parse_isp(self, xisp: etree._Element) -> str:
        """解析并返回运营商"""
        if xisp is None:
            return None

        items: list = xisp.xpath('.//text()')
        if items is None or len(items) < 1:
            return (None, None)

        txt: str = ''.join(items).strip()
        if not isinstance(txt, str) or txt == "":
            return None
        return txt

    def _parse_response_sec(self, xresp: etree._Element) -> float:
        """解析并返回响应速度（秒）"""
        if xresp is None:
            return None

        items: list = xresp.xpath('.//text()')
        if items is None or len(items) < 1:
            return (None, None)

        txt: str = ''.join(items).strip()
        if not isinstance(txt, str) or txt == "":
            return None

        respsec = None
        if txt.__contains__("秒"):
            respsec = float(txt.replace('秒', '').strip())

        return respsec

    def _parse_lastverifytime(self, xverify: etree._Element) -> float:
        """解析并返回最后验证时间"""
        if xverify is None:
            return None

        items: list = xverify.xpath('.//text()')
        if items is None or len(items) < 1:
            return (None, None)

        txt: str = ''.join(items).strip()
        if not isinstance(txt, str) or txt == "":
            return None

        lastvt: float = None
        if txt.__contains__("秒前"):
            tmp = float(txt.replace('秒', '').replace('前', '').strip())
            lastvt = datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() - tmp
        elif txt.__contains__('分钟前'):
            tmp = 60 * float(
                txt.replace('分', '').replace('钟', '').replace('前', '').strip())
            lastvt = datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() - tmp

        return lastvt
