"""proxy config"""

# -*- coding:utf-8 -*-

from commonbaby.proxy import ProxyDbConfig


class ProxyConfig:
    """"""

    def __init__(
            self,
            proxy_fetch_thread_count: int = 1,
            max_pool_item_count: int = 100,
            dbconfig: ProxyDbConfig = None,
            proxyspiders: list = None,
    ):
        pass