"""Http access"""

# -*- coding:utf-8 -*-

import io
import re
import sys
import threading
import time
import traceback
from urllib import parse

import requests
from commonbaby import charsets
from commonbaby.helpers import helper_compress, helper_str
from requests import Request, Response

from .managedcookie import ManagedCookie
from .myhttperrorprocessor import MyHttpErrorProcessor
from .redirecthdlr import RedirectHandler
from .responseio import ResponseIO


class HttpAccess(requests.Session):
    """Provide session control in a HttpAccess object, 
    cookie manage and http protocol access functions.\n
    interval: interval time in seconds between two HTTP requests.\n
    cookie: the initial cookie str in format 'a=a; b=b; c=c...'\n
    domain: the initial domain for initial cookie\n
    """

    _DEFUALT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36"

    # content-type: text/html; charset=GB18030
    # content-type: text/html; charset="utf-8"
    re_resp_charset = re.compile(r'charset="?(.+)"?\s*?$', re.S)

    @property
    def interval(self):
        """the interval seconds between any two requests"""
        return self._interval

    @interval.setter
    def interval(self, value):
        """the interval seconds between any two requests"""
        if not type(value) in [int, float] or value <= 0:
            return
        with self._interval_locker:
            self._interval = value

    @classmethod
    def setting_bandwidth_monitor(cls):
        """settings for http upload and download bandwidth monitoring."""
        pass

    def __init__(self,
                 interval: float = 0,
                 cookie: str = None,
                 domain: str = None):

        super(HttpAccess, self).__init__()
        self._interval = 0
        if type(interval) in [int, float] and interval > 0:
            self._interval = interval
        self._interval_locker = threading.RLock()
        self._lastaccesstime: float = 0  # 上一次请求的时间

        self._defualt_ua = HttpAccess._DEFUALT_UA
        # self._opener = requests.Session()

        self._global_proxies = {}
        self._global_proxies_locker = threading.Lock()

        # make processors and opener
        self._managedCookie = ManagedCookie(self.cookies)

        if not cookie is None and isinstance(cookie, str) \
           and not domain is None and isinstance(domain, str):
            self._managedCookie.add_cookies(cookie, domain)

    def getstring(
            self,
            url: str,
            req_data: str = None,
            headers: str = None,
            encoding: str = "utf-8",
            params=None,
            json=None,
            files=None,
            auth=None,
            proxies=None,
            verify=None,
            cert=None,
            timeout=None,
    ) -> str:
        """Request, and return a tuple (html, redir). 
        which html is the response data, and the redir is 
        the redirection url if a redirection happened.\n
        Useage: \n
        ha = HttpAccess()\n
        html = ha.getstring(\n
            'https://www.google.com',\n
            headers='''\n
            accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\n
            accept-encoding:gzip, deflate, br\n
            accept-language:,zh-CN,zh;q=0.9\n
            ''')\n
        """
        html = None
        redir = None
        try:
            html, redir = self._getstring(
                url=url,
                req_data=req_data,
                headers=headers,
                encoding=encoding,
                params=params,
                json=json,
                files=files,
                auth=auth,
                proxies=proxies,
                stream=False,
                verify=verify,
                cert=cert,
                timeout=timeout,
                allow_redirects=True)

        except Exception as ex:
            raise ex
        return html

    def getstring_with_reurl(
            self,
            url: str,
            req_data: str = None,
            headers: str = None,
            encoding: str = "utf-8",
            params=None,
            json=None,
            files=None,
            auth=None,
            proxies=None,
            verify=None,
            cert=None,
            timeout=None,
    ) -> (str, str):
        """Access a url with auto redirection, and return tuple (html,redirect_url)\n
        Useage: \n
        ha = HttpAccess()\n
        html,redirect_url = ha.getstring_with_reurl(\n
            'https://www.google.com',\n
            headers='''\n
            accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\n
            accept-encoding:gzip, deflate, br\n
            accept-language:,zh-CN,zh;q=0.9\n
            ''')\n"""
        html = None
        redir = None
        try:
            html, redir = self._getstring(
                url=url,
                req_data=req_data,
                headers=headers,
                encoding=encoding,
                params=params,
                json=json,
                files=files,
                auth=auth,
                proxies=proxies,
                stream=False,
                verify=verify,
                cert=cert,
                timeout=timeout,
                allow_redirects=True)
        except Exception as ex:
            raise ex
        return (html, redir)

    def getstring_unredirect(
            self,
            url: str,
            req_data: str = None,
            headers: str = None,
            encoding: str = "utf-8",
            params=None,
            json=None,
            files=None,
            auth=None,
            proxies=None,
            verify=None,
            cert=None,
            timeout=None,
    ) -> str:
        """return (html,redirect_url)\n
        Useage: \n
        ha = HttpAccess()\n
        html,redirect_url = ha.getstring_unredirect(\n
            'https://www.google.com',\n
            headers='''\n
            accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\n
            accept-encoding:gzip, deflate, br\n
            accept-language:,zh-CN,zh;q=0.9\n
            ''')\n"""
        html = None
        redir = None
        try:
            html, redir = self._getstring(
                url=url,
                req_data=req_data,
                headers=headers,
                encoding=encoding,
                params=params,
                json=json,
                files=files,
                auth=auth,
                proxies=proxies,
                stream=False,
                verify=verify,
                cert=cert,
                timeout=timeout,
                allow_redirects=False)
        except Exception as ex:
            raise ex
        return (html, redir)

    def _getstring(
            self,
            url: str,
            req_data: str = None,
            headers: str = None,
            encoding: str = "utf-8",
            params=None,
            json=None,
            files=None,
            auth=None,
            proxies=None,
            stream=True,
            verify=None,
            cert=None,
            timeout=None,
            allow_redirects: bool = True,
    ) -> (str, str):
        """return (html, redirection url)"""
        res = None
        redirected_url: str = None
        try:
            resp: requests.Response = self.get_response(
                url=url,
                req_data=req_data,
                headers=headers,
                params=params,
                json=json,
                files=files,
                auth=auth,
                proxies=proxies,
                stream=stream,
                verify=verify,
                cert=cert,
                timeout=timeout,
                allow_redirects=allow_redirects)

            if resp.is_redirect or resp.is_permanent_redirect or 300 <= resp.status_code < 400:
                redirected_url = self.get_redirect_target(resp)
                host = parse.urlparse(resp.url)
                redirected_url = parse.urljoin("{}://{}".format(
                    host.scheme, host.netloc), redirected_url)
            elif not helper_str.is_none_or_empty(resp.url) and resp.url != url:
                redirected_url = resp.url

            resp.encoding = 'utf-8'
            if not helper_str.is_none_or_empty(encoding):
                resp.encoding = encoding
            _respheaders = self._parse_resp_headers(resp)
            res = resp.text
            # resp_data = self._decompress_data(_respheaders, resp_data)
            # res = self._decode_data(_respheaders, resp_data, encoding)
        except Exception as ex:
            raise ex
        return (res, redirected_url)

    def get_response(self,
                     url: str,
                     req_data: str = None,
                     headers: str = None,
                     params=None,
                     json=None,
                     files=None,
                     auth=None,
                     proxies=None,
                     stream=False,
                     verify=None,
                     cert=None,
                     timeout=None,
                     allow_redirects: bool = True) -> requests.Response:
        """get response stream\n
        Useage: \n
        ha = HttpAccess()\n
        resp = ha.get_response(\n
            'https://www.google.com',\n
            headers='''\n
            accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\n
            accept-encoding:gzip, deflate, br\n
            accept-language:,zh-CN,zh;q=0.9\n
            ''')\n
        print(resp.headers)\n
        print(resp.text)\n

        ########################################\n
        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary or bytes to be sent in the query
            string for the :class:`Request`.
        :param req_data: (optional) Dictionary, bytes, or file-like object to send
            in the body of the :class:`Request`.
        :param json: (optional) json to send in the body of the
            :class:`Request`.
        :param headers: (optional) Dictionary of HTTP Headers to send with the
            :class:`Request`.
        :param cookies: (optional) Dict or CookieJar object to send with the
            :class:`Request`.
        :param files: (optional) Dictionary of ``'filename': file-like-objects``
            for multipart encoding upload.
        :param auth: (optional) Auth tuple or callable to enable
            Basic/Digest/Custom HTTP Auth.
        :param timeout: (optional) How long to wait for the server to send
            data before giving up, as a float, or a :ref:`(connect timeout,
            read timeout) <timeouts>` tuple.
        :type timeout: float or tuple
        :param allow_redirects: (optional) Set to True by default.
        :type allow_redirects: bool
        :param proxies: (optional) Dictionary mapping protocol or protocol and
            hostname to the URL of the proxy.
        :param stream: (optional) whether to immediately download the response
            content. Defaults to ``False``.
        :param verify: (optional) Either a boolean, in which case it controls whether we verify
            the server's TLS certificate, or a string, in which case it must be a path
            to a CA bundle to use. Defaults to ``True``.
        :param cert: (optional) if String, path to ssl client cert file (.pem).
            If Tuple, ('cert', 'key') pair.
        :rtype: requests.Response"""
        res = None
        try:
            req = self._prepare_request(
                url=url,
                req_data=req_data,
                headers=headers,
                params=params,
                json=json,
                files=files,
                auth=auth,
            )
            resp: requests.Response = self._get_response(
                req=req,
                proxies=proxies,
                stream=stream,
                verify=verify,
                cert=cert,
                timeout=timeout,
                allow_redirects=allow_redirects)

            res = resp

        except Exception as ex:
            raise ex
        return res

    def get_response_data(self,
                          url: str,
                          req_data: str = None,
                          headers: str = None,
                          params=None,
                          json=None,
                          files=None,
                          auth=None,
                          proxies=None,
                          verify=None,
                          cert=None,
                          timeout=None,
                          allow_redirects: bool = True) -> bytes:
        """get response data bytes, this suits response 
        with small data size\n
        Useage: \n
        ha = HttpAccess()\n
        data:bytes = ha.get_response_data(\n
            'https://www.google.com',\n
            headers='''\n
            accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\n
            accept-encoding:gzip, deflate, br\n
            accept-language:,zh-CN,zh;q=0.9\n
            ''')\n
        with open('filepath', mode='wb') as fs:\n
            fs.write(data)\n
        """
        res = None
        try:
            resp: requests.Response = self.get_response(
                url=url,
                req_data=req_data,
                headers=headers,
                params=params,
                json=json,
                files=files,
                auth=auth,
                proxies=proxies,
                stream=False,
                verify=verify,
                cert=cert,
                timeout=timeout,
                allow_redirects=allow_redirects)

            _respheaders = self._parse_resp_headers(resp)
            res = resp.content
        except Exception as ex:
            raise ex
        return res

    def get_response_iter_content(self,
                                  url: str,
                                  req_data: str = None,
                                  headers: str = None,
                                  params=None,
                                  json=None,
                                  files=None,
                                  auth=None,
                                  proxies=None,
                                  verify=None,
                                  cert=None,
                                  timeout=None,
                                  allow_redirects: bool = True,
                                  chunk_size: int = 4096,
                                  decode_unicode: bool = False) -> iter:
        """get response chunck blocks as iterable.
        This returns the Response.iter_content()\n
        Useage: \n
        ha = HttpAccess()\n
        data_iter = ha.get_response_iter_content(\n
            'https://www.google.com',\n
            headers='''\n
            accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\n
            accept-encoding:gzip, deflate, br\n
            accept-language:,zh-CN,zh;q=0.9\n
            ''',\n
            chunck_size=4096,\n
            decode_unicode=False)\n
        with open('filepath', mode='wb') as fs:\n
            for bys in data_iter:\n
                fs.write(bys)\n
        """
        res = None
        try:
            resp: requests.Response = self.get_response(
                url=url,
                req_data=req_data,
                headers=headers,
                params=params,
                json=json,
                files=files,
                auth=auth,
                proxies=proxies,
                stream=False,
                verify=verify,
                cert=cert,
                timeout=timeout,
                allow_redirects=allow_redirects)

            _respheaders = self._parse_resp_headers(resp)
            res = resp.iter_content(
                chunk_size=chunk_size, decode_unicode=decode_unicode)
        except Exception as ex:
            raise ex
        return res

    def get_response_stream(
            self,
            url: str,
            req_data: str = None,
            headers: str = None,
            params=None,
            json=None,
            files=None,
            auth=None,
            proxies=None,
            verify=None,
            cert=None,
            timeout=None,
            allow_redirects: bool = True,
    ) -> ResponseIO:
        """get response as a readable httpaccess.responseio.ResponseIO\n
        Useage: \n
        ha = HttpAccess()\n
        respio = ha.get_response_stream(\n
            'https://www.google.com',\n
            headers='''\n
            accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\n
            accept-encoding:gzip, deflate, br\n
            accept-language:,zh-CN,zh;q=0.9\n
            ''')\n        
        # read all bytes at once:\n
        bs = respio.read()\n
        # or:\n
        # copy to:\n
        with open('filepath', mode='wb') as fs:\n
            respio.copy_to(fs)\n
        """
        res = None
        try:
            resp: requests.Response = self.get_response(
                url=url,
                req_data=req_data,
                headers=headers,
                params=params,
                json=json,
                files=files,
                auth=auth,
                proxies=proxies,
                stream=True,
                verify=verify,
                cert=cert,
                timeout=timeout,
                allow_redirects=allow_redirects)

            _respheaders = self._parse_resp_headers(resp)
            res: ResponseIO = ResponseIO(resp)

        except Exception as ex:
            raise ex
        return res

    def _prepare_request(
            self,
            url: str,
            req_data: str = None,
            headers: str = None,
            params=None,
            json=None,
            files=None,
            auth=None,
    ) -> requests.Request:
        res: requests.Request = None
        try:
            # _datas = self._parse_data(data)
            _reqheaders = self._parse_req_headers(headers)
            self._check_default_user_agent(_reqheaders)
            self._check_req_cookie_header(_reqheaders, url)
            self._check_other_headers(_reqheaders, url)

            req: requests.Request = None
            if req_data is None:
                req = requests.Request(
                    method='GET',
                    url=url,
                    headers=_reqheaders,
                    params=params,
                    json=json,
                    files=files,
                    auth=auth)
            else:
                data = req_data.encode('ascii')
                self._check_req_content_len(_reqheaders, data)
                req = requests.Request(
                    method='POST',
                    url=url,
                    data=data,
                    headers=_reqheaders,
                    params=params,
                    json=json,
                    files=files,
                    auth=auth)

            res = req

        except Exception as ex:
            raise ex
        return res

    def _get_response(self,
                      req: requests.Request,
                      proxies=None,
                      stream=None,
                      verify=None,
                      cert=None,
                      timeout=None,
                      allow_redirects: bool = True) -> requests.Response:
        """get http response"""
        res: requests.Response = None
        try:

            if not isinstance(req, requests.Request):
                raise Exception("Param 'req' is invalid.")

            # requests.Session will automatically deal request
            # header 'host'
            popkeys = []
            if not req.headers is None:
                for k in req.headers.keys():
                    if k.lower() == "host":
                        # req.headers.pop(k, None)
                        popkeys.append(k)
            for key in popkeys:
                req.headers.pop(key, None)

            prep = self.prepare_request(req)

            proxies = proxies or self._global_proxies

            settings = self.merge_environment_settings(prep.url, proxies,
                                                       stream, verify, cert)

            # Send the request.
            send_kwargs = {
                'timeout': timeout,
                'allow_redirects': allow_redirects,
            }
            send_kwargs.update(settings)

            # check request interval
            self._check_interval()

            resp = self.send(prep, **send_kwargs)

            res = resp
        except Exception:
            raise Exception(traceback.format_exc())
        return res

    def _check_interval(self):
        """检查请求间时间间隔，并睡眠相应的时间"""
        # 小于0表示两个请求之间不需要停顿
        if self._interval <= 0:  # 这里取值时暂时不加锁，提升性能
            return
        with self._interval_locker:
            if self._interval <= 0:
                return
            currtime = time.time()
            # 第一次请求不睡眠
            if self._lastaccesstime == 0:
                self._lastaccesstime = currtime
                return
            # 两次请求间已经间隔了>interval的时间数量
            tmp = currtime - self._lastaccesstime
            if tmp >= self._interval:
                self._lastaccesstime = currtime
                return
            time.sleep(self._interval - tmp)
            self._lastaccesstime = time.time()

    def set_global_proxies(self, proxies):
        """set default global proxies.
        :param proxies: a dict like:\n
        {
            'http': 'http://127.0.0.1:1080', 
            'https': 'https://127.0.0.1:1080', 
            'ftp': 'ftp://127.0.0.1:1080'
        }"""
        with self._global_proxies_locker:
            if not isinstance(proxies, dict):
                raise Exception("Param 'proxies' must be a dict")
            self._global_proxies = proxies

    def __resp_contains_header(self, resp: requests.Response, header: str):
        res = False
        if resp is None:
            return res
        if header is None or header == "":
            return res
        resp.headers: dict = resp.headers
        for key in resp.headers.keys():
            if key.lower() == header:
                res = True
                break
        return res

    def _parse_data(self, data: str):
        """parse str data like:
        aaa=aaa&bbb=bbb
        ...

        to 

        {
            "aaa":"aaa",
            "bbb":"bbb"
        }
        """
        res = {}
        try:
            if data is None or data == "":
                return res
            alldatas = data.split('&')
            for onedata in alldatas:
                k, v = helper_str.get_kvp(onedata, '=')
                if k is None or k == "" or v is None or v == "":
                    continue
                # do not check duplicate keys here
                res[k] = v

        except Exception as ex:
            raise ex
        return res

    def _parse_req_headers(self, headers: str):
        """parse str headers like:
        aaa:aaa
        bbb:bbb
        ...

        to 

        {
            "aaa":"aaa",
            "bbb":"bbb"
        }
        """
        res = {}
        try:
            if headers is None or headers == "":
                return res
            allheaders = headers.split('\n')
            for oneheader in allheaders:
                k, v = helper_str.get_kvp(oneheader, ':')
                if k is None or k == "" or v is None or v == "":
                    continue
                # do not check duplicate keys here
                res[k.strip()] = v.strip()

        except Exception as ex:
            raise ex
        return res

    def _check_default_user_agent(self, headers: {}):
        """check if headers contains user-agent header, 
        then change the default user-agent. If not contains,
        add defualt user-agent header to headers"""
        if headers is None:
            headers = {}

        if len(headers) < 1:
            headers["user-agent"] = self._defualt_ua

        if headers.__contains__("user-agent"):
            self._defualt_ua = headers["user-agent"]
        elif headers.__contains__("User-Agent"):
            self._defualt_ua = headers["User-Agent"]
        else:
            headers["user-agent"] = self._defualt_ua.strip()

    def _check_req_cookie_header(self, headers: {}, url: str):
        """check if cookies were set"""
        if url is None or url == "":
            raise Exception("Url cannot be None.")
        if headers is None:
            headers = {}
        if len(headers) < 1:
            return

        cookies = self._managedCookie.get_cookie_for_domain(url)
        if cookies is None or cookies == "":
            return

        cookie_key = None
        if headers.__contains__("cookie"):
            cookie_key = "cookie"
        elif headers.__contains__("Cookie"):
            cookie_key = "Cookie"
        else:
            cookie_key = "cookie"

        headers[cookie_key] = cookies.strip()

    def _check_req_content_len(self, headers: {}, req_data: bytes):
        """check if request data is not None, add the Content-Length header."""

        header_key = "content-length"
        if headers.__contains__("Content-Length"):
            header_key = "Content-Length"
        if headers.__contains__("content-length"):
            header_key = "content-length"

        if req_data is None or len(req_data) < 1:
            if headers.__contains__(header_key):
                headers.pop(header_key)
        else:
            if not headers.__contains__(header_key):
                headers[header_key] = str(len(req_data))

    def _check_other_headers(self, headers: {}, url: str):
        """check host headers and blablabla..."""
        # check host
        return
        # if not url is None and not url == "":
        #     uri = parse.urlparse(url)
        #     if headers.__contains__("host"):
        #         headers["host"] = uri.netloc.strip()
        #     elif headers.__contains__("Host"):
        #         headers["Host"] = uri.netloc.strip()
        #     else:
        #         headers["host"] = uri.netloc.strip()

    def _parse_resp_headers(self, resp: requests.Response) -> {}:
        """Parse response headers from HTTPResponse and return a {}"""
        res = {}
        if resp is None or resp.headers is None:
            return res
        for h in resp.headers.items():
            res[h[0].lower()] = h[1]
        return res

    def _decompress_data(self, respheaders, respdata: bytes) -> str:
        """decompress data and return str"""
        res = None
        if respheaders is None or respdata is None:
            return res

        compmode = "Text"
        if respheaders.__contains__("content-encoding"):
            compmode = respheaders["content-encoding"]
        if compmode is None:
            compmode = "Text"

        if compmode == "Text":
            res = respdata
        elif compmode == "gzip":
            res = helper_compress.gzip_decompress(respdata)
        elif compmode == "deflate":
            res = helper_compress.deflate_decompress(respdata)

        return res

    def _decode_data(self,
                     respheaders,
                     respdata: bytes,
                     encoding: str = 'utf-8'):
        """decode data useing specified charset or the charset in HTTPResponse"""
        res = None
        if respdata is None:
            return res
        charset = "utf-8"
        if respheaders.__contains__(
                "content-type") and "charset=" in respheaders["content-type"]:
            match = HttpAccess.re_resp_charset.search(
                respheaders["content-type"])
            if not match is None:
                tmp = match.group(1)
                # if charsets.contains_charset(tmp):
                charset = tmp
        elif not encoding is None and not encoding == "":
            charset = encoding
        else:
            charset = 'utf-8'

        res = respdata.decode(charset)
        return res
