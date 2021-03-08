"""
scan tool base
"""

import os
import subprocess
import sys
import threading
from abc import ABCMeta, abstractmethod

from commonbaby.helpers import helper_dir

from datacontract.iscandataset.iscantask import IscanTask

from ...config_output import tmpdir
from .scanplugbase import ScanPlugBase


class ScanToolBase(ScanPlugBase):
    """scanner tool base"""

    __metaclass = ABCMeta

    # scan_ip_ports queues
    _dir_lockers: dict = {}

    def __init__(self, toolmark: str):
        ScanPlugBase.__init__(self)
        if not isinstance(toolmark, str) or toolmark == "":
            raise Exception("invalid toolmark for scantool initialize")
        self._toolmark = toolmark

        if not ScanToolBase._dir_lockers.__contains__(toolmark):
            ScanToolBase._dir_lockers[toolmark] = threading.RLock()

        self._tmpdir: str = os.path.abspath(tmpdir)

        with ScanToolBase._dir_lockers[toolmark]:
            if not isinstance(self._tmpdir, str):
                self._tmpdir = os.path.abspath("./_clienttmpdir")
            self._tmpdir = os.path.abspath(os.path.join(self._tmpdir, self._toolmark))
            if os.path.isdir(self._tmpdir):
                helper_dir.remove_dirs(self._tmpdir)

            os.makedirs(self._tmpdir)

    def _run_process(
        self,
        executable: str,
        *args,
        sudo: bool = False,
        rootDir: str = "./",
    ) -> subprocess.Popen:
        """
        run process under current operation system.
        executable: the executable binary path.
        arg: all args in a str.
        sudo: True if sudo
        rootDir: current work dir
        """
        try:
            p = None
            if not os.path.exists(rootDir):
                os.makedirs(rootDir)

            cmd = ""
            if sudo and not sys.platform.startswith("win32"):
                cmd = "sudo "
            params = " ".join(args)
            params = "%s %s" % (executable, params)
            cmd = cmd + params
            # logmsg = ''
            # if not is_none_or_empty(taskid):
            #     logmsg += 'taskid=%s: ' % taskid
            # logmsg += cmd
            self._logger.debug(cmd)
            if (
                sys.platform.startswith("freebsd")
                or sys.platform.startswith("linux")
                or sys.platform.startswith("darwin")
            ):
                p = subprocess.Popen(
                    cmd,
                    shell=True,
                    cwd=rootDir,
                    bufsize=1,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    close_fds=True,
                    universal_newlines=True,
                )
            else:
                p = subprocess.Popen(
                    cmd,
                    cwd=rootDir,
                    shell=True,
                    bufsize=1,
                    stdout=subprocess.PIPE,
                    universal_newlines=True,
                )

            return p
        except Exception as ex:
            raise ex

    def _is_cmd_not_found(self, p: subprocess.Popen):
        """judge the output text if it says 'command not found.
        return (strstdout,strstderr,is_not_found)'"""
        is_not_found = False
        output, error = p.communicate()  # sav stdout
        if not output is None and not output == "":
            if "command not found" in output or "No such file or directory" in output:
                is_not_found = True
        elif not error is None and not error == "":
            if "command not found" in error or "No such file or directory" in error:
                is_not_found = True
        return output, error, is_not_found
