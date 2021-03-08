"""
zoomeye插件的编写，据说是要按照cmd里面的设置来
虽然我目前还不知道怎么写
但是可以先写着
create by judy 2019/06/26
"""
import json
import threading
import time

from commonbaby.httpaccess import HttpAccess

from datacontract import IscanTask
from idownclient.clientdatafeedback.scandatafeedback import PortInfo, PortInfo_one, HttpData, SiteInfo_One, Geoinfo, \
    Search
from idownclient.config_spiders import zoomeyeconf
from .scanplugbase import ScanPlugBase


class ZoomEye(ScanPlugBase):
    __is_initialed: bool = False
    __init_locker = threading.RLock()
    _accesstoken = None

    @classmethod
    def __static_init(cls):
        if cls.__is_initialed:
            return
        with cls.__init_locker:
            if cls.__is_initialed:
                return
            if cls._get_accesstoken():
                cls.__is_initialed = True
                return
            else:
                raise Exception('Init failed,canot get accesstoken')

    def __init__(self, tsk: IscanTask):
        ScanPlugBase.__init__(self, tsk)

        ZoomEye.__static_init()

        # api的账号信息
        self._accesstoken = ZoomEye._accesstoken

        # 主机搜索过滤器
        self.host_filter = [
            'app', 'ver', 'device', 'os', 'service', 'ip', 'cidr', 'hostname',
            'port', 'city', 'country', 'asn'
        ]
        self.web_filter = [
            'app', 'header', 'keywords', 'desc', 'title', 'ip', 'site', 'city',
            'country'
        ]

    @classmethod
    def _get_accesstoken(cls):
        """
        首先需要账号登陆获取token
        :return:
        """
        # res = False
        _user = zoomeyeconf.get('username')
        _password = zoomeyeconf.get('password')
        try:
            url = "https://api.zoomeye.org/user/login"
            postdata = f'{{"username": "{_user}","password": "{_password}"}}'
            ha = HttpAccess()
            html = ha.getstring(url, postdata)
            if html is None:
                raise Exception("Get accesstoken failed")
            js = json.loads(html)
            accesstoken = js["access_token"]
            cls._accesstoken = accesstoken
            res = True
        except Exception as ex:
            res = False
        return res

    def _get_cmd_fileter(self, condition: list):
        """
        获取cmd中的查询条件
        :return:
        """
        filter_dict = self.task.cmd.stratagyscan.search.filter
        query = ''
        for k, v in filter_dict.items():
            if k == 'keyword': k = 'keywords'
            if v is not None and k in condition:
                query += f'{k}:{v}%20'
        return query.rstrip('%20')

    def _parse_host_portinfo(self, port_dict: dict):
        pinf = PortInfo()
        port = port_dict.get('port')
        banner = port_dict.get('banner')
        service = port_dict.get('service')
        pinf_one = PortInfo_one(port, banner, service)
        pinf_one.app = port_dict.get('app')
        pinf_one.device = port_dict.get('device')
        pinf_one.extrainfo = port_dict.get('extrainfo')
        pinf_one.hostname = port_dict.get('hostname')
        pinf_one.version = port_dict.get('version')
        pinf_one.os = port_dict.get('os')
        pinf.append_one(pinf_one)
        return pinf

    def _parse_web_portinfo(self, data_dict: dict):
        pinf = PortInfo()
        port = '80'
        pinf_one = PortInfo_one(port, None, 'http')
        http_data = HttpData()
        http_data.reqheader = data_dict.get('headers')
        site_one = SiteInfo_One(http_data)
        site_one.site = data_dict.get('site')
        site_one.title = data_dict.get('title')
        site_one.meta = data_dict.get('description')
        site_one.domains = data_dict.get('domains')
        site_one.ips = data_dict.get('ip')
        site_one.language = data_dict.get('language')
        site_one.waf = data_dict.get('waf')
        site_one.server = data_dict.get('server')
        site_one.webapp = data_dict.get('webapp')
        site_one.framework = data_dict.get('framework')
        site_one.component = data_dict.get('component')
        site_one.db = data_dict.get('db')
        site_one.plugin = data_dict.get('plugin', [])
        site_one.frontend = data_dict.get('frontend', [])
        pinf_one.append_siteinfo(site_one)
        pinf.append_one(pinf_one)
        return pinf

    def _parse_geoinfo(self, geodict: dict):
        gen_asn = geodict.get('asn')
        ginfo = Geoinfo(gen_asn)
        ginfo.city = geodict.get('city', {})
        if 'geoname_id' in ginfo.city:
            ginfo.city.pop('geoname_id')
        ginfo.continent = geodict.get('continent', {})
        if 'geoname_id' in ginfo.continent:
            ginfo.continent.pop('geoname_id')
        ginfo.country = geodict.get('country', {})
        if 'geoname_id' in ginfo.country:
            ginfo.country.pop('geoname_id')
        ginfo.location = geodict.get('location')
        return ginfo

    def _parse_dict(self, datainfo: dict):
        portinfo = datainfo.get('portinfo')
        if portinfo is not None:
            pinf = self._parse_host_portinfo(portinfo)
        else:
            pinf = self._parse_web_portinfo(datainfo)

        ginfod = datainfo.get('geoinfo')
        if ginfod is not None:
            ginfo = self._parse_geoinfo(ginfod)
        else:
            # 没有获取到数据那么就为None
            ginfo = ginfod
        # --------------------------------
        # ip有可能有多个
        rdns = datainfo.get('rdns')
        if rdns is not None and not isinstance(rdns, list):
            # 目前拿到的rdns是只有一个，所以
            rdns = [rdns]

        ip = datainfo.get('ip')
        if isinstance(ip, list):
            for ip_one in ip:
                sinfo = Search(self.task, ip_one, rdns, ginfo, pinf)
                yield sinfo.__dict__
        else:
            sinfo = Search(self.task, ip, rdns, ginfo, pinf)
            yield sinfo.__dict__

    def _search_host(self, pagestart):
        """
        host可以扫描端口，所以当条件里面有端口时只调用这个方法
        :return:
        """
        page = pagestart
        query = self._get_cmd_fileter(self.host_filter)
        if query == '':
            # 表示没有符合条件的查询
            self._logger.info(f'No zoomeye query criteria match.')
            return
        while True:
            url = f'https://api.zoomeye.org/host/search?query={query}&page={page}'
            try:
                html = self._ha.getstring(
                    url, headers=f'''Authorization: JWT {self._accesstoken}''')
                if html is None or html == '':
                    return
                h_dict = json.loads(html)
                matchs = h_dict.get('matches')
                if matchs is None or matchs == []:
                    return
                for match in matchs:
                    for el in self._parse_dict(match):
                        yield el
            except Exception as ex:
                self._logger.error(f"Search host will exit, reason:{ex}")
                return
            finally:
                time.sleep(1)
                # 翻页
                page += 1

    def _search_web(self, pagestart):
        """
        web默认的是80端口，所以可能扫描不到端口
        :return:
        """
        page = pagestart
        query = self._get_cmd_fileter(self.web_filter)
        if query == '':
            # 没有符合要求的查询条件
            self._logger.error(f'No zoomeye query criteria match.')
            return
        while True:
            url = f'https://api.zoomeye.org/web/search?query={query}&page={page}'
            try:
                html = self._ha.getstring(
                    url, headers=f'''Authorization: JWT {self._accesstoken}''')
                if html is None or html == '':
                    return
                w_dict = json.loads(html)
                matchs = w_dict.get('matches')
                if matchs is None or matchs == []:
                    return
                for match in matchs:
                    for el in self._parse_dict(match):
                        yield el
            except Exception as ex:
                self._logger.error(f"Search web will exit, reason:{ex}")
                return
            finally:
                time.sleep(1)
                # 翻页
                page += 1

    def _download_data(self):
        """
        子类自己的下载流程
        :return:
        """
        page_start = int(self.task.cmd.stratagyscan.search.index)

        for sd in self._search_host(page_start):
            if self.count >= self.count_limit:
                return
            yield sd
            self.count += 1
        for wd in self._search_web(page_start):
            if self.count >= self.count_limit:
                return
            yield wd
            self.count += 1
