"""
ftp
zgrab2 search ftp
create by judy 19/11/26
ftp拿到的也不全，只能认证tls
"""

import os
import traceback

from datacontract.iscoutdataset import IscoutTask
from .zgrab2scannerbase import Zgrab2ScannerBase
from ..zgrab2parser import Zgrab2ParserFtp
from .....clientdatafeedback.scoutdatafeedback import PortInfo


class Zgrab2ScannerFtp(Zgrab2ScannerBase):
    """zgrab2 http scanner"""

    def __init__(self, zgrab_path: str):
        Zgrab2ScannerBase.__init__(self, 'zgrab2ftp')
        self._parser: Zgrab2ParserFtp = Zgrab2ParserFtp()

    def get_banner_ftp(
            self,
            task: IscoutTask,
            level,
            portinfo: PortInfo,
            *args,
            zgrab2path: str = 'zgrab2',
            sudo: bool = False,
            timeout: float = 600,
    ) -> iter:
        """scan http services and get the banner"""
        try:
            port: int = portinfo._port
            if not isinstance(port, int) or port < 0 or port > 65535:
                raise Exception("Invalid port: {}".format(port))

            hosts: list = [portinfo._host]
            for h in portinfo.hostnames:
                if h not in hosts:
                    hosts.append(h)
            for d in portinfo.domains:
                if d not in hosts:
                    hosts.append(d)

            hostfi = self._write_hosts_to_file(task, hosts)
            if hostfi is None:
                return

            outfi = self._scan_ftp(
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
            # should there be modified?
            self._parser.parse_banner_ftp(task, level, portinfo, outfi)

        except Exception:
            self._logger.error("Scan ftp error: {}".format(
                traceback.format_exc()))

    def _scan_ftp(
            self,
            task: IscoutTask,
            level,
            host_file: str,
            port: int,
            *args,
            zgrab2path: str = 'zgrab2',
            sudo: bool = False,
            timeout: float = 600,
    ) -> str:
        """
        scan the ips or domains, and write the output files to specified output directory.
        host_file: the full path of a file with list of ['1.1.1.1','www.xxx.com'] in the file per line
        port: '80' or '443'
        outfi: result file path
        """
        outfi: str = None
        try:
            enhanced_args = []

            # add hosts and ports to args
            enhanced_args.append('ftp')
            enhanced_args.append(f'-p {port}')
            # zgrab2 ftp -p 21 -n ftp -t 10 -o ./mt1.json -f ./mtip.txt
            enhanced_args.append("-n ftp")
            enhanced_args.append(f"-t {timeout}")

            if '--heartbeat-enabled' not in enhanced_args:
                enhanced_args.append('--heartbeat-enabled')
            if '--dsa-enabled' not in enhanced_args:
                enhanced_args.append('--dsa-enabled')
            if '--verbose' not in enhanced_args:
                enhanced_args.append('--verbose')
            if '--authtls' not in enhanced_args:
                enhanced_args.append('--authtls')

            # 这个args里面几乎没有东西，除非真的是外面有特殊说明这个才有值，所以还是先留在这里
            enhanced_args.extend(args)

            if '--input-file=' not in args or '-f' not in args:
                enhanced_args.append(f'-f {host_file}')  # input file

            outfi = os.path.join(self._tmpdir, "{}_{}.ftp".format(task.batchid, port))
            if '--output-file=' not in args or '-o' not in args:
                # here must use -o, use '--output-file' will cause exception 'No such file or directory'
                # this may be a bug
                # 人家没说可以用--output-file
                enhanced_args.append(f'-o {outfi}')  # output file

            # 如果没有当前文件夹那么就创建当前文件夹
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
                if stdout is not None:
                    self._logger.trace(stdout)
                if stderr is not None:
                    self._logger.trace(stderr)
                if exitcode != 0:
                    raise Exception(f"Scan ftp error: {stdout}\n{stderr}")
                self._logger.info(
                    f"Scan ftp exitcode={str(exitcode)}\ntaskid:{task.taskid}\nbatchid:{task.batchid}\nport:{port}")
            finally:
                if curr_process is not None:
                    curr_process.kill()
        except Exception:
            if outfi is not None and os.path.isfile(outfi):
                os.remove(outfi)
            outfi = None
            self._logger.info(
                f"Scan ftp exitcode={str(exitcode)}\ntaskid:{task.taskid}\nbatchid:{task.batchid}\nport:{port}")

        return outfi
