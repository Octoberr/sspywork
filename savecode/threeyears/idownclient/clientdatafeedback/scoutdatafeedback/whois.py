"""represents a whois info"""

# -*- coding:utf-8 -*-

import threading

from datacontract.iscoutdataset.iscouttask import IscoutTask


class Whois(object):
    """represents a whois info"""

    def __init__(self, task: IscoutTask, level: int, registrar: str, registtime: str):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid iscouttask")
        if not isinstance(level, int):
            raise Exception("Invalid level")
        if not isinstance(registrar, str) or registrar == '':
            raise Exception("Invalid registrar for whois info")
        if not isinstance(registtime, str) or registtime == '':
            raise Exception("Invalid registtime for whois info")

        self._task: IscoutTask = task
        self._level: int = level

        self._registrar: str = registrar
        self.registrant: str = None
        self._registtime: str = registtime

        self.registraremail: str = None
        self.registrarphone: str = None
        self.registraraddr: str = None

        self.registrantorg: str = None
        self.registrantemail: str = None
        self.registrantphone: str = None
        self.registrantaddr: str = None

        self.expiretime: str = None
        self.infotime: str = None

        self._dns_servers: dict = {}
        # self._dns_servers_locker=threading.RLock()

    def set_dns_server(self, dns_server_ip: str):
        if not isinstance(dns_server_ip, str) \
                or dns_server_ip == '' \
                or self._dns_servers.__contains__(dns_server_ip):
            return

        # 暂时不加锁，太耗性能，后面有遇到异步添加再加锁
        # with self._dns_servers_locker
        self._dns_servers[dns_server_ip] = None

    def get_whois_outputdict(self) -> dict:
        """生成当前whois的字典"""

        whoisdict = {}
        whoisdict["registrar"] = self._registrar
        if isinstance(self.registraremail,
                      str) and not self.registrantemail == '':
            whoisdict["registraremail"] = self.registraremail
        if isinstance(self.registrarphone,
                      str) and not self.registrarphone == '':
            whoisdict["registrarphone"] = self.registrarphone
        if isinstance(self.registraraddr,
                      str) and not self.registraraddr == '':
            whoisdict["registraraddr"] = self.registraraddr
        # registrant
        whoisdict["registrant"] = self.registrant
        if isinstance(self.registrantorg,
                      str) and not self.registrantorg == '':
            whoisdict["registrantorg"] = self.registrantorg
        if isinstance(self.registrantemail,
                      str) and not self.registrantemail == '':
            whoisdict["registrantemail"] = self.registrantemail
        if isinstance(self.registrantphone,
                      str) and not self.registrantphone == '':
            whoisdict["registrantphone"] = self.registrantphone
        if isinstance(self.registrantaddr,
                      str) and not self.registrantaddr == '':
            whoisdict["registrantaddr"] = self.registrantaddr
        if isinstance(self._registtime,
                      str) and not self._registtime == '':
            whoisdict["registtime"] = self._registtime
        if isinstance(self.expiretime,
                      str) and not self.expiretime == '':
            whoisdict["expiretime"] = self.expiretime
        if isinstance(self.infotime,
                      str) and not self.infotime == '':
            whoisdict["infotime"] = self.infotime
        # dns
        if isinstance(self._dns_servers,
                      dict) and len(self._dns_servers) > 0:
            whoisdict["dns"] = []
            for dns in self._dns_servers.keys():
                whoisdict["dns"].append(dns)

        return whoisdict
