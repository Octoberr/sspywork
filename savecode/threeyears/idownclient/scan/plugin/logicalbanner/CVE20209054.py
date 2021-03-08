"""
CVE20209054漏洞匹配
1、title里面有指定字段
2、请求文件 utility/flag.js
"""
import re
import traceback

import requests

from idownclient.scan.plugin.component.webalyzer import WebAlyzer
from .logicalhttp import LogicalHttp
from ....clientdatafeedback.scoutdatafeedback import (PortInfo, SiteInfo)


class CVE20209054(LogicalHttp):
    vuln = 'zyxel_command_injection'

    def __init__(self):
        LogicalHttp.__init__(self, CVE20209054.vuln)
        self.ca = WebAlyzer(self._name)
        self.products = ['NAS326', 'NAS520', 'NAS540', 'NAS542',
                         'ATP100', 'ATP200', 'ATP500', 'ATP800',
                         'ZyWALL110', 'ZyWALL310', 'ZyWALL1100',
                         'NSA210', 'NSA-220', 'NSA221', 'NSA310', 'NSA310S', 'NSA320', 'NSA320S', 'NSA325', 'NSA325v2',
                         'USG20-VPN', 'USG20W-VPN', 'VPN50', 'VPN100', 'VPN300', 'VPN1000',
                         'USG40', 'USG40W', 'USG60', 'USG60W', 'USG110', 'USG210', 'USG310', 'USG1100', 'USG1900',
                         'USG2200']

    def make_siteinfo(self, url, response, portinfo):
        """
        可能会生成多个site所以就把方法独立出来了
        """
        self._logger.debug(f"Succeed get {self.vuln}, url:{url}")
        siteinfo: SiteInfo = SiteInfo(url)
        respheard = ""
        for k, v in response.headers.items():
            respheard += f"{k}:{v}\n"
        siteinfo.set_httpdata(None, None, respheard, response.text)
        wapres = 0
        try:
            self._logger.info(f"Start {self.vuln} wappalyzer: {url}")
            for com in self.ca.get_alyzer_res(level=1, url=url):
                wapres += 1
                siteinfo.set_components(com)
        except:
            self._logger.error(
                f"Get {self.vuln} components error"
            )
        portinfo.set_siteinfo(siteinfo)
        self._logger.info(f"Stop {self.vuln} wappalyzer: {url} rescount:{wapres}")

    def run_logic_grabber(self, host: str, portinfo: PortInfo, **kwargs):
        outlog = kwargs.get('outlog')
        log = f"开始扫描漏洞: {CVE20209054.vuln}"
        self._logger.debug(log)
        outlog(log)
        sa = requests.Session()
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': f'{host}',
            'Pragma': 'no-cache',
            'Proxy-Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
        }
        sa.headers.update(headers)
        http_str = 'http'
        if portinfo.ssl_flag:
            http_str = 'https'
        # 最开始的url
        url = f"{http_str}://{host}"
        self._logger.debug(f"Start {self.vuln} url:{url}")
        try:
            # 这个页面有时候会自动跳转，需要允许自动跳转
            response = sa.get(url, verify=False, timeout=10)
            if response is None or response.status_code != 200:
                self._logger.debug(f"Cannt connect {url},resp:{response.status_code if response is not None else None}")
                return
            self._logger.debug(f"Succeed get {self.vuln}, url:{url}")
            if response.text.find('/zyxel/loginwrap.html') == -1:
                self._logger.debug("Not found js page : /zyxel/loginwrap.html")
                return
            url = url + "/zyxel/loginwrap.html"
            self._logger.debug(f"Start {self.vuln} url:{url}")
            response = sa.get(url, verify=False, timeout=10)
            if response is None or response.status_code != 200 or response.text is None:
                self._logger.debug(f"Cannt connect {url},resp:{response.status_code if response is not None else None}")
                return
            find = False
            match = re.search('<title>(.*)</title>', response.text, re.I | re.M)
            if match:
                title = match.group(1).strip()
                for product in self.products:
                    if title.lower().endswith(product.lower()):
                        find = True
                        break
            # 如果没有找到就需要去走这一步
            if find:
                self.make_siteinfo(url, response, portinfo)
                # 走到上面就可以了，但是为了拿版本号可以继续走
                if response.text.find('utility/flag.js') != -1:
                    try:
                        resurl = response.url[:response.url.rfind('/')]
                        url = resurl + '/utility/flag.js'
                        self._logger.debug(f"Start {self.vuln} url:{url}")
                        response = sa.get(url, verify=False, timeout=10)
                        if response is None or response.status_code != 200:
                            self._logger.debug(
                                f"Cannt connect {url} resp:{response.status_code if response is not None else None}")
                            return
                        self.make_siteinfo(url, response, portinfo)
                    except:
                        self._logger.error(f"Cant connect {url}")
            log = f"{CVE20209054.vuln} 漏洞扫描完成"
            outlog(log)
        except Exception:
            self._logger.error(f"{self.vuln} scan error\nerr:{traceback.format_exc()}")
