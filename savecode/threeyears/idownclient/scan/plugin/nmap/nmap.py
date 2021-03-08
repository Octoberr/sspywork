"""
nmap
先扫一遍tcp端口再扫一遍udp端口
性能不够加机器，领导说的

modify by judy 20200414
"""

import os
import traceback
from pathlib import Path
import random
from shutil import copyfile

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscandataset.iscantask import IscanTask
from idownclient.config_scanner import nmap_tcp_timeout, nmap_udp_timeout
from idownclient.config_task import clienttaskconfig
from .parser import NmapParserAliveHosts
from .parser import NmapParserOpenPorts
from .scanner import NmapScannerAliveHosts
from .scanner import NmapScannerOpenPorts


class Nmap(object):
    """nmap api"""

    def __init__(self):
        self._logger: MsLogger = MsLogManager.get_logger("Nmap")

        self._scanner_openports: NmapScannerOpenPorts = NmapScannerOpenPorts()
        self._scanner_alivehosts: NmapScannerAliveHosts = NmapScannerAliveHosts()
        self.tmpdir = clienttaskconfig.tmppath

    ####################################
    # scan open ports

    def _save_error_ipranges_file(self, filepath: str):
        """
        保存扫描失败和扫描超时的ip段用于本地开发寻找原因
        create by judy 2020/08/20
        """
        try:
            error_path = self.tmpdir / "nmap_scan_error_ips"
            error_path.mkdir(exist_ok=True)
            src = Path(filepath)
            dst = error_path / src.name
            copyfile(src.as_posix(), dst.as_posix())
            self._logger.info(f"Save timeout ipranges to file, path:{dst.as_posix()}")
        except:
            self._logger.error(
                f"Cant save nmap error ip ranges:\nerror:{traceback.format_exc()}"
            )
        return

    def scan_open_ports(
        self, task: IscanTask, level, hosts: list, ports: list, *args
    ) -> iter:
        """scan open ports, yield return PortInfo"""
        if not isinstance(hosts, list) or len(hosts) < 1:
            return
        count = 0
        # 扫tcp端口
        if len(ports) > 0:
            outfi = self._scanner_openports.scan_open_ports(task, hosts, ports, *args)
            self._logger.info(f"Nmap scan tcp res outfile :{outfi}")

            if not isinstance(outfi, str) or not os.path.isfile(outfi):
                return

            for port in NmapParserOpenPorts.parse_open_ports(task, level, outfi):
                count += 1
                yield port

            # 局域网扫描演示先不开zmap和nmap的udp扫描 modify by judy 2020/07/07
            # udp_outfi = self._scanner_openports.scan_open_ports(task, hosts, ports, '-sU', '--host-timeout 10')
            # self._logger.info(f'Nmap scan udp res outfile :{udp_outfi}')
            # if not isinstance(udp_outfi, str) or not os.path.isfile(udp_outfi):
            #     return
            #
            # for port in NmapParserOpenPorts.parse_open_ports(task, level, udp_outfi):
            #     count += 1
            #     yield port
        self._logger.info(f"Parser nmap res:{count}")

    def scan_open_ports_by_file(
        self, task: IscanTask, level, hostsfi: str, ports: list, *args, **kwargs
    ) -> iter:
        """scan open ports, yield return PortInfo"""
        outlog = kwargs.get("outlog")
        if not isinstance(hostsfi, str) or not os.path.isfile(hostsfi):
            return
        count = 0
        tcp_ports = []
        udp_ports = []
        for pinfo in ports:
            flag = pinfo.flag
            p = pinfo.port
            if flag == "tcp":
                tcp_ports.append(p)
            elif flag == "udp":
                udp_ports.append(p)
            else:
                self._logger.debug(f"Unknown flag:{flag}, how did that happen")
                continue

        if len(tcp_ports) > 0:
            outfi = self._scanner_openports.scan_open_ports_by_file(
                task, hostsfi, tcp_ports, f"--host-timeout {nmap_tcp_timeout}"
            )
            self._logger.info(f"Nmap scan tcp res outfile :{outfi}")

            if not isinstance(outfi, str) or not os.path.isfile(outfi):
                self._save_error_ipranges_file(hostsfi)
                return

            for port in NmapParserOpenPorts.parse_open_ports(task, level, outfi):
                count += 1
                yield port
            # 最后删除解析完成的文件
            if outfi is not None and os.path.isfile(outfi):
                os.remove(outfi)
            if outlog is not None:
                log = f"完成主机协议探测，端口:{tcp_ports}, 传输协议:tcp"
                outlog(log)

        if len(udp_ports) > 0:
            # 局域网扫描演示先不开zmap和nmap的udp扫描 modify by judy 2020/07/07

            # udp端口在nmap扫描后，停止。
            # 不再使用其他的扫描器扫描

            # 返回结果包含扫描端口和对应扫描的文件
            # 方便根据不同的端口，使用不同的解析函数
            results = self._scanner_openports.scan_open_ports_by_file_udp(
                task, hostsfi, udp_ports, "-sU", f"--host-timeout {nmap_udp_timeout}"
            )
            for r in results:
                udp_outfi = r["file"]
                udp_port = r["port"]
                self._logger.info(f"Nmap scan udp res outfile :{udp_outfi}")
                if not isinstance(udp_outfi, str) or not os.path.isfile(udp_outfi):
                    return

                if udp_port == 10001:
                    for port in NmapParserOpenPorts.parse_udp_10001(
                        task, level, udp_outfi
                    ):
                        count += 1
                        yield port
                else:
                    for port in NmapParserOpenPorts.parse_open_ports(
                        task, level, udp_outfi
                    ):
                        count += 1
                        yield port

                if udp_outfi is not None and os.path.isfile(udp_outfi):
                    os.remove(udp_outfi)

            if outlog is not None:
                log = f"完成主机协议探测，端口:{udp_ports}, 传输协议:udp"
                outlog(log)

        self._logger.info(f"Parser nmap res:{count}")

    ####################################
    # scan alive hosts

    def scan_alive_hosts(self, task: IscanTask, level, hosts: list, *args) -> iter:
        """scan alive hosts for rangec detecting"""
        if not isinstance(hosts, list) or len(hosts) < 1:
            return

        # scan alive hosts no ping
        outfi = self._scanner_alivehosts.scan_alive_hosts_no_ping(
            task, level, hosts, *args
        )
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
