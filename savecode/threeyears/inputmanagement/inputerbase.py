"""inputer base interface"""

# -*- coding:utf-8 -*-

import threading
import traceback
from abc import ABCMeta, abstractmethod

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.inputdata import InputData


class InputerBase:
    """define the input manager.
    使用uniquename作为唯一标识，
    避免多线程或多进程监视同一目录/端口。\n
    uniquename: 当前输入管理器对象唯一限定名\n
    inputsrc: 当前输入甘利奇对象输入来源\n
    platform: 所属平台\n
    clasifiers: 分类器字典，用于区分当前输入源输入的数据所属的分类，
        例如<'appclasify','mail'>,<'apptype':'1001telegram'>
    error_data_delete:处理出错的数据是否删除，默认False\n
    succ_data_delete:处理成功的数据是否删除，默认False"""

    __metaclass = ABCMeta

    @property
    def on_data_in_inputer(self):
        return self._on_data_in_inputer

    @on_data_in_inputer.setter
    def on_data_in_inputer(self, value):
        if not callable(value) or value is None:
            raise Exception(
                "Inputer.on_data_in_inputer.setter value cannot be None")
        self._on_data_in_inputer = value

    def __init__(self,
                 uniquename: str,
                 inputsrc: str,
                 platform: str,
                 clasifiers: dict = None,
                 error_data_delete: bool = False,
                 succ_data_delete: bool = True,
                 ):
        if not isinstance(uniquename, str) or uniquename == "":
            raise Exception("Uniquename of inputer cannot be None")
        if not isinstance(inputsrc, str) or inputsrc is None:
            raise Exception("Input source cannot be None")
        if not isinstance(platform, str) or platform == "":
            raise Exception("Inputer platform cannot be None")

        # 当前输入管理器对象唯一限定名
        self._uniquename = uniquename
        self._logger: MsLogger = MsLogManager.get_logger(self._uniquename)
        # 当前输入数据对象输入来源
        self._inputsrc = inputsrc
        # 当前Inputer所属平台
        self._paltform = platform
        # 分类器
        self._clasifiers = {}
        if isinstance(clasifiers, dict) and len(clasifiers) > 0:
            self._clasifiers = clasifiers

        # 数据处理完成后的处理方式
        self._error_data_delete: bool = False
        if not isinstance(error_data_delete, bool):
            self._logger.warn("Param 'error_data_delete' should be boolean")
        else:
            self._error_data_delete: bool = error_data_delete

        self._succ_data_delete: bool = True
        if not isinstance(succ_data_delete, bool):
            self._logger.warn("Param 'succ_data_delete' should be boolean")
        else:
            self._succ_data_delete: bool = succ_data_delete

        self._on_data_in_inputer: callable = None

    def start(self):
        """对外接口"""
        try:
            self._start()
            self._logger.info("Inputer start: %s" % self._inputsrc)
        except Exception:
            self._logger.error("Start inputer eror: %s %s" %
                               (self._inputsrc, traceback.format_exc()))

    @abstractmethod
    def _start(self):
        """内部接口，子类实现时应开始新数据监控"""
        pass

    def stop(self, timeoutsec: int = 5):
        """对外接口，停止监控新数据。\n
        timeoutsec: 等待停止超时时间（秒）"""
        try:
            t = threading.Thread(target=self._stop)
            t.start()
            t.join(timeoutsec)
            self._logger.info("Inputer stoped: %s" % self._inputsrc)
        except TimeoutError:
            self._logger.info("Stop inputer timeout: %s" % self._inputsrc)
            t._stop()
        except Exception:
            self._logger.error("Stop inputer error: %s %s" %
                               (self._inputsrc, traceback.format_exc()))

    @abstractmethod
    def _stop(self):
        """内部接口，子类实现时应停止数据监控线程"""
        pass

    def _on_data_in_wrapper(self, data: InputData):
        try:
            if self._on_data_in_inputer is None or not callable(self._on_data_in_inputer):
                self._logger.error(
                    "No input data recieve delegate function specified, and dealt error: %s" % data._originname)
                data.on_complete(True)
                return

            if data is None or not isinstance(data, InputData):
                self._logger.error("Input data is None")
                return

            data.classifier = self._clasifiers.copy()
            self._on_data_in_inputer(data)

        except Exception:
            self._logger.error(
                "Input data error:\ndata:%s\nerror:%s" % (data._source, traceback.format_exc()))
            if not data is None:
                data.on_complete(False)
