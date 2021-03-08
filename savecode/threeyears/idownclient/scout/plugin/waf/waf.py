"""WAF detect plugin"""

import traceback

# -*- coding:utf-8 -*-
from wafw00f.main import WAFW00F

from datacontract import IscoutTask
from idownclient.scout.plugin.scoutplugbase import ScoutPlugBase


class WafDetect(ScoutPlugBase):
    """represents a WAF detect info"""
    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        self.task = task

    def waf_detect(self, target: str) -> iter:
        """
        target: the hostname or ip of the target server (目标服务器的主机名或IP)
        port: defaults to 80
        ssl: defaults to false
        return: yield return wafs"""
        try:
            # target---
            if not isinstance(target, str):
                self._logger.error(
                    "Invalid target host for waf detecting: {}".format(target))
                return

            # 这个wafw00f的whl包是手动修改了python调用问题并重新打包的；
            # 修改的地方为：wafw00f.main.py 227行 identwaf()函数内；
            # 它global rq在是为了在命令行调用时用的，直接引用main.py找不到rq对象的；
            # 所以需要在 identwaf() 函数的try代码块中添加rq定义，并初始化，代码如下:
            # global rq
            # rq = self.normalRequest()
            # if rq is None:
            #     self.log.error('Site %s appears to be down' % self.target)
            #     return

            # 攻击者
            attacker = WAFW00F(
                target=target,
                debuglevel=0,
                path='/',
                followredirect=True,
                extraheaders={},
            )

            # 攻击者的身份waf
            for waf in attacker.identwaf(True):
                self._logger.info('Ident WAF: target={}, waf={}'.format(
                    target, waf))  # 输出身份waf名称
                yield waf

        except Exception:
            self._logger.error("Waf detecting error, host={}, err: {}".format(
                target, traceback.format_exc()))
