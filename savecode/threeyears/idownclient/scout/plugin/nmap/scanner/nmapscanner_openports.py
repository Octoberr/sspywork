"""nmap scanner for open ports"""

# -*- coding:utf-8 -*-

import os
import re
import threading
import traceback
import uuid

from datacontract.iscoutdataset.iscouttask import IscoutTask

from .nmapscannerbase import NmapScannerBase


class NmapScannerOpenPorts(NmapScannerBase):
    """nmap scanner for open ports"""

    _port_scan_args: list = [
        # 禁用主机发现，就好像每个主机都是活动的（也确实是，因为经过了预扫描）
        '-Pn',
        # 不用在扫描时对ip进行域名反解析（因为一般会很慢，且用户任务下发时是反解了域名过来的）
        '-n',
        # 指定速度
        '-T3',
        # 启用服务版本探测
        '-sV',
        # 启用操作系统探测
        '-O',
        # 只针对活动的主机进行操作系统检测
        '--osscan-limit',
        # 只输出开放的端口
        '--open',
        # 每秒发包最少多少个
        # '--min-rate 100',
        # 最小同时扫描的主机数
        # '--min-hostgroup 256',
        # 探针失败重试次数
        '--max-retries 2',
        # 对一个主机发送两个探测报文之间的等待时间(毫秒)，可以控制带宽，和用于躲避IPS
        # '--max-scan-delay 1',
    ]

    def __init__(self, ):
        NmapScannerBase.__init__(self)

    def scan_open_ports(self, task: IscoutTask, hosts: list, ports: list,
                        *args) -> str:
        """扫描指定ip段的指定端口是否开放，返回结果文件路径"""
        outfi: str = None
        try:
            if not isinstance(hosts, list):
                raise Exception("Invalid hosts for scannig: {}".format(
                    type(hosts)))
            if not isinstance(ports, list):
                raise Exception("Invalid ports for scanning: {}".format(
                    type(ports)))

            args_all: list = []
            args_all.append(' '.join(hosts))
            arg_ports: list = '-p ' + ','.join(str(p) for p in ports)
            args_all.append(arg_ports)

            for a in args:
                if not a in args_all:
                    args_all.append(a)

            for a in self._port_scan_args:
                if not a in args_all:
                    args_all.append(a)

            outfi = self._scan(*args_all)

        except Exception:
            if not outfi is None and os.path.isfile(outfi):
                os.remove(outfi)
            outfi = None
            self._logger.error(
                "Scan ports error:\ntaskid:{}\nbatchid:{}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()))
        return outfi

    def scan_open_ports_udp(self, task: IscoutTask, hosts: list, ports: list,
                        *args) -> str:
        """扫描指定ip段的指定端口是否开放，返回结果文件路径"""
        outfi: str = None
        try:
            if not isinstance(hosts, list):
                raise Exception("Invalid hosts for scannig: {}".format(
                    type(hosts)))
            if not isinstance(ports, list):
                raise Exception("Invalid ports for scanning: {}".format(
                    type(ports)))

            args_all: list = []
            args_all.append(' '.join(hosts))

            for a in args:
                if not a in args_all:
                    args_all.append(a)

            for a in self._port_scan_args:
                if not a in args_all:
                    args_all.append(a)

            for p in ports:
                arg_ports: str = '-p ' + str(p)
                args_all.append(arg_ports)

                if p == 10001:
                    ubiquiti_args = '--script ubiquiti-discovery.nse'
                    args_all.append(ubiquiti_args)

                outfi = self._scan(*args_all)

                res = {'port': p, 'file': outfi}
                yield res

        except Exception:
            if not outfi is None and os.path.isfile(outfi):
                os.remove(outfi)
            outfi = None
            self._logger.error(
                "Scan ports error:\ntaskid:{}\nbatchid:{}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()))