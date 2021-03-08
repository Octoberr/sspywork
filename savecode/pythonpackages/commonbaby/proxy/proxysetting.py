"""proxy item"""

# -*- coding:utf-8 -*-

from ..countrycodes import ALL_COUNTRIES
from .eproxyanonymity import EProxyAnonymity
from .eproxytype import EProxyType


class ProxySetting:
    """一个代理IP抓取设置。\n
    默认配置为：\n
    count=100 本次采集代理IP个数\n
    port=None 指定代理IP的端口\n
    proxy_type=None 指定代理IP的类型\n
    is_ssl=None 指定是否需要支持SSL通道\n
    proxy_anonymous=None 指定代理IP的匿名程度\n
    countrycode=None 指定代理IP所属的国家码\n    
    alive_sec=None 指定剩余存活时间不少于（秒）\n
    iptype=None 指定IP地址类型，1：ipv4，2:ipv6\n
    isp=None 指定运营商（字符串包含）\n
    location=None 指定IP地址所在地（字符串包含）\n
    lastverifytime=None 指定最后验证的时刻大于（浮点数时间戳）\n
    response_sec=None 指定响应速度小于（浮点数秒）\n
    """

    # ip: str,
    # port: int,
    # proxy_type: EProxyType = EProxyType.HTTP,
    # is_ssl: bool = False,
    # proxy_anonymous: EProxyAnonymity = EProxyAnonymity.Elite,
    # countrycode: str = None,
    # alive_sec: float = None,
    # iptype: int = 1,
    # isp: str = None,
    # location: str = None,
    # lastverifytime: float = None,
    # response_sec: float = None,
    def __init__(
            self,
            count: int = 100,
            port: int = None,
            proxy_type: EProxyType = None,
            is_ssl: bool = None,
            proxy_anonymous: EProxyAnonymity = None,
            countrycode: str = None,
            alive_sec: float = None,
            iptype: int = None,
            isp: str = None,
            location: str = None,
            lastverifytime: float = None,
            response_sec: float = None,
    ):
        if not isinstance(count, int) or count < 1:
            count = 100
        if not isinstance(port, int) or port < 0 or port > 65535:
            port = None
        if not isinstance(proxy_type, EProxyType):
            proxy_type = None
        if not isinstance(proxy_anonymous, EProxyAnonymity):
            proxy_anonymous = None
        if not ALL_COUNTRIES.__contains__(countrycode):
            countrycode = None

        self.count: int = count
        self.port: int = port
        self.proxytype: EProxyType = proxy_type
        self.is_ssl: bool = is_ssl
        self.anonymous: EProxyAnonymity = proxy_anonymous
        self.countrycode: str = countrycode
        self.alive_sec: float = alive_sec
        self.iptype: int = iptype
        self.isp: str = isp
        self.location: str = location
        self.lastverifytime: float = lastverifytime
        self.response_sec: float = response_sec

    def compare(
            self,
            port: int = None,
            proxy_type: EProxyType = None,
            is_ssl: bool = None,
            proxy_anonymous: EProxyAnonymity = None,
            countrycode: str = None,
            alive_sec: float = None,
            iptype: int = None,
            isp: str = None,
            location: str = None,
            lastverifytime: float = None,
            response_sec: float = None,
    ) -> bool:
        """对比指定配置的值 是否符合当前 setting 指定的配置，符合返回True，不符合返回False"""
        if not self.port is None and port != self.port:
            return False
        if not self.proxytype is None and proxy_type != self.proxytype:
            return False
        if not self.is_ssl is None and is_ssl != self.is_ssl:
            return False
        if not self.anonymous is None and proxy_anonymous != self.anonymous:
            return False
        if not self.alive_sec is None and (alive_sec is None
                                           or alive_sec < self.alive_sec):
            return False
        if not self.iptype is None and iptype != self.iptype:
            return False
        if not self.isp is None and (isp is None
                                     or not self.isp.__contains__(isp)):
            return False
        if not self.location is None and (
                location is None or not self.location.__contains__(location)):
            return False
        if not self.lastverifytime is None and (
                lastverifytime is None
                or lastverifytime < self.lastverifytime):
            return False
        if not self.response_sec is None and (
                response_sec is None or response_sec > self.response_sec):
            return False
        return True

    def __eq__(self, obj):
        if not isinstance(obj, ProxySetting):
            return False

        if obj.port != self.port or \
            obj.proxytype != self.proxytype or \
            obj.is_ssl != self.is_ssl or \
            obj.anonymous != self.anonymous or \
            obj.countrycode != self.countrycode or \
            obj.alive_sec != self.alive_sec or \
            obj.iptype != self.iptype or \
            obj.isp != self.isp or \
            obj.location != self.location or \
            obj.lastverifytime != self.lastverifytime or \
            obj.response_sec != self.response_sec:
            return False

        return True
