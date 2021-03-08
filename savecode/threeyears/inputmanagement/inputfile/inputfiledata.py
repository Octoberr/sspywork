"""input file data"""

# -*- coding:utf-8 -*-

import io
import os
import time
import traceback

from commonbaby import charsets

from datacontract.inputdata import InputData


class InputFileData(InputData):
    """文件数据"""

    def __init__(self, source: str, platform: str, oncomplete: callable, srcmark: str, encoding: str = 'utf-8'):
        InputData.__init__(self, source, platform, oncomplete, srcmark)

        self._encoding = 'utf-8'
        if not isinstance(encoding, str) or not charsets.contains_charset(encoding):
            raise Exception(
                "Invalid charset '%s' for initial InputFileData" % encoding)
        else:
            self._encoding = encoding

    def _load_stream(self, mode: str = 'r', enc='')->io.IOBase:
        """加载文件流"""
        res: io.IOBase = None
        try:
            if not isinstance(self.fullname, str) or self.fullname == "" or not os.path.exists(self.fullname):
                raise Exception(
                    "Data file path is None or not exists when trying to load data filestream")

            flag = 0
            fs = None
            while True:
                try:
                    if enc == '':
                        enc = self._encoding

                    if not self._stream is None and not self._stream.closed:
                        self._stream.close()
                    fs = open(self.fullname, mode=mode,
                              encoding=enc)
                    break
                except Exception:
                    flag += 1
                    if flag < 15:
                        time.sleep(2)
                    else:
                        raise Exception(
                            "Load data stream error for %s time(s), %d, give up: %s" % (flag, flag*2, traceback.format_exc()))

            if fs is None:
                return res

            res = fs
        except Exception:
            raise Exception(
                "Load file stream error:\ndata:%s\nerror:%s" % (self.fullname, traceback.format_exc()))
        return res
