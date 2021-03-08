"""Shopping 网站基类"""

# -*- coding: utf-8 -*-

import traceback
from abc import ABCMeta, abstractmethod

from datacontract.idowndataset.task import Task
from ..spiderbase import SpiderBase
from ...clientdatafeedback import ISHOPPING, ISHOPPING_ONE


class SpiderShoppingBase(SpiderBase):
    __metaclass = ABCMeta

    def __init__(self, task: Task, appcfg, clientid):
        SpiderBase.__init__(self, task, appcfg, clientid)

    def _download(self) -> iter:
        """继承基类的下载方法，抽象出子类应实现的方法"""
        try:
            orders: ISHOPPING = ISHOPPING(self._clientid, self.task, self._appcfg._apptype)
            for data in self._get_orders():
                if not isinstance(data, ISHOPPING_ONE):
                    # self._logger.info("Got data %s" % data.get_uniqueid())
                    yield data
                else:
                    orders.append_innerdata(data)
                    self._logger.info("Got order: %s %s" %
                                      (data.get_uniqueid(), self._username))

            self._logger.info("Got %s orders of account %s" %
                              (orders.innerdata_len, self._account))
            yield orders

        except Exception:
            self._logger.error("Download error: {}".format(traceback.format_exc()))

    @abstractmethod
    def _get_orders(self) -> iter:
        return []
