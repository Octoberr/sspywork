"""convert cmd"""

# -*- coding:utf-8 -*-

import traceback

from datacontract import DataSeg, ETokenType, IdownCmd, InputData
from dataparser import DataParser

from .converterstandard import ConverterStandard


class ConverterCmd(ConverterStandard):
    """将中心下发的.idown_cmd任务转换为IDownCmd对象.\n
    uniquename: 当前转换器唯一标识\n
    extensions: 当前转换器匹配数据的后缀名\n
    fields: 当前转换器需要验证的字段集合，<fieldname:<bool,bool>> <字段名，<是否必要，是否区分大小写>>"""

    def __init__(self, uniquename, fields: dict, extendfields: dict,
                 extensions: list):
        if not isinstance(extensions, list) or len(extensions) < 1:
            raise Exception("Specified ConverterCmd extension is invalid")

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

                    cmd: IdownCmd = IdownCmd.parse_from_dict(
                        dicseg._fields, data._platform)

                    cmd.segindex = dicseg.segindex
                    cmd.segline = dicseg.segline

                    if cmd is None or not isinstance(cmd, IdownCmd):
                        self._logger.error("Parse task failed.")
                        continue

                    yield cmd

                except Exception:
                    self._logger.error(
                        "Generate Task from dic fields error:\ndata:%s\nex:%s"
                        % (data._source, traceback.format_exc()))
                    if not data is None:
                        data.on_complete(False)

        except Exception:
            self._logger.error("Convert data to Task error:\ndata:%s\nex:%s" %
                               (data._source, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)
