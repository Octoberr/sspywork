"""
huawei hg532 vuln
"""
from requests.models import Response
from proxymanagement.proxymngr import ProxyItem, ProxyMngr

from idownclient.scan.plugin.component.webalyzer import WebAlyzer
from .logicalunknown import LogicalUnknown
from ....clientdatafeedback.scoutdatafeedback import (PortInfo, SiteInfo)


class HuaweiHg532(LogicalUnknown):
    vuln = 'Huawei_HG532_command_inject'

    def __init__(self):
        LogicalUnknown.__init__(self, HuaweiHg532.vuln)

    def run_logic_grabber(self, host: str, portinfo: PortInfo, **kwargs):
        try:
            outlog = kwargs.get('outlog')
            log = f"开始扫描漏洞: {HuaweiHg532.vuln}"
            outlog(log)
            
            self._logger.debug(log)

            failnum = 0
            url = None
            resp: Response = None
            got = False
            while True:
                url = f"http://{host}/ctrlt/DeviceUpgrade_1"

                self._logger.debug(f"Start huawei hg532 url:{url}")

                try:
                    p: ProxyItem = ProxyMngr.get_one_crosswall()
                    proxydict = None
                    if isinstance(p, ProxyItem):
                        proxydict = p.proxy_dict
                        self._logger.debug(f"proxy ip: {p._ip}, port: {p._port}")

                    headers = """
                        'Authorization':'Digest username=dslf-config, realm=HuaweiHomeGateway, nonce=88645cefb1f9ede0e336e3569d75ee30, uri=/ctrlt/DeviceUpgrade_1, response=3612f843a42db38f48f59d2a3597e19c, algorithm=MD5, qop=auth, nc=00000001, cnonce=248d1a2560100669',
                        'User-Agent'        :   'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
                        'Accept-Encoding'   :   'gzip, deflate',
                        'Connection'        :   'keep-alive',
                        'Content-Type'      :   'application/x-www-form-urlencoded'
                    """

                    TEMPLATE = '<?xml version="1.0" ?> <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"> <s:Body><u:%s xmlns:u="urn:schemas-upnp-org:service:WANPPPConnection:1">%s</u:%s></s:Body></s:Envelope>'
                    data = TEMPLATE % ('GetSoftwareVersion', '<NewSoftwareVersion></NewSoftwareVersion>' ,'GetSoftwareVersion')

                    resp: Response = self._ha.get_response(
                        url,
                        req_data=data,
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
                    self._logger.debug(f"Request {url} error: {ex}")
                    failnum += 1
                finally:
                    if not got and failnum >= 1:
                        break

            if resp is None or resp.status_code != 200:
                self._logger.debug(
                    f"Connect {url} fail three times, get nothing, resp:{resp.status_code if resp is not None else None}")
                return

            self._logger.debug(f"Succeed get huawei hg532, url:{url}")
            siteinfo: SiteInfo = SiteInfo(url)

            respheard = ""
            for k, v in resp.headers.items():
                respheard += f"{k}:{v}\n"

            siteinfo.set_httpdata(None, None, respheard, resp.text)
            
            if portinfo.service == 'unknown':
                portinfo.service = 'http'
            portinfo.set_siteinfo(siteinfo)
            log = f"{HuaweiHg532.vuln} 漏洞扫描完成"
            outlog(log)

        except Exception as ex:
            self._logger.error("Huawei hg532 vuln error")
