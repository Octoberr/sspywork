"""zgrab2 scanner tls"""

# -*- coding:utf-8 -*-

import json
import os
import traceback

from datacontract.iscoutdataset import IscoutTask

from .....clientdatafeedback.scoutdatafeedback import PortInfo, SiteInfo
from ..zgrab2parser import Zgrab2ParserTls
from .zgrab2scannerbase import Zgrab2ScannerBase


class Zgrab2ScannerTls(Zgrab2ScannerBase):
    """zgrab2 http scanner"""
    def __init__(self, zgrab_path: str):
        Zgrab2ScannerBase.__init__(self, "zgrab2tls")
        self._parser_tls: Zgrab2ParserTls = Zgrab2ParserTls()

    def get_banner_tls(
            self,
            task: IscoutTask,
            level,
            portinfo: PortInfo,
            *args,
            zgrab2path: str = "zgrab2",
            sudo: bool = False,
            timeout: float = 600,
    ) -> iter:
        """"""
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

            outfi = self._scan_tls(
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
            self._logger.error("Scan http error: {}".format(
                traceback.format_exc()))
        finally:
            if not hostfi is None and os.path.isfile(hostfi):
                os.remove(hostfi)
            if not outfi is None and os.path.isfile(outfi):
                os.remove(outfi)

    def _scan_tls(
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
        host_file: the full path of a file with list of ['1.1.1.1','www.xxx.com'] in the file per line\n
        port: any\n
        outfi: result file path
        """
        outfi: str = None
        exitcode = None
        try:
            enhanced_args = []

            # add hosts and ports to args
            enhanced_args.append("tls")
            enhanced_args.append("--port=%s" % port)

            # zgrab2 http 192.168.40.114  --port=8020 --endpoint='/' --heartbleed
            # --extended-master-secret --extended-random --max-redirects=2
            # --session-ticket --follow-localhost-redirects --retry-https --timeout=30
            # --user-agent="Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
            # -f ./a.list -o ./a.json

            # if not "--heartbleed" in args:
            #     enhanced_args.append("--heartbleed")
            if not "--extended-master-secret" in args:
                enhanced_args.append("--extended-master-secret")
            if not "--extended-random" in args:
                enhanced_args.append("--extended-random")
            # if not "--no-sni" in args:  # do not send domain name unless know
            #     enhanced_args.append("--no-sni")
            # if not "--keep-client-logs" in args:
            #     enhanced_args.append("--keep-client-logs")
            # if not "-dsa-enabled" in args:
            #     enhanced_args.append("-dsa-enabled")

            enhanced_args.extend(args)

            if not "--input-file=" in args or "-f" in args:
                enhanced_args.append("-f %s" % host_file)  # input file

            outfi = os.path.join(self._tmpdir,
                                 "{}_{}.tls".format(task.batchid, port))
            if not "--output-file=" in args or "-o" in args:
                # here must use -o, use '--output-file' will cause exception 'No such file or directory'
                # this may be a bug
                enhanced_args.append("-o %s" % outfi)  # output file

            outdir = os.path.dirname(outfi)
            if not os.path.exists(outdir) or not os.path.isdir(outdir):
                os.makedirs(outdir)

            curr_process = None
            try:

                curr_process = self._run_process(zgrab2path,
                                                 *enhanced_args,
                                                 rootDir=outdir,
                                                 sudo=sudo)
                stdout, stderr = curr_process.communicate(timeout=timeout)
                exitcode = curr_process.wait(timeout=timeout)
                if not stdout is None:
                    self._logger.trace(stdout)
                if not stderr is None:
                    self._logger.info(stderr)
                if exitcode != 0:
                    raise Exception("Scan TLS error: %s\n%s" %
                                    (stdout, stderr))
                self._logger.info(
                    "Scan TLS exitcode={}\ntaskid:{}\nbatchid:{}\nport:{}".
                    format(str(exitcode), task.taskid, task.batchid, port))
            finally:
                if not curr_process is None:
                    curr_process.kill()
        except Exception:
            if not outfi is None and os.path.isfile(outfi):
                os.remove(outfi)
            outfi = None
            self._logger.info(
                "Scan TLS exitcode={}\ntaskid:{}\nbatchid:{}\nport:{}".format(
                    str(exitcode), task.taskid, task.batchid, port))
        return outfi

    def _parse_result(self, task: IscoutTask, level: int, portinfo: PortInfo,
                      outfi):
        """parse http infor and ssl info"""
        try:

            if not os.path.isfile(outfi):
                self._logger.error(
                    "Resultfi not exists:\ntaskid:{}\nbatchid:{}\nresultfi:{}".
                    format(task.taskid, task.batchid, outfi))
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

                        # self._parser_tls._parse_cert(sj, portinfo)
                        self._parse_tls(task, sj, portinfo)

                    except Exception:
                        self._logger.error(
                            "Parse one http banner json line error:\ntaskid:{}\nbatchid:{}\nresultfi:{}\nlinenum:{}\nerror:{}"
                            .format(
                                task.taskid,
                                task.batchid,
                                outfi,
                                linenum,
                                traceback.format_exc(),
                            ))
                    finally:
                        linenum += 1
        except Exception:
            self._logger.error(
                "Parse http result error:\ntaskid:{}\nbatchid:{}\nresultfi:{}".
                format(task.taskid, task.batchid, outfi))

    def _parse_tls(self, task: IscoutTask, sj, portinfo: PortInfo):
        """parse site(http) info"""
        try:
            if (not sj.__contains__("data")
                    or not sj["data"].__contains__("tls")
                    or not sj["data"]["tls"].__contains__("result")
                    or not sj["data"]["tls"]["result"].__contains__(
                        "handshake_log")
                    or not sj["data"]["tls"].__contains__("status")):
                return
            if sj["data"]["tls"]["status"] != "success":
                return

            sjtls = sj["data"]["tls"]
            self._parser_tls._parse_tls(sjtls, portinfo)

            # # sjtls = sj["data"]["tls"]
            # sjhandshake = sj["data"]["tls"]["result"]["handshake_log"]
            # if sjhandshake is None or len(sjhandshake) < 1:
            #     return

            # self._parser_tls._parse_cert(sjhandshake, portinfo)
        except Exception:
            self._logger.error(
                "Parse http tls result error:\ntaskid:{}\nbatchid:{}\nerror:{}"
                .format(task.taskid, task.batchid, traceback.format_exc()))
