"""represents an ip with openning ports"""

# -*- coding:utf-8 -*-

import threading

from datacontract.iscoutdataset.iscouttask import IscoutTask


class RangeCHost(object):
    """C段探测到的存活主机\n
    represents an ip with openning ports.\n
    task: IScoutTask\n
    level: the recursion level\n
    ip: str 存活主机的IP地址"""
    def __init__(self, task: IscoutTask, level: int, ip: str):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid iscouttask")
        if not isinstance(level, int):
            raise Exception("Invalid level")
        if not isinstance(ip, str) or ip == '':
            raise Exception("Invalid ip for rangeC detect")

        self._task: IscoutTask = task
        self._level: int = level

        # current fields
        self._ip: str = ip
        self._ports: dict = {}
        self._ports_locker = threading.RLock()

        self.iptype: str = 'ipv4'

    def __len__(self):
        res = 1
        with self._ports_locker:
            res += len(self._ports)
        return res

    def set_port(self, port: int, transport: str = "tcp", service=None):
        """设置 C段探测到的 当前存活主机 开放的端口\n
        port: 端口"""
        if not isinstance(port, int) or port < 0 or port > 65535:
            return
        if self._ports.__contains__(port):
            return
        with self._ports_locker:
            if self._ports.__contains__(port):
                return
            self._ports[port] = (port, transport, service)

    def merge(self, rangechost):
        """merge another RangeCHost object into current one, 
        and return the current RangeCHost instance"""
        if not isinstance(rangechost, RangeCHost):
            return self

        if rangechost._ip != self._ip:
            return self

        if len(rangechost._ports) < 1:
            return self

        for p, t, s in rangechost._ports.values():
            if not self._ports.__contains__(p):
                self._ports[p] = (p, t, s)
            else:
                p1, t1, s1 = self._ports[p]
                # 先简单搞了，如果当前值有为None的，
                # 且新数据没有为None的，就覆盖替换整个结果，不能只替换一部分。
                if (not t is None and not s is None) and (t1 is None
                                                          or s1 is None):
                    self._ports[p] = (p, t, s)

        return self

    def get_outputdict(self) -> dict:
        """return rangec detect data dict"""
        res: dict = {}
        res["ip"] = self._ip
        if len(self._ports) < 1:
            return res

        if not res.__contains__("ports"):
            res["ports"] = []
        for p, t, s in self._ports.values():
            res["ports"].append({
                "port": p,
                "transport": t,
                "service": s,
            })

        return res
