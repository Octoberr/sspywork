"""
domino/Lotus/smtp
create by judy 2020/09/07
"""
import traceback

from requests.models import Response
from proxymanagement.proxymngr import ProxyItem, ProxyMngr

from idownclient.scan.plugin.component.webalyzer import WebAlyzer
from .logicalhttp import LogicalHttp
from ....clientdatafeedback.scoutdatafeedback import (PortInfo, SiteInfo)


class LotusSmtp(LogicalHttp):
    vuln = 'ibm_lotus_domino_password_hash_extraction'

    def __init__(self):
        LogicalHttp.__init__(self, LotusSmtp.vuln)
        self.ca = WebAlyzer(self._name)

    def run_logic_grabber(self, host: str, portinfo: PortInfo, **kwargs):
        try:
            outlog = kwargs.get('outlog')
            log = f"开始扫描漏洞: {LotusSmtp.vuln}"
            self._logger.debug(log)
            outlog(log)
            failnum = 0
            url = None
            resp: Response = None
            got = False
            while True:
                url = f"http://{host}/names.nsf"
                if portinfo.ssl_flag:
                    url = f"https://{host}/names.nsf"
                self._logger.debug(f"Start lotussmtp url:{url}")
                try:
                    p: ProxyItem = ProxyMngr.get_one_crosswall()
                    proxydict = None
                    if isinstance(p, ProxyItem):
                        proxydict = p.proxy_dict
                        self._logger.debug(f"proxy ip: {p._ip}, port: {p._port}")
                    headers = f"""
                    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                    Accept-Encoding: gzip, deflate
                    Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
                    Cache-Control: no-cache
                    Host: {host}
                    Pragma: no-cache
                    Proxy-Connection: keep-alive
                    Upgrade-Insecure-Requests: 1
                    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36
                    """
                    resp: Response = self._ha.get_response(
                        url,
                        headers=headers,
                        verify=False,
                        timeout=10,
                        allow_redirects=False
                    )
                    if resp is None or resp.status_code != 200:
                        self._logger.debug(f"Cannt connect {url},resp:{resp.status_code if resp is not None else None}")
                        failnum += 1
                        continue
                    got = True
                    break
                except Exception as ex:
                    self._logger.debug(f"Request {url} error")
                    failnum += 1
                finally:
                    if not got and failnum >= 1:
                        break
            if resp is None or resp.status_code != 200:
                self._logger.debug(
                    f"Connect {url} fail three times, get nothing, resp:{resp.status_code if resp is not None else None}")
                return
            self._logger.debug(f"Succeed get lotussmtp, url:{url}")
            siteinfo: SiteInfo = SiteInfo(url)
            respheard = ""
            for k, v in resp.headers.items():
                respheard += f"{k}:{v}\n"
            siteinfo.set_httpdata(None, None, respheard, resp.text)
            wapres = 0
            try:
                self._logger.info(f"Start lotussmtp wappalyzer: {url}")
                for com in self.ca.get_alyzer_res(level=1, url=url):
                    wapres += 1
                    siteinfo.set_components(com)
            except:
                self._logger.error(
                    f"Get lotussmtp components error"
                )
            portinfo.set_siteinfo(siteinfo)
            self._logger.info(f"Stop lotussmtp wappalyzer: {url} rescount:{wapres}")
            log = f"{LotusSmtp.vuln} 漏洞扫描完成"
            outlog(log)
        except Exception as ex:
            self._logger.error(f"Lotus smtp error")
