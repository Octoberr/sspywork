"""nmap config"""

# -*- coding:utf-8 -*-


class NmapConfig:
    """nmap config"""

    def __init__(
            self,
            maxthread: int = 5,
            timeout: float = 600,
            sudo: bool = False,
            nmappath=[
                'nmap', '/usr/bin/nmap', '/usr/local/bin/nmap', '/sw/bin/nmap',
                '/opt/local/bin/nmap'
            ],
    ):

        self.maxthread: int = 5
        if isinstance(maxthread, int):
            self.maxthread = maxthread

        self.timeout: float = 600  # 600秒
        if type(timeout) in [int, float]:
            self.timeout = timeout

        self.sudo: bool = False
        if isinstance(sudo, bool):
            self.sudo = sudo

        self.nmappath: list = [
            'nmap', '/usr/bin/nmap', '/usr/local/bin/nmap', '/sw/bin/nmap',
            '/opt/local/bin/nmap'
        ]
        if isinstance(nmappath, list) and len(nmappath) > 0:
            self.nmappath = nmappath

        # self.scanargs: list = [
        #     # 禁用主机发现，就好像每个主机都是活动的（也确实是，因为经过了预扫描）
        #     '-Pn',
        #     # 不用在扫描时对ip进行域名反解析（因为一般会很慢，且用户任务下发时是反解了域名过来的）
        #     '-n',
        #     # 指定速度
        #     '-T4',
        #     # 启用服务版本探测
        #     '-sV',
        #     # 启用操作系统探测
        #     '-O',
        #     # 只针对活动的主机进行操作系统检测
        #     '--osscan-limit',
        #     # 只输出开放的端口
        #     '--open',
        #     # 每秒发包最少多少个
        #     '--min-rate 100',
        #     # 最小同时扫描的主机数
        #     '--min-hostgroup 256',
        #     # 探针失败重试次数
        #     '--max-retries 2',
        #     # 对一个主机发送两个探测报文之间的等待时间(毫秒)，可以控制带宽，和用于躲避IPS
        #     '--max-scan-delay 10',
        #     # 扫描网站http响应头 (absoluted..use zgrab instead)
        #     #'--script http-headers',
        #     # 扫描网站http响应体 (absoluted..use zgrab instead)
        #     #'--script http-fetch',
        # ]
        # if isinstance(scanargs, list) and len(scanargs) > 0:
        #     self.scanargs = scanargs