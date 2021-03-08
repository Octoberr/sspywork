"""
存储side site的一些信息
create by judy 2019/11/15
"""


class SideSite(object):

    def __init__(self, host, ip, hosttype, port, isssl):
        if host is None:
            raise Exception('host cant be None')
        self.host = host
        if ip is None:
            raise Exception('ip cant be None')
        self.ip = ip
        if hosttype is None:
            raise Exception('hosttype cant be None')
        self.hosttype = hosttype
        if port is None:
            raise Exception('port cant be None')
        self.port = port
        if isssl is None:
            raise Exception('isssl cant be None')
        self.isssl = isssl
        self.url = None

    def get_sidesite_output_dict(self) -> dict:
        """
        确定side site的输出格式
        :return:
        """
        side_site_dict = {}
        side_site_dict['host'] = self.host
        side_site_dict['ip'] = self.ip
        side_site_dict['hosttype'] = self.hosttype
        side_site_dict['port'] = self.port
        side_site_dict['isssl'] = self.isssl
        # 新增url，方便界面提取节点，by judy 2020/07/21
        side_site_dict['url'] = self.url
        return side_site_dict
