"""
zgrab2去扫imap
create by judy 2019/11/19
imap 没有CAPABILITY，NOOP，和LOGOUT
LOGIN

"""

import os
import traceback

from datacontract.iscoutdataset import IscoutTask
from .zgrab2scannerbase import Zgrab2ScannerBase
from ..zgrab2parser import Zgrab2ParserImap
from .....clientdatafeedback.scoutdatafeedback import PortInfo


class Zgrab2ScannerImap(Zgrab2ScannerBase):
    """zgrab2 http scanner"""

    def __init__(self, zgrab_path: str):
        Zgrab2ScannerBase.__init__(self, 'zgrab2imap')
        self._parser: Zgrab2ParserImap = Zgrab2ParserImap()

    def get_banner_imap(
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

            outfi = self._scan_imap(
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
            self._parser.parse_banner_imap(task, level, portinfo, outfi)

        except Exception:
            self._logger.error("Scan imap error: {}".format(
                traceback.format_exc()))

    def _scan_imap(
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
        """scan the ips or domains, and write the output files to specified output directory.
        host_file: the full path of a file with list of ['1.1.1.1','www.xxx.com'] in the file per line
        port: '80' or '443'
        outfi: result file path
        """
        outfi: str = None
        try:
            enhanced_args = []

            # add hosts and ports to args
            enhanced_args.append('imap')
            enhanced_args.append(f'-p {port}')
            # zgrab2 imap -p 143 -n imap -t 10 -o ./mt1.json -f ./mtip.txt or
            # 993 imaps
            enhanced_args.append("-n imap")
            enhanced_args.append(f"-t {timeout}")

            if port == 143 and '--starttls' not in enhanced_args:
                enhanced_args.append('--starttls')
            elif port == 993 and '--imaps' not in enhanced_args:
                enhanced_args.append('--imaps')

            if '--send-close' not in enhanced_args:
                enhanced_args.append('--send-close')

            # 这个args里面几乎没有东西，除非真的是外面有特殊说明这个才有值，所以还是先留在这里
            enhanced_args.extend(args)

            if '--input-file=' not in args or '-f' not in args:
                enhanced_args.append(f'-f {host_file}')  # input file

            outfi = os.path.join(self._tmpdir, "{}_{}.imap".format(task.batchid, port))
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
                    raise Exception(f"Scan Imap error: {stdout}\n{stderr}")
                self._logger.info(
                    f"Scan Imap exitcode={str(exitcode)}\ntaskid:{task.taskid}\nbatchid:{task.batchid}\nport:{port}")
            finally:
                if curr_process is not None:
                    curr_process.kill()
        except Exception:
            if outfi is not None and os.path.isfile(outfi):
                os.remove(outfi)
            outfi = None
            self._logger.info(
                f"Scan Imap exitcode={str(exitcode)}\ntaskid:{task.taskid}\nbatchid:{task.batchid}\nport:{port}")

        return outfi
