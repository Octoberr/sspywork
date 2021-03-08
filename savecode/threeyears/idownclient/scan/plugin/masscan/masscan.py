"""
masscan扫描工具
功能
1、扫描指定ip和给定端口，得到开放端口输出到文件
masscan 23.76.76.66 -p 20,21,22,23,25,53,80,110,143,443,3389,27017,6379,1433,123,143,993,110,995,8080 -oX scan.xml
扫描这个工具按着后续的开发只会在linux平台运行，所以不再需要判断平台
直接按照linux来即可
暂停编写 by swm 20200320
"""
import json
import threading
import uuid
from pathlib import Path
from subprocess import Popen, PIPE
from ....clientdatafeedback.scoutdatafeedback import PortInfo
from datacontract.iscandataset.iscantask import IscanTask

from idownclient.config_task import clienttaskconfig
from ..scantoolbase import ScanPlugBase


class Masscan(ScanPlugBase):
    _outfi_locker = threading.Lock()

    def __init__(self):
        ScanPlugBase.__init__(self, 'masscan')
        self.tmp_path: Path = clienttaskconfig.tmppath
        self.scan_dir = self.tmp_path / 'scandir'
        self.scan_dir.mkdir(exist_ok=True, parents=True)
        self.timeout = 30  # 这个是命令执行完成后多少秒没有结束进程强制结束，单位:/s

    def init_masscan(self):
        """
        查看masscan是否安装，如果没有安装会报错
        不使用masscan --regress 每次检测的时间太长了快要5分钟了
        直接在docker环境里面运行命令即可
        :return:
        """
        proc = Popen(f'masscan --regress', stdout=PIPE, shell=True)
        outs, errs = proc.communicate(timeout=15)
        res = outs.decode('utf-8')
        print(res)

    def masscan_scan(self, hosts: list, ports: list, *args) -> Path:
        """
        masscan扫描
        :return:
        """
        outfi: Path = None
        try:
            cmd = 'masscan '
            cmd += ','.join(hosts)
            # 转换需要将list里面的int转换为str，无论如何转一次保证0
            strports = [str(el) for el in ports]
            cmd += ' -p' + ','.join(strports)
            with self._outfi_locker:
                outfi: Path = self.scan_dir / str(uuid.uuid1())
                while outfi.exists():
                    outfi: Path = self.scan_dir / str(uuid.uuid1())
            cmd += f' -oJ {outfi.as_posix()}'
            self._logger.debug(cmd)
            p: Popen = None
            try:
                p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True,
                          universal_newlines=True)
                stdout, stderr = p.communicate()
                exitcode = p.wait(timeout=15)
                if stdout is not None:
                    self._logger.trace(stdout)
                if stderr is not None:
                    self._logger.trace(stderr)
                if exitcode != 0:
                    raise Exception(f"Masscan error, {stdout}\n{stderr}")
            finally:
                if p is not None:
                    p.kill()
        except Exception as error:
            self._logger.error(f'Masscan error, err:{error}')
            if outfi is not None and outfi.exists():
                outfi.unlink()
            outfi = None

        return outfi

    def parse_masscan_result(self, task: IscanTask, level, outfi: Path, transprotocol='tcp') -> iter:
        """
        解析masscan的扫描结果
        返回的结果为portinfo
        :param task:
        :param outfi:
        :return:
        """
        if not outfi.exists():
            return

        with outfi.open('r', encoding='utf-8') as fp:
            msscan_res = fp.read()

        try:
            msres_dict = json.loads(msscan_res)
        except:
            self._logger.error(f"Masscan not get the result, res:{msres_dict}")
            return
        for el in msres_dict:
            ip = el.get('ip')
            for p in el.get('ports', []):
                port = p.get('port')
                pinfo: PortInfo = PortInfo(task, level, ip, int(port), transprotocol)
                yield pinfo

    def scan_open_ports(self, task: IscanTask, level: int, hosts: list, ports: list, *args) -> iter:
        """
        masscan开放端口的扫描
        :param task:
        :param level:
        :param hosts:
        :param ports:
        :param args:
        :return:
        """
        if not isinstance(hosts, list) or len(hosts) < 1:
            return

        outfi = None

        try:
            outfi = self.masscan_scan(hosts, ports)

            if outfi is None or not outfi.exists():
                return

            for port in self.parse_masscan_result(task, level, outfi):
                yield port
        except Exception as error:
            self._logger.error(f'Scan error, taskid:{task.taskid}, batchid:{task.batchid}, error:{error}')
        finally:
            if outfi is not None and outfi.exists():
                outfi.unlink()


