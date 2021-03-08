"""convert cookie standard"""

# -*- coding:utf-8 -*-

import traceback

from datacontract import InputData, Task
from dataparser import DataParser

from .converterstandard import ConverterStandard


class ConverterCookie(ConverterStandard):
    """将原有cookie标准转为idown任务标准"""

    def __init__(self, uniquename, fields: dict, extendfields: dict,
                 extensions: list):
        if not isinstance(extensions, list) or len(extensions) < 1:
            raise Exception("Specified ConverterCookie extension is invalid")

        ConverterStandard.__init__(self, uniquename, fields, extensions,
                                   extendfields)

    def _convert(self, data: InputData) -> iter:
        """将中心下发的任务转换为自有的通用任务结构Task体枚举（一个文件可能有多个任务段）"""
        succ = True
        try:
            if data.stream is None or not data.stream.readable():
                self._logger.error(
                    "Data stream is None when trying to convert to standard Task: %s"
                    % data._source)
                succ = False
                return

            for seg in DataParser.parse_standard_data(data.stream):
                if seg is None or len(seg._fields) < 1:
                    continue
                try:
                    # 必要字段
                    self._add_required_fields(seg, data)

                    # 根据host拿apptype
                    if not seg.contains_key("apptype"):
                        apptype = self._get_apptype(seg._fields, data)
                        if not apptype is None:
                            seg.append_to_fields('apptype', apptype)

                    # 验证字段有效性
                    if not self._validation_fields(seg, data):
                        succ = False
                        continue

                    tsk: Task = Task(seg._fields)
                    tsk.segindex = seg.segindex
                    tsk.segline = seg.segline

                    if tsk is None:
                        continue

                    yield tsk

                except Exception:
                    succ = False
                    self._logger.error(
                        "Generate Task from dic fields error:\ndata:%s\nex:%s"
                        % (data._source, traceback.format_exc()))

        except Exception:
            succ = False
            self._logger.error("Convert data to Task error:\ndata:%s\nex:%s" %
                               (data._source, traceback.format_exc()))
        finally:
            if not succ and not data is None:
                data.on_complete(False)
