"""nmap parser"""

# -*- coding:utf-8 -*-

import traceback

from commonbaby.mslog import MsLogger, MsLogManager
from lxml import etree

from datacontract.iscandataset.iscantask import IscanTask

from .....clientdatafeedback.scoutdatafeedback import RangeCHost


class NmapParserAliveHosts:
    """NmapParserOpenPorts"""

    _logger: MsLogger = MsLogManager.get_logger("NmapParser")

    def __init__(self):
        self._name = type(self).__name__

    @classmethod
    def parse_alive_hosts(
        cls, task: IscanTask, level: int, nmap_result_fi: str
    ) -> iter:
        """yield RangeCHost"""
        try:
            doc: etree._ElementTree = etree.parse(nmap_result_fi)
            # xroot: minidom.Document = doc.documentElement
            xroot: etree._Element = doc.getroot()
            xhosts = xroot.findall("host")
            for xhost in xhosts:
                xhost: etree._Element = xhost
                if xhost is None:
                    continue
                # get opening ports
                host: RangeCHost = cls._get_host(xhost, task, level)
                if not isinstance(host, RangeCHost):
                    continue

                yield host

        except Exception:
            cls._logger.error(
                "Parse Nmap result error: {}".format(traceback.format_exc())
            )

    @classmethod
    def _get_host(
        cls, xhost: etree._Element, task: IscanTask, level: int
    ) -> RangeCHost:
        """parse xml, yield return RangeCHost"""
        host: RangeCHost = None
        try:
            # get ip address
            ip, iptype = cls._get_ip(xhost)
            if not isinstance(ip, str) or ip == "":
                return host

            host: RangeCHost = RangeCHost(task, level, ip)
            host.iptype = iptype

            # open ports
            xports = xhost.findall("ports/port")
            if xports is None or len(xports) < 1:
                return host

            for xp in xports:
                try:
                    if not cls._check_port_open(xp):
                        continue

                    port: int = int(xp.get("portid").strip())
                    transprotocol = xp.get("protocol")
                    service: str = None
                    xservice = xp.find("service")
                    if not xservice is None:
                        service = xservice.get("name")

                    host.set_port(port, transprotocol, service)

                except Exception:
                    cls._logger.debug(
                        "Get ports warn: {}".format(traceback.format_exc())
                    )

        except Exception:
            cls._logger.error(
                "Parse one alive host error: taskid={} batchid={}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()
                )
            )
        return host

    @classmethod
    def _get_ip(cls, xhost: etree._Element):
        """Get and return ip address from a nmap result xml 'host' section.
        return: (ip, iptype)
        iptype: ipv4/ipv6"""
        ipaddr = None
        iptype = None
        if xhost is None:
            return
        xaddrs = xhost.findall("address")
        if xaddrs is None or len(xaddrs) < 1:
            return
        for xaddr in xaddrs:
            # get ip address type from the ipaddr type attribute
            xiptp = xaddr.get("addrtype")
            if not isinstance(xiptp, str) or xiptp == "" or not xiptp.startswith("ip"):
                continue
            iptype = xiptp
            # get ip address from the ipaddr attribute
            xip = xaddr.get("addr")
            if not isinstance(xip, str) or xip is None or xip == "":
                return
            ipaddr = xip

        return (ipaddr, iptype)

    @classmethod
    def _check_port_open(cls, xport: etree._Element) -> bool:
        """<port... <state state="open" ...
        To check the xml document if the port's state is open."""
        res = False
        if xport is None:
            return res
        xstate: etree._Element = xport.find("state")
        if xstate is None:
            return res
        astate = xstate.get("state")
        if astate is None or astate == "" or astate != "open":
            return res
        res = True
        return res
