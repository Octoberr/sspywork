"""
处理ip的一些工具，
因为要增加的东西可能有点多
所以目前直接在这里使用静态方法
create by judy 20200707
"""
from IPy import IP
import re
from subprocess import Popen, PIPE
import traceback

# 保留ip地址可扩展
reserved_ip = [
    IP('10.0.0.0/8'),
    IP('127.0.0.0/8'),
    IP('172.16.0.0/12'),
    IP('192.0.0.0/24'),
    IP('192.168.0.0/16'),
    IP('198.18.0.0/15'),
]


class IpProcessTools(object):

    def __init__(self):
        pass

    @staticmethod
    def judge_reserved_ip_addresses(ip: str):
        """
        判断一个ip是否为保留ip地址
        """
        #  默认不是保留ip
        res = False
        try:
            ip_ipy = IP(ip)
        except:
            return res
        for el in reserved_ip:
            if ip_ipy in el:
                res = True
                break
        return res

    @staticmethod
    def ping_domain(mail_domian):
        """
        根据mx查询到的domain，去ping一下获取到当前的ip
        根据操作系统的不同，使用不同的正则去提取
        nslookup和ping都是采用dns解析域名的，所以直接使用ping
        :param mail_domian:
        :return:
        """
        re_ip = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
        res = None
        proc = None
        try:
            proc = Popen(f'ping -c 2 {mail_domian}', stdout=PIPE, shell=True)
            outs, errs = proc.communicate(timeout=10)
            res = outs.decode('utf-8')
        except:
            print(f"Linux ping result error, err:{traceback.format_exc()}")
            res = None
        finally:
            if proc is not None:
                proc.kill()

        if res is not None:
            ips: list = re_ip.findall(res)
            if len(ips) > 0:
                return ips[0]
        else:
            return res

    @staticmethod
    def judge_ip_or_domain(hosts: list):
        """
        判断host是否是domain或者是ip
        如果是domain的话需要找出ip
        """
        new_host = []
        domain_ip_dict = {}
        for el in hosts:
            # ip和domain必须是string
            if not isinstance(el, str):
                continue
            # 如果是domain则去拿ip
            if bool(re.search('[a-z]', el)):
                ip = IpProcessTools.ping_domain(el)
                if ip is not None:
                    new_host.append(ip)
                    domain_ip_dict[ip] = el
                    continue
            else:
                # 上面的步骤都不会报错，所以把剩下的直接加入列表即可
                new_host.append(el)
        return new_host, domain_ip_dict
