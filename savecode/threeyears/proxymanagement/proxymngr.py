"""proxy management"""

# -*- coding:utf-8 -*-

import threading
import time
import traceback

from commonbaby.design import SingletonDecorator
from commonbaby.mslog import MsLogger, MsLogLevel, MsLogLevels, MsLogManager
from commonbaby.proxy import (EProxyAnonymity, EProxyType, ProxyDbConfig,
                              ProxyItem, ProxyManager, ProxyPool, ProxySetting,
                              ProxySpiderbase)
from .staticproxy import luminati_proxy_dict


class ProxyMngr(object):
    """
    此类的初始化参数只有在第一次实例化时生效，
    后面再实例化就是直接返回以前创建好的实例对象的引用\n
    用法：\n
    直接实例化 ProxyMngr 对象\n
    或使用 ProxyMngr.static_init()都可以\n
    使用流程：\n
    1. 创建你的ProxySpider，继承于ProxySpiderbase，并实现。\n
    manager = ProxyManager()\n
    spider = 你的ProxSpider()\n
    manager.append_custom_proxy_spider(spider)\n
    manager.append/set_proxy_fetch_settings(params)\n
    manager.start_fetch_proxy()\n
    ProxyItem = manager.get_one_proxy(params)\n
    proxies = manager.get_proxies(count, params)\n
    manager.stop_fetch_proxy()\n
    manager.dispose()\n
    """

    __inst: ProxyManager = None
    __inst_locker = threading.RLock()
    __inst_initialed: bool = False

    _logger: MsLogger = None
    _pool: ProxyPool = None

    @classmethod
    def proxypool_fullfilled(cls) -> bool:
        """返回当前proxymanager管理的代理IP池中的代理IP数量是否已达到上限"""
        return cls.__inst.proxypool_fullfilled

    @classmethod
    def proxypool_curr_count(cls) -> int:
        """返回当前proxymanager管理的代理IP池中的代理IP数量"""
        return cls.__inst.proxypool_curr_count

    @classmethod
    def static_init(
            cls,
            proxy_fetch_thread_count: int = 1,
            max_pool_item_count: int = 100,
            verify_thread_count: int = 5,
            recheck_interval_sec: float = 180,
            dbconfig: ProxyDbConfig = None,
            logger_hook=None,
            proxyspiders: list = None,
    ):
        """
        provide uniform proxy API\n
        proxy_fetch_thread_count: 设置每一个代理抓取插件的抓取线程数\n
        max_pool_item_count: 设置本地代理池最大代理IP数量，超过此数量将暂停抓取\n
        verify_thread_count: 代理IP有效性验证的线程数\n
        recheck_interval_sec: 库中已有代理IP重新验证时间间隔，秒\n
        dbconfig: 本地存储配置\n
        logger_hook: 传入一个函数，用于打印日志，函数参数为：\n
            log_func(self, msg:str, level: MsLogLevel)\n
        proxyspiders: 代理IP爬虫实例列表\n
                
        使用流程：
        1. 创建你的ProxySpider，继承于ProxySpiderbase，并实现。\n
        manager = ProxyManager()\n
        spider = 你的ProxSpider()\n
        manager.append_custom_proxy_spider(spider)\n
        manager.append/set_proxy_fetch_settings(params)\n
        manager.start_fetch_proxy()\n
        ProxyItem = manager.get_one_proxy(params)\n
        proxies = manager.get_proxies(count, params)\n
        manager.stop_fetch_proxy()\n
        manager.dispose()\n
        """

        if cls.__inst_initialed:
            return
        with cls.__inst_locker:
            if cls.__inst_initialed:
                return

            cls._logger = MsLogManager.get_logger(ProxyMngr.__name__)

            if not callable(logger_hook):
                logger_hook = cls._loghook
            cls.__inst: ProxyManager = ProxyManager(
                proxy_fetch_thread_count=proxy_fetch_thread_count,
                max_pool_item_count=max_pool_item_count,
                verify_thread_count=verify_thread_count,
                recheck_interval_sec=recheck_interval_sec,
                dbconfig=dbconfig,
                logger_hook=logger_hook,
                proxyspiders=proxyspiders,
            )

            cls._pool = cls.__inst.pool

            cls.__inst_initialed = True

    def __init__(
            self,
            proxy_fetch_thread_count: int = 1,
            max_pool_item_count: int = 100,
            dbconfig: ProxyDbConfig = None,
            logger_hook=None,
            proxyspiders: list = None,
    ):
        if ProxyMngr.__inst_initialed:
            return
        with ProxyMngr.__inst_locker:
            if ProxyMngr.__inst_initialed:
                return

            ProxyMngr.static_init(
                proxy_fetch_thread_count=proxy_fetch_thread_count,
                max_pool_item_count=max_pool_item_count,
                dbconfig=dbconfig,
                logger_hook=logger_hook,
                proxyspiders=proxyspiders,
            )

    @classmethod
    def _loghook(cls, msg: str, lvl: MsLogLevel):
        if msg is None or not isinstance(msg, str):
            return
        cls._logger.log(msg, lvl)

    ###############################################
    # start/stop
    @classmethod
    def start_fetch_proxy(cls):
        cls.__inst.start_fetch_proxy()

    @classmethod
    def stop_fetch_proxy(cls):
        cls.__inst.stop_fetch_proxy()

    ###############################################
    # proxy fetching settings
    @classmethod
    def set_proxy_fetch_settings(cls, proxysetting: ProxySetting):
        """覆盖设置当前的代理IP抓取设置"""
        cls.__inst.set_proxy_fetch_settings(proxysetting)

    @classmethod
    def append_proxy_fetch_settings(cls, proxysetting: ProxySetting):
        """添加设置到当前的代理IP抓取设置"""
        cls.__inst.append_proxy_fetch_settings(proxysetting)

    @classmethod
    def remove_proxy_fetch_settings(cls, proxysetting: ProxySetting):
        """删除设置到当前的代理IP抓取设置"""
        cls.__inst.__instance.remove_proxy_fetch_settings(proxysetting)

    ###############################################
    # custom proxy spider settings
    @classmethod
    def append_custom_proxy_spider(cls, spider: ProxySpiderbase):
        """向当前代理IP管理器添加自定义的代理IP采集器"""
        cls.__inst.append_custom_proxy_spider(spider)

    @classmethod
    def remove_custom_proxy_spider(cls, spider: ProxySpiderbase):
        """删除前代理IP管理器中的指定代理IP采集器"""
        cls.__inst.remove_custom_proxy_spider(spider)

    ###############################################
    # get proxyitem

    @classmethod
    def get_one_by_setting_nowait(cls, setting: ProxySetting) -> ProxyItem:
        """返回指定配置的代理IP对象，并将其从库中移除，若没有则返回None"""
        return cls._pool.get_one_by_setting(setting)

    @classmethod
    def get_one_by_setting(
            cls,
            setting: ProxySetting,
            timeout: int = 30,
    ) -> ProxyItem:
        """
        wait for a proxyitem, until timeout(second),\n
        timeout: -1为无限等待
        """
        p = None
        try:
            p = cls.get_one_by_setting_nowait(setting)
            failedtimes = 0
            while p is None:
                try:
                    p = cls.get_one_by_setting_nowait(setting)
                    if not p is None:
                        break

                    time.sleep(1)
                    failedtimes += 1
                    if timeout >= 0 and failedtimes > timeout:
                        break

                except Exception:
                    failedtimes += 1
        except Exception:
            cls._logger.debug("Get proxyitem by setting error: {}".format(
                traceback.format_exc()))
        return p

    @classmethod
    def get_one_crosswall_nowait(
            cls,
            proxytype: EProxyType = EProxyType.HTTP,
            ssl: bool = True,
    ) -> ProxyItem:
        """返回一个国外的代理IP对象，并将其从库中移除，若没有则返回None"""
        return cls._pool.get_one_crosswall(proxytype=proxytype, ssl=ssl)

    @classmethod
    def get_one_crosswall(
            cls,
            proxytype: EProxyType = EProxyType.HTTP,
            ssl: bool = True,
            timeout=30,
    ):
        """
         -> ProxyItem
        返回一个国外的代理IP对象，并将其从库中移除，若没有则返回None"""
        p = None
        # return p
        try:
            p = cls.get_one_crosswall_nowait(proxytype=proxytype, ssl=ssl)
            failedtimes = 0
            while p is None:
                try:
                    p = cls.get_one_crosswall_nowait(proxytype=proxytype,
                                                     ssl=ssl)
                    if not p is None:
                        break

                    time.sleep(1)
                    failedtimes += 1
                    if timeout >= 0 and failedtimes > timeout:
                        break

                except Exception:
                    failedtimes += 1
        except Exception:
            cls._logger.debug("Get proxyitem by setting error: {}".format(
                traceback.format_exc()))
        return p

    @classmethod
    def get_one_internal_nowait(
            cls,
            proxytype: EProxyType = EProxyType.HTTP,
            ssl: bool = True,
    ) -> ProxyItem:
        """返回一个国内的代理IP对象，并将其从库中移除，若没有则返回None"""
        return cls._pool.get_one_internal(proxytype=proxytype, ssl=ssl)

    @classmethod
    def get_one_internal(
            cls,
            proxytype: EProxyType = EProxyType.HTTP,
            ssl: bool = True,
            timeout=30,
    ) -> ProxyItem:
        """返回一个国内的代理IP对象，并将其从库中移除，若没有则返回None"""
        p = None
        try:
            p = cls.get_one_internal_nowait(proxytype=proxytype, ssl=ssl)
            failedtimes = 0
            while p is None:
                try:
                    p = cls.get_one_internal_nowait(proxytype=proxytype, ssl=ssl)
                    if not p is None:
                        break

                    time.sleep(1)
                    failedtimes += 1
                    if timeout >= 0 and failedtimes > timeout:
                        break

                except Exception:
                    failedtimes += 1
        except Exception:
            cls._logger.debug("Get proxyitem by setting error: {}".format(
                traceback.format_exc()))
        return p

    @classmethod
    def get_static_proxy(cls) -> dict:
        """
        获取一个静态的代理字典
        代理的ip已经固定了，不再需要频繁去获取
        目前只有luminati网站的固定ip那么就直接返回了
        后续增加了新的静态代理ip写逻辑
        update by judy 2020/10/27
        """
        return luminati_proxy_dict


################################################
# sample:
def test_proxy():
    """这个函数拷贝出去就可以测"""
    from .proxyspiders import Goubanjia
    ProxyMngr.static_init(proxyspiders=[
        Goubanjia(),
    ])

    ProxyMngr.start_fetch_proxy()

    while True:
        try:
            p = ProxyMngr.get_one_internal()
            if p is None:
                continue
            print("{}:{}    {}  {}".format(p._ip, p._port, p._proxytype.name,
                                           p._anonymous.name))
            print("fullfilled: {}    total_in_db: {}".format(
                ProxyMngr.proxypool_fullfilled(),
                ProxyMngr.proxypool_curr_count()))
            # time.sleep(1)
        except Exception as e:
            traceback.print_exc()
        finally:
            time.sleep(1)
