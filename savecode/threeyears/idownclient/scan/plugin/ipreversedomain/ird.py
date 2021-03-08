"""
ip反查域名
目前有两种方式，
1、nslookup ptr
2、bing api查询
create by judy 2020/06/19
扫描专用，直接承接zgrab2的数据,直接在portinfo里增加数据
"""


class IRD(object):

    @staticmethod
    def ip_ptr_domain(service_dict: dict):
        """
        ptr查询域名记录
        """
        # for ip, portinfo in service_dict.items():
        pass


    @staticmethod
    def ip_bing_domain(ip: str) -> list:
        """
        bing domain记录
        """
        pass
