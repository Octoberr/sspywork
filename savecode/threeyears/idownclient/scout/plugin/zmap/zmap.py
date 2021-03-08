"""zmap"""

# -*- coding:utf-8 -*-

import os
import re
import shutil
import threading
import traceback
import uuid

import IPy
from commonbaby.helpers.helper_domain import is_valid_domain

from datacontract.iscoutdataset.iscouttask import IscoutTask
from .zmapconfig import ZmapConfig
from .zmapparser import ZmapParser
from ..scantoolbase import ScanToolBase


class Zmap(ScanToolBase):
    """zmap"""

    _init_locker = threading.Lock()

    # true if we have found nmap
    _is_zmap_found: bool = False

    _zmap_may_path: list = [
        'zmap', '/usr/bin/zmap', '/usr/local/bin/zmap', '/sw/bin/zmap',
        '/opt/local/bin/zmap'
    ]

    _zmap_path: str = 'zmap'
    _zmap_version = ''  # zmap version
    _zmap_subversion = 0  # zmap subversion number

    # regex for zmap version
    # zmap 2.1.1
    _re_version = re.compile(r'zmap [0-9]*\.[0-9]*\.?[0-9]*?')

    _port_scan_args: list = []

    def __init__(self):
        ScanToolBase.__init__(self, 'zmap')

        # self._config: ZmapConfig = zmapconfig
        self._config: ZmapConfig = None
        if not isinstance(self._config, ZmapConfig):

            # raise Exception("Must specific interface card for Zmap config")
            self._config = ZmapConfig(interface_card='ens32', sudo=True)

        Zmap._port_scan_args.append('--max-sendto-failures=1')
        # 虚拟机需要指定网卡，物理机docker部署不需要指定网卡by judy 2020/06/16
        # Zmap._port_scan_args.append('-i {}'.format(self._config._interface_card))
        # 带宽限制
        Zmap._port_scan_args.append('-B 10M')
        Zmap._port_scan_args.append('-w /home/idownclient/resource/wi')
        Zmap._port_scan_args.append('-b /home/idownclient/resource/bi')

        for zpath in self._config.zmappath:
            if not zpath in Zmap._zmap_may_path:
                Zmap._zmap_may_path.append(zpath)

        self._init_zmap()

    def _init_zmap(self):
        try:
            if Zmap._is_zmap_found:
                return

            with Zmap._init_locker:
                if Zmap._is_zmap_found:
                    return

                for zpath in Zmap._zmap_may_path:
                    try:
                        p = self._run_process(
                            zpath, *['--version'], sudo=self._config.sudo)
                    except Exception:
                        self._logger.debug(
                            "Zmap not found in '{}'".format(zpath))
                    else:
                        output, error, notfound = self._is_cmd_not_found(p)
                        if notfound:
                            continue
                        if isinstance(output, str) and output != '':
                            self._logger.info(output)
                        if isinstance(error, str) and output != '':
                            self._logger.info(error)
                        Zmap._zmap_path = zpath  # save path
                        break
                    finally:
                        if not p is None:
                            p.kill()
                else:
                    raise Exception(
                        'zmap program was not found in path. PATH is : {0}'.
                            format(os.getenv('PATH')))

                # get result of zmap --version
                Zmap._zmap_version = output
                Zmap._is_zmap_found = True

                if not Zmap._is_zmap_found:
                    raise EnvironmentError(
                        'zmap program was not found in path: %s' % error)
        except Exception:
            self._logger.error("Init zmap error: {}".format(
                traceback.format_exc()))

    #########################################
    # scan interfaces

    def scan_open_ports(self, task: IscoutTask, level: int, hosts: list,
                        ports: list, *args) -> iter:
        """扫描指定ip段的指定端口是否开放，返回 PortInfo """
        try:
            if not isinstance(hosts, list) or len(hosts) < 1:
                return

            for p in ports:
                outfi = None
                try:
                    if not isinstance(p, int):
                        p = int(p)

                    outfi = self._scan(task, hosts, p, *args)

                    if not isinstance(outfi, str) or not os.path.isfile(outfi):
                        continue

                    for port in ZmapParser.parse_open_ports(
                            task, level, outfi, p, 'tcp'):
                        yield port

                except Exception:
                    self._logger.error(
                        "Scan one port ({}) error:\ntaskid:{}\nbatchid:{}\nerror:{}"
                            .format(p, task.taskid, task.batchid,
                                    traceback.format_exc()))
                finally:
                    if os.path.isfile(outfi):
                        os.remove(outfi)

        except Exception:
            self._logger.error(
                "Scan error:\ntaskid:{}\nbatchid:{}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()))

    def _scan(self, task: IscoutTask, hosts: list, port: int, *args) -> str:
        """yield PortInfo"""
        outfi: str = None
        try:
            if not isinstance(hosts, list):
                raise Exception("Invalid hosts for scannig: {}".format(
                    type(hosts)))
            if not isinstance(port, int):
                raise Exception("Invalid port for scanning: {}".format(
                    type(port)))

            args_all: list = []
            args_all.append(' '.join(hosts))
            arg_ports: list = '-p {}'.format(port)
            args_all.append(arg_ports)

            for a in args:
                if not a in args_all:
                    args_all.append(a)

            for a in Zmap._port_scan_args:
                if not a in args_all:
                    args_all.append(a)

            outfi: str = os.path.join(self._tmpdir, str(uuid.uuid1()))
            arg_out = '-o {}'.format(outfi)
            if not '-o' in args_all:
                args_all.append(arg_out)

            curr_process = None
            try:
                curr_process = self._run_process(
                    self._zmap_path,
                    *args_all,
                    sudo=self._config.sudo,
                    rootDir=self._tmpdir,
                )
                stdout, stderr = curr_process.communicate(
                    timeout=self._config.timeout)
                exitcode = curr_process.wait()  # (timeout=self.timeout)
                if not stdout is None:
                    self._logger.trace(stdout)
                if not stderr is None:
                    self._logger.trace(stderr)
                if exitcode != 0:
                    raise Exception(
                        "Scan port error:\ntaskid:{}\nbatchid:{}\nstdout:{}\nstderror:{}"
                            .format(task.taskid, task.batchid, stdout, stderr))
                self._logger.info(
                    "Scan complete:\ntaskid:{}\nbatchid:{}\nhost:{}\nport:{}\nexitcode:{}"
                        .format(task.taskid, task.batchid, hosts, port,
                                str(exitcode)))
            finally:
                if not curr_process is None:
                    curr_process.kill()

            if os.path.isfile(outfi):
                self.__remove_headline(outfi)

        except Exception:
            if os.path.isfile(outfi):
                os.remove(outfi)
            outfi = None
            self._logger.error(
                "Scan ports error:\ntaskid:{}\nbatchid:{}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()))
        return outfi

    def __remove_headline(self, fi: str):
        """remove the head line of zmap result file"""
        err = False
        try:
            if fi is None or fi == '' or not os.path.exists(
                    fi) or not os.path.isfile(fi):
                raise Exception(
                    "Zmap scan result file not exists while removing headline of it"
                )
            fiold = "%s_back" % fi
            if os.path.exists(fiold) and os.path.isfile(fiold):
                os.remove(fiold)
            shutil.move(fi, fiold)

            fs = open(fiold, mode='r', encoding='utf-8')
            fsnew = open(fi, mode='a', encoding='utf-8')

            while True:
                line: str = fs.readline()
                if line is None or line == '':
                    break
                line = line.strip().rstrip()
                isip = False
                isdomain = False
                try:
                    IPy.IP(line)
                    isip = True
                except Exception:
                    pass

                isdomain = is_valid_domain(line)
                if not isip and not isdomain:
                    continue
                fsnew.write(line + "\n")
        except Exception:
            err = True
            if not fs is None:
                fs.close()
            if not fsnew is None:
                fsnew.close()
            if os.path.exists(fi):
                os.remove(fi)
            if os.path.exists(fiold):
                shutil.move(fiold, fi)
        finally:
            if not fs is None:
                fs.close()
            if not fsnew is None:
                fsnew.close()
            if not err:
                if os.path.exists(fiold):
                    os.remove(fiold)
