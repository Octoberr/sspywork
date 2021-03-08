"""
因为要增加下载某个国家数据的功能
以前这个功能就是随便应付下，但是现在好像是确实需要这个功能
所以重新好好写下
这里把shodan的代码整理下
"""
import re
import threading
import traceback
from abc import abstractmethod

import requests
from commonbaby.httpaccess import HttpAccess

from common.tools import sslparse
from idownclient.clientdatafeedback.scandatafeedback import (
    PortInfo,
    PortInfo_one,
    HttpData,
    SiteInfo_One,
    Geoinfo,
)
from idownclient.config_spiders import shodanconf
from idownclient.scan.scanplugbase import ScanPlugBase
from .cmsfinger import cmsver


class ShodanBase(ScanPlugBase):
    def __init__(self, task):
        ScanPlugBase.__init__(self, task)
        # 把一些基本不动的参数放在这个构造函数里
        self._basic_url = "https://api.shodan.io"
        self.apikey = shodanconf.get("apikey", None).strip()
        if self.apikey is None:
            raise Exception("Shodan api key cant be None")
        # cidr=net, app=product, ver=version, title=http.title
        self.query = [
            "after",
            "asn",
            "before",
            "city",
            "country",
            "geo",
            "has_ipv6",
            "has_screenshot",
            "hostname",
            "isp",
            "link",
            "cidr",
            "org",
            "os",
            "port",
            "postal",
            "app",
            "state",
            "ver",
            "bitcoin.ip",
            "bitcoin_ip_count",
            "bitcoin.port",
            "bitcoin.version",
            "ip",
            "http.component",
            "http.component_category",
            "http.html",
            "http.status",
            "title",
            "ntp.ip",
            "ntp.ip_count",
            "ntp.more",
            "ntp.port",
            "ssl",
            "ssl.alpn",
            "ssl.chain_count",
            "ssl.version",
            "ssl.cert.alg",
            "ssl.cert.expired",
            "ssl.cert.extension",
            "ssl.cert.serial",
            "ssl.cert.pubkey.bits",
            "ssl.cert.pubkey.type",
            "ssl.cipher.version",
            "ssl.cipher.bits",
            "ssl.cipher.name",
            "telnet.option",
            "telnet.do",
            "telnet.dont",
            "telnet.will",
            "telnet.wont",
        ]
        # 访问一页出错的尝试次数
        self.errortimes = 0
        # 连续访问出错的页数
        self.page_error_times = 0

        self.error_limit = shodanconf.get("error_times", 5)

        # 获取所有数据的开关,默认为false,但是这次需要全部数据
        # 现在这个数据是直接配置的，但是要增加这个功能那么需要带在command里面，目前可以先这样放在这里
        # 后期再说
        self.__get_all_data_switch = shodanconf.get("get_all_data_switch", False)
        # 文件锁，与文件相关的操作增加这个锁
        self.shodan_file_locker = threading.RLock()
        self._cmsver_lower = {}
        for k, v in cmsver.items():
            self._cmsver_lower[k.lower()] = v

    def _get_cmd_fileter(self, condition: list):
        """
        获取cmd中的查询条件
        condition就是shodan的限制查询条件
        需要在内部做字段转换
        :return:
        """
        filter_dict = self.task.cmd.stratagyscan.search.filter
        # 做一个特殊查询
        query = ""
        # # 产品的话写最前面
        if filter_dict.__contains__("app"):
            v = filter_dict.pop("app")
            if v is not None and v != "":
                query += f'"{v}"+'
        for k, v in filter_dict.items():
            if v != "" and v is not None and v is not False and k in condition:
                # 真不知道为啥明明没有值给你传一个空的字符串过来，毛病
                # 为了兼容标准中的搜索字段，在程序内部做字段转换
                if k == "cidr":
                    k = "net"
                if k == "ver":
                    k = "version"
                if k == "title":
                    k = "http.title"
                # 需要特殊处理v为false的值
                if v is True:
                    v = "true"
                # 需要特殊处理的几个键
                if k == "ssl":
                    query += f"{k}+"
                    continue
                query += f'{k}:"{v}"+'
        return query.strip("+")

    def _parse_geoinfo(self, asn, ginfodict: dict):
        """
        解析geoinfo
        :param ginfodict:
        :return:
        """
        try:
            ginfo = Geoinfo(asn)
            city = {"names": {"en": ginfodict.get("city"), "zh-CN": None}}
            # shodan是英文的，这两个东西好像是没有的
            # continent = {}
            # province = {}
            country = {
                "code": ginfodict.get("country_code"),
                "names": {"en": ginfodict.get("country_name"), "zh-CN": None},
            }
            location = {
                "lat": ginfodict.get("latitude"),
                "lon": ginfodict.get("longitude"),
            }
            ginfo.city = city
            # ginfo.continent = continent
            # ginfo.province = province
            ginfo.country = country
            ginfo.location = location
            return ginfo
        except:
            self._logger.error(f"Get geoinfo error, err:{traceback.format_exc()}")

    def _get_cms_ver(self, host: str, path: str, rgx: re.Pattern):
        ver: str = None
        try:
            ha = HttpAccess()

            # access home page to get cookie
            url = "http://" + host.strip("/")
            ha.getstring(
                url,
                headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: en-US,en;q=0.9
            Cache-Control: no-cache
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36""",
            )

            # access version page
            url = "http://" + host.strip("/") + "/" + path.lstrip("/")
            html = ha.getstring(
                url,
                headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: en-US,en;q=0.9
            Cache-Control: no-cache
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36""",
            )

            if html is None or html == "":
                return ver

            # <version>(.+)</version>
            m: re.Match = re.search(rgx, html, re.S)
            if m is None:
                return ver

            ver = m.group(1)

        except Exception as e:
            self._logger.error("Get joomla version faile: {} {}".format(host, e.args))
        return ver

    def _recognize_cms_ver(self, host: str, name: str) -> str:
        """recognize cms and version"""
        ver: str = None
        try:
            if not self._cmsver_lower.__contains__(name.lower()):
                return ver

            path, rgx = self._cmsver_lower[name.lower()]

            ver: str = self._get_cms_ver(host, path, rgx)

        except Exception:
            self._logger.error(
                "Recognize cms err: host={} name={} err={}".format(
                    host, name, traceback.format_exc()
                )
            )
        return ver

    def _add_a_sit(self, ip, port):
        """
        尝试去获取个site
        """
        if int(port) == 443:
            urls = [
                f"https://{ip}/wordpress/wp-content/plugins/wp-file-manager/lib/php/connector.minimal.php",
                f"https://{ip}/wordpress/wp-content/plugins/wp-file-manager/lib/php/connector.minimal.php",
            ]
        else:
            urls = [
                f"http://{ip}/wordpress/wp-content/plugins/wp-file-manager/lib/php/connector.minimal.php",
                f"http://{ip}/wordpress/wp-content/plugins/wp-file-manager/lib/php/connector.minimal.php",
            ]
        try:
            for url in urls:
                try:
                    site_one = None
                    http_data = HttpData()
                    resp = requests.get(url, verify=False, timeout=5)
                    if resp.status_code == 200:
                        respheard = ""
                        for k, v in resp.headers.items():
                            respheard += f"{k}:{v}\n"
                        http_data.respbody = resp.text
                        http_data.respheader = respheard
                        site_one = SiteInfo_One(http_data)
                        site_one.site = url
                    print(f"Get {url} response success")
                    yield site_one
                except:
                    print(f"Cannt connect to {url}")
        except:
            print(f"Cannt connect to url")

    def _parse_siteone(self, port, banner, service, http: dict, ip):
        """
        解析port_one
        :return:
        """
        pinf_one = None
        try:
            # port info
            pinf_one = PortInfo_one(port, banner, service)
            # site info
            # 需要先去拿http_data
            if http is not None:
                http_data = HttpData()
                http_data.respbody = http.get("html")
                site_one = SiteInfo_One(http_data)
                http_host = http.get("host")
                site_one.site = http_host
                site_one.location = http.get("location")
                # site_one.server.append({'name': http.get('server'), 'version': None})
                # site_one.waf.append({'name': http.get('waf'), 'version': None})
                server = http.get("server")
                if server is not None:
                    site_one.component.append(
                        {"name": server, "version": None, "category": "server"}
                    )
                waf = http.get("waf")
                if waf is not None:
                    site_one.component.append(
                        {"name": waf, "version": None, "category": "waf"}
                    )
                # add redirects
                redis = http.get("redirects", [])
                for rs in redis:
                    site_one.redirects.append(rs.get("host") + rs.get("location", ""))
                # ---------------------------------------------------------------------
                # add favicon
                favicon = http.get("favicon", {})
                site_one.favicon = favicon
                # ---------------------------------------------------------------
                # component
                cptinfo: dict = http.get("components", {})
                for k, v in cptinfo.items():
                    categories = v.get("categories", [])
                    if len(categories) == 0 and k.lower() == "joomla":
                        categories = ["CMS"]
                    for el in categories:
                        version = None
                        if el.lower() == "cms":
                            ver = self._recognize_cms_ver(http_host, k)
                            if not ver is None:
                                version = ver
                                self._logger.debug(
                                    "Got cms version: {}:{}".format(k, version)
                                )
                        site_one.component.extend(
                            [{"name": k, "version": version, "category": el}]
                        )
                # 增加site_one
                pinf_one.append_siteinfo(site_one)
            # 获取特定目标的
            # for aso in self._add_a_sit(ip, port):
            #     if aso is not None:
            #         pinf_one.append_siteinfo(aso)
        except:
            self._logger.error(f"Get a port info error, err:{traceback.format_exc()}")
        return pinf_one

    def _parse_port_vuln(self, vulns: dict) -> list:
        """
        解析port里面的cve漏洞信息,做了一点单独的处理
        返回的是一个list里面带有的cve的信息
        :param vulns:
        :return:
        """
        res = []
        for k, v in vulns.items():
            v["cve"] = k
            res.append(v)
        return res

    def _get_ssl_info(self, ssldata: str):
        """
        这里获取ssl的详细信息，这里会去调命令行的信息，如果
        当前程序如果不是运行在docker容器里可能就会无法解析
        ssl信息，所以尽量让当前的程序运行在容器里
        调用的是openssl去解析的，所以需要做一个限制
        :param ssldata:
        :return:
        """
        res = ""
        try:
            with self.shodan_file_locker:
                res = sslparse.parse_ssl_raw(ssldata)
        except Exception:
            self._logger.error(f"parser ssl error, err:{traceback.format_exc()}")
        return res

    def _parse_portinfo(self, dinfo: dict, hostnames, domains, ip, vulns=None):
        """
        解析portinfo
        :param dinfo:
        :param hostnames:
        :param domains:
        :param vulns:
        :return:
        """
        # port---------------------------------------------------------------------
        pinf = PortInfo()
        cpe: list = dinfo.get("cpe")
        info = dinfo.get("info")
        tags: list = dinfo.get("tags")
        # timestamp的时间格式为2019-08-14T23:32:22.144111
        timestamp: str = dinfo.get("timestamp", None)
        if timestamp is not None:
            timestamp = timestamp.replace("T", " ")
        app = dinfo.get("product")
        banner = dinfo.get("data")
        port = dinfo.get("port")
        os = dinfo.get("os")
        version = dinfo.get("version")
        transport = dinfo.get("transport")
        link = dinfo.get("link")
        uptime = dinfo.get("uptime")
        device = dinfo.get("devicetype")
        # 端口服务
        http: dict = dinfo.get("http", None)
        ssl = dinfo.get("ssl", None)
        ftp = dinfo.get("ftp", None)
        ssh = dinfo.get("ssh", None)
        opts = dinfo.get("opts", {})
        service = dinfo.get("_shodan", {}).get("module")
        # --------------------------------------------------------------这里面尽量拿能拿到的数据
        # port_one实例化的时候会实例化port, banner, service,主要是为了解析siteone,并且给一个port_one对象
        pinf_one = self._parse_siteone(port, banner, service, http, ip)
        if pinf_one is not None:
            pinf_one.app = app
            pinf_one.hostnames = hostnames
            pinf_one.domains = domains
            pinf_one.version = version
            pinf_one.os = os
            pinf_one.timestamp = timestamp
            pinf_one.transport = transport
            pinf_one.cpe = cpe
            pinf_one.tags = tags
            pinf_one.link = link
            pinf_one.uptime = uptime
            pinf_one.extrainfo = info
            pinf_one.device = device
            # ------------------------------------------------给port_one对象赋值
            if ssl is not None:
                pinf_one.append_sslinfo(ssl)
                # 这里还需要将ssl里面的信息加入到banner,所以需要开个方法
                chain = ssl.get("chain", [])
                for el in chain:
                    ssldata = el
                    sslinfo = self._get_ssl_info(ssldata)
                    banner += "\n"
                    banner += sslinfo
                pinf_one.banner = banner
            if ftp is not None:
                pinf_one.append_ftpinfo(ftp)
            if ssh is not None:
                pinf_one.append_sshinfo(ssh)
            if vulns is not None:
                # 这里好像是要处理下,shodan特有
                v_data = self._parse_port_vuln(vulns)
                pinf_one.append_vulns(v_data)
            # 新增opts.screenshot
            screenshot = opts.get("screenshot", None)
            pinf_one.opt_set_screenshot(screenshot)
            # 新增telent,by judy 190814
            telnet = opts.get("telnet", None)
            pinf_one.opt_set_telnet(telnet)
            # ----------------------------------------使用port对象，添加一个port_one
            pinf.append_one(pinf_one)
        return pinf

    def _download_data(self):
        """
        继承base的下载接口，
        但是这里可能需要分两步走了
        :return:
        """
        if not self.__get_all_data_switch:
            # 搜索接口
            for data in self._download_search_data():
                yield data
        else:
            # 下载国家数据接口
            for data in self._download_all_data():
                yield data

    @abstractmethod
    def _download_search_data(self) -> iter:
        """
        下载搜索的数据，
        数据量比较小，但是需要去搜索ip然后获取ip的完整数据
        :return:
        """
        return []

    @abstractmethod
    def _download_all_data(self) -> iter:
        """
        下载一个国家完整的数据
        数据量比较大
        :return:
        """
        return []
