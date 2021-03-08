"""proxy spiderbase"""

# -*- coding:utf-8 -*-

from abc import ABCMeta, abstractmethod
from enum import Enum

from ..countrycodes import ALL_COUNTRIES
from .eproxyanonymity import EProxyAnonymity
from .proxyitem import ProxyItem
from .proxysetting import ProxySetting


class ProxySpiderbase:
    """ProxySpiderbase.
    Provide uniform Proxy Spider API\n
    :param spider_crosswall: 指示当前爬虫爬代理IP是否需要翻墙"""

    __metaclass = ABCMeta

    def __init__(
            self,
            spider_crosswall: bool,
    ):
        if not isinstance(spider_crosswall, bool):
            raise Exception("Invalid param 'spider_crosswall' for PorxySpider")

        self._spider_crosswall: bool = spider_crosswall

    def get_proxy(
            self,
            proxysetting: ProxySetting,
    ) -> iter:
        """
        proxysetting: 指定代理要抓取的代理IP的相关参数配置\n
        return ProxyItem\n
        返回 ProxyItem"""
        if not isinstance(proxysetting, ProxySetting):
            raise Exception("Invalid {}: {}".format(
                type(ProxySetting).__name__, proxysetting))

        return self._get_proxy_sub(proxysetting)

    def _get_proxy_sub(
            self,
            proxysetting: ProxySetting,
    ) -> iter:
        """
        proxysetting: 指定代理要抓取的代理IP的相关参数配置\n
        return ProxyItem\n
        返回 ProxyItem"""
        raise NotImplementedError(
            "Subclasses should implement this method to fetch proxies")
