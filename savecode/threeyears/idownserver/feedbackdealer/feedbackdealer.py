"""feedback data dealer"""

# -*- coding:utf-8 -*-

import traceback

from datacontract import DataMatcher, InputData
from outputmanagement import OutputManagement

from ..servicemanager import DealerBase


class FeedbackDealer(DealerBase):
    """deal result data to center"""

    def __init__(self, datamatcher: DataMatcher):
        DealerBase.__init__(self, datamatcher)

    def _deal_data(self, data: InputData) -> bool:
        """deal feedback data"""
        # 此函数永远返回None，并自行解决InputData成败处理
        try:
            if data._stream_loaded:
                data.stream.close()

            # 暂时不进行任何处理，直接移动返回
            if not OutputManagement.output_move_file(data._platform,
                                                     data._source):
                self._logger.error(
                    "Output data to center failed:\nplatform:{}\ndata:{}".
                    format(data._platform, data.name))
                data.on_complete(False, False)
            else:
                data.on_complete(True, False)
                self._logger.info("Output data to center: {}\t{}".format(
                    data._platform, data.name))

        except Exception:
            self._logger.error("Deal data error:\ndata:{}\nerror:{}".format(
                data.name, traceback.format_exc()))