"""Manage cookies"""

# -*- coding:utf-8 -*-

import re
from urllib import parse

from commonbaby.helpers import helper_str
from requests.cookies import RequestsCookieJar, cookielib


class ManagedCookie:
    """Manage cookies"""
    # cookie = "Hm_lvt_3eec0b7da6548cf07db3bc477ea905ee=1533870688; \
    #    _ga=GA1.2.17492658.1533870688; _gid=GA1.2.1358769836.1533870688; \
    #    Hm_lpvt_3eec0b7da6548cf07db3bc477ea905ee=1533870698"

    # @"^((?<oneCookie>(?<name>[^,;= ]+?)=(?<value>[^;]*?)) *(;|$) *)*(?=$)"
    re_cookies = re.compile("((([^,;= ]+?)=([^;]*?)) *(;|$) *)", re.S)

    #re_cookies = re.compile("^([^,;= ]+?=[^;]*? *(;|$) *)*(?=$)", re.S)

    def __init__(self, jar: RequestsCookieJar = None):
        self._jar = None
        if not jar is None:
            self._jar = jar
        else:
            self._jar = cookielib.CookieJar()

    def add_cookies(self, domain: str, cookie: str):
        """parse cookies and add them to jar under specified domain"""
        try:
            if cookie is None or cookie == "":
                return
            if domain is None or domain == "":
                return

            matches = ManagedCookie.re_cookies.findall(cookie)
            if matches is None or len(matches) < 1:
                return
            for m in matches:
                self.add_one_cookie(domain, m[0])

        except Exception as ex:
            raise ex

    def add_one_cookie(self, domain: str, cookie: str):
        """parse one cookie and add it to cookie jar"""
        try:
            if cookie is None or cookie == "":
                return
            if domain is None or domain == "":
                return
            name, value = self._get_cookie_kvp(cookie)
            if name is None or name == '':
                raise Exception(
                    "Parse cookie key value pair faild: %s" % cookie)
            if not domain.startswith('.'):
                domain = '.' + domain
            ck = self.make_cookie(name, value, domain)

            self._jar.set_cookie(ck)
        except Exception as ex:
            raise ex

    def _get_cookie_kvp(self, cookie: str) -> (str, str):
        """parse cookie str to key-value pair"""
        k, v = helper_str.get_kvp(cookie, '=')
        if k is None or k == "" or v is None or v == "":
            return (k, v)
        v = v.rstrip().rstrip(';')
        return (k, v)

    @staticmethod
    def make_cookie(name, value, domain) -> cookielib.Cookie:
        return cookielib.Cookie(
            version=0,
            name=name,
            value=value,
            port=None,
            port_specified=False,
            domain=domain,
            domain_specified=True,
            domain_initial_dot=False,
            path="/",
            path_specified=True,
            secure=False,
            expires=None,
            discard=False,
            comment=None,
            comment_url=None,
            rest=None)

    def contains_cookie(self, name: str) -> bool:
        """check if specified cookie name exists"""
        # 只分域名，不分path
        res = False
        if name is None or name == "":
            raise Exception("Specified cookie key is None.")
        for domains in self._jar._cookies.values():
            # domains: dict = domains
            for domain in domains.values():
                # domain: dict = domain
                if domain.__contains__(name):
                    res = True
                    break
            if res:
                break
        return res

    def get_cookie_valuestr(self, name: str) -> str:
        """get the specified cookie value by name. 
        return None if not exists."""
        res: str = None
        ck = self.get_cookie_value(name)
        if not ck is None:
            res = ck.value
        return res

    def get_cookie_value(self, name: str):
        """get the specified cookie value by name. 
        return None if not exists."""
        res = None
        succ = False
        if name is None or name == "":
            raise Exception("Specified cookie key is None.")
        for domains in self._jar._cookies.values():
            # domains: dict = domains
            for domain in domains.values():
                # domain: dict = domain
                if domain.__contains__(name):
                    succ = True
                    res = domain[name]
                    break
            if succ:
                break
        return res

    def get_cookie_value_in_domain(self, domain: str, name: str):
        """get the specified cookie value by name in specified domain 
        return None if not exists."""
        res = None
        if domain is None or domain == "":
            raise Exception("Domain cannot be None.")
        if name is None or name == "":
            raise Exception("Specified cookie key is None.")
        if not self._jar._cookies.__contains__(domain):
            return res
        for dm in self._jar._cookies[domain]:
            if dm.__contains__(name):
                res = dm[name]
                break
        return res

    def get_cookie_for_domain(self, url: str):
        """return all cookies in the domain"""
        res = ""
        if url is None or url == "":
            return res

        uri = parse.urlparse(url)
        domain: str = uri.netloc
        path: str = uri.path.strip()

        if not domain.startswith('.'):
            domain = '.' + domain
        if path is None or path == "":
            path = '/'
        if not path.startswith('/'):
            path = '/' + path

        for origindomain in self._jar._cookies.items():
            if domain.endswith(origindomain[0]):
                for originpath in origindomain[1].items():
                    if path.startswith(originpath[0]):
                        for ck in originpath[1].values():
                            res = "%s%s=%s; " % (res, ck.name, ck.value)

        if res == "":
            res = None
        else:
            res = res.strip().strip(';')
        return res

    def get_all_cookie(self):
        """get all cookies in current cookie container"""
        res: str = ""
        for domain in self._jar._cookies.values():
            for path in domain.values():
                for ck in path.values():
                    res = "%s%s=%s; " % (res, ck.name, ck.value)
        return res
