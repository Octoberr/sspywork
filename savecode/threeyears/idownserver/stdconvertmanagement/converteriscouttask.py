"""convert iscouttask"""

# -*- coding:utf-8 -*-

import traceback

from datacontract import DataSeg, InputData, IscoutTask
from dataparser import DataParser

from .converterstandard import ConverterStandard


class ConverterIScoutTask(ConverterStandard):
    """
    fields: 当前转换器需要验证的字段集合，<fieldname:<bool,bool>> <字段名，<是否必要，是否区分大小写>>
    """

    def __init__(self, uniquename, fields: dict, extendfields: dict,
                 extensions: list):

        if not isinstance(extensions, list) or len(extensions) < 1:
            raise Exception(
                "Specified ConverterIScoutTask extension is invalid")

        ConverterStandard.__init__(self, uniquename, fields, extensions,
                                   extendfields)

    def _convert(self, data: InputData) -> iter:
        """将中心下发的任务转换为自有的通用任务结构Task体枚举（一个文件可能有多个任务段）"""
        try:
            if data.stream is None or not data.stream.readable():
                self._logger.error(
                    "Data stream is None when trying to convert to standard Task: %s"
                    % data._source)
                return

            for dicseg in self._get_segments(data):
                if dicseg is None or len(dicseg._fields) < 1:
                    continue
                try:
                    # 创建任务对象

                    task: IscoutTask = IscoutTask.create_from_dict(
                        dicseg._fields, data._platform)

                    task.segindex = dicseg.segindex
                    task.segline = dicseg.segline

                    if task is None or not isinstance(task, IscoutTask):
                        self._logger.error("Parse IscoutTask failed.")
                        continue

                    yield task

                except Exception:
                    self._logger.error(
                        "Generate  IscoutTask from dic fields error:\ndata:%s\nex:%s"
                        % (data._source, traceback.format_exc()))
                    if not data is None:
                        data.on_complete(False)

        except Exception:
            self._logger.error(
                "Convert data to IscoutTask error:\ndata:%s\nex:%s" %
                (data._source, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)
