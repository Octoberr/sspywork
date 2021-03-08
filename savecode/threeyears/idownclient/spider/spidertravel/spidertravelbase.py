"""Travel 网站基类
账密测试
检测张是否朱
已可以测试
"""

# -*- coding: utf-8 -*-

import traceback
from abc import ABCMeta, abstractmethod

from datacontract.idowndataset.task import Task
from ..appcfg import AppCfg
from ..spiderbase import SpiderBase
from ...clientdatafeedback import ITRAVELORDER, ITRAVELORDER_ONE


class SpiderTravelBase(SpiderBase):
    __metaclass = ABCMeta

    def __init__(self, task: Task, appcfg: AppCfg, clientid):
        SpiderBase.__init__(self, task, appcfg, clientid)

    def _download(self) -> iter:
        """继承基类的下载方法，抽象出子类应实现的方法"""
        try:
            orders: ITRAVELORDER = ITRAVELORDER(self._clientid, self.task, self._appcfg._apptype)
            for data in self._get_orders():
                if isinstance(data, ITRAVELORDER_ONE):
                    orders.append_innerdata(data)
                    self._logger.info("Got order: %s %s" %
                                      (data.get_uniqueid(), self._username))
                else:
                    yield data
                    # self._logger.info("Got data %s" % data.get_uniqueid())

            self._logger.info("Got %s orders of account %s" %
                              (orders.innerdata_len, self._account))
            yield orders

        except Exception:
            self._logger.error("Download error: {}".format(traceback.format_exc()))

    @abstractmethod
    def _get_orders(self) -> iter:
        """子类实现此方法，ITRAVELORDER_ONE数据"""
        return []
