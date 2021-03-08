"""nmap"""

# -*- coding:utf-8 -*-

import os
import re
import threading
import traceback
import uuid

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask

# from ....config_scanner import nmapconfig
# from ..scantoolbase import ScanToolBase
# from .nmapconfig import NmapConfig
from .parser import NmapParserOpenPorts
from .scanner import NmapScannerOpenPorts
from .scanner import NmapScannerAliveHosts
from .parser import NmapParserAliveHosts


class Nmap:
    """nmap api"""

    def __init__(self):
        self._logger: MsLogger = MsLogManager.get_logger("Nmap")

        self._scanner_openports: NmapScannerOpenPorts = NmapScannerOpenPorts()
        self._scanner_alivehosts: NmapScannerAliveHosts = NmapScannerAliveHosts(
        )

    ####################################
    # scan open ports

    def scan_open_ports(self, task: IscoutTask, level, hosts: list,
                        ports: list, *args, **kwargs) -> iter:
        """scan open ports, yield return PortInfo"""
        if not isinstance(hosts, list) or len(hosts) < 1:
            return

        # 这里端口扫描的策略需要优化
        # 有些端口是tcp和udp都开的，各有用处
        # 需要界面配合指定是扫tcp还是udp
        outlog = kwargs.get('outlog')
        log = f"开始探测目标的主机协议:{hosts}"
        outlog(log)
        tcp_ports = []
        udp_ports = []
        for p in ports:
            if p.flag == 'udp':
                udp_ports.append(p.port)
            else:
                tcp_ports.append(p.port)
        if len(tcp_ports) > 0:
            outfi = self._scanner_openports.scan_open_ports(task, hosts, tcp_ports, *args)

            if not isinstance(outfi, str) or not os.path.isfile(outfi):
                return

            for port in NmapParserOpenPorts.parse_open_ports(task, level, outfi):
                yield port
            log = f"主机协议探测完成, Ports:{tcp_ports}, 传输协议:TCP"
            outlog(log)
        if len(udp_ports) > 0:
            results = self._scanner_openports.scan_open_ports_udp(task, hosts, udp_ports, '-sU')

            for r in results:
                udpoutfi = r['file']
                udp_port = r['port']

                if not isinstance(udpoutfi, str) or not os.path.isfile(udpoutfi):
                    return
                
                if udp_port == 10001:
                    for port in NmapParserOpenPorts.parse_udp_10001(task, level, udpoutfi):
                        yield port
                else:
                    for port in NmapParserOpenPorts.parse_open_ports(task, level, udpoutfi):
                        yield port
            
            log = f"主机协议探测完成, Ports:{udp_ports}, 传输协议:UDP"
            outlog(log)

    def scan_alive_hosts(self, task: IscoutTask, level, hosts: list,
                         *args) -> iter:
        """scan alive hosts for rangec detecting"""
        if not isinstance(hosts, list) or len(hosts) < 1:
            return

        # scan alive hosts no ping
        outfi = self._scanner_alivehosts.scan_alive_hosts_no_ping(
            task, level, hosts, *args)
        if not isinstance(outfi, str) or not os.path.isfile(outfi):
            return
        for host in NmapParserAliveHosts.parse_alive_hosts(task, level, outfi):
            yield host

        # ACK ping
        # DO NOT scan ports at alive host detecting
        # outfi = self._scanner_alivehosts.scan_alive_hosts_ack(
        #     task, level, hosts, *args)
        # if not isinstance(outfi, str) or not os.path.isfile(outfi):
        #     return
        # for host in NmapParserAliveHosts.parse_alive_hosts(
        #         task, level, outfi):
        #     yield host
