"""nmap scanner for open ports"""

# -*- coding:utf-8 -*-

from idownclient.clientdatafeedback.scoutdatafeedback.portinfo import ubiquiti
import os
import random
import traceback

from datacontract.iscandataset.iscantask import IscanTask
from .nmapscannerbase import NmapScannerBase
from idownclient.config_scanner import nmap_min_host_group


class NmapScannerOpenPorts(NmapScannerBase):
    """nmap scanner for open ports"""

    _port_scan_args: list = [
        # 禁用主机发现，就好像每个主机都是活动的（也确实是，因为经过了预扫描）
        "-Pn",
        # 不用在扫描时对ip进行域名反解析（因为一般会很慢，且用户任务下发时是反解了域名过来的）
        "-n",
        # 指定速度
        "-T5",
        # 启用服务版本探测
        "-sV",
        # '-version-light',
        # 启用操作系统探测
        "-O",
        # 只针对活动的主机进行操作系统检测
        "--osscan-limit",
        # 只输出开放的端口
        "--open",
        # 每秒发包最少多少个,用于香港大数据扫描可以将值设大点
        # '--min-rate 1000',
        # 最小同时扫描的主机数，用于香港大数据扫描可以将值设大点
        f"--min-hostgroup {nmap_min_host_group}",
        # 探针失败重试次数
        "--max-retries 2",
        # 对一个主机发送两个探测报文之间的等待时间(毫秒)，可以控制带宽，和用于躲避IPS
        # '--max-scan-delay 1',
        #  --host-timeout <msec>: Give up on target after this long,一般来说几秒钟就行了
        # '--host-timeout 10m'
    ]

    def __init__(
        self,
    ):
        NmapScannerBase.__init__(self)

    def scan_open_ports(self, task: IscanTask, hosts: list, ports: list, *args) -> str:
        """扫描指定ip段的指定端口是否开放，返回结果文件路径"""
        nmapports = []
        outfi: str = None
        try:
            if not isinstance(hosts, list):
                raise Exception("Invalid hosts for scannig: {}".format(type(hosts)))
            if not isinstance(ports, list):
                raise Exception("Invalid ports for scanning: {}".format(type(ports)))
            # 默认添加一个不常用的tcp端口，用来探测操作系统，modify by judy 2020/08/19
            nmapports.extend(ports)
            # rport = random.randint(1, 65535)
            # while rport in ports:
            #     rport = random.randint(1, 65535)
            # nmapports.append(rport)
            args_all: list = []
            args_all.append(" ".join(hosts))
            arg_ports: str = "-p " + ",".join(str(p) for p in nmapports)
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
                    task.taskid, task.batchid, traceback.format_exc()
                )
            )
        return outfi

    def scan_open_ports_by_file(
        self, task: IscanTask, hostsfi: str, ports: list, *args
    ) -> str:
        """扫描指定ip段的指定端口是否开放，返回结果文件路径"""
        nmapports = []
        outfi: str = None
        try:
            if not isinstance(hostsfi, str):
                raise Exception("Invalid hosts for scannig: {}".format(type(hostsfi)))
            if not isinstance(ports, list):
                raise Exception("Invalid ports for scanning: {}".format(type(ports)))
            # 默认添加一个不常用的tcp端口，用来探测操作系统，modify by judy 2020/08/19
            # 原始的port不能动，新建一个by judy 2020/08/19
            nmapports.extend(ports)
            # rport = random.randint(1, 65535)
            # while rport in ports:
            #     rport = random.randint(1, 65535)
            # nmapports.append(rport)

            # ports.append(55558)
            args_all: list = []
            args_all.append(f"-iL {hostsfi}")
            arg_ports: str = "-p " + ",".join(str(p) for p in nmapports)
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
                    task.taskid, task.batchid, traceback.format_exc()
                )
            )
        return outfi

    def scan_open_ports_by_file_udp(
        self, task: IscanTask, hostsfi: str, ports: list, *args
    ) -> str:
        """扫描指定ip段的指定端口是否开放，返回结果文件路径"""
        nmapports = []
        outfi: str = None
        try:
            if not isinstance(hostsfi, str):
                raise Exception("Invalid hosts for scannig: {}".format(type(hostsfi)))
            if not isinstance(ports, list):
                raise Exception("Invalid ports for scanning: {}".format(type(ports)))

            nmapports.extend(ports)

            args_all: list = []
            args_all.append(f"-iL {hostsfi}")

            for a in args:
                if not a in args_all:
                    args_all.append(a)

            for a in self._port_scan_args:
                if not a in args_all:
                    args_all.append(a)

            for p in nmapports:
                arg_ports: str = "-p " + str(p)
                args_all.append(arg_ports)

                if p == 10001:
                    ubiquiti_args = "--script ubiquiti-discovery.nse"
                    args_all.append(ubiquiti_args)

                outfi = self._scan(*args_all)

                # 由于不同的端口，udp的扫描结构可能不同，将扫描端口和结果文件绑定，方便处理解析
                res = {"port": p, "file": outfi}

                yield res

        except Exception:
            if not outfi is None and os.path.isfile(outfi):
                os.remove(outfi)
            outfi = None
            self._logger.error(
                "Scan ports error:\ntaskid:{}\nbatchid:{}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()
                )
            )
