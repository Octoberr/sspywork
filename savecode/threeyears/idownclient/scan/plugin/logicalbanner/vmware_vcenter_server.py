"""
vmware_vcenter_server
"""
from idownclient.clientdatafeedback.scoutdatafeedback import url
from requests.models import Response
from proxymanagement.proxymngr import ProxyItem, ProxyMngr

# from idownclient.scan.plugin.component.webalyzer import WebAlyzer
from .logicalhttp import LogicalHttp
from ....clientdatafeedback.scoutdatafeedback import (PortInfo, SiteInfo)


class VmwareVcenterServer(LogicalHttp):
    vuln = 'Vmware_VCenter_Arbitrary_File_Read'

    def __init__(self):
        LogicalHttp.__init__(self, VmwareVcenterServer.vuln)

    def run_logic_grabber(self, host: str, portinfo: PortInfo, **kwargs):
        try:
            outlog = kwargs.get('outlog')
            log = f"开始扫描漏洞: {VmwareVcenterServer.vuln}"
            outlog(log)
            self._logger.debug(log)

            address = host.split(":")
            ip = address[0]
            
            url_health = f'https://{ip}/eam/healthstatus'
            headers_health = f"""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Cookie: JSESSIONID=055D48EDB2F1871F87642C363C69B03D
            Host: {ip}
            Sec-Fetch-Dest: document
            Sec-Fetch-Mode: navigate
            Sec-Fetch-Site: none
            Sec-Fetch-User: ?1
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
            """

            self._logger.debug(f"Start vmware_vcenter_server url_health:{url_health}")
            resp = self.get_resp(url_health, headers_health)
            if resp is None:
                self._logger.debug(f"Cannt connect {url_health}")
                return

            if resp.status_code == 200:
                siteinfo: SiteInfo = SiteInfo(url_health)
                respheard = ""
                for k, v in resp.headers.items():
                    respheard += f"{k}:{v}\n"
            
                siteinfo.set_httpdata(None, None, respheard, resp.text)
                portinfo.set_siteinfo(siteinfo)
            self._logger.debug(f"Succeed get vmware_vcenter_server, url_health:{url_health}")
            portinfo.banner += f'\n\n{resp.text}'
            
            url_websso = f'https://{ip}/websso/SAML2/SSO/vsphere.local?SAMLRequest='
            headers_websso = f"""
                Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                Accept-Encoding: gzip, deflate, br
                Accept-Language: zh-CN,zh;q=0.9
                Cache-Control: max-age=0
                Connection: keep-alive
                Host: {ip}
                Sec-Fetch-Dest: document
                Sec-Fetch-Mode: navigate
                Sec-Fetch-Site: none
                Sec-Fetch-User: ?1
                Upgrade-Insecure-Requests: 1
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
            """
            self._logger.debug(f"Start vmware_vcenter_server url_websso:{url_websso}")
            resp = self.get_resp(url_websso, headers_websso)
            if resp is None:
                self._logger.debug(f"Cannt connect {url_health}")
                return

            if resp.status_code == 400:
                siteinfo: SiteInfo = SiteInfo(url_websso)
                respheard = ""
                for k, v in resp.headers.items():
                    respheard += f"{k}:{v}\n"
            
                siteinfo.set_httpdata(None, None, respheard, resp.text)
                portinfo.set_siteinfo(siteinfo)
            self._logger.debug(f"Succeed vmware_vcenter_server url_websso:{url_websso}")

            portinfo.banner += f'\n\n{resp.text}'

            log = f"{VmwareVcenterServer.vuln} 漏洞扫描完成"
            outlog(log)
        except Exception as ex:
            self._logger.error(f"vmware_vcenter_server error: {ex}")


    def get_resp(self, url: str, headers: str):
        failnum = 0
        resp: Response = None
        got = False
        while True:
            try:
                p: ProxyItem = ProxyMngr.get_one_crosswall()
                proxydict = None
                if isinstance(p, ProxyItem):
                    proxydict = p.proxy_dict
                    self._logger.debug(f"proxy ip: {p._ip}, port: {p._port}")
                
                resp: Response = self._ha.get_response(
                    url,
                    verify=False,
                    headers=headers,
                    timeout=30,
                    allow_redirects=False
                )
                if resp is None:
                    self._logger.debug(f"Cannt connect {url},resp:{None}")
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

        if resp is None:
            self._logger.debug(
                f"Connect {url} fail three times, get nothing, resp: {None}")

        return resp
