"""
huawei hg532 vuln
"""

from socket import timeout
import traceback
from urllib import parse
from requests.models import Response
from proxymanagement.proxymngr import ProxyItem, ProxyMngr

from idownclient.scan.plugin.component.webalyzer import WebAlyzer
from .logicalhttp import LogicalHttp
from ....clientdatafeedback.scoutdatafeedback import PortInfo, SiteInfo


class TempScan(LogicalHttp):
    vuln = "Temp_KB"

    def __init__(self):
        LogicalHttp.__init__(self, TempScan.vuln)

    def run_logic_grabber(self, host: str, portinfo: PortInfo, **kwargs):
        try:

            funclist = [
                self.kb1,  # KB demand 210119
                self.kb2,  # KB demand 210119
            ]

            for f in funclist:
                f(host, portinfo, **kwargs)

        except Exception as ex:
            self._logger.error(f"{TempScan.vuln} error: {ex.args}")

    ###################################

    def kb1(self, host, portinfo: PortInfo, **kwargs):
        try:
            # kb20210121
            url = f"http://{host}/Login.php"

            outlog = kwargs.get("outlog")
            log = f"Start special scan: {TempScan.vuln}"
            outlog(log)

            # self._logger.debug(log)
            failnum = 0
            resp: Response = None
            html: str = None
            got = False
            redirect = False
            redirectcnt = 0
            while True:
                log = f"Start {TempScan.vuln}: {url}"
                try:
                    # p: ProxyItem = ProxyMngr.get_one_crosswall()
                    # proxydict = None
                    # if isinstance(p, ProxyItem):
                    #     proxydict = p.proxy_dict
                    #     log = log + f"proxy: {p.ip}:{p.port}"
                    #     self._logger.debug(
                    #         f"proxy ip: {p._ip}, port: {p._port}")
                    # self._logger.debug(log)
                    html = None
                    redirected_url = None
                    bs_html = bytes()
                    with self._ha.get_response(
                        url,
                        verify=False,
                        timeout=10,
                        allow_redirects=False,
                        stream=True,
                        headers="""
                    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                    Upgrade-Insecure-Requests: 1
                    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36""",
                    ) as resp:

                        if resp is None:
                            self._logger.debug(f"Access {url} failed, get nothing")
                            return
                        res_count = 0
                        for chunk in resp.iter_content(8196):
                            bs_html += chunk
                            res_count += len(chunk)
                            # 10M
                            if res_count > 10000000:
                                break
                        get_headers = resp.headers
                        html = self._ha._decode_data(get_headers, bs_html)

                        siteinfo: SiteInfo = SiteInfo(url)

                        respheard = ""
                        for k, v in get_headers.items():
                            respheard += f"{k}:{v}\n"

                        siteinfo.set_httpdata(None, None, respheard, html)

                        if portinfo.service == "unknown":
                            portinfo.service = "http"
                        portinfo.set_siteinfo(siteinfo)

                        # parse redirect
                        if (
                            resp.is_redirect
                            or resp.is_permanent_redirect
                            or 300 <= resp.status_code < 400
                        ):
                            redirected_url = self._ha.get_redirect_target(resp)
                            host = parse.urlparse(resp.url)
                            redirected_url = parse.urljoin(
                                "{}://{}".format(host.scheme, host.netloc),
                                redirected_url,
                            )
                        elif resp.url and resp.url != url:
                            redirected_url = resp.url

                        # redirect
                        redirect = False
                        # <script>DD_belatedPNG.fix('*');</script>
                        if (
                            not html is None
                            and html.__contains__("<title>登录</title>")
                            and html.lower().__contains__(
                                "<script>dd_belatedpng.fix('*');</script>"
                            )
                            and html.lower().__contains__("h-ui.admin")
                        ):
                            got = True
                            self._logger.debug(
                                f"Succeed get {TempScan.vuln}, url:{url}"
                            )
                            break
                        elif not redirected_url is None:
                            url = redirected_url
                            redirected_url = None
                            redirect = True
                            redirectcnt += 1
                            self._logger.info(f"Redirected: {url}")
                            continue
                        else:
                            failnum += 1
                            continue

                except Exception as ex:
                    self._logger.debug(f"Request {url} error: {ex}")
                    failnum += 1
                finally:
                    if not redirect or not got and failnum >= 1:
                        break
                    if redirectcnt > 5:
                        break

            log = f"{TempScan.vuln} special scan complete"
            outlog(log)

        except Exception as ex:
            self._logger.error(f"{TempScan.vuln} error: {ex.args}")

    def kb2(self, host, portinfo: PortInfo, **kwargs):
        try:
            # kb20210121
            url = f"http://{host}/admin/common/login.shtml"

            outlog = kwargs.get("outlog")
            log = f"Start special scan: {TempScan.vuln}"
            outlog(log)

            # self._logger.debug(log)

            failnum = 0
            resp: Response = None
            html: str = None
            got = False

            redirect = False
            redirectcnt = 0
            while True:
                log = f"Start {TempScan.vuln}: {url}"
                try:
                    # p: ProxyItem = ProxyMngr.get_one_crosswall()
                    # proxydict = None
                    # if isinstance(p, ProxyItem):
                    #     proxydict = p.proxy_dict
                    #     log = log + f"proxy: {p.ip}:{p.port}"
                    #     self._logger.debug(
                    #         f"proxy ip: {p._ip}, port: {p._port}")
                    # self._logger.debug(log)

                    html = None
                    bs_html = bytes()
                    # parse redirect
                    redirected_url = None
                    with self._ha.get_response(
                        url,
                        verify=False,
                        timeout=10,
                        allow_redirects=False,
                        stream=True,
                        headers="""
                    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                    Upgrade-Insecure-Requests: 1
                    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36""",
                    ) as resp:
                        if resp is None:
                            self._logger.debug(f"Access {url} failed, get nothing")
                            return
                        res_count = 0
                        for chunk in resp.iter_content(8196):
                            bs_html += chunk
                            res_count += len(chunk)
                            # 10M
                            if res_count > 10000000:
                                break
                        get_heaers = resp.headers

                        html = self._ha._decode_data(get_heaers, bs_html)

                        # record
                        # html = bs_html.decode("utf-8")
                        siteinfo: SiteInfo = SiteInfo(url)

                        respheard = ""
                        for k, v in get_heaers.items():
                            respheard += f"{k}:{v}\n"

                        siteinfo.set_httpdata(None, None, respheard, html)

                        if portinfo.service == "unknown":
                            portinfo.service = "http"
                        portinfo.set_siteinfo(siteinfo)

                        if (
                            resp.is_redirect
                            or resp.is_permanent_redirect
                            or 300 <= resp.status_code < 400
                        ):
                            redirected_url = self._ha.get_redirect_target(resp)
                            host = parse.urlparse(resp.url)
                            redirected_url = parse.urljoin(
                                "{}://{}".format(host.scheme, host.netloc),
                                redirected_url,
                            )
                        elif resp.url and resp.url != url:
                            redirected_url = resp.url

                        # redirect
                        redirect = False
                        if (
                            not html is None
                            and html.lower().__contains__("/admin/common/login.shtml")
                            and html.lower().__contains__("layui-form-item")
                        ):
                            self._logger.debug(
                                f"Succeed get {TempScan.vuln}, url:{url}"
                            )
                            got = True
                            break
                        elif not redirected_url is None:
                            url = redirected_url
                            redirected_url = None
                            redirect = True
                            redirectcnt += 1
                            self._logger.info(f"Redirected: {url}")
                            continue
                        else:
                            failnum += 1
                            continue

                except Exception as ex:
                    self._logger.debug(f"Request {url} error: {ex}")
                    failnum += 1
                finally:
                    if not redirect or not got and failnum >= 1:
                        break
                    if redirectcnt > 5:
                        break

            log = f"{TempScan.vuln} special scan complete"
            outlog(log)

        except Exception as ex:
            self._logger.error(f"{TempScan.vuln} error: {ex.args}")