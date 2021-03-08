"""nmap"""

# -*- coding:utf-8 -*-

import os
import re
import threading
import traceback
import uuid

from datacontract.iscoutdataset.iscouttask import IscoutTask

# from idownclient.scan.plugin.nmap import nmapconfig
from ...scantoolbase import ScanToolBase
from ..nmapconfig import NmapConfig
from ..parser import NmapParserOpenPorts


class NmapScannerBase(ScanToolBase):
    '''nmap'''

    _init_locker = threading.Lock()

    # true if we have found nmap
    _is_nmap_found: bool = False

    _nmap_may_path: list = [
        'nmap', '/usr/bin/nmap', '/usr/local/bin/nmap', '/sw/bin/nmap',
        '/opt/local/bin/nmap'
    ]

    _nmap_path = ''  # nmap path
    _nmap_version = ''  # nmap version
    _nmap_subversion = 0  # nmap subversion number

    # regex for nmap version
    _re_version = re.compile(
        r'Nmap version [0-9]*\.[0-9]*[^ ]* \( http(|s)://.* \)')

    def __init__(self):
        ScanToolBase.__init__(self, 'nmap')

        # self._config: NmapConfig = nmapconfig
        self._config: NmapConfig = None
        if not isinstance(self._config, NmapConfig):
            self._config = NmapConfig()

        for npath in self._config.nmappath:
            if not npath in NmapScannerBase._nmap_may_path:
                NmapScannerBase._nmap_may_path.append(npath)

        self._init_nmap()

    def _init_nmap(self):
        try:

            if NmapScannerBase._is_nmap_found:
                return

            with NmapScannerBase._init_locker:
                if NmapScannerBase._is_nmap_found:
                    return

                # call nmap -V
                for npath in NmapScannerBase._nmap_may_path:
                    try:
                        p = self._run_process(npath,
                                              *['-V'],
                                              sudo=self._config.sudo)
                    except Exception as ex:
                        self._logger.debug(
                            "Nmap not found in '{}' : {}".format(npath, ex))
                    else:
                        output, error, notfound = self._is_cmd_not_found(p)
                        if notfound:
                            continue
                        if isinstance(output, str) and output != '':
                            self._logger.info(output)
                        if isinstance(error, str) and output != '':
                            self._logger.info(error)
                        NmapScannerBase._nmap_path = npath  # save path
                        break
                    finally:
                        if not p is None:
                            p.kill()
                else:
                    raise Exception(
                        'nmap program was not found in path. PATH is : {0}'.
                        format(os.getenv('PATH')))

                # get result of nmap -V
                for line in output.split('\n'):
                    if self._re_version.match(line) is not None:
                        NmapScannerBase._is_nmap_found = True
                        # Search for version number
                        regex_version = re.compile(r'[0-9]+')
                        regex_subversion = re.compile(r'\.[0-9]+')

                        rv = regex_version.search(line)
                        rsv = regex_subversion.search(line)

                        if rv is not None and rsv is not None:
                            # extract version/subversion
                            NmapScannerBase._nmap_version = int(
                                line[rv.start():rv.end()])
                            NmapScannerBase._nmap_subversion = int(
                                line[rsv.start() + 1:rsv.end()])
                        break

                NmapScannerBase._is_nmap_found = True

        except Exception as ex:
            self._logger.error("Init nmap error: {}".format(
                traceback.format_exc()))

    def _scan(self, *args) -> str:
        """使用指定参数进行扫描，返回结果文件路径\n
        args: iterator of params\n
        return: 结果文件路径"""
        outfi: str = None
        args_all: list = []
        try:
            for a in args:
                if not a in args_all:
                    args_all.append(a)

            outfi: str = os.path.join(self._tmpdir, str(uuid.uuid1()))
            arg_out = '-oX {}'.format(outfi)
            if not '-oX' in args_all:
                args_all.append(arg_out)

            curr_process = None
            try:
                curr_process = self._run_process(
                    self._nmap_path,
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
                    raise Exception("Scan error:\nstdout:{}\nstderr:{}".format(
                        stdout, stderr))
                self._logger.info(
                    "Scan complete, params:{}, exitcode:{}".format(
                        args_all, str(exitcode)))
            finally:
                if not curr_process is None:
                    curr_process.kill()

        except Exception:
            if not outfi is None and os.path.isfile(outfi):
                os.remove(outfi)
            outfi = None
            self._logger.error("Scan error:\nargs:{}\nerror:{}".format(
                args_all, traceback.format_exc()))
        return outfi
