"""zgrab2 scanner ssh"""

# -*- coding:utf-8 -*-

import os
import traceback
import json
from datacontract.iscoutdataset import IscoutTask

from .....clientdatafeedback.scoutdatafeedback import PortInfo
from ..zgrab2parser.zgrab2parserssh import Zgrab2ParserSsh
from .zgrab2scannerbase import Zgrab2ScannerBase


class Zgrab2ScannerSsh(Zgrab2ScannerBase):
    """zgrab2 ssh scanner"""

    def __init__(self, zgrab_path: str):
        Zgrab2ScannerBase.__init__(self, "zgrab2ssh")
        self._parser: Zgrab2ParserSsh = Zgrab2ParserSsh()

    def get_banner(
        self,
        task: IscoutTask,
        level,
        portinfo: PortInfo,
        *args,
        zgrab2path: str = "zgrab2",
        sudo: bool = False,
        timeout: float = 600,
    ) -> iter:
        """get banner ssh"""
        hostfi = None
        outfi = None
        try:
            port: int = portinfo._port
            if not isinstance(port, int) or port < 0 or port > 65535:
                raise Exception("Invalid port: {}".format(port))

            # scan tls both domains and ips
            hosts: list = []
            hosts.append(portinfo._host)
            for h in portinfo.hostnames:
                if not h in hosts:
                    hosts.append(h)
            for d in portinfo.domains:
                if not d in hosts:
                    hosts.append(d)

            hostfi = self._write_hosts_to_file(task, hosts)
            if hostfi is None:
                return

            outfi = self._scan_ssh(
                task,
                level,
                hostfi,
                port,
                *args,
                zgrab2path=zgrab2path,
                sudo=sudo,
                timeout=timeout,
            )
            if outfi is None or not os.path.isfile(outfi):
                return

            self._parse_result(task, level, portinfo, outfi)

        except Exception:
            self._logger.error("Scan ssh error: {}".format(traceback.format_exc()))
        finally:
            if not hostfi is None and os.path.isfile(hostfi):
                os.remove(hostfi)
            if not outfi is None and os.path.isfile(outfi):
                os.remove(outfi)

    def _scan_ssh(
        self,
        task: IscoutTask,
        level,
        host_file: str,
        port: int,
        *args,
        zgrab2path: str = "zgrab2",
        sudo: bool = False,
        timeout: float = 600,
    ) -> str:
        """scan ssh"""
        outfi: str = None
        exitcode = None
        try:
            enhanced_args = []

            # add hosts and ports to args
            enhanced_args.append("ssh")
            enhanced_args.append("--port=%s" % port)

            # zgrab2 ssh --client="SSH-2.0-nsssh2_6.0.0030 NetSarang Computer, Inc." --verbose -f host.txt -o ./ssh.json

            if not "--client" in args:
                enhanced_args.append(
                    '--client="SSH-2.0-nsssh2_6.0.0030 NetSarang Computer, Inc."'
                )

            # --verbose is for client detail

            enhanced_args.extend(args)

            if not "--input-file=" in args or "-f" in args:
                enhanced_args.append("-f %s" % host_file)  # input file

            outfi = os.path.join(self._tmpdir, "{}_{}.tls".format(task.batchid, port))
            if not "--output-file=" in args or "-o" in args:
                # here must use -o, use '--output-file' will cause exception 'No such file or directory'
                # this may be a bug
                enhanced_args.append("-o %s" % outfi)  # output file

            outdir = os.path.dirname(outfi)
            if not os.path.exists(outdir) or not os.path.isdir(outdir):
                os.makedirs(outdir)

            curr_process = None
            try:

                curr_process = self._run_process(
                    zgrab2path, *enhanced_args, rootDir=outdir, sudo=sudo
                )
                stdout, stderr = curr_process.communicate(timeout=timeout)
                exitcode = curr_process.wait(timeout=timeout)
                if not stdout is None:
                    self._logger.trace(stdout)
                if not stderr is None:
                    self._logger.info(stderr)
                if exitcode != 0:
                    raise Exception("Scan TLS error: %s\n%s" % (stdout, stderr))
                self._logger.info(
                    "Scan TLS exitcode={}\ntaskid:{}\nbatchid:{}\nport:{}".format(
                        str(exitcode), task.taskid, task.batchid, port
                    )
                )
            finally:
                if not curr_process is None:
                    curr_process.kill()
        except Exception:
            if not outfi is None and os.path.isfile(outfi):
                os.remove(outfi)
            outfi = None
            self._logger.info(
                "Scan TLS exitcode={}\ntaskid:{}\nbatchid:{}\nport:{}".format(
                    str(exitcode), task.taskid, task.batchid, port
                )
            )
        return outfi

    def _parse_result(self, task: IscoutTask, level: int, portinfo: PortInfo, outfi):
        """parse http infor and ssl info"""
        try:

            if not os.path.isfile(outfi):
                self._logger.error(
                    "Resultfi not exists:\ntaskid:{}\nbatchid:{}\nresultfi:{}".format(
                        task.taskid, task.batchid, outfi
                    )
                )
                return

            # its' one json object per line
            linenum = 1
            with open(outfi, mode="r") as fs:
                while True:
                    try:
                        line = fs.readline()
                        if line is None or line == "":
                            break

                        sj = json.loads(line)
                        if sj is None:
                            continue

                        self._parser.parse_ssh(sj, portinfo)

                    except Exception:
                        self._logger.error(
                            "Parse one ssh banner json line error:\ntaskid:{}\nbatchid:{}\nresultfi:{}\nlinenum:{}\nerror:{}".format(
                                task.taskid,
                                task.batchid,
                                outfi,
                                linenum,
                                traceback.format_exc(),
                            )
                        )
                    finally:
                        linenum += 1
        except Exception:
            self._logger.error(
                "Parse http result error:\ntaskid:{}\nbatchid:{}\nresultfi:{}".format(
                    task.taskid, task.batchid, outfi
                )
            )
