"""task dispath manager"""

# -*- coding:utf-8 -*-

import traceback

from datacontract import DataMatcher, InputData

from ..config_dispatch import dispatchconfig
from ..servicemanager.dealerbase import DealerBase
# from .taskdispatcher import TaskDispatcher
from .dispatcherbase import DispatcherBase


class TaskDispatchManager(DealerBase):
    """dispatch tasks"""

    def __init__(self, datamatcher: DataMatcher):
        DealerBase.__init__(self, datamatcher)

        # 任务数据分配器，配置读取
        self._taskdispatchers: dict = dispatchconfig._taskdispatchers

    def _start(self):
        """启动数据分配/状态解析线程"""
        for disp in self._taskdispatchers.items():
            disp[1].start()

    def _deal_data(self, data: InputData) -> bool:
        res: bool = False
        try:
            # 若dealer返回None，说明其内部自行处理data的处理情况，
            # 外部不处理data.on_complete()
            res = self._to_dispatcher(data)
            if res == False:
                self._logger.error("Unrecognized data: %s" % data._source)
                data.on_complete(False)

        except Exception:
            self._logger.error("On data in error:\ndata:%s\nerror:%s" %
                               (data, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)
        return res

    def _to_dispatcher(self, data: InputData) -> bool:
        """按分配器关联的数据源，将任务分配到任务分配器"""
        res: bool = None
        try:
            matched: bool = False
            # 若处理正常则返回None，表示内部自行处理Task的完成状态
            for disp in self._taskdispatchers.values():
                disp: DispatcherBase = disp

                if disp._datamatcher.match_data(data):
                    matched = True
                    disp.on_data_in(data)
                elif isinstance(
                        disp._relation_inputer_src,
                        list) and data._srcmark in disp._relation_inputer_src:
                    # 找出所有显式配置的，与当前data关联的分配器
                    matched = True
                    disp.on_data_in(data)

            if not matched:
                self._logger.error("No dealer matches data: {}".format(
                    data.name))
                data.on_complete(False)

        except Exception:
            self._logger.error("Task allocate to dispatcher error: %s" %
                               traceback.format_exc())
            res = False
        return res
