"""
iscan 的cmd实在是太多了，分一个文件出来写
create by judy 2019/06/25

iscan的stratagy和idown的不一样，是搜索条件预置，所以只取已有的
"""


class Port(object):
    def __init__(self, port, flag='tcp'):
        self.port = port
        self.flag = flag


class Scan(object):
    def __init__(self, scan_data: dict):
        self.location = scan_data.get('location')
        # 这个是扫描的默认端口，在cmd_policy_default哪里可以配置默认的端口，这里的端口是无效的
        ports = scan_data.get('ports', [22, 80, 443])
        # 前端是所有值都传了一遍，所以如果为None需要手动赋值
        if ports is None:
            ports = []
        self.ports = self._process_port(ports)
        # ports现在改版了分为tcp和udp
        # 如果前端没有改那么我就改
        # if len(self.ports) == 0:
        #     self.ports = None
        self.hosts = scan_data.get('hosts')
        # 新增vuls by judy 2020/09/17
        vuls = scan_data.get('vuls', [])
        if vuls is None:
            vuls = []
        self.vuls = vuls

    def _process_port(self, ports: list):
        """
        这个是需要支持端口段，[10,11,12-80]
        需要单独处理下端口
        :param ports:
        :return:
        """
        res = []
        # 默认的flag都是tcp
        flag = 'tcp'
        for el in ports:
            if isinstance(el, str):
                # 判断是tcp还是udp
                if el.lower().startswith('u'):
                    flag = 'udp'
                    port = el[el.index(':') + 1:]
                else:
                    flag = 'tcp'
                    port = el
                if '-' in port:
                    tmprange = port.split('-')
                    for rp in range(int(tmprange[0].strip()), int(tmprange[1].strip()) + 1):
                        if rp > 65535:
                            continue
                        res.append(Port(rp, flag))
                else:
                    res.append(Port(int(port), flag))
            else:
                res.append(Port(int(el), flag))
        return res

    def fill_defscan(self, defscan):
        if self.location is None:
            self.location = defscan.location
        if self.ports is None or len(self.ports) == 0:
            self.ports = defscan.ports
        if self.hosts is None:
            self.hosts = defscan.hosts


class Search(object):
    @property
    def searchdict(self):
        """
        根据实际情况使用最多的是dict
        所以就用这就好
        :return:
        """
        return self._searchdict

    def __init__(self, search_data: dict):
        self._searchdict = search_data
        self.filter = search_data.get('filter', {})
        self.count = search_data.get('count')
        self.index = search_data.get('index', 1)
        # self.app = search_data.get('app')
        # self.ver = search_data.get('ver')
        # self.device = search_data.get('device')
        # self.os = search_data.get('os')
        # self.service = search_data.get('service')
        # self.ip = search_data.get('ip')
        # self.cidr = search_data.get('cidr')
        # self.hostname = search_data.get('hostname')
        # self.port = search_data.get('port')
        # self.city = search_data.get('city')
        # self.state = search_data.get('state')
        # self.country = search_data.get('country')
        # self.asn = search_data.get('asn')
        # self.header = search_data.get('header')
        # self.keywords = search_data.get('keywords')
        # self.desc = search_data.get('desc')
        # self.title = search_data.get('title')
        # self.site = search_data.get('site')

    def fill_defsearch(self, defsearch):
        if self.count is None:
            self.count = defsearch.count
        if self.index is None:
            self.index = defsearch.index


class StratagyScan(object):
    @property
    def stratagyscan_dict(self):
        return self.__stratagrsacn_dict

    def __init__(self, stratagyscan_json: dict):
        _scan_data = stratagyscan_json.get('scan')
        if _scan_data is None:
            self.scan = _scan_data
        else:
            self.scan = Scan(_scan_data)

        _search_data = stratagyscan_json.get('search')
        if _search_data is None:
            self.search = _search_data
        else:
            self.search: Search = Search(_search_data)
        # 需要一份完整的dict
        self.__stratagrsacn_dict = stratagyscan_json

    def fill_defstratagyscan(self, defstratagyscan):
        if self.scan is None:
            self.scan = defstratagyscan.scan
        else:
            self.scan.fill_defscan(defstratagyscan.scan)
        self.__stratagrsacn_dict['scan'] = self.scan.__dict__

        if self.search is None:
            self.search: Search = defstratagyscan.search
        else:
            self.search.fill_defsearch(defstratagyscan.search)
        self.__stratagrsacn_dict['search'] = self.search.__dict__
