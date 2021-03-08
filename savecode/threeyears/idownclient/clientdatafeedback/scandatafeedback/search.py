# -*- coding: <encoding utf-8> -*-
"""
search文件的回馈
create by judy 19/06/13
"""
from datacontract import IscanTask
from .scanfeedbackbase import ScanFeedBackBase


class Names(object):
    def __init__(self):
        self.names = {}


class City(Names):
    """
    geoinfo的city name
    """

    def __init__(self):
        Names.__init__(self)


class Continent(Names):
    """
    geoinfo的continent
    """

    def __init__(self, code):
        Names.__init__(self)
        self.code = code


class Country(Continent):
    """
    geoinfo的country
    """

    def __init__(self, code):
        Continent.__init__(self, code)


class Location(object):
    """
    geoinfo的location
    """

    def __init__(self):
        self.lat = None
        self.lng = None


# 新增province
class Province(Names):
    def __init__(self):
        Names.__init__(self)


class Geoinfo(object):
    """
    search里面的geoinfo
    """

    def __init__(self, asn):
        self.asn = asn
        # self.city = city.__dict__
        self.city = None
        self.continent = None
        self.country = None
        self.location = None
        self.province = None


# -------------------------------------------------------------------------上面是geoinfo
# class NameVersion(object):
#     """
#     name and version 这里要__dict__
#     """
#
#     def __init__(self, name, version):
#         self.name = name
#         self.version = version
#
#
# class NameVersionUrl(NameVersion):
#     """
#     name version url
#     """
#
#     def __init__(self, name, version, url):
#         NameVersion.__init__(self, name, version)
#         self.url = url


class HttpData(object):
    """
    site info的 http data
    """

    def __init__(self):
        self.reqheader = None
        self.reqbody = None
        self.respheader = None
        self.respbody = None


class SiteInfo_One(object):

    def __init__(self, httpdata: HttpData = None):
        self.site = None
        self.location = None
        self.title = None
        self.meta = None
        if httpdata is not None:
            self.httpdata = httpdata.__dict__
        # 直接添加域名信息
        self.domains: list = []
        # 直接添加ip信息
        self.ips: list = []
        # self.language = []
        # self.waf = []
        # self.server = []
        # self.webapp = []
        # self.framework = []
        self.component = []
        # self.plugin = []
        # self.db = []
        # self.frontend = []
        # 新加字段,shodan现有的
        self.redirects = []
        # {'data':xxx, 'hash':m, 'location':'https://sadas.com'}
        self.favicon = {}


class PortInfo_one(object):
    """
    search里面的portinfo
    list 使用append
    dict 使用set
    """

    def __init__(self, port, banner, service):
        self.port = port
        self.app = None
        self.banner = banner
        self.device = None
        self.extrainfo = None
        self.hostnames = None
        self.domains = None
        self.service = service
        self.version = None
        self.os = None
        # 2019-07-28T22:24:56.123456
        self.timestamp = None
        self.transport = None
        self.cpe = []
        self.tags = []
        self.link = None
        self.uptime = None
        # 下面就是一些端口上的特定信息
        self.siteinfo = []
        self.sslinfo = []
        self.ftpinfo = []
        self.sshinfo = []
        # 新增opts
        self.opts = {}
        self.vulns_sp: list = []

    def append_siteinfo(self, site_one: SiteInfo_One):
        if not isinstance(site_one, SiteInfo_One):
            raise Exception('Object is not Site_One.')
        self.siteinfo.append(site_one.__dict__)

    def append_sslinfo(self, ssl: dict):
        """
        这个主要是为了shodan
        :param ssl:
        :return:
        """
        self.sslinfo.append(ssl)

    def append_sshinfo(self, ssh: dict):
        """
        这个也主要是为了shodan
        :param ssh:
        :return:
        """
        self.sshinfo.append(ssh)

    def append_ftpinfo(self, ftp: dict):
        """
        这个也是shodan才有的
        :param ftp:
        :return:
        """
        self.ftpinfo.append(ftp)

    def append_vulns(self, vulns):
        """
        vulns可能为单个数据
        也可能为一个列表
        :param vulns:
        :return:
        """
        if isinstance(vulns, list):
            self.vulns_sp.extend(vulns)
        else:
            self.vulns_sp.append(vulns)

    def opt_set_screenshot(self, sshot):
        """
        为opt赋值screenshot
        :param sshot:
        :return:
        """
        if sshot is not None:
            self.opts['screenshot'] = sshot

    def opt_set_telnet(self, telnet):
        """
        为opt赋值telnet
        :param telnet:
        :return:
        """
        if telnet is not None:
            self.opts['telnet'] = telnet


