"""nmap scanner for open ports"""

# -*- coding:utf-8 -*-

import os
import re
import threading
import traceback
import uuid

from datacontract.iscandataset.iscantask import IscanTask

from .nmapscannerbase import NmapScannerBase


class NmapScannerAliveHosts(NmapScannerBase):
    """nmap scan for alive hosts"""

    def __init__(self):
        NmapScannerBase.__init__(self)

    #############################
    # scan alive hosts

    def scan_alive_hosts_no_ping(
        self, task: IscanTask, level: int, hosts: list, *args
    ) -> str:
        """扫描，返回结果文件路径"""
        outfi: str = None
        try:
            if not isinstance(hosts, list):
                raise Exception("Invalid hosts for scannig: {}".format(type(hosts)))

            args_all: list = []
            args_all.append(" ".join(hosts))

            for a in args:
                if not a in args_all:
                    args_all.append(a)
            extra_args = ["-sn", "-n"]
            for a in extra_args:
                if not a in args_all:
                    args_all.append(a)

            outfi = self._scan(*args_all)

        except Exception:
            if not outfi is None and os.path.isfile(outfi):
                os.remove(outfi)
            outfi = None
            self._logger.error(
                "Scan alive hosts error:\ntaskid:{}\nbatchid:{}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()
                )
            )
        return outfi

    def scan_alive_hosts_ack(
        self, task: IscanTask, level: int, hosts: list, *args
    ) -> str:
        """扫描，返回结果文件路径"""
        outfi: str = None
        try:
            if not isinstance(hosts, list):
                raise Exception("Invalid hosts for scannig: {}".format(type(hosts)))

            args_all: list = []
            args_all.append(" ".join(hosts))

            for a in args:
                if not a in args_all:
                    args_all.append(a)

            extra_args = ["-PA", "-Pn", "-n", "-T4", "--open", "--max-retries 1"]
            for a in extra_args:
                if not a in args_all:
                    args_all.append(a)

            outfi = self._scan(*args_all)

        except Exception:
            if not outfi is None and os.path.isfile(outfi):
                os.remove(outfi)
            outfi = None
            self._logger.error(
                "Scan alive hosts error:\ntaskid:{}\nbatchid:{}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()
                )
            )
        return outfi
