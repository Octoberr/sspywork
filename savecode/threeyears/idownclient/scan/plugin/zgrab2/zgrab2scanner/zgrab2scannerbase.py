"""zgrab2 scanner http"""

# -*- coding:utf-8 -*-

import os
import subprocess
import sys
import threading
import traceback
import uuid

from commonbaby.helpers import helper_dir
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscandataset.iscantask import IscanTask
from .....config_output import tmpdir


class Zgrab2ScannerBase(object):
    """zgrab2 scanner base"""

    def __init__(self, toolmark: str):

        if not isinstance(toolmark, str) or toolmark == "":
            raise Exception("Zgrab2 scanner toolmark is invalid")

        self._logger: MsLogger = MsLogManager.get_logger(type(self).__name__)

        self._toolmark: str = toolmark

        self._tmpdir: str = os.path.abspath(tmpdir)
        if not isinstance(self._tmpdir, str):
            self._tmpdir = os.path.abspath("./_clienttmpdir")
        self._tmpdir = os.path.abspath(os.path.join(self._tmpdir, self._toolmark))
        if os.path.isdir(self._tmpdir):
            helper_dir.remove_dirs(self._tmpdir)

        # 文件锁
        self._outfile_locker = threading.RLock()

        os.makedirs(self._tmpdir)

    def _write_hosts_to_file(self, task: IscanTask, hosts: iter) -> str:
        """"""
        fi: str = None
        try:
            # 多线程操作增加文件锁
            with self._outfile_locker:
                fi = os.path.join(self._tmpdir, str(uuid.uuid1()))
                while os.path.isfile(fi):
                    fi = os.path.join(self._tmpdir, str(uuid.uuid1()))
                with open(fi, mode="w", encoding="utf-8") as fs:
                    for h in hosts:
                        fs.write("{}\n".format(h))
        except Exception:
            if not fi is None and os.path.isfile(fi):
                os.remove(fi)
            fi = None
            self._logger.error(
                "Write hosts to file error:\ntaskid:{}\nerror:{}".format(
                    task.taskid, traceback.format_exc()
                )
            )
        return fi

    def _run_process(
        self,
        executable: str,
        *args,
        sudo: bool = False,
        rootDir: str = "./",
    ) -> subprocess.Popen:
        """run process under current operation system.
        executable: the executable binary path.
        arg: all args in a str.
        sudo: True if sudo
        rootDir: current work dir"""
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
            if "command not found" in output:
                is_not_found = True
        elif not error is None and not error == "":
            if "command not found" in error:
                is_not_found = True
        return output, error, is_not_found
