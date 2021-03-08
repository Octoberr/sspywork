"""represents a whoisr info"""

# -*- coding:utf-8 -*-

from datacontract.iscoutdataset.iscouttask import IscoutTask


class Whoisr(object):
    """represents a whoisr info.
    task: IScoutTask\n
    level: the recursion level\n
    domain: the domain which registered by object"""

    def __init__(self, task: IscoutTask, level: int, domain: str):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid iscouttask")
        if not isinstance(level, int):
            raise Exception("Invalid level")
        if not isinstance(domain, str) or domain == '':
            raise Exception("Invalid domain for whois info")

        self._task: IscoutTask = task
        self._level: int = level

        self._domain: str = domain

        self.registrant: str = None
        self.registrar: str = None
        self.registtime: str = None
        self.expiretime: str = None

        self._dns_servers: dict = {}
        # self._dns_servers_locker=threading.RLock()

    def set_dns_server(self, dns_server_ip: str):
        if not isinstance(
                dns_server_ip, str
        ) or dns_server_ip == '' or dns_server_ip in self._dns_servers:
            return

        # 暂时不加锁，太耗性能，后面有遇到异步添加再加锁
        # with self._dns_servers_locker
        self._dns_servers[dns_server_ip] = None

    def get_outputdict(self) -> dict:
        """
        这里用来获取whoisr输出的字典，免得到处去写了
        :return:
        """
        wrdict: dict = {}
        wrdict["domain"] = self._domain
        if isinstance(self.registrant, str) and not self.registrant == "":
            wrdict["registrant"] = self.registrant
        if isinstance(self.registrar, str) and not self.registrar == "":
            wrdict["registrar"] = self.registrar
        if isinstance(self.registtime, str) and not self.registtime == "":
            wrdict["registtime"] = self.registtime
        if isinstance(self.expiretime, str) and not self.expiretime == "":
            wrdict["expiretime"] = self.expiretime
        if len(self._dns_servers) > 0:
            wrdict["dns"] = [d for d in self._dns_servers.keys()]
        return wrdict
