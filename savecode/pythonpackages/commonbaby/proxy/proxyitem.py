"""proxy item"""

# -*- coding:utf-8 -*-

import threading
import time

from ..httpaccess import HttpAccess
from .eproxyanonymity import EProxyAnonymity
from .eproxytype import EProxyType


class ProxyItem:
    """一个代理IP对象\n
    ip: str, IP地址\n
    port: int, 端口号\n
    proxy_type: EProxyType = EProxyType.HTTP, 代理类型\n
    is_ssl: bool = False, 是否支持SSL加密通道\n
    proxy_anonymous: EProxyAnonymity = EProxyAnonymity.Elite, 代理匿名度\n
    countrycode: str = None, 代理所属国家\n
    alive_sec: float = None, 代理剩余的存活时间，秒\n
    iptype: int = 1, 代理IP地址的类型 1-ipv4 2-ipv6 \n
    isp: str = None, 代理IP所属的运营商\n
    location: str = None, 代理IP所属的地理位置\n
    lastverifytime: float = None, 代理IP最后验证的时间（时间戳）\n
    response_sec: float = None, 代理IP的响应速度，秒\n
    user:str = None, 代理IP的HTTP Basic Auth的用户名\n
    pwd:str = None, 代理IP的HTTP Basic Auth的密码\n
    \n
    
    # 官方文档讲代理参数怎么传：\n
    # http://2.python-requests.org/zh_CN/latest/user/advanced.html\n
    # 要为某个特定的连接方式或者主机设置代理，使用 scheme://hostname 作为 key\n 
    # 它会针对指定的主机和连接方式进行匹配：\n
    # proxies = {'http://10.20.1.128': 'http://10.10.1.10:5323'}\n
    # SOCKS代理需要第三方库：\n
    # pip install requests[socks]\n
    """

    # 用于验证HTTP代理的，全局静态http访问器
    __ha: HttpAccess = HttpAccess()

    @property
    def ip(self) -> str:
        """当前代理IP对象的IP地址"""
        return self._ip

    @ip.setter
    def ip(self, value):
        """当前代理IP对象的IP地址"""
        if not isinstance(value, str) or value == "":
            raise Exception("Invalid IP for proxyitem")
        self._ip = value
        self.__make_proxy_fields()

    @property
    def port(self) -> int:
        """当前代理IP对象的端口号"""
        return self._port

    @port.setter
    def port(self, value):
        """当前代理IP对象的端口号"""
        if not isinstance(value, int) or value < 0 or value > 65535:
            raise Exception("Invalid Port for proxyitem")
        self._port = value
        self.__make_proxy_fields()

    @property
    def proxytype(self) -> EProxyType:
        """当前代理IP对象的类型"""
        return self._proxytype

    @proxytype.setter
    def proxytype(self, value):
        """当前代理IP对象的类型"""
        if not isinstance(value, EProxyType):
            raise Exception("Invalid ProxyType for proxyitem")
        self._proxytype = value
        self.__make_proxy_fields()

    @property
    def is_ssl(self) -> bool:
        """当前代理IP对象是否支持SSL加密通道"""
        return self._is_ssl

    @is_ssl.setter
    def is_ssl(self, value):
        """当前代理IP对象的类型"""
        if not isinstance(value, bool):
            raise Exception("Invalid IsSsl for proxyitem")
        self._is_ssl = value
        self.__make_proxy_fields()

    @property
    def user(self) -> str:
        """当前代理IP对象的BasicAuth的用户名"""
        return self._user

    @user.setter
    def user(self, value):
        """当前代理IP对象的BasicAuth的用户名"""
        if not isinstance(value, str) or value == "":
            raise Exception("Invalid user for proxyitem")
        self._user = value
        self.__make_proxy_fields()

    @property
    def pwd(self) -> str:
        """当前代理IP对象的BasicAuth的用户名"""
        return self._user

    @pwd.setter
    def pwd(self, value):
        """当前代理IP对象的BasicAuth的密码"""
        if not isinstance(value, str) or value == "":
            raise Exception("Invalid pwd for proxyitem")
        self._pwd = value
        self.__make_proxy_fields()

    @property
    def proxy_http(self) -> str:
        """构建好的requests使用的HTTP代理字符串：\n
        对当前代理的 IP/Port/ProxyType/IsSsl/user/pwd赋值都会动态更新\n
        这种：http://x.x.x.x:xx"""
        return self._proxy_http

    @property
    def proxy_https(self) -> str:
        """构建好的requests使用的HTTPS代理字符串：\n
        对当前代理的 IP/Port/ProxyType/IsSsl/user/pwd赋值都会动态更新\n
        这种：http://x.x.x.x:xx"""
        return self._proxy_https

    @property
    def proxy_dict(self) -> dict:
        """构建好的requests使用的HTTPS代理字符串：\n
        对当前代理的 IP/Port/ProxyType/IsSsl/user/pwd赋值都会动态更新\n
        这种：\n
        {
            'http':'http://x.x.x.x:xx',
            'https':'http://x.x.x.x:xx'
        }
        """
        return self._proxy_dict

    @staticmethod
    def create_from_dict(fields: dict) -> object:
        """return ProxyItem"""
        fields: dict = fields
        return ProxyItem(
            fields.get("ip"),
            fields.get("port"),
            fields.get("proxytype", None),
            fields.get("isssl", False),
            fields.get("anonymous", None),
            fields.get("country", None),
            fields.get("alivesec", None),
            fields.get("iptype"),
            fields.get("isp", None),
            fields.get("location", None),
            fields.get("lastverifytime", None),
            fields.get("responsesec", None),
            fields.get("user", None),
            fields.get("pwd", None),
        )

    def __init__(
            self,
            ip: str,
            port: int,
            proxy_type: EProxyType = EProxyType.HTTP,
            is_ssl: bool = False,
            proxy_anonymous: EProxyAnonymity = EProxyAnonymity.Elite,
            countrycode: str = None,
            alive_sec: float = None,
            iptype: int = 1,
            isp: str = None,
            location: str = None,
            lastverifytime: float = None,
            response_sec: float = None,
            user: str = None,
            pwd: str = None,
    ):
        if not isinstance(ip, str) or ip == "":
            raise Exception("Invalid proxy IP")
        if not isinstance(port, int) or port < 0 or port > 65535:
            raise Exception("Invalid proxy Port")

        self._ip: str = ip
        self._port: int = port

        self._proxytype: EProxyType = proxy_type
        if not self._proxytype is None and not isinstance(
                self._proxytype, EProxyType):
            self._proxytype = EProxyType(int(self._proxytype))

        self._is_ssl: bool = is_ssl
        if self.is_ssl is None:
            self.is_ssl = False
        if not isinstance(self._is_ssl, bool):
            self._is_ssl = bool(is_ssl)

        self._anonymous: EProxyAnonymity = proxy_anonymous
        if not self._anonymous is None and not isinstance(
                self._anonymous, EProxyAnonymity):
            self._anonymous = EProxyAnonymity(int(self._anonymous))
        if self._anonymous is None:
            self._anonymous = EProxyAnonymity.Unknow

        self.countrycode = countrycode
        self.alive_sec: float = alive_sec
        if not self.alive_sec is None and not type(
                self.alive_sec) in [int, float]:
            self.alive_sec = float(self.alive_sec)
        self.iptype = iptype

        self.isp: str = isp  # 运营商/网络服务商

        self.location: str = location  # 地理位置

        self.lastverifytime: float = lastverifytime  #当前代理IP最后验证的时间
        if not self.lastverifytime is None and not type(
                self.lastverifytime) in [int, float]:
            self.lastverifytime = float(self.lastverifytime)

        self.response_sec: float = response_sec  # 当前代理IP的响应速度，单位秒
        if not self.response_sec is None and not type(
                self.response_sec) in [int, float]:
            self.response_sec = float(self.response_sec)

        self._user: str = user  # HTTP basic auth的账号
        self._pwd: str = pwd  # HTTP basic auth的密码

        # 官方文档讲代理怎么传
        # http://2.python-requests.org/zh_CN/latest/user/advanced.html
        # 构建代理IP参数
        self._proxy_http: str = None
        self._proxy_https: str = None
        self._proxy_dict: dict = {}
        self.__make_proxy_fields()

        # 代理IP验证相关
        self._is_verified: bool = False
        self._verify_locker = threading.RLock()

    def __make_proxy_fields(self):
        scheme: str = None
        if self.proxytype == EProxyType.HTTP:
            scheme = "http"
        elif self.proxytype == EProxyType.Socks:
            scheme = "socks5"

        # proxy http
        if isinstance(self.user, str) and not self.user == "":
            self._proxy_http = "{}://{}:{}@{}:{}".format(
                scheme, self.user, self.pwd, self.ip, self.port)
        else:
            self._proxy_http: str = "{}://{}:{}".format(
                scheme, self.ip, self.port)
        self._proxy_dict["http"] = self._proxy_http

        # proxy https
        if self.is_ssl:
            if isinstance(self.user, str) and not self.user == "":
                self._proxy_https = "{}://{}:{}@{}:{}".format(
                    scheme, self.user, self.pwd, self.ip, self.port)
            else:
                self._proxy_https: str = "{}://{}:{}".format(
                    scheme, self.ip, self.port)
            self._proxy_dict["https"] = self._proxy_https


