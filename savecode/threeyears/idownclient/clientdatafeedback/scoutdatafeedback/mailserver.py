"""represents a mailserver info"""

# -*- coding:utf-8 -*-

import threading

import IPy
from commonbaby.helpers import helper_domain

from datacontract.iscoutdataset.iscouttask import EObjectType, IscoutTask

# from .scoutfeedbackbase import ScoutFeedBackBase


# class MailServer(ScoutFeedBackBase)
class MailServer(object):
    """represents a whois info\n
    邮服地址有个host字段，实际上就是一个 域名，或IP，这个host需要
    拿去进行下一步侦察。\n
    servertype: "IMAP" or "POP"\n
    host: 目标邮服地址的 域名或IP地址"""
    def __init__(
            self,
            task: IscoutTask,
            level: int,
            host: str,
            servertype: str,
    ):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid iscouttask")
        if not isinstance(level, int):
            raise Exception("Invalid level")
        if not isinstance(host, str) or host == '':
            raise Exception("Invalid host for MailServer")
        if not isinstance(servertype,
                          str) or not servertype in ('POP', 'IMAP', 'SMTP'):
            raise Exception("Invalid mailserver for MailServer")

        # 邮服地址有个host字段，实际上就是一个 域名，或IP，这个host需要
        # 拿去进行下一步侦察。看后面需求再加这个逻辑。
        # if helper_domain.is_valid_domain(host):
        #     ScoutFeedBackBase.__init__(self, task, level, EObjectType.Domain,
        #                                host, 'iscout_domain')
        # else:
        #     try:
        #         IPy.IP(host)
        #         ScoutFeedBackBase.__init__(self, task, level, EObjectType.Ip,
        #                                    host, 'iscout_ip')
        #     except Exception:
        #         raise Exception(
        #             "Invalid host for mailserver, not an IP nor a domain: {}".
        #             format(host))

        self._task: IscoutTask = task
        self._level: int = level

        self._servertype: str = servertype

        self._host: str = host

        self._ips: dict = {}
        self._ips_locker = threading.RLock()

    def set_ip(self, ip: str):
        """向当前MailServer根节点添加 当前MailServer的域名解析出来的IP地址"""
        if not isinstance(ip, str) or ip == '' or self._ips.__contains__(ip):
            return
        with self._ips_locker:
            if self._ips.__contains__(ip):
                return
            self._ips[ip] = ip
