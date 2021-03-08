"""object real_ip plugin"""

# -*- coding:utf-8 -*-
import traceback

from commonbaby import HttpAccess

from datacontract import IscoutTask
from idownclient.scout.plugin.scoutplugbase import ScoutPlugBase
from proxymanagement import ProxyMngr, ProxyItem


class RealipDetect(ScoutPlugBase):
    """represents a realip info"""

    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36",
    }

    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid IScoutTask")
        self.task = task
        self._ha: HttpAccess = HttpAccess()

    def get_real_ip(self, host: str, lvl) -> iter:
        try:
            if not isinstance(host, str):
                self._logger.error("Invalid host for Realip detecting: {}".format(host))
                return

            p = None  # ProxyMngr.get_one_crosswall(ssl=True)
            # p = ProxyMngr.get_one_internal(ssl=True)

            failedtimes = 0
            while True:
                try:
                    for i in self.__get_realip(host, lvl, p):
                        yield i

                    break
                except Exception:
                    failedtimes += 1
                    if failedtimes >= 3:
                        self.task.fail_count('real_ip', lvl)
                        self._logger.error("Get realip error: host={}, err={}".format(host, traceback.format_exc()))
                        return
                    p = ProxyMngr.get_one_crosswall(ssl=True)
                    # p = ProxyMngr.get_one_internal(ssl=True)

            self.task.success_count('real_ip', lvl)

        except Exception:
            self.task.fail_count('real_ip', lvl)
            self._logger.error("Get realip error: host={}, err={}".format(host, traceback.format_exc()))

    def __get_realip(self, host: str, lvl, p: ProxyItem = None):
        if not isinstance(host, str) or host == "":
            return

        # 查realip的api接口
        url = "https://api.hackertarget.com/dnslookup/?q={}".format(host)
        # 使用静态ip代理，modify by judy 20201027
        html = self._ha.getstring(
            url,
            proxies=ProxyMngr.get_static_proxy(),
            timeout=30,  # timeout至少30，以免网络不稳定时无法获取数据
            headers="""
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Accept-Encoding: gzip, deflate
            Accept-Language: en
            Cache-Control: no-cache
            Connection: keep-alive
            Pragma: no-cache
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36
            """)
        if html is None or html == "":
            return

        # 拿真实ip(A记录)
        lines = html.splitlines()
        if lines is None or len(lines) < 1:
            return

        for line in lines:
            items = line.split()
            if len(items) < 3:
                continue
            if items[0] != 'A':
                continue
            ip = items[2]
            yield ip
