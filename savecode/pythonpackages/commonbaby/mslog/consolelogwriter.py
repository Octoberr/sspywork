"""The console log writer"""

# -*- coding:utf-8 -*-

import os
import queue
import sys
import threading
import time
import traceback

from .mslogconfig import MsConsoleLogConfig
from .msloglevel import MsLogLevels
from .mslogmsg import MsLogMessage
from .mslogwriter import MsLogWriter

__mutex = threading.RLock()
__instances: dict = {}


def __check_mutex(name: str) -> bool:
    """检查数据库文件互斥锁，若互斥，则返回已有的SqliteConnManager实例，否则返回False"""
    if name is None:
        raise Exception("Param 'name' for dbfi mutex is None or empty")
    with __mutex:
        if __instances.__contains__(name):
            return __instances[name]
        else:
            return False


def __add_current_instance(inst, name):
    """将当前实例添加到互斥锁集合"""
    if inst is None:
        raise Exception("Given param 'inst' is invalid")
    with __mutex:
        if not __instances.__contains__(name):
            __instances[name] = inst


def __remove_current_instance(inst):
    """从互斥锁集合中移除当前实例"""
    if inst is None:
        raise Exception("Given param 'inst' is invalid")
    with __mutex:
        if __instances.__contains__(inst.name):
            __instances.pop(inst.name, None)


def __singleton(cls):
    """单例"""

    # __singleton.__doc__ = cls.__doc__

    def _singleton(name: str = None, cfg: MsConsoleLogConfig = None):
        """"""

        with __mutex:
            # 检查互斥锁
            mtx_result = __check_mutex(name)
            if isinstance(mtx_result, cls):
                return mtx_result

            inst = cls(name, cfg)
            __add_current_instance(inst, name)
            return inst

    _singleton.__doc__ = cls.__doc__
    return _singleton


@__singleton
class MsConsoleLogWriter(MsLogWriter):
    """The console log writer"""

    # # in console logger, all logger share one _real_log_write thread
    # __THREAD_STARTED: bool = False
    # __THREAD_LOCKER = threading.Lock()
    name = None
    config = None

    # static_initailed: bool = False
    # static_locker = threading.RLock()

    # # the queue belongs to consolelogwriter class
    # _log_queue: queue.Queue = queue.Queue()

    def __init__(self, name: str = None, cfg: MsConsoleLogConfig = None):
        if (cfg is None) or (not isinstance(cfg, MsConsoleLogConfig)):
            cfg = MsConsoleLogConfig(
                cfg.level if cfg is not None else MsLogLevels.DEBUG)
        MsLogWriter.__init__(self, name, cfg)

        self._timeok: bool = False
        self._maxwaittime = 1  # second
        # self._timeok_locker = threading.RLock()
        self._stdwritebuffer_locker = threading.RLock()
        self._stdwritebuffer: list = []

        self._t_timer = threading.Thread(
            target=self._timer_thread, name="tasktimer", daemon=True)
        self._t_write = threading.Thread(
            target=self._do_real_log_write,
            name="cls_{}_{}".format(type(self).__name__, self.name),
            args=())
        self._t_flush = threading.Thread(
            target=self.__flush_thread,
            name="cls_flush_{}_{}".format(type(self).__name__, self.name))

    def _timer_thread(self, intervalsec: float = 0.1):
        """定时器，定时分配任务。\n
        intervalsec: 轮询间隔，单位秒，默认0.1"""
        if not type(intervalsec) in [int, float]:
            raise Exception("Timer param inverval sec type wrong.")
        if intervalsec < 0 or intervalsec > 10:
            intervalsec = 0.1
        elapsed: float = 0
        while True:
            try:
                if elapsed >= self._maxwaittime:
                    self._timeok = True
                    elapsed = 0
            except Exception:
                print(
                    "Task dispatcher timer error: %s" % traceback.format_exc())
            finally:
                time.sleep(intervalsec)
                # 当timeok为True时，表示自上次将timeok设置为true到现在都
                # 还没完成一次分配，所以逝去时间elapsed不涨
                if not self._timeok:
                    elapsed += intervalsec

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def _enqueue_msg(self, msmsg: MsLogMessage):
        """Enqueue the message object to queue"""
        self._log_queue.put(msmsg)

    def _start_thread(self):
        """start one writing thread"""
        if self._thread_started:
            return
        with self._t_start_locker:
            if self._thread_started:
                return

            self._t_timer.start()
            self._t_write.start()
            # self._t_flush.start()

            if self.config.debug:
                tdebug = threading.Thread(target=self._debug_log)
                tdebug.start()

            self._thread_started = True

    def _debug_log(self):
        while True:
            try:
                print('{} {}:{}'.format(self._t_write.name, self.name,
                                        self._log_queue.qsize()))
            except Exception:
                traceback.print_exc()
            finally:
                time.sleep(10)

    def _do_real_log_write(self):
        """The log write thread. The subclass implementation should do the
        real log write"""
        got = False
        while True:
            try:
                got = False
                msg = self._log_queue.get(timeout=3)
                got = True

                # 省点性能...这句暂时不要了
                # if not isinstance(msg, MsLogMessage):
                #     print("invalid MsLogMessage object: {}".format(msg))
                #     continue

                if self._do_real_log_write_sub(msg):
                    self._on_succeed()
                else:
                    self._on_failed()
            except queue.Empty:
                continue
            except Exception:
                traceback.print_exc()
            finally:
                if got:
                    self._log_queue.task_done()

    def _do_real_log_write_sub_(self, msg: MsLogMessage):
        """do the real log writing action"""

        self._stdwritebuffer.append(msg.message)
        if not self._timeok and len(self._stdwritebuffer) < 500:
            return
        try:
            # sys.stdout.write(self._stdwritebuffer)
            # print(len(self._stdwritebuffer))
            sys.stdout.write('\n'.join(self._stdwritebuffer))
            self._stdwritebuffer.clear()
            # sys.stdout.writelines('{}\n'.format(msg.message))
            # print(msg.message)
            #print("console:" + str(cls._log_queue.empty()))
        except Exception:
            traceback.print_exc()
        finally:
            # with self._timeok_locker:
            if self._timeok:
                self._timeok = False

    def _do_real_log_write_sub(self, msg: MsLogMessage):
        """do the real log writing action"""

        # with self._stdwritebuffer_locker:
        #     self._stdwritebuffer.append(msg.message)
        # if not self._timeok and len(self._stdwritebuffer) < 500:
        #     return
        try:
            # with self._stdwritebuffer_locker:
            #     tmp = '\n'.join(self._stdwritebuffer)
            #     sys.stdout.write(tmp+'\n')
            #     self._stdwritebuffer.clear()
            print(msg.message)

            # sys.stdout.write(self._stdwritebuffer)
            # print(len(self._stdwritebuffer))
            # sys.stdout.writelines('{}\n'.format(msg.message))
            # print(msg.message)
            # print("console:" + str(cls._log_queue.empty()))
        except Exception:
            traceback.print_exc()
        finally:
            # with self._timeok_locker:
            if self._timeok:
                self._timeok = False

    def __flush_thread(self):
        """Flush per 0.5 seconds"""
        while True:
            try:
                # sys.stdout.flush()
                continue
            except Exception:
                traceback.print_exc()
            finally:
                time.sleep(2)

    def _on_succeed(self):
        pass

    def _on_failed(self):
        pass
