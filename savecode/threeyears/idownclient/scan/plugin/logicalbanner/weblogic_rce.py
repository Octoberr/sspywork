"""
weblogic_rce漏洞脚本匹配
"""
from idownclient.scan.plugin.component.webalyzer import WebAlyzer
from requests.models import Response
from proxymanagement.proxymngr import ProxyItem, ProxyMngr

from .logicalhttp import LogicalHttp
from ....clientdatafeedback.scoutdatafeedback import (PortInfo, SiteInfo,
                                                      WeblogicT3)
import socket


class WeblogicRCE(LogicalHttp):
    vuln = 'Weblogic_WSAT_Unserialize_RCE'

    def __init__(self):
        LogicalHttp.__init__(self, WeblogicRCE.vuln)
        self.ca = WebAlyzer(self._name)

    def run_logic_grabber(self, host: str, portinfo: PortInfo, **kwargs):
        try:
            outlog = kwargs.get('outlog')
            log = f"开始扫描漏洞: {WeblogicRCE.vuln}"
            outlog(log)
            self._logger.debug(log)

            addr = host.split(':')
            ip = addr[0]
            port = int(addr[1])

            failnum = 0
            url = None
            resp: Response = None
            got = False
            while True:
                url = f'http://{host}/console/login/LoginForm.jsp'

                try:
                    resp: Response = self._ha.get_response(
                        url, verify=False, timeout=10, allow_redirects=False)
                    if resp is None or resp.status_code != 200:
                        self._logger.debug(
                            f"Cannt connect {url},resp:{resp.status_code if resp is not None else None}"
                        )
                        failnum += 1
                        continue
                    got = True
                    break
                except Exception as ex:
                    self._logger.debug(f"Request {url} error: {ex}")
                    failnum += 1
                finally:
                    if not got and failnum >= 1:
                        break

            if resp is None or resp.status_code != 200:
                self._logger.debug(
                    f"Connect {url} fail three times, get nothing, resp:{resp.status_code if resp is not None else None}"
                )
                return

            portinfo.banner += f'\n\n{resp.text}'

            siteinfo: SiteInfo = SiteInfo(url)
            respheard = ""
            for k, v in resp.headers.items():
                respheard += f"{k}:{v}\n"
            siteinfo.set_httpdata(None, None, None, resp.text)
            portinfo.set_siteinfo(siteinfo)

            addr = (ip, port)
            so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            so.connect(addr)
            msg = b't3 7.0.0.0\nAS:10\nHL:19\n\n'
            so.send(msg)
            resp = so.recv(4096).decode('utf-8')

            portinfo.service += '/weblogic-t3'
            portinfo.banner += f'\n\n{resp}'

            weblogic_t3 = WeblogicT3()
            weblogic_t3.banner = resp
            portinfo.set_weblgict3(weblogic_t3)

            self._logger.debug(f"Succeed get weblogic rce, url:{url}")
            log = f"{WeblogicRCE.vuln} 漏洞扫描完成"
            outlog(log)

        except Exception as ex:
            self._logger.error(f"weblogic_rce error: {ex}")
