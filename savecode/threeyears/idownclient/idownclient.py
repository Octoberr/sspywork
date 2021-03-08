"""
Author: judy
Date: 2020-10-29 17:39:19
LastEditTime: 2020-11-09 09:30:55
LastEditors: judy
Description: 使用新的编译器
FilePath: \idown_new\idownclient\idownclient.py
"""

import threading
import time
import traceback

from commonbaby.mslog import MsLogger, MsLogManager, MsLogLevel

from datacontract import EClientBusiness, InputData
from inputmanagement.inputmanagement import InputManagement
from outputmanagement import OutputManagement
from proxymanagement import ProxyMngr, proxyspiders, ProxySetting
from .autotaskmanagement import AutoTaskDownloadManager
from .clientdbmanager import DbManager
from .clientstatus.clientstatusstart import CollectClientInfo

# 任务线程开关配置
from .config_client import basic_client_config
from .config_input import inputconfig
from .config_output import outputconfig
from .config_outputstandard import stdconfig
from .iscanmanagement import ScanDownloadManager
from .iscoutmanagement import ScoutDownloadManager
from .taskmanagement.taskcookiealive import TaskCookieAlive
from .taskmanagement.taskdownload import TaskDownload
from .taskmanagement.taskmanager import TaskManager
from .tools import DPPF

NAME = "IdownClient"
VERSION = "1.1.3"
DATE = "2020.11.25"


class IDownClient:
    """idown client"""

    def __init__(self):
        self._logger: MsLogger = MsLogManager.get_logger("IdownClient")
        # 初始化sqlite, 最开始就初始化，因为需要存入数据和读取数据
        DbManager()
        self._inputmanagement = InputManagement(inputconfig, self.on_data_in)
        # proxy代理池管理器
        self._loaded_proxy_spiders = []
        # self._init_proxy()
        #  --------------------------------task相关
        self._taskmanger = TaskManager()
        self._taskdownload = TaskDownload()
        self._cookie_keeper = TaskCookieAlive()
        self._clientcollect = CollectClientInfo()
        # 新增iscantask下载启动
        self._iscandownload = ScanDownloadManager()
        # 新增iscouttask下载启动
        self._iscoutdownload = ScoutDownloadManager()
        # 新增autotask下载启动
        self._automateddownload = AutoTaskDownloadManager()
        # 新增删除程序产生无用文件 by judy 2020/08/20
        self._dppf = DPPF()
        # 初始化输出器
        OutputManagement.static_initial(outputconfig, stdconfig)
        # 任务启动开关
        self.__switch = eval(basic_client_config.clientbusiness)
        self.all_business = EClientBusiness.ALL.value

    def log_func(self, msg: str, level: MsLogLevel):
        self._logger.log(msg, level)

    def _init_proxy(self):
        """初始化代理池"""
        self._loaded_proxy_spiders.append(proxyspiders.QiYunProxy())
        ProxyMngr.static_init(
            max_pool_item_count=50,
            verify_thread_count=10,
            proxyspiders=self._loaded_proxy_spiders,
            logger_hook=self.log_func,
        )

        ProxyMngr.set_proxy_fetch_settings(
            ProxySetting(count=50, is_ssl=True, countrycode="US")
        )
        ProxyMngr.start_fetch_proxy()
        tproxylog = threading.Thread(target=self.proxy_log)
        tproxylog.start()

    def proxy_log(self):
        """日志记录代理池状态"""
        while True:
            try:
                self._logger.info(
                    "ProxyStatus: available count={}  fullfilled={}".format(
                        ProxyMngr.proxypool_curr_count(),
                        ProxyMngr.proxypool_fullfilled(),
                    )
                )
            except Exception:
                self._logger.error(
                    "ProxyStatus log error: {}".format(traceback.format_exc())
                )
            finally:
                # 2分半钟打印一次数据
                time.sleep(150)

    def start(self):
        """
        多线程并发开启程序
        :return:
        """
        # 读取任务文件，获取任务文件数据流，这个线程是无论如何都要开的
        self._inputmanagement.start()
        # 预先处理任务，idowntask,idowncmd,iscantask,iscout,autotask,cmd是直接入库的
        self._taskmanger.start()
        # 搜集计算机本机的信息
        self._clientcollect.start_collect_client()

        # ----------------------------------------------------------------------后续处理任务的线程
        if (
            self.all_business in self.__switch
            or EClientBusiness.IDownTask.value in self.__switch
        ):
            # 下载idowntask
            self._taskdownload.start()
            self._logger.info("Idown task has been launched")
            # cookie保活，绑定在idowntask，用于保持task是活的
            self._cookie_keeper.start()
            self._logger.info("Idown task cookie_keeper has been launched")
        # -------------------------------新增下载iscantask,by judy 190625
        if (
            self.all_business in self.__switch
            or EClientBusiness.IScanTask.value in self.__switch
        ):
            self._iscandownload.start()
            self._logger.info("Iscan task has been launched")
        # -------------------------------新增下载iscouttask, by judy 190710
        if (
            self.all_business in self.__switch
            or EClientBusiness.IScoutTask.value in self.__switch
        ):
            self._iscoutdownload.start()
            self._logger.info("Iscout task has been launched")
        # -------------------------------新增auto内部下载任务, create by judy 190729
        if (
            self.all_business in self.__switch
            or EClientBusiness.AutoTask.value in self.__switch
        ):
            self._automateddownload.start()
            self._logger.info("Auto task has been launched")
        # 最后开启删除程序产生无用文件
        self._dppf.start()

    def on_data_in(self, data: InputData):
        """
        回调函数获取data
        :param data:
        :return:
        """
        try:
            # data就不可能为None
            if data is None:
                self._logger.error("Input data is None.")
                data.on_complete(False)
                return

            self._taskmanger.on_task_in(data)
        except Exception:
            self._logger.error(
                f"Deal error:\ndata:{data._source}\nex:{traceback.format_exc()}"
            )
            data.on_complete(False)
