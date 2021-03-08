"""
获取当前电脑的运行状态
包括cpu，内存，存储，或者gpu
create by judy 2018/10/19

update by judy 2019/03/05
更改为统一输出output
"""
from datetime import datetime
import threading
import time
import traceback

import psutil
import pytz

from datacontract import StatusBasic
from idownclient.config_client import basic_client_config
from idownclient.config_task import clienttaskconfig
from outputmanagement import OutputManagement


class ClientBasicInfo(object):

    def __init__(self):
        self._clientinfo = {}
        # self.suffix = '.idown_status_basic'
        # cpu 使用率
        self._cpu_per: float = 1.0
        # 下载速度
        self._net_per: float = 1.0
        self._period = basic_client_config.period

    def _get_cpu_per(self):
        """
        每15秒获取一次cpu的使用率
        :return:
        """
        while True:
            self._cpu_per = psutil.cpu_percent(self._period)

    def _get_net_per(self):
        """
        15秒获取一次cpu的
        :return:
        """
        while True:
            net_before = psutil.net_io_counters().bytes_recv
            time.sleep(self._period)
            net_after = psutil.net_io_counters().bytes_recv
            self._net_per = (net_after - net_before) / self._period

    def get_basic_status_info(self):
        cpu_per = threading.Thread(target=self._get_cpu_per)
        cpu_per.start()
        net_per = threading.Thread(target=self._get_net_per)
        net_per.start()
        # 内存
        virtual = psutil.virtual_memory()
        self._clientinfo['memsize'] = virtual.total  # 内存总大小
        self._clientinfo['memperc'] = virtual.percent  # 内存使用率
        # 硬盘
        diskinfo = psutil.disk_usage(clienttaskconfig.driver)
        self._clientinfo['disksize'] = diskinfo.total  # 使用硬盘的总大小
        self._clientinfo['diskperc'] = diskinfo.percent  # 硬盘的使用率

        self._clientinfo['time'] = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        self._clientinfo['clientid'] = basic_client_config.clientid
        self._clientinfo['systemver'] = basic_client_config.systemver
        self._clientinfo['ip'] = basic_client_config.ip
        self._clientinfo['mac'] = basic_client_config.mac
        self._clientinfo['country'] = basic_client_config.country
        self._clientinfo['crosswall'] = basic_client_config.crosswall
        self._clientinfo['platform'] = basic_client_config.platform
        self._clientinfo['apptype'] = basic_client_config.apptype
        self._clientinfo['tasktype'] = basic_client_config.tasktype
        self._clientinfo['appclassify'] = basic_client_config.appclassify
        self._clientinfo['cpusize'] = basic_client_config.cpusize
        self._clientinfo['cpuperc'] = str(self._cpu_per)
        self._clientinfo['bandwidthd'] = basic_client_config.bandwidthd
        self._clientinfo['bandwidthdperc'] = str(self._net_per)
        self._clientinfo['updatetime'] = datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
        self._clientinfo['clientbusiness'] = basic_client_config.clientbusiness
        return

    def start(self):
        while True:
            try:
                self.get_basic_status_info()
                lines = StatusBasic(self._clientinfo)
                OutputManagement.output(lines)
            except:
                print(f"Write clientbasicstatus info error, err:{traceback.format_exc()}")
            finally:
                time.sleep(clienttaskconfig.collect_client_times)
