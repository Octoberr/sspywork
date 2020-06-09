"""
masscan 单元性尝试
create by judy 2020/05/28
"""
import threading
import uuid
from pathlib import Path
from subprocess import Popen, PIPE


class Masscan(object):

    def __init__(self):
        self.scan_dir = Path('./swmdir')
        self.scan_dir.mkdir(exist_ok=True)
        self._outfi_locker = threading.Lock()

    def _init_masscan(self):
        """
        查看masscan是否安装
        不测试，实例化的时间太长了，快要3分钟了
        在docker环境里面直接运行命令即可
        :return:
        """
        proc = Popen(f'masscan --regress', stdout=PIPE, shell=True)
        outs, errs = proc.communicate(timeout=15)
        res = outs.decode('utf-8')
        print(res)

    def masscan_scan(self, hosts: list, ports: list):
        """
        masscan扫描
        :return:
        """
        cmd = 'masscan '
        cmd += ','.join(hosts)
        # 转换需要将list里面的int转换为str
        strports = [str(el) for el in ports]
        cmd += ' -p' + ','.join(strports)
        with self._outfi_locker:
            outfi: Path = self.scan_dir / str(uuid.uuid1())
            while outfi.exists():
                outfi: Path = self.scan_dir / str(uuid.uuid1())
        cmd += f' -oJ {outfi.as_posix()}'
        print(cmd)
        p: Popen = None
        try:
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True, universal_newlines=True)
            stdout, stderr = p.communicate()
            exitcode = p.wait(timeout=15)
            if stdout is not None:
                print(stdout)
            if stderr is not None:
                print(stderr)
            if exitcode != 0:
                raise Exception(f"Masscan error, {stdout}\n{stderr}")
        finally:
            if p is not None:
                p.kill()




if __name__ == '__main__':
    ms = Masscan()
    ms.masscan_scan(['45.192.106.0/23'], [80])
