"""data dealer config"""

# -*- coding:utf-8 -*-

from .dealerbase import DealerBase
import threading


class DealerConfig:
    """配置数据处理器"""

    def __init__(self, dealers: list):
        """"""

        if not isinstance(dealers, list) or len(dealers) < 1:
            raise Exception("Invalid param 'dealers' for DealerConfig")

        self._dealers: list = []
        self._dealers_locker = threading.RLock()
        for d in dealers:
            self._append_dealer(d)

    def _append_dealer(self, dealer: DealerBase):
        """"""
        if not isinstance(dealer, DealerBase):
            raise Exception("Invalid dealer object: {}".format(dealer))
        with self._dealers_locker:
            if dealer in self._dealers:
                # 不允许同一个对象添加两次
                return
            self._dealers.append(dealer)
