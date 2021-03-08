"""joomla /careers"""

# -*- coding:utf-8 -*-

import traceback
from wsgiref import headers

from requests.models import Response

from idownclient.scan.plugin.component.webalyzer import WebAlyzer
from proxymanagement.proxymngr import ProxyItem, ProxyMngr

from ....clientdatafeedback.scoutdatafeedback import (Certificate, CertIssuer,
                                                      CertSubject, Component,
                                                      PortInfo, SiteInfo,
                                                      SslCert)
from .logicalhttp import LogicalHttp


class JoomlaCareers(LogicalHttp):
    """
    grabber for looking for the special url of a website.
    /host/careers
    """
    vuln = 'joomla_3_4_6'

    def __init__(self) -> None:
        LogicalHttp.__init__(self, JoomlaCareers.vuln)
        self.ca = WebAlyzer(self._name)

    def run_logic_grabber(self, host: str, portinfo: PortInfo, **kwargs):
        """
        2020/09/24
        wsy：这个漏洞的目录应该是/index.php/component/users/
        目前应该是搜集的指定目录的
        """
        try:
            outlog = kwargs.get('outlog')
            log = f"开始扫描漏洞: {JoomlaCareers.vuln}"
            outlog(log)
            failnum = 0
            url = None
            resp: Response = None
            got = False
            iserr = False
            while True:
                try:
                    p: ProxyItem = ProxyMngr.get_one_crosswall()
                    proxydict = None
                    if isinstance(p, ProxyItem):
                        proxydict = p.proxy_dict
                        self._logger.debug(f"proxy ip: {p._ip}, port: {p._port}")
                    url = f"http://{host}/index.php/component/users"
                    if portinfo.ssl_flag:
                        url = f"https://{host}/index.php/component/users"
                    self._logger.debug(f"Start joomlacareers url:{url}")
                    try:
                        resp: Response = self._ha.get_response(
                            url,
                            timeout=10,
                            headers="""
                        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                        accept-encoding: gzip, deflate
                        accept-language: en-US,en;q=0.9
                        cache-control: no-cache
                        pragma: no-cache
                        sec-fetch-dest: document
                        sec-fetch-mode: navigate
                        sec-fetch-site: none
                        sec-fetch-user: ?1
                        upgrade-insecure-requests: 1
                        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36""",
                            verify=False,
                        )
                    except:
                        iserr = True

                    if iserr or resp is None or resp.status_code != 200:
                        url = f"http://{host}/index.php/component/users"
                        if not portinfo.ssl_flag:
                            url = f"https://{host}/index.php/component/users"
                    else:
                        got = True
                        break

                    p: ProxyItem = ProxyMngr.get_one_crosswall()
                    proxydict = None
                    if isinstance(p, ProxyItem):
                        proxydict = p.proxy_dict
                        self._logger.debug(f"proxy ip: {p._ip}, port: {p._port}")

                    iserr = False
                    try:
                        resp: Response = self._ha.get_response(
                            url,
                            timeout=10,
                            headers="""
                        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                        accept-encoding: gzip, deflate
                        accept-language: en-US,en;q=0.9
                        cache-control: no-cache
                        pragma: no-cache
                        sec-fetch-dest: document
                        sec-fetch-mode: navigate
                        sec-fetch-site: none
                        sec-fetch-user: ?1
                        upgrade-insecure-requests: 1
                        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36""",
                            verify=False,
                        )
                    except:
                        iserr = True

                    if iserr or resp is None or resp.status_code != 200:
                        failnum += 1
                        continue

                    got = True
                    break

                except Exception as ex:
                    self._logger.trace(f"Get {url} error")
                    failnum += 1
                finally:
                    if not got or failnum >= 1:
                        break

            if iserr or resp is None or resp.status_code != 200:
                return
            self._logger.debug(f"Succeed get {JoomlaCareers.vuln}, url:{url}")
            siteinfo: SiteInfo = SiteInfo(url)
            respheader = ""
            for k, v in resp.headers.items():
                respheader += f"{k}:{v}\n"
            siteinfo.set_httpdata(None, None, respheader, resp.text)
            # 将组件信息加入到site里面
            wapres = 0
            try:
                self._logger.info(f"Start joomlacareers wappalyzer: {url}")
                for com in self.ca.get_alyzer_res(level=1, url=url):
                    wapres += 1
                    siteinfo.set_components(com)
            except:
                self._logger.error(
                    f"Get joomlacareers components error"
                )
            portinfo.set_siteinfo(siteinfo)
            self._logger.info(f"Stop joomlacareers wappalyzer: {url} rescount:{wapres}")
            log = f"{JoomlaCareers.vuln} 漏洞扫描完成"
            outlog(log)
        except Exception as ex:
            self._logger.error(f"Joomla careers error")
