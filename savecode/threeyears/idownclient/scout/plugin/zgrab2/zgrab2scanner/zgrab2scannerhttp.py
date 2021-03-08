"""zgrab2 scanner http"""

# -*- coding:utf-8 -*-

import json
import os
import traceback

from datacontract.iscoutdataset import IscoutTask

from .....clientdatafeedback.scoutdatafeedback import PortInfo, SiteInfo
from ..zgrab2parser import Zgrab2ParserHttp, Zgrab2ParserTls
from .zgrab2scannerbase import Zgrab2ScannerBase


class Zgrab2ScannerHttp(Zgrab2ScannerBase):
    """zgrab2 http scanner"""

    def __init__(self, zgrab_path: str):
        Zgrab2ScannerBase.__init__(self, "zgrab2http")
        self._parser_http: Zgrab2ParserHttp = Zgrab2ParserHttp()
        self._parser_tls: Zgrab2ParserTls = Zgrab2ParserTls()

    def get_banner_http(
        self,
        task: IscoutTask,
        level,
        portinfo: PortInfo,
        *args,
        zgrab2path: str = "zgrab2",
        sudo: bool = False,
        timeout: float = 600,
    ) -> iter:
        """scan http services and get the banner"""
        hostfi = None
        outfi = None
        try:
            port: int = portinfo._port
            if not isinstance(port, int) or port < 0 or port > 65535:
                raise Exception("Invalid port: {}".format(port))

            hosts: list = []
            for d in portinfo.domains:
                if not d in hosts:
                    hosts.append(d)
            if len(hosts) < 1:
                # scan ip is not good, only scan them when
                # no domain is available
                hosts.append(portinfo._host)
                for h in portinfo.hostnames:
                    if not h in hosts:
                        hosts.append(h)

            hostfi = self._write_hosts_to_file(task, hosts)
            if hostfi is None:
                return

            outfi = self._scan_http(
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
            self._logger.error("Scan http error: {}".format(traceback.format_exc()))
        finally:
            if not hostfi is None and os.path.isfile(hostfi):
                os.remove(hostfi)
            if not outfi is None and os.path.isfile(outfi):
                os.remove(outfi)

    #################################
    # scan

    def _scan_http(
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
        """scan the ips or domains, and write the output files to specified output directory.
        host_file: the full path of a file with list of ['1.1.1.1','www.xxx.com'] in the file per line
        port: '80' or '443'
        outfi: result file path
        """
        outfi: str = None
        exitcode = None
        try:
            enhanced_args = []

            # add hosts and ports to args
            enhanced_args.append("http")
            enhanced_args.append("--port=%s" % port)

            # zgrab2 http 192.168.40.114  --port=8020 --endpoint='/' --heartbleed
            # --extended-master-secret --extended-random --max-redirects=2
            # --session-ticket --follow-localhost-redirects --retry-https --timeout=30
            # --user-agent="Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
            # -f ./a.list -o ./a.json

            if not "--endpoint=" in args:
                enhanced_args.append("--endpoint='/'")
            if not "--heartbleed" in args:
                enhanced_args.append("--heartbleed")
            if not "--extended-master-secret" in args:
                enhanced_args.append("--extended-master-secret")
            if not "--extended-random" in args:
                enhanced_args.append("--extended-random")
            if not "--max-redirects=" in args:
                enhanced_args.append("--max-redirects=2")
            if not "--session-ticket" in args:
                enhanced_args.append("--session-ticket")
            if not "--retry-https" in args:
                enhanced_args.append("--retry-https")
            if not "--timeout=" in args:
                enhanced_args.append("--timeout=30")
            if not "--user-agent=" in args:
                enhanced_args.append(
                    '--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"'
                )

            enhanced_args.extend(args)

            if not "--input-file=" in args or "-f" in args:
                enhanced_args.append("-f %s" % host_file)  # input file

            outfi = os.path.join(self._tmpdir, "{}_{}.http".format(task.batchid, port))
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
                    self._logger.trace(stderr)
                if exitcode != 0:
                    raise Exception("Scan HTTP error: %s\n%s" % (stdout, stderr))
                self._logger.info(
                    "Scan HTTP exitcode={}\ntaskid:{}\nbatchid:{}\nport:{}".format(
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
                "Scan HTTP exitcode={}\ntaskid:{}\nbatchid:{}\nport:{}".format(
                    str(exitcode), task.taskid, task.batchid, port
                )
            )

        return outfi

    #################################
    # parse

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

                        # self._parser_http._parse_http(sj, portinfo)
                        self._parse_http(task, sj, portinfo)

                        # do not parse ssl certificate here,
                        # cuz already got tls information
                        # self._parser_tls._parse_cert(sj, portinfo)
                        # self._parse_tls(task, sj, portinfo)

                    except Exception:
                        self._logger.error(
                            "Parse one http banner json line error:\ntaskid:{}\nbatchid:{}\nresultfi:{}\nlinenum:{}\nerror:{}".format(
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

    def _parse_http(self, task: IscoutTask, sj, portinfo: PortInfo):
        """parse site(http) info"""
        try:
            self._parser_http._parse_http(sj, portinfo)
        except Exception:
            self._logger.error(
                "Parse http site result error:\ntaskid:{}\nbatchid:{}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()
                )
            )

    def _parse_tls(self, task: IscoutTask, sj, portinfo: PortInfo):
        """parse site(http) info"""
        try:
            if not sj.__contains__("data") or not sj["data"].__contains__("http"):
                return
            if sj["data"]["http"]["status"] != "success":
                return

            sjresp = sj["data"]["http"]["result"]["response"]

            if not sjresp.__contains__("request") or not sjresp["request"].__contains__(
                "tls_log"
            ):
                return

            sjtls = sjresp["request"]["tls_log"]
            sjhandshake = sjtls.get("handshake_log")
            if sjhandshake is None or len(sjhandshake) < 1:
                return

            self._parser_tls._parse_cert(sjhandshake, portinfo)
        except Exception:
            self._logger.error(
                "Parse http tls result error:\ntaskid:{}\nbatchid:{}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()
                )
            )
