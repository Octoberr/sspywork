"""SideSite Detect plugin"""

# -*- coding:utf-8 -*-

import re
import traceback

import requests
import urllib3
from commonbaby import HttpAccess

from datacontract.iscoutdataset import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import SideSite
from idownclient.scout.plugin.scoutplugbase import ScoutPlugBase
from proxymanagement import ProxyMngr

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class SideSiteDetect(ScoutPlugBase):
    """represents a SideSiteDetect info"""

    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36",
    }
    re_ip = re.compile("^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", re.S)

    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid IScoutTask")
        self._task: IscoutTask = task
        self._ha: HttpAccess = HttpAccess()

    def side_site_detect(self, host: str, lvl) -> iter:
        """"""
        try:
            if not isinstance(host, str):
                self._logger.error("Invalid host for side-site detecting: {}".format(host))
                return

            failedtimes = 0
            while True:
                try:
                    for i in self.__side_site_detect(host, lvl):
                        yield i

                    break
                except Exception:
                    failedtimes += 1
                    if failedtimes >= 3:
                        self._task.fail_count('side_site_detect', lvl)
                        self._logger.error("Get side_site error: host={}, err={}".format(host, traceback.format_exc()))
                        return
                    p = ProxyMngr.get_one_crosswall(ssl=True)
                    # p = ProxyMngr.get_one_internal(ssl=True)

            self._task.success_count('side_site_detect', lvl)

        except Exception:
            self._task.fail_count('side_site_detect', lvl)
            self._logger.error("Get side_site error: host={}, err={}".format(host, traceback.format_exc()))

    def __side_site_detect(self, host: str, lvl) -> iter:
        if not isinstance(host, str) or host == "":
            return

        proxydict = ProxyMngr.get_static_proxy()

        # 查side_site的api接口
        url = 'https://api.hackertarget.com/reverseiplookup/?q={}'.format(host)
        html = self._ha.getstring(
            url,
            proxies=proxydict,
            timeout=30,  # 至少30，以免网络不稳定时无法获取数据
            headers="""
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Accept-Encoding: gzip, deflate
            Accept-Language: en
            Cache-Control: no-cache
            Connection: keep-alive
            Pragma: no-cache
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36
            """
        )
        if html is None or html == "":
            return

        # 拿旁站信息
        lines = html.split()
        if len(lines) < 1:
            self._logger.info("No result line found for side-site: {}".format(host))
            return

        for h in lines:
            for ss in self._parse_side_site(h):
                if not isinstance(ss, SideSite):
                    continue
                self._logger.info("Got a sidesite: srchost={}, host={}, ip={}, port={}"
                                  .format(host, ss.host, ss.ip, ss.port))
                yield ss  # 按SideSite标准返回去

    def _parse_side_site(self, host: str) -> iter:
        """
        ②解析旁站
        host: 目标域名或IP
        :param host:
        :return:
        """
        try:
            if not isinstance(host, str) or host == "":
                return

            # 判断host类型
            if self.re_ip.match(host):
                hosttype = 2  # 当前旁站是ip,为2
            else:
                hosttype = 1  # 是域名,为1

            # 每个旁站去拿它的真实IP(api接口)
            if self.re_ip.match(host):
                ip: str = host  # 当前旁站是ip的情况,直接把旁站(ip)赋给ip,不用再去调函数拿了
            else:
                ip: str = self.get_one_realip(host)

            if ip is None:
                return

            # 检查80端口
            resp = None
            try:
                http_url = "http://{}".format(host)
                resp = requests.request("GET",
                                        url=http_url,
                                        headers=self.HEADERS,
                                        allow_redirects=True,
                                        verify=False,
                                        timeout=(3, 7))
            except Exception as e:
                self._logger.info("Check 80 port failed: host={}, error:{}".format(host, e))

            if resp is not None:
                ss = SideSite(host, ip, hosttype, port=80, isssl=0)
                ss.url = http_url
                yield ss  # 返80的数据

                # 满足80的同时,继续检查其是否跳转location
                # 即:发的http出去中间一些列网络跳转,最终的跳到的url(可简单粗暴就理解为响应的url)
                location = resp.url
                if location is None:
                    location = resp.headers.get("location")
                    if location is None:
                        location = resp.headers.get("Location")
                if location is not None and location.startswith("https"):
                    # 如果跳到了443,则返443,并退出函数
                    ss = SideSite(host, ip, hosttype, port=443, isssl=1)
                    ss.url = location
                    yield ss
                    return

            # 当80端口未开,就直接单独去检查443
            # 即:当前host直接发https请求
            resp = None
            try:
                https_url = "https://{}".format(host)
                resp = requests.request("GET",
                                        url=https_url,
                                        headers=self.HEADERS,
                                        verify=False,
                                        timeout=3)
            except Exception as e:
                self._logger.info("Check 443 port error: host={}, error:{}".format(host, e))

            if resp is not None:
                ss = SideSite(host, ip, hosttype, 443, 1)
                ss.url = https_url
                yield ss  # 返443的数据

            return

        except Exception:
            self._logger.error("check Sidesite port error: host={}, error:{}".format(host, traceback.format_exc()))

    def get_one_realip(self, host: str):
        """
        ③获取旁站的一个realip
        :param host: 传入的一个旁站
        :return: ip
        """
        ip = None
        try:
            # 查realip的api接口
            realip_api1_url = "http://api.hackertarget.com/dnslookup/?q={}".format(host)
            res = requests.request('GET',
                                   url=realip_api1_url,
                                   headers=self.HEADERS,
                                   timeout=(3, 7)
                                   )
            if res is None or res == "":
                return

            # 拿真实ip(A记录)
            lines = res.text.splitlines()
            for line in lines:
                items = line.split()
                if len(items) < 3:
                    continue
                if items[0] != 'A':
                    continue
                ip = items[2]
                break

        except Exception as e:
            self._logger.error("Sidesite get realip error, host={}, error:{}".format(host, e))

        return ip
