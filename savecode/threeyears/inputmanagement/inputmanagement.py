"""input management. file/netwok/pipe"""

# -*- coding:utf-8 -*-


import queue
import threading
import time
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.inputdata import InputData

from .inputconfig import InputConfig
from .inputerbase import InputerBase


class InputManagement:
    """input management\n
    用法：\n
    写一个config.py，里面直接将要使用的Inputer类型导入，并实例化出来，
    再将实例化好的Inputer对象，和一个回调函数作为参数，实例化一个InputManagement，
    并调用InputManagment对象的start()方法即可，数据处理完成后应调用InputData.on_complete(succ:bool)。
    具体见 idownserver.idownserver.py和idownserver.config_input.py"""

    def __init__(self, cfg: InputConfig, ondatain: callable):
        if not isinstance(cfg, InputConfig) or cfg is None:
            raise Exception("Specified inputer config is invalid")

        self._config = cfg
        self._ondatain: callable = ondatain

        # 对外输出队列，避免数据监视器线程阻塞
        self._datain_queue: queue.Queue = queue.Queue()
        self._logger: MsLogger = MsLogManager.get_logger("inputmanager")

    def start(self):
        """开始监控输入数据"""
        try:
            for inputer in self._config._inputers.values():
                # inputer: InputerBase = inputer
                inputer.on_data_in_inputer = self.__on_data_in_management
                inputer.start()

            toutput = threading.Thread(
                target=self.__output, name='taskmanagement')
            toutput.start()

        except Exception:
            self._logger.error("Start inputers error: %s" % traceback.format_exc())

    def __on_data_in_management(self, data: InputData):
        """将各输入管器拿到的数据对象丢到队列中，避免阻塞"""
        while self._datain_queue.unfinished_tasks >= self._config._max_q_count:
            time.sleep(1)

        self._datain_queue.put(data)

    def __output(self):
        """引导各inputer监控到的数据到外部调用方"""
        while True:
            try:
                data: InputData = self._datain_queue.get(block=True, timeout=2)
                self._datain_queue.task_done()

                # 新数据来了的日志提示改为在实现类中自行输出
                # 以便减少日志量，且日志可以简单关联输出模块
                # self._logger.info("New data: %s" % data._source)

                self._ondatain(data)

            except queue.Empty:
                pass
            except Exception:
                if data is None:
                    self._logger.error("External error: %s" % traceback.format_exc())
                else:
                    self._logger.error(
                        "External error:\ndata:%s\nex:%s" % (data._source, traceback.format_exc()))
                    if not data._iscallback_called:
                        data.on_complete(succ=False)
