"""Control redirect"""

# -*- coding:utf-8 -*-

import string
from http.client import HTTPResponse
from urllib import request
from urllib.error import HTTPError, URLError
from urllib.parse import (quote, splitattr, splithost, splitpasswd, splitport,
                          splitquery, splittag, splittype, splituser,
                          splitvalue, to_bytes, unquote, unquote_to_bytes,
                          unwrap, urljoin, urlparse, urlsplit, urlunparse)


class RedirectHandler(request.HTTPRedirectHandler):
    """Control redirect"""

    def __init__(self, allow_redirect: bool = True, *args, **kwargs):
        super(RedirectHandler, self).__init__(*args, **kwargs)
        self.allow_redirect = True
        if isinstance(allow_redirect, bool):
            self.allow_redirect = allow_redirect

    def http_error_301(self, req, fp, code, msg, headers):
        if self.allow_redirect:
            return super(RedirectHandler, self).http_error_301(
                req, fp, code, msg, headers)
            # # return super(RedirectHandler, self).http_error_301(
            # #     req, fp, code, msg, headers)
            # if "location" in headers:
            #     newurl = headers["location"]
            # elif "uri" in headers:
            #     newurl = headers["uri"]
            # else:
            #     return

            # # fix a possible malformed URL
            # urlparts = urlparse(newurl)

            # # For security reasons we don't allow redirection to anything other
            # # than http, https or ftp.

            # if urlparts.scheme not in ('http', 'https', 'ftp', ''):
            #     raise HTTPError(
            #         newurl, code,
            #         "%s - Redirection to url '%s' is not allowed" % (
            #             msg, newurl),
            #         headers, fp)

            # if not urlparts.path and urlparts.netloc:
            #     urlparts = list(urlparts)
            #     urlparts[2] = "/"
            # newurl = urlunparse(urlparts)

            # # http.client.parse_headers() decodes as ISO-8859-1.  Recover the
            # # original bytes and percent-encode non-ASCII bytes, and any special
            # # characters such as the space.
            # newurl = quote(
            #     newurl, encoding="iso-8859-1", safe=string.punctuation)
            # newurl = urljoin(req.full_url, newurl)
            # m = req.get_method()

            # if (not (code in (301, 302, 303, 307) and m in ("GET", "HEAD")
            #          or code in (301, 302, 303) and m == "POST")):
            #     raise HTTPError(req.full_url, code, msg, headers, fp)

            # newurl = newurl.replace(' ', '%20')
            # CONTENT_HEADERS = ("content-length", "content-type")
            # newheaders = dict((k, v) for k, v in req.headers.items()
            #                   if k.lower() not in CONTENT_HEADERS)

            # req: request.Request = req
            # fp: HTTPResponse = fp
            # if req.full_url == newurl:
            #     return self.parent._open(req, data=req._data)

            # newreq = request.Request(newurl, headers=newheaders)
            # if newreq is None:
            #     return fp

            # fp.read()
            # fp.close()

            # return self.parent.open(newreq, timeout=req.timeout)
        else:
            return fp

    def http_error_302(self, req, fp, code, msg, headers):
        if self.allow_redirect:
            return super(RedirectHandler, self).http_error_302(
                req, fp, code, msg, headers)
        else:
            return fp

    def http_error_303(self, req, fp, code, msg, headers):
        if self.allow_redirect:
            return super(RedirectHandler, self).http_error_303(
                req, fp, code, msg, headers)
        else:
            return fp

    def http_error_307(self, req, fp, code, msg, headers):
        if self.allow_redirect:
            return super(RedirectHandler, self).http_error_307(
                req, fp, code, msg, headers)
        else:
            return fp

    # def redirect_request(self, req, fp, code, msg, headers, newurl):
    #     if self.allow_redirect:
    #         return super(RedirectHandler, self).redirect_request(
    #             req, fp, code, msg, headers, newurl)
    #     else:
    #         return None
