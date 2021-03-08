"""represents a portinfo"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.helpers import helper_str

from ..component import Component


# class SiteComponent:
#     """represents a website component/technology stack\n
#     name: cannot be None\n
#     category: defaults to '' empty str\n
#     version: the version of the component"""
#     def __init__(self, name: str, category: str = "", version: str = None):
#         if not isinstance(name, str) or name == "":
#             raise Exception("Invalid SiteComponent.name")
#
#         self._name: str = name
#         self.category: str = category
#         self.version: str = version
#
#     def get_outputdict(self) -> dict:
#         com: dict = {}
#         com["name"] = self._name
#         if not self.category is None and self.category != "":
#             com["category"] = self.category
#         if not self.version is None and self.version != "":
#             com["version"] = self.version


class SiteInfo(object):
    """网站服务信息\n
    site: 当前网站的 域名（完整域名，非根域名）"""

    def get_banner(self) -> str:
        """return the banner that is construct by the
         full http response header and body"""
        return '{}\n{}\n'.format(
            self.__httpdata['respheader'],
            self.__httpdata['respbody'],
        )

    def __init__(self, site: str):
        if not isinstance(site, str) or site == "":
            raise Exception("Invalid site domain for SiteInfo")

        self._site: str = site
        self._location: str = None

        self.__redirects: list = []
        self.__redirects_locker = threading.RLock()

        self._title: str = None
        self._meta: str = None

        self.__httpdata_locker = threading.RLock()
        self.__httpdata: dict = {
            'reqheader': None,
            'reqbody': None,
            'respheader': None,
            'respbody': None,
        }

        self.__favicon_locker = threading.RLock()
        self.__favicon: dict = {
            'data': None,
            'hash': None,
            'location': None,
        }

        self.__ips: list = []
        self.__ips_locker = threading.RLock()

        self.__components: dict = {}
        self.__components_locker = threading.RLock()

    @property
    def location(self) -> str:
        """该网站主页的最终响应的重定向路径"""
        return self._location

    @location.setter
    def location(self, value):
        """该网站主页的最终响应的重定向路径"""
        if not isinstance(value, str) or value == "":
            raise Exception("Invalid location")
        self._location = value

    @property
    def redirects(self) -> iter:
        """yield redirect urls"""
        with self.__redirects_locker:
            for r in self.__redirects:
                yield r

    def set_redirect(self, *redir_urls: str):
        """append an url to redirect chain"""
        with self.__redirects_locker:
            for red in redir_urls:
                if not red in self.__redirects:
                    self.__redirects.append(red)

    @property
    def title(self) -> str:
        """the title of the page"""
        return self._title

    @title.setter
    def title(self, value: str):
        """the title of the page"""
        if not isinstance(value, str):
            # this could be empty str
            raise Exception("Invalid title")
        self._title = value

    @property
    def meta(self) -> str:
        """the meta of the page"""
        return self._meta

    @meta.setter
    def meta(self, value: str):
        """the meta of the page"""
        if not isinstance(value, str):
            # this could be empty str
            raise Exception("Invalid meta")
        self._meta = value

    @property
    def httpdata_reqheader(self) -> str:
        return self.__httpdata['reqheader']

    @property
    def httpdata_reqbody(self) -> str:
        return self.__httpdata['reqbody']

    @property
    def httpdata_respheader(self) -> str:
        return self.__httpdata['respheader']

    @property
    def httpdata_respbody(self) -> str:
        return self.__httpdata['respbody']

    def set_httpdata(
            self,
            reqheader: str = None,
            reqbody: str = None,
            respheader: str = None,
            respbody: str = None,
    ):
        """set http data"""
        if isinstance(reqheader, str) and not reqheader == "":
            self.__httpdata["reqheader"] = reqheader
        if isinstance(reqbody, str) and not reqbody == "":
            self.__httpdata["reqbody"] = reqbody
        if isinstance(respheader, str) and not respheader == "":
            self.__httpdata["respheader"] = respheader
        if isinstance(respbody, str) and not respbody == "":
            self.__httpdata["respbody"] = respbody

    @property
    def favicon_data(self) -> str:
        return self.__favicon['data']

    @property
    def favicon_location(self) -> str:
        return self.__favicon['location']

    @property
    def favicon_hash(self) -> str:
        return self.__favicon['hash']

    def set_favicon(
            self,
            data: [bytes, str],
            location_: str,
            hash_: str = None,
    ):
        """set favicon of the site\n
        data: the favicon image, could be bytes or base64-ed str\n
        location: the original url of the favicon image.\n
        hash: the hash code of the favicon image"""
        if data is None or not isinstance(location_, str) or location_ == "":
            raise Exception("Invalid favicon params")

        favstr = data
        if isinstance(data, bytes):
            favstr = helper_str.base64bytes(data, encoding='ascii')

        self.__favicon['data'] = favstr
        self.__favicon['location'] = location_
        self.__favicon['hash'] = hash_

    @property
    def ips(self) -> iter:
        """yield ips"""
        with self.__ips_locker:
            for ip in self.__ips:
                yield ip

    def set_ips(self, *ips):
        """set the ips that the current site domain resolved to"""
        with self.__ips_locker:
            for ip in ips:
                if not ip in self.__ips:
                    self.__ips.append(ip)

    def set_components(self, component: Component):
        """set components of current site"""
        with self.__components_locker:
            # for c in component:
            if isinstance(component, Component):
                # raise Exception("Invalid Site Component: {}".format(c))
                self.__components[component._name] = component

    #########################################
    # build banner

    def build_banner(self) -> str:
        res = "{}\n\n{}\n\n{}\n\n{}".format(self.httpdata_reqheader, "",
                                            self.httpdata_respheader,
                                            self.httpdata_respbody)

        if not res is None and res != "":
            res = "HTTP:\n" + res
        return res

    ##########################################
    # output dict

    def get_outputdict(self) -> dict:
        """return siteinfo dict"""
        siteinfo: dict = {}
        siteinfo["site"] = self._site
        if not self.location is None and self.location != "":
            siteinfo["location"] = self.location

        if len(self.__redirects) > 0:
            siteinfo["redirects"] = []
            for r in self.__redirects:
                if not r in siteinfo["redirects"]:
                    siteinfo["redirects"].append(r)
        if not self.title is None and self.title != "":
            siteinfo["title"] = self.title
        if not self.meta is None and self.meta != "":
            siteinfo["meta"] = self.meta

        # httpdata
        siteinfo["httpdata"] = {}
        if not self.httpdata_reqheader is None and self.httpdata_reqheader != "":
            siteinfo["httpdata"]["reqheader"] = self.httpdata_reqheader
        if not self.httpdata_reqbody is None and self.httpdata_reqbody != "":
            siteinfo["httpdata"]["reqbody"] = self.httpdata_reqbody
        if not self.httpdata_respheader is None and self.httpdata_respheader != "":
            siteinfo["httpdata"]["respheader"] = self.httpdata_respheader
        if not self.httpdata_respbody is None and self.httpdata_respbody != "":
            siteinfo["httpdata"]["respbody"] = self.httpdata_respbody

        # favicon
        siteinfo["favicon"] = {}
        if not self.favicon_data is None and self.favicon_data != "":
            siteinfo["favicon"]["data"] = self.favicon_data
        if not self.favicon_hash is None and self.favicon_hash != "":
            siteinfo["favicon"]["hash"] = self.favicon_hash
        if not self.favicon_location is None and self.favicon_location != "":
            siteinfo["favicon"]["location"] = self.favicon_location

        # ips
        if len(self.__ips) > 0:
            siteinfo["ips"] = []
            for i in self.__ips:
                if not i in siteinfo["ips"]:
                    siteinfo["ips"].append(i)

        # components
        if len(self.__components) > 0:
            siteinfo["component"] = []
            for c in self.__components.values():
                c: Component = c
                comdict = c.get_outputdict()
                # if not c._name in [
                #         com["name"] for com in siteinfo["component"]
                # ]:
                siteinfo["component"].append(comdict)

        return siteinfo
