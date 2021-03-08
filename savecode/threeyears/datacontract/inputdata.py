"""input data structure"""

# -*- coding:utf-8 -*-

import io
import threading
from abc import ABCMeta, abstractmethod


class InputData:
    """表示一个输入的数据，不同数据加载数据流方法不一样，所以抽象一层出来
    source: 数据来源（文件路径，网络地址）。\n
    oncomplete: 数据处理完成的回调函数， 
                oncomplete(self, data:InputData, 
                                 succ:bool=True, 
                                 finaldeal:bool=True)。\n
    srcmark: 数据来源标识，产生当前数据的Inputer的uniquename标识，可用于判断数据来源"""

    __metaclass = ABCMeta

    @property
    def stream(self):
        if self._stream_loaded:
            return self._stream
        with self.__streamload_locker:
            if self._stream_loaded:
                return self._stream
            self._stream = self._load_stream()
            self._stream_loaded = True
        return self._stream

    def __init__(self, source: str, platform: str, oncomplete: callable,
                 srcmark: str):
        if not isinstance(source, str) or source == "":
            raise Exception("The source of input data is invalid.")
        if not isinstance(platform, str) or platform == "":
            raise Exception("The platform of input data cannot be None.")
        if not callable(oncomplete):
            raise Exception("On complete should be callback function")
        if not isinstance(srcmark, str) or srcmark == "":
            raise Exception("The srcmark cannot be None")

        # 数据来源标识/Inputer的uniquename
        self._srcmark = srcmark

        # 原始来源/原始数据名
        self._source: str = source
        # 数据来源平台
        self._platform: str = platform
        # 回调函数，当当前数据处理完成时，应调用此函数
        self.__on_complete: callable = oncomplete

        # 数据来源自定义的分类器字典
        self.classifier: dict = None
        # 数据全名
        self.fullname: str = None
        # 数据名
        self.name: str = None
        # 后缀
        self.extension: str = None
        # 数据流，解析时应读取此流获取数据文本
        self._stream: io.RawIOBase = None
        self._stream_loaded: bool = False
        self.__streamload_locker = threading.RLock()

        # 指示回调函数是否已被调用
        self._iscallback_called: bool = False
        self.__iscallback_called_locker = threading.RLock()

    def on_complete(self, succ: bool = True, finaldeal: bool = True):
        """数据处理完成时应调用此回调函数。\n
        succ:指示当前数据处理是否 True成功/False出错\n
        finaldeal:指示当前数据是否需要做最终处理"""
        if self._iscallback_called:
            return

        with self.__iscallback_called_locker:
            if self._iscallback_called:
                return
            self._iscallback_called = True

        self.__on_complete(self, succ, finaldeal)

    @abstractmethod
    def _load_stream(self, mode: str = 'r', enc='') -> io.IOBase:
        """子类实现时加载数据流并返回io.IOBase"""
        pass