##################################################
# verify validation

    def verify_try(
            self,
            url: str = 'api.github.com',
            headers: str = None,
            timeout: float = 5,
    ) -> bool:
        """验证当前代理IP（自身）的有效性，返回成功或失败。
        若发生异常会抛出异常。\n
        url: 用于代理验证的要访问的目标URL，默认用api.github.com比较快\n
        timeout:float 允许的最大网络请求延迟，单位秒，请求响应时间大于延迟则判定为代理测试失败\n
        headers: Chrome里那种直接copy出来的HTTP请求头键值对字符串\n
            当headers为''空字符串时，不使用任何请求头。
        默认为:\n
        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3\n
        Accept-Encoding: gzip, deflate\n
        Accept-Language: en\n
        Cache-Control: no-cache\n
        Connection: keep-alive\n
        Pragma: no-cache\n
        Upgrade-Insecure-Requests: 1\n
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36\n
        """
        succ: bool = False
        try:
            succ = self.verify()
        except Exception:
            succ = False
        return succ

    def verify(
            self,
            url: str = 'api.github.com',
            headers: str = None,
            timeout: float = 2,
    ) -> bool:
        """验证当前代理IP（自身）的有效性，返回成功或失败。
        若发生异常会抛出异常。\n
        url: 用于代理验证的要访问的目标URL，默认用api.github.com比较快\n
        timeout:float 允许的最大网络请求延迟，单位秒，请求响应时间大于延迟则判定为代理测试失败\n
        headers: Chrome里那种直接copy出来的HTTP请求头键值对字符串\n
            当headers为''空字符串时，不使用任何请求头。
        默认为:\n
        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3\n
        Accept-Encoding: gzip, deflate\n
        Accept-Language: en\n
        Cache-Control: no-cache\n
        Connection: keep-alive\n
        Pragma: no-cache\n
        Upgrade-Insecure-Requests: 1\n
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36\n
        """
        succ: bool = False
        if self._is_verified:
            succ = True
            return succ
        with self._verify_locker:
            if self._is_verified:
                succ = True
                return succ

            try:
                if not isinstance(url, str) or url == "":
                    raise Exception("Invalid verify url: {}".format(url))
                if not url.startswith('http'):
                    if self.is_ssl:
                        url = "https://{}".format(url)
                    else:
                        url = "http://{}".format(url)

                if headers is None:
                    headers = """ccept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
                            Accept-Encoding: gzip, deflate
                            Accept-Language: en,zh-CN;q=0.9,zh;q=0.8
                            Cache-Control: no-cache
                            Connection: keep-alive
                            Host: api.github.com
                            Pragma: no-cache
                            Upgrade-Insecure-Requests: 1
                            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"""

                timestart = time.time()
                html, redir = self.__ha.getstring_unredirect(
                    url=url,
                    headers=headers,
                    proxies=self._proxy_dict,
                    timeout=timeout,
                )
                timeend = time.time()
                if html is None and redir is None:
                    return succ

                self.response_sec = timeend - timestart
                self.lastverifytime = timeend
                succ = True

            except Exception as ex:
                raise ex
            finally:
                if succ:
                    self._is_verified = True

        return succ
