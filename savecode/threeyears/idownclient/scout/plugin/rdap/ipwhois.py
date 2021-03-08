"""ip whois search"""

# -*- coding:utf-8 -*-

import json
import traceback

import IPy

from datacontract import EObjectType, IscoutTask

from ....clientdatafeedback.scoutdatafeedback import (IPWhoisData,
                                                      IPWhoisEntityData)
from ....config_client import basic_client_config
from ..scoutplugbase import ScoutPlugBase
from .afrinic import Afrinic
from .apnic import Apnic
from .arin import Arin
from .ripe import Ripe


class IPWhois(ScoutPlugBase):
    """搜索目标IP地址的Whois信息"""

    def __init__(self):
        ScoutPlugBase.__init__(self)
        self._apnic: Apnic = Apnic()
        self._arin: Arin = Arin()
        self._afrinic: Afrinic = Afrinic()
        self._ripe: Ripe = Ripe()

    def get_ipwhois(self, ip: str, reason) -> IPWhoisData:
        """get ipwhois"""
        res: IPWhoisData = None
        try:
            try:
                IPy.IP(ip)
            except Exception:
                self._logger.error(
                    "Invalid ip for getting ipwhois error: ip:{}, error: {}".
                        format(ip, traceback.format_exc()))
                return res

            # 查最新记录时，可以直接查一个arin/apnic啥的，
            # 会自动路由并跳转到目标结果
            # arin 的要翻墙才过得去

            if basic_client_config.crosswall:
                res = self._arin.get_ipwhois(ip, reason)
            else:
                res = self._apnic.get_ipwhois(ip, reason)
            pass

        except Exception:
            self._logger.error("Get ipwhois error: ip:{}, error: {}".format(
                ip, traceback.format_exc()))
        return res

    def get_ipwhois_history(self, task: IscoutTask, ip: str, reason,
                            level: int) -> iter:
        """get ipwhois"""
        try:
            try:
                IPy.IP(ip)
            except Exception:
                task.fail_count('ipwhois', level=level)
                self._logger.error(
                    "Invalid ip for getting ipwhois error: ip:{}, error: {}".
                        format(ip, traceback.format_exc()))
                return
            # 查历史记录时，应做路由并查询

            # 目前暂不支持路由，
            # 且只有apnic做了查历史的，
            # 所以查一下apnic的历史，并查一下arin的最新记录

            # apnic 查亚洲
            for iw in self._apnic.get_ipwhois_history(ip, reason):
                yield iw

            iw = self._apnic.get_ipwhois(ip, reason)
            yield iw

            # arin 查美洲
            iw = self._arin.get_ipwhois(ip, reason)
            yield iw

            # afrinic 非洲
            iw = self._afrinic.get_ipwhois(ip, reason)
            yield iw

            # ripe 欧洲、中东和中亚
            # ripe 很强大，东西很多，暂时做不过来，
            # 上面的可以先用着，后面再加
            # iw = self._ripe.get_ipwhois(ip, reason)
            # yield iw

            # lacnic 拉丁美洲和一些加勒比岛屿
            task.success_count('ipwhois', level=level)

        except Exception:
            task.fail_count('ipwhois', level=level)
            self._logger.error(
                "Get ipwhois history error: ip:{}, error: {}".format(
                    ip, traceback.format_exc()))
