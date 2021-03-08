"""proxy manager"""

# -*- coding:utf-8 -*-

import queue
import threading
import time
import traceback

from ..countrycodes import ALL_COUNTRIES
from ..design.singleton import SingletonDecorator, SingletonInstance
from ..mslog.loghook import LogHook
from ..mslog.msloglevel import MsLogLevel, MsLogLevels
from .eproxyanonymity import EProxyAnonymity
from .proxydbconfig import ProxyDbConfig
from .proxyitem import ProxyItem
from .proxypool import ProxyPool
from .proxysetting import ProxySetting
from .proxyspiderbase import ProxySpiderbase


# @SingletonDecorator
class ProxyManager(object):
    """provide uniform proxy API\n
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
    manager.dispose()\n"""

    @property
    def proxypool_fullfilled(self) -> bool:
        """返回当前proxymanager管理的代理IP池中的代理IP是否已达到上限"""
        return self.__proxy_pool.full_filled

    @property
    def proxypool_curr_count(self) -> int:
        """返回当前proxymanager管理的代理IP池中的代理IP数量"""
        return self.__proxy_pool.curr_proxy_count

    def __init__(
            self,
            proxy_fetch_thread_count: int = 1,
            max_pool_item_count: int = 100,
            verify_thread_count: int = 5,
            recheck_interval_sec: float = 600,
            dbconfig: ProxyDbConfig = None,
            logger_hook: callable = None,
            proxyspiders: list = None,
    ):
        self._logger: LogHook = LogHook(logger_hook)
        self._max_pool_item_count: int = max_pool_item_count
        self._verify_thread_count: int = 5
        if isinstance(verify_thread_count, int) and verify_thread_count > 0:
            self._verify_thread_count = verify_thread_count
        self._recheck_interval_sec: float = 600
        if type(recheck_interval_sec) in [int, float
                                          ] and recheck_interval_sec > 10:
            self._recheck_interval_sec = recheck_interval_sec

        # 代理IP采集线程数
        self._proxy_fetch_thread_count: int = 1
        if not isinstance(proxy_fetch_thread_count,
                          int) or proxy_fetch_thread_count < 0:
            raise Exception(
                "Invalid parma proxy_fetch_thread_count: {}".format(
                    proxy_fetch_thread_count))
        self._proxy_fetch_thread_count = proxy_fetch_thread_count

        # 代理IP采集线程 {spider: [thread1, thread2] }
        self.__t_fetch_start: bool = False
        self.__t_fetches: dict = {}
        self.__t_fetches_locker = threading.RLock()

        # 代理IP验证线程
        self._q_verify: queue.Queue = queue.Queue()
        self.__t_verifys: list = []
        self.__t_verify_locker = threading.RLock()
        self.__t_verify_started: bool = False
        for i in range(self._verify_thread_count):
            t = threading.Thread(target=self._proxy_verify, daemon=True)
            self.__t_verifys.append(t)

        # 库中已有代理IP重检验线程
        self.__t_recheck = threading.Thread(
            target=self._proxy_recheck, daemon=True)
        self.__t_recheck_locker = threading.RLock()
        self.__t_recheck_started: bool = False

        # 获取的代理IP参数
        self.__proxy_settings_locker = threading.RLock()
        self.__default_proxy_setting: ProxySetting = ProxySetting()
        self.__proxy_settings: list = []
        self.__proxy_settings.append(ProxySetting())

        # 采集器
        self.__spiders: dict = {}
        self.__spiders_locker = threading.RLock()
        self._t_task_dispatch = threading.Thread(
            target=self.__task_dispatch, daemon=True)

        # 抓取任务池
        self.__task_queue: queue.Queue = queue.Queue()

        # 本地代理池
        self.__proxy_pool: ProxyPool = ProxyPool(
            dbconfig=dbconfig,
            maxitemcount=self._max_pool_item_count,
            logger_hook=logger_hook,
        )

        if isinstance(proxyspiders, list) and len(proxyspiders) > 0:
            for spd in proxyspiders:
                self.append_custom_proxy_spider(spd)

        # 其他
        self.__disposed: bool = False
        self.__disposed_locker = threading.RLock()

    ###############################################
    # start/stop

    def _init_spider_threads(self):
        """每次调用start_fetch_proxy函数，
        或新增一个Spider，都会重新检测并初始化新的
        spider抓取线程"""
        with self.__t_fetches_locker:
            for spider in self.__spiders.keys():
                if not self.__t_fetches.__contains__(spider):
                    self.__t_fetches[spider] = []

                for i in range(self._proxy_fetch_thread_count):
                    t = threading.Thread(
                        target=self.__fetch_proxies,
                        args=(spider,),
                        daemon=True)
                    self.__t_fetches[spider].append(t)

    def start_fetch_proxy(self):
        """开始抓取代理IP"""
        if len(self.__spiders) < 1:
            self._logger.info("No proxy spider available...")
            return

        # proxy verify threads
        if not self.__t_verify_started:
            with self.__t_verify_locker:
                if not self.__t_verify_started:
                    for t in self.__t_verifys:
                        t.start()
                    self.__t_verify_started = True

        # proxy recheck thread
        if not self.__t_recheck_started:
            with self.__t_recheck_locker:
                if not self.__t_recheck_started:
                    self.__t_recheck.start()
                    self.__t_recheck_started = True

        if self.__t_fetch_start:
            self._logger.debug("Proxy spiders are already running.")
            return
        with self.__t_fetches_locker:
            # proxy fetch threads
            if not self.__t_fetch_start:
                self.__t_fetch_start = True

                if not self._t_task_dispatch._started._flag:
                    self._t_task_dispatch.start()

                self._init_spider_threads()
                for tlist in self.__t_fetches.values():
                    for t in tlist:
                        if not t._started._flag:
                            t.start()
                self._logger.debug("Proxy spiders started.")
            else:
                self._logger.debug("Proxy spiders are already running.")

    def stop_fetch_proxy(self):
        """停止抓取代理IP"""
        with self.__t_fetches_locker:
            self.__t_fetch_start = False
            self._logger.info("Proxy spiders stoped.")

    ###############################################
    # proxy fetching settings

    def set_proxy_fetch_settings(self, proxysetting: ProxySetting):
        """覆盖设置当前的代理IP抓取设置"""
        if not isinstance(proxysetting, ProxySetting):
            raise Exception("Invalid {}: {}".format(
                type(ProxySetting).__name__, proxysetting))

        with self.__proxy_settings_locker:
            self.__proxy_settings.clear()
            self.__proxy_settings.append(proxysetting)

    def append_proxy_fetch_settings(self, proxysetting: ProxySetting):
        """添加设置到当前的代理IP抓取设置"""
        if not isinstance(proxysetting, ProxySetting):
            raise Exception("Invalid {}: {}".format(
                type(ProxySetting).__name__, proxysetting))

        if any(p == proxysetting for p in self.__proxy_settings):
            return
        with self.__proxy_settings_locker:
            if any(p == proxysetting for p in self.__proxy_settings):
                return
            self.__proxy_settings.append(proxysetting)

    def remove_proxy_fetch_settings(self, proxysetting: ProxySetting):
        """添加设置到当前的代理IP抓取设置"""
        if not isinstance(proxysetting, ProxySetting):
            raise Exception("Invalid {}: {}".format(
                type(ProxySetting).__name__, proxysetting))

        if not any(p == proxysetting for p in self.__proxy_settings):
            return
        with self.__proxy_settings_locker:
            rm = None
            for p in self.__proxy_settings:
                if p == proxysetting:
                    rm = p
                    break
            self.__proxy_settings.remove(rm)

    ###############################################
    # custom proxy spider settings

    def append_custom_proxy_spider(self, spider: ProxySpiderbase):
        """向当前代理IP管理器添加自定义的代理IP采集器"""
        if not isinstance(spider, ProxySpiderbase):
            raise Exception(
                "Invalid custom Proxy Spider, need to be the subclass of {}".
                    format(type(ProxySpiderbase).__name__))

        if self.__spiders.__contains__(spider):
            return
        with self.__spiders_locker:
            if self.__spiders.__contains__(spider):
                return
            self.__spiders[spider] = None

    def remove_custom_proxy_spider(self, spider: ProxySpiderbase):
        """删除前代理IP管理器中的指定代理IP采集器"""
        if not isinstance(spider, ProxySpiderbase):
            raise Exception(
                "Invalid custom Proxy Spider, need to be the subclass of {}".
                    format(type(ProxySpiderbase).__name__))

        if not self.__spiders.__contains__(spider):
            return
        with self.__spiders_locker:
            if not self.__spiders.__contains__(spider):
                return
            self.__spiders.pop(spider, None)

    ###############################################
    # get proxyitem

    @property
    def pool(self) -> ProxyPool:
        """返回当前代理池管理器的代理池对象，用于获取代理IP"""
        return self.__proxy_pool

    ###############################################
    # proxy fetch control

    def __task_dispatch(self):
        """代理采集任务分配"""
        curr_settings: list = None
        while True:
            try:
                while self.__task_queue.qsize(
                ) > 20 or self.__proxy_pool._full_filled:
                    time.sleep(1)

                curr_settings = None
                with self.__proxy_settings_locker:
                    curr_settings = self.__proxy_settings.copy()

                for setting in curr_settings:

                    self.__task_queue.put(setting)

                    while self.__task_queue.qsize(
                    ) > 20 or self.__proxy_pool._full_filled:
                        time.sleep(1)

            except queue.Empty:
                pass
            except Exception:
                self._logger.error("Proxy task dispatch error: {}".format(
                    traceback.format_exc()))

    def __fetch_proxies(self, spider: ProxySpiderbase):
        """代理IP采集线程"""
        got: bool = True
        while True:
            try:
                while not self.__t_fetch_start or self.__proxy_pool._full_filled:
                    time.sleep(1)

                got = False
                proxysetting: ProxySetting = self.__task_queue.get(timeout=3)
                got = True

                for proxyitem in spider.get_proxy(proxysetting):
                    while self.__proxy_pool._full_filled:
                        time.sleep(1)

                    while self._q_verify.qsize() >= 100:
                        time.sleep(1)

                    self._q_verify.put(proxyitem)
                    self._logger.trace("Got proxyitem: {}:{} {} {} {}".format(
                        proxyitem._ip,
                        proxyitem._port,
                        proxyitem._proxytype.name,
                        proxyitem._anonymous.name,
                        'ssl' if proxyitem.is_ssl else '',
                    ))

            except queue.Empty:
                pass
            except Exception:
                self._logger.error('Fetch proxy error: {}'.format(
                    traceback.format_exc()))
            finally:
                if got:
                    self.__task_queue.task_done()

    ###############################################
    # proxy verify

    def _proxy_verify(self):
        """验证代理IP的有效性"""
        got: bool = False
        while True:
            try:
                got = False
                proxyitem: ProxyItem = self._q_verify.get(timeout=3)
                got = True

                if not isinstance(proxyitem, ProxyItem):
                    continue

                if not proxyitem._is_verified:
                    if not proxyitem.verify_try():
                        continue

                self.__proxy_pool.append_proxyitem(proxyitem)
                self._logger.trace(
                    "Append verified proxyitem OK: {}:{} {} {} {}".format(
                        proxyitem._ip,
                        proxyitem._port,
                        proxyitem._proxytype.name,
                        proxyitem._anonymous.name,
                        'ssl' if proxyitem.is_ssl else '',
                    ))
            except queue.Empty:
                # 队列里没东西了才开始睡眠
                while not self.__t_fetch_start:
                    time.sleep(1)
            except Exception:
                self._logger.error("Proxy verify error: {}".format(
                    traceback.format_exc()))
            finally:
                if got:
                    self._q_verify.task_done()

    ###############################################
    # proxy in db recheck

    def _proxy_recheck(self):
        """库中已有IP重新检验线程"""
        while True:
            try:
                for proxyitem in self.pool._pop_items_verify_required(
                        self._recheck_interval_sec):
                    if not isinstance(proxyitem, ProxyItem):
                        continue

                    self._q_verify.put(proxyitem)

            except Exception:
                self._logger.error("Proxy recheck error: {}".format(
                    traceback.format_exc()))
            finally:
                time.sleep(10)
