"""The log writer base, witch do the real log writing action"""

# -*- coding:utf-8 -*-

import queue
import threading
import time
import traceback
from abc import ABCMeta, abstractmethod

from .mslogconfig import MsLogConfig
from .msloglevel import MsLogLevels
from .mslogmsg import MsLogMessage


class MsLogWriter:
    """The log writer base, witch do the real log writing action"""

    __metaclass = ABCMeta

    name = None

    def __init__(self, name: str = None, cfg: MsLogConfig = None):
        # init config
        if name is None or name == '':
            raise ValueError("logger name cannot be None")
        if not isinstance(cfg, MsLogConfig):
            raise ValueError("invalid MsLogConfig")

        self.name = name
        if cfg is None:
            cfg = MsLogConfig(MsLogLevels.DEBUG)
        self.config: MsLogConfig = cfg

        # the log queue
        self._log_queue: queue.Queue = queue.Queue()
        # the thread for real log writing
        self._t_write = None
        self._t_start_locker = threading.RLock()
        self._thread_started: bool = False

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def log(self, msmsg: MsLogMessage):
        """This method will enqueue the log message into a queue, the backgroud thread
        will do the real log action"""
        try:
            if msmsg is None:
                return
            # return if level is not enabled
            if msmsg.level < self.config.level:
                return

            # 强制同步等待，，python太慢了，可能跟不上（优化不来了。）
            while self._log_queue.qsize() > 10000:
                time.sleep(1)
            self._enqueue_msg(msmsg)
            self._start_thread()

        except Exception:
            traceback.print_exc()

    @abstractmethod
    def _enqueue_msg(self, msmsg: MsLogMessage):
        """Enqueue the message object to queue"""
        self._log_queue.put(msmsg)

    @abstractmethod
    def _start_thread(self):
        # start the thread if not started yet
        if self._thread_started:
            return

        with self._t_start_locker:
            if self._thread_started:
                return

            self._t_write = threading.Thread(
                target=self._do_real_log_write,
                name="obj_%s_%s" % (type(self).__name__, self.name),
                args=())
            self._t_write.start()
            self._thread_started = True

    @abstractmethod
    def _do_real_log_write(self):
        """The log write thread. The subclass implementation should do the
        real log write"""

        while True:
            try:
                msg = self._log_queue.get()

                if (msg is None) or (not isinstance(msg, MsLogMessage)):
                    continue

                if self._do_real_log_write_sub(msg):
                    self.__on_succeed()
                else:
                    self.__on_failed()

            except Exception as ex:
                traceback.print_exc()
            finally:
                self._log_queue.task_done()

    @abstractmethod
    def _do_real_log_write_sub(self, msg: MsLogMessage) -> bool:
        """Do the real log writing action"""
        raise NotImplementedError()

    def __on_succeed(self):
        try:
            return self._on_succeed()
        except Exception:
            traceback.print_exc()

    @abstractmethod
    def _on_succeed(self):
        """when the subclass impelements, do something after a log writes succeed"""
        pass

    def __on_failed(self):
        """"""
        try:
            return self._on_failed()
        except Exception:
            traceback.print_exc()

    def _on_failed(self):
        """when the subclass implements, do something after a log writes failed"""
        pass
