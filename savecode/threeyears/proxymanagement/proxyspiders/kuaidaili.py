"""proxy spiders"""

# -*- coding:utf-8 -*-
import time
import traceback

from commonbaby.countrycodes import ALL_COUNTRIES, CountryCode
from commonbaby.httpaccess import HttpAccess
from commonbaby.mslog import MsLogger, MsLogLevel, MsLogLevels, MsLogManager
from commonbaby.proxy import (EProxyAnonymity, EProxyType, ProxyItem,
                              ProxySetting, ProxySpiderbase)
from lxml import etree


class KuaiProxy(ProxySpiderbase):
    """www.kuaidaili.com"""

    def __init__(self):
        ProxySpiderbase.__init__(self, False)

        self._loggr: MsLogger = MsLogManager.get_logger(self.__class__.__name__)

        # 慢点，interval=1表示1秒/次请求
        self._ha: HttpAccess = HttpAccess(interval=1)

    def _get_proxy_sub(self, setting: ProxySetting, ) -> iter:
        """
        proxysetting: 指定代理要抓取的代理IP的相关参数配置
        return ProxyItem: 返回 ProxyItem
        """
        try:
            for item in self._get_proxy_free(setting):
                if not isinstance(item, ProxyItem):
                    continue
                yield item

        except Exception:
            self._loggr.error("Get proxyitem error: {}".format(traceback.format_exc()))

    def _get_proxy_free(self, setting: ProxySetting) -> iter:
        """free proxies"""
        try:
            url = 'https://www.kuaidaili.com/free/'
            html = self._ha.getstring(url, headers="""Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
        Accept-Encoding: gzip, deflate, br
        Accept-Language: zh-CN,zh;q=0.9
        Cache-Control: max-age=0
        Connection: keep-alive
        Host: www.kuaidaili.com
        Sec-Fetch-Mode: navigate
        Sec-Fetch-Site: none
        Sec-Fetch-User: ?1
        Upgrade-Insecure-Requests: 1
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36""")
            # print(html)
            if not isinstance(html, str) or html == '':
                return
            html_doc: etree._Element = etree.HTML(html, etree.HTMLParser())
            # print(html_doc)
            if html_doc is None:
                return

            # 定位标签: <table class="table table-bordered table-striped">
            xtrs: list = html_doc.xpath(".//table[@class='table table-bordered table-striped']/tbody/tr")
            if xtrs is None or len(xtrs) < 1:
                return

            # 遍历xtrs列表
            for xtr in xtrs:  # xtrs,当前页面全部15条行数据
                # print(xtr)
                if xtr is None:
                    continue
                try:
                    xtds = xtr.xpath('./td')  # 取1条行数据(包含各个字段项)
                    if xtds is None or len(xtds) < 7:
                        continue

                    # 各个字段如下:
                    # IP
                    ip = self._parse_ip(xtds[0])
                    if not isinstance(ip, str) or ip == "":
                        continue
                    # 端口
                    port = self._parse_port(xtds[1])
                    if not isinstance(port, int) or port == "" or not isinstance(port, int) or port < 0 or port > 65535:
                        continue
                    # 匿名度
                    anon: EProxyAnonymity = self._parse_anonymous(xtds[2])
                    # 类型
                    ptype, isssl = self._parse_proxytype(xtds[3])
                    # 位置(国家码)
                    countrycode, location = self._parse_location(xtds[4])
                    # 响应速度
                    respsec: float = self._parse_response_sec(xtds[5])
                    # 最后验证时间
                    lastvf = self._parse_lastverifytime(xtds[6])

                    if not setting.compare(
                            port=port, proxy_type=ptype, is_ssl=isssl, proxy_anonymous=anon, countrycode=countrycode,
                            alive_sec=None, iptype=1, isp=None, location=location, lastverifytime=lastvf,
                            response_sec=respsec, ):
                        continue

                    proxyitem: ProxyItem = ProxyItem(
                        ip, port, ptype, isssl, anon, countrycode, None, 1, None, location, lastvf, respsec, )

                    yield proxyitem

                except Exception:
                    self._loggr.error("Parse one Proxy ip error: {}".format(traceback.format_exc()))

        except Exception:
            self._loggr.error("Get proxyitem error: {}".format(traceback.format_exc()))

    ############################################################
    # Parse each
    def _parse_ip(self, xip):
        """解析ip"""
        if xip is None:
            return None

        ip = xip.text
        return ip

    def _parse_port(self, xport):
        """解析port"""
        port = -1
        try:
            if xport is None:
                return None
            port = int(xport.text)

        except Exception:
            pass

        return port

    # 解析匿名程度
    def _parse_anonymous(self, xanony: etree._Element) -> EProxyAnonymity:
        """解析匿名程度"""
        if xanony is None:
            return EProxyAnonymity.Unknow

        txt: str = xanony.text
        if not isinstance(txt, str) or txt == "":
            return EProxyAnonymity.Unknow

        if txt == "透明":
            return EProxyAnonymity.Transparent
        elif txt == "高匿名":
            return EProxyAnonymity.Elite
        elif txt == "匿名":
            return EProxyAnonymity.Anonymous
        else:
            return EProxyAnonymity.Unknow

    # 类型
    def _parse_proxytype(self, xptype: etree._Element) -> (EProxyType, bool):
        """返回 (EProxyType,is_ssl)"""
        if xptype is None:
            return (None, None)

        txt: str = xptype.text
        if not isinstance(txt, str) or txt == "":
            return (None, None)

        if txt == "HTTP":
            return (EProxyType.HTTP, False)
        if txt == "HTTPS":
            return (EProxyType.HTTP, True)
        if txt.__contains__("SOCKS"):
            return (EProxyType.Socks, True)
        else:
            return (EProxyType.Unknow, False)

    # 位置
    def _parse_location(self, xctry: etree._Element) -> (str, str):
        """返回 (2位国家码CountryCode,其他地理位置信息)，
        不知道则返回None"""
        if xctry is None:
            return (None, None)

        xas = xctry.text
        if xas is None or len(xas) < 1:
            return (None, None)

        # 国家码
        countrycode: str = None
        strctry: str = "中国"  # 暂时写死的,该网站只有国内代理
        for ctcode in ALL_COUNTRIES.values():
            ctcode: CountryCode = ctcode
            if ctcode.country_names["CN"] == strctry:
                countrycode = ctcode.iso2
                break

        # 地理位置
        location = xas[3:]  # 暂时写死,取到中国后边的 省市区名称
        return (countrycode, location)

    # 响应速度
    def _parse_response_sec(self, xresp: etree._Element) -> float:
        """解析并返回响应速度（秒）"""
        if xresp is None:
            return None

        items = xresp.text
        if items is None or len(items) < 1:
            return (None, None)

        txt: str = ''.join(items).strip()
        if not isinstance(txt, str) or txt == "":
            return None

        respsec = None
        if txt.__contains__("秒"):
            respsec = float(txt.replace('秒', '').strip())

        return respsec

    # 最后验证时间
    def _parse_lastverifytime(self, xverify: etree._Element) -> float:
        """解析并返回最后验证时间"""
        try:
            if xverify is None:
                return None

            lastvt = xverify.text
            # 先转换为时间数组
            lastvt_t = time.strptime(lastvt, "%Y-%m-%d %H:%M:%S")
            # 再转换为时间戳
            lastvt = int(time.mktime(lastvt_t))

        except Exception:
            lastvt = None

        return lastvt
