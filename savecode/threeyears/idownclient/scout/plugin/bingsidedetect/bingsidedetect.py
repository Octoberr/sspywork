"""
使用bing进行旁站探测
create by judy 2019/11/14
"""
import re
import traceback
from subprocess import Popen, PIPE
from sys import platform

import requests

from idownclient.clientdatafeedback.scoutdatafeedback import SideSite
from ..searchengine.bing.azbing import AzBingApi
from ..scoutplugbase import ScoutPlugBase


class BingSideDetect(ScoutPlugBase):

    def __init__(self):
        ScoutPlugBase.__init__(self)
        self.pf = 'linux'
        if platform == 'linux' or platform == 'linux2':
            self.pf = 'linux'
        elif platform == 'win32':
            self.pf = 'windows'

        # 因为使用bing拿到的就是url所有hosttype都为1
        self.hosttype = 1

    def __ping_domain(self, mail_domian):
        """
        去探测domain的旁站那么就需要拿到这个domain的ip
        再去探测
        :param mail_domian:
        :return: ip str
        """
        re_ip = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
        res = None
        if self.pf == 'linux':
            try:
                proc = Popen(f'ping -c 2 {mail_domian}', stdout=PIPE, shell=True)
                outs, errs = proc.communicate(timeout=15)
                res = outs.decode('utf-8')
            except:
                self._logger.error(f"Linux ping result error, err:{traceback.format_exc()}")
                res = None
        elif self.pf == 'windows':
            try:
                proc = Popen(f'ping {mail_domian}', stdout=PIPE, shell=True)
                outs, errs = proc.communicate(timeout=15)
                res = outs.decode('gbk')
            except:
                self._logger.error(f"Windows ping result error, err:{traceback.format_exc()}")
                res = None

        if res is not None:
            ips: list = re_ip.findall(res)
            if len(ips) > 0:
                return ips[0]
        else:
            return res

    def _bing_web_search_ip(self, ip):
        """
        这里是共有方法使用ip去bing那边查询,
        这里应该是要把结果拿全的
        :param ip:
        :return:
        """
        query = f"ip:{ip}"
        for el in AzBingApi.bing_web_search(query, 0, 15):
            url = el.get('url')
            if url is not None:
                yield url

    def _make_side_site(self, url: str, ip):
        """
        尝试访问拿到的url，如果有效那么就是一个旁站
        :param url:
        :return:
        """
        if url.startswith('https'):
            port = 443
            isssl = 1
        else:
            port = 80
            isssl = 0
        response = requests.get(url)
        status = response.status_code
        if status == 200:
            side_site = SideSite(url, ip, self.hosttype, port, isssl)
            return side_site

    def bing_domain_side_site(self, domain, level, reason=None):
        """
        使用bing去寻找domain的旁站
        :param domain:
        :param level:
        :param reason:
        :return:
        """
        ip = self.__ping_domain(domain)
        if ip is None:
            # ip为空说明网络出现了问题
            return
        for url in self._bing_web_search_ip(ip):
            side_site = self._make_side_site(url, ip)
            if side_site is not None:
                yield side_site

    def bing_ip_side_site(self, ip, level, reason=None):
        """
        使用bing去寻找domain的旁站
        :param ip:
        :param level:
        :param reason:
        :return:
        """
        if ip is None or ip == '':
            # ip为空说明网络出现了问题
            return
        for url in self._bing_web_search_ip(ip):
            side_site = self._make_side_site(url, ip)
            if side_site is not None:
                yield side_site