class PortInfo(object):
    """
    search里面的portinfo
    """

    def __init__(self):
        self.portinfo = []

    def append_one(self, pinfo_one: PortInfo_one):
        if not isinstance(pinfo_one, PortInfo_one):
            raise Exception("Object is not Portinfo_one")
        self.portinfo.append(pinfo_one.__dict__)


# ----------------------------------------------------------------这上面是port的

class Search(ScanFeedBackBase):

    def __init__(self, tsk: IscanTask, ip, hostnames: list, vulns: dict, geoinfo: Geoinfo, portinfo=None):
        ScanFeedBackBase.__init__(self, tsk=tsk)
        if ip is None:
            raise Exception('Unique ip cant be None.')
        self.ip = ip
        if geoinfo is not None:
            self.geoinfo = geoinfo.__dict__
        if portinfo is not None:
            self.portinfo = portinfo.portinfo
        # 新增字段
        self.org = None
        self.isp = None
        # hostnames不可能为None
        self.hostnames = []
        for el in hostnames:
            self.hostnames.append({'name': el})
        # 但是vulns就很有可能为None了
        if vulns is not None:
            self.vulns_si = list(vulns.keys())

# -----------------------------------------------------------------扫描的结果和搜索还是会有差别
# class Scan(ScanFeedBackBase):应该不需要开新的数据结构

