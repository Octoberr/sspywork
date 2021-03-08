"""
app太多了，所以分类存储，这里写基本的数据结构
"""
import enum


class EAppClassify(enum.Enum):
    """App大类枚举值，用于区分某个app是属于哪个大类的。
    控制端和采集端应遵照此配置"""

    # 社交
    Social = 1
    # 网约车租车共享车
    Taxi = 2
    # 邮箱类
    Mail = 3
    # 行程订单
    Travel = 4
    # 购物网站
    Shopping = 5
    # 网盘

    Netdisk = 6


class EServiceType(enum.Enum):
    """指示某个APP支持的服务类型"""
    No = 0
    WebMail = 1
    POP3 = 2
    # WebMail + POP3 = 3
    IMAP = 4
    # WebMail + IMAP = 5
    # POP3 + IMAP = 6
    # WebMail + POP3 + IMAP = 7


class AppConfig:
    """表示一个采集端插件的类型字典和固定参数配置。\n
    apphosts: 当前app所属域名列表\n
    apptype: app类型枚举。\n
    appclassify: app插件所属大类\n
    appclass: app插件的实现类\n
    crosswall: 当前app是否需要翻墙\n
    requirepreaccount:检查账号在线信息时是否需要预置账号\n
    enable: 当前插件是否启用。\n
    concurrentcnt: 当前插件的最大插件下载实例并发数\n
    """
    def __init__(
            self,
            appname: str,
            apphosts: list,
            apptype: int,
            appclassify: EAppClassify,
            appclass: type,
            crosswall: bool = False,
            requirepreaccount: bool = True,
            # enable这个默认值先设为false，后面做一个开一个，多了再写成默认值True
            enable: bool = False,
            concurrentcnt: int = 1,
            exts: list = [],
            ishttps: bool = True,
    ):
        if not isinstance(appname, str) or appname == '':
            raise Exception("Param appname is invalid.")
        if not isinstance(apphosts, list) or len(apphosts) < 1:
            raise Exception("Param apphost is invalid.")
        if not isinstance(apptype, int) or apptype < 1:
            raise Exception("Param apptype is invalid.")
        if not isinstance(crosswall, bool):
            raise Exception("Param crosswall is invalid.")
        if not isinstance(appclassify, EAppClassify):
            raise Exception("Param appclassify is invalid.")
        if not isinstance(appclass, type):
            raise Exception("Param appclass is invalid.")
        if not isinstance(requirepreaccount, bool):
            raise Exception("Param requirepreaccount is invalid.")
        if not isinstance(enable, bool):
            raise Exception("Param enable is invalid.")
        if not isinstance(concurrentcnt, int) or concurrentcnt < 1:
            raise Exception("Param concurrentcnt is invalid.")
        if not isinstance(ishttps, bool):
            raise Exception("Param ishttps is invalid.")

        # 判断apptype和appclassify是否相符
        if not str(apptype).startswith(str(appclassify.value)):
            raise Exception("Apptype and appclassify not match.")

        self._appanme: str = appname
        self._apphosts: str = apphosts
        self._apptype: int = apptype
        self._appclassify: EAppClassify = appclassify
        self._appclass: type = appclass
        self._crosswall: bool = crosswall
        self._requirepreaccount: bool = requirepreaccount
        self._enable: bool = enable
        self._concurrentcnt: int = concurrentcnt
        self._ishttps: bool = ishttps

        self._exts: list = []
        if isinstance(exts, list) and len(exts) > 0:
            self._exts.extend(exts)