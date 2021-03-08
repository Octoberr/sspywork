"""spider config"""

# -*- coding:utf-8 -*-


class AppCfg(object):
    """clone of AppConfig"""

    def __init__(self, appname, apphosts, apptype, appclassify, appclass, crosswall, enable, ishttps=True):
        self._appanme = appname
        self._apphosts = apphosts
        self._apptype = apptype
        self._appclassify = appclassify
        self._appclass = appclass
        self._crosswall = crosswall
        self._enable = enable
        self._ishttps = ishttps