# class Test(object):
#
#     def _parse_host_portinfo(self, port_dict: dict):
#         pinf = PortInfo()
#         port = port_dict.get('port')
#         banner = port_dict.get('banner')
#         service = port_dict.get('service')
#         pinf_one = PortInfo_one(port, banner, service)
#         pinf_one.app = port_dict.get('app')
#         pinf_one.device = port_dict.get('device')
#         pinf_one.extrainfo = port_dict.get('extrainfo')
#         pinf_one.hostname = port_dict.get('hostname')
#         pinf_one.version = port_dict.get('version')
#         pinf_one.os = port_dict.get('os')
#         pinf.append_one(pinf_one)
#         return pinf
#
#     def _parse_web_portinfo(self, data_dict: dict):
#         pinf = PortInfo()
#         port = '80'
#         pinf_one = PortInfo_one(port, None, None)
#         http_data = HttpData()
#         http_data.reqheader = data_dict.get('headers')
#         site_one = SiteInfo_One(http_data)
#         site_one.site = data_dict.get('site')
#         site_one.title = data_dict.get('title')
#         site_one.meta = data_dict.get('description')
#         site_one.domains = data_dict.get('domains')
#         site_one.ips = data_dict.get('ip')
#         site_one.language = data_dict.get('language')
#         site_one.waf = data_dict.get('waf')
#         site_one.server = data_dict.get('server')
#         site_one.webapp = data_dict.get('webapp')
#         site_one.framework = data_dict.get('framework')
#         site_one.component = data_dict.get('component')
#         site_one.db = data_dict.get('db')
#         site_one.plugin = data_dict.get('plugin', [])
#         site_one.frontend = data_dict.get('frontend', [])
#         pinf_one.append_siteinfo(site_one)
#         pinf.append_one(pinf_one)
#         return pinf
#
#     def _parse_geoinfo(self, geodict: dict):
#         gen_asn = geodict.get('asn')
#         ginfo = Geoinfo(gen_asn)
#         ginfo.city = geodict.get('city', {})
#         if 'geoname_id' in ginfo.city:
#             ginfo.city.pop('geoname_id')
#         ginfo.continent = geodict.get('continent', {})
#         if 'geoname_id' in ginfo.continent:
#             ginfo.continent.pop('geoname_id')
#         ginfo.country = geodict.get('country', {})
#         if 'geoname_id' in ginfo.country:
#             ginfo.country.pop('geoname_id')
#         ginfo.location = geodict.get('location')
#         return ginfo
#
#     def parse_dict(self, datainfo: dict):
#         portinfo = datainfo.get('portinfo')
#         if portinfo is not None:
#             pinf = self._parse_host_portinfo(portinfo)
#         else:
#             pinf = self._parse_web_portinfo(datainfo)
#         print(pinf.__dict__)
#
#         ginfod = datainfo.get('geoinfo')
#         if ginfod is not None:
#             ginfo = self._parse_geoinfo(ginfod)
#             print(ginfo.__dict__)
#
#
# if __name__ == '__main__':
#     tt = Test()
#     dd = '''
#     {
#     "protocol": {
#         "application": "HTTP",
#         "probe": "GetRequestHost",
#         "transport": "tcp"
#     },
#     "ip": "221.182.218.209",
#     "timestamp": "2019-06-27T14:41:33",
#     "geoinfo": {
#         "city": {
#             "geoname_id": null,
#             "names": {
#                 "zh-CN": "海口",
#                 "en": "Haikou"
#             }
#         },
#         "country": {
#             "geoname_id": null,
#             "code": "CN",
#             "names": {
#                 "zh-CN": "中国",
#                 "en": "China"
#             }
#         },
#         "isp": "ChinaMobile",
#         "asn": 9808,
#         "subdivisions": {
#             "geoname_id": null,
#             "code": null,
#             "names": {
#                 "zh-CN": "海南",
#                 "en": "Hainan"
#             }
#         },
#         "location": {
#             "lat": "20.031971",
#             "lon": "110.33119"
#         },
#         "organization": "China Mobile Guangdong",
#         "aso": "Guangdong Mobile Communication Co.Ltd.",
#         "continent": {
#             "geoname_id": null,
#             "code": "AP",
#             "names": {
#                 "zh-CN": "亚洲",
#                 "en": "Asia"
#             }
#         },
#         "PoweredBy": "IPIP",
#         "base_station": "",
#         "idc": ""
#     },
#     "portinfo": {
#         "hostname": "",
#         "service": "http",
#         "extrainfo": "",
#         "version": "",
#         "device": "",
#         "os": "",
#         "port": 443,
#         "title": "301 Moved Permanently",
#         "app": "nginx",
#         "banner": ""
#     }
# }
#     '''
#
#     dd1 = '''
#         {
#     "geoinfo": {
#         "city": {
#             "geoname_id": 0,
#             "names": {
#                 "zh-CN": "",
#                 "en": ""
#             }
#         },
#         "country": {
#             "geoname_id": 6252001,
#             "code": "US",
#             "names": {
#                 "zh-CN": "美国",
#                 "en": "United States"
#             }
#         },
#         "isp": "Cloudflare",
#         "asn": 13335,
#         "subdivisions": {
#             "geoname_id": 0,
#             "code": null,
#             "names": {
#                 "zh-CN": "",
#                 "en": ""
#             }
#         },
#         "location": {
#             "lat": 37.751,
#             "lon": -97.822
#         },
#         "organization": "Cloudflare",
#         "aso": "Cloudflare, Inc.",
#         "continent": {
#             "geoname_id": 6255149,
#             "code": "NA",
#             "names": {
#                 "zh-CN": "北美洲",
#                 "en": "North America"
#             }
#         }
#     },
#     "description": "Cendien - Chengdu McKesson software consulting firm. McKesson experts with McKesson developers in Chengdu. ",
#     "language": [],
#     "title": "McKesson Software Consulting in Chengdu",
#     "ip": [
#         "104.28.15.5",
#         "104.28.14.5"
#     ],
#     "waf": [
#         {
#             "chinese": "CloudFlare",
#             "name": "CloudFlare",
#             "version": null
#         }
#     ],
#     "component": [
#         {
#             "chinese": "Page Speed",
#             "name": "Page Speed",
#             "version": "1.13.35.2"
#         }
#     ],
#     "system": [],
#     "site": "coveriant.com",
#     "db": [],
#     "headers": "asdsad",
#     "framework": [],
#     "timestamp": "2019-06-27T14:17:27.511438",
#     "keywords": "Chengdu McKesson software consulting Chengdu,  Chengdu McKesson experts, McKesson consultants ",
#     "webapp": [],
#     "server": [],
#     "domains": [
#         "cendien.com",
#         "www.cendien.com"
#     ]
# }
#     '''
#     data_dict = json.loads(dd, encoding='utf-8')
#     tt.parse_dict(data_dict)
