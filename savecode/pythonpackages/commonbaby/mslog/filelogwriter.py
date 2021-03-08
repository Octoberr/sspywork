"""File log writer which provids log writing threads for each logger.
    The flag of the log file is Numer, like log1.log, log2.log..."""

# -*- coding:utf-8 -*-

import os
import queue
import threading
import time
import traceback

from ..helpers import helper_platform
from .mslogconfig import MsFileLogConfig
from .msloglevel import MsLogLevels
from .mslogmsg import MsLogMessage
from .mslogwriter import MsLogWriter

LINE_SEP = helper_platform.get_sys_linesep()


class MsFileLogWriter(MsLogWriter):
    """File log writer which provids log writing threads for each logger.
    The flag of the log file is Numer, like log1.log, log2.log..."""

    config = None
    name = None

    # the locker for writing and flushing
    _write_flush_locker = threading.RLock()
    _t_flush = None

    # the locker for delete extra log file
    _delete_logfile_locker = threading.RLock()

    # the log queue
    _log_queue: queue.Queue = None

    # the thread for real log writing
    _t_write = None
    _t_start_locker = threading.RLock()
    _thread_started: bool = False

    log_file_path = None
    log_file_stream = None
    last_flag = 0

    # existing log files that found when initializing
    _existing_files = None

    def __init__(self, name: str = None, cfg: MsFileLogConfig = None):
        if (cfg is None) or (not isinstance(cfg, MsFileLogConfig)):
            cfg = MsFileLogConfig(
                sep_logfile=True,
                lvl=cfg.level if cfg is not None else MsLogLevels.DEBUG)

        MsLogWriter.__init__(self, name, cfg)

        self._log_queue = queue.Queue()
        self._existing_files = {}

        # init log file stream (separate directory by logger name)
        self.logdir = os.path.join(self.config.log_file_dir, name)
        self.__init_fistream(self.logdir, cfg.log_file_name)
        self.__check_size()
        self._t_write = threading.Thread(
            target=self._do_real_log_write,
            name="obj_write_%s_%s" % (type(self).__name__, self.name),
            args=())
        # start flush thread
        self._t_flush = threading.Thread(
            target=self.__flush_thread,
            name="cls_flush_%s_%s" % (type(self).__name__, self.name))

    def __init_fistream(self, fdir: str, fname: str) -> None:
        """Initial the file stream"""
        if not os.path.exists(fdir):
            os.makedirs(fdir)

        if self.log_file_stream is not None:
            self.log_file_stream.close()

        fname_prefix = fname.split('.')[0]

        for finame in os.listdir(fdir):
            if not finame.startswith(fname_prefix):
                continue
            fipath = os.path.abspath(os.path.join(fdir, finame))
            if not os.path.isfile(fipath):
                continue
            # get log file flag number
            flag = finame[len(fname_prefix):finame.find('.')]
            if (flag is None) or flag == '':
                flag = 0
            iflag = int(flag)
            if self.last_flag == 0 or iflag > self.last_flag:
                self.last_flag = iflag
                self.log_file_path = fipath
            # add to existing list
            self._existing_files[iflag] = fipath
        if self.last_flag == 0 and len(
                self._existing_files) < 1 and self.log_file_path is None:
            self.log_file_path = os.path.abspath(os.path.join(fdir, fname))

        self.log_file_stream = open(
            self.log_file_path,
            mode='at',
            encoding=self.config.log_file_enc.name)
        self._existing_files[self.last_flag] = self.log_file_path

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

            self._t_write.start()
            self._t_flush.start()

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

                if (msg is None) or (not isinstance(msg, MsLogMessage)):
                    continue

                if self._do_real_log_write_sub(msg):
                    self._on_succeed()
                else:
                    self._on_failed()
            except queue.Empty:
                continue
            except Exception:
                traceback.print_exc()
                self._on_failed()
            else:
                self._on_succeed()
            finally:
                if got:
                    self._log_queue.task_done()

    def _do_real_log_write_sub(self, msg: MsLogMessage) -> bool:
        """do the real log writing action"""
        res: bool = False
        with self._write_flush_locker:
            if self.log_file_stream is None:
                self.__init_fistream(self.config.log_file_dir,
                                     self.config.log_file_name)
                # s = "{}{}".format(msg.message, LINE_SEP).encode(
                #     self.config.log_file_enc.name)
                # self.log_file_stream.write(msg.message + LINE_SEP)
                # self.log_file_stream.write(s)
            self.log_file_stream.write(msg.message + LINE_SEP)
            res = True

        return res

    def _on_succeed(self):
        """on succeed"""
        pass

    def _on_failed(self):
        """on failed"""
        pass

    def __flush_thread(self):
        """Flush per 0.5 seconds"""
        while True:
            try:
                with self._write_flush_locker:
                    if self.log_file_stream is not None:
                        self.log_file_stream.flush()
                    self.__check_size()

            except Exception:
                traceback.print_exc()
            finally:
                time.sleep(1)

    def __check_size(self):
        """check if the log file is up to the max size"""
        size = os.path.getsize(self.log_file_path)
        if size < self.config.log_file_maxsize:
            return
        self.last_flag = self.last_flag + 1
        self.__switch_to_new_file(self.last_flag)

    def __switch_to_new_file(self, flg: int):
        """switch to new log file stream using specified flag"""
        with self._write_flush_locker:
            if self.log_file_stream is not None:
                self.log_file_stream.close()
            while True:
                name_kv = self.config.log_file_name.split('.')
                name = name_kv[0] + str(flg) + "." + name_kv[1]
                self.log_file_path = os.path.abspath(
                    os.path.join(self.config.log_file_dir, self.name, name))
                if os.path.exists(self.log_file_path):
                    continue
                else:
                    break
            self.log_file_stream = open(
                self.log_file_path,
                'at',
                encoding=self.config.log_file_enc.name)
            self._existing_files[flg] = self.log_file_path
            self.__delete_extra_log_file()

    def __delete_extra_log_file(self):
        """to delete the extra log file"""
        if len(self._existing_files) < self.config.log_file_maxcount:
            return

        with self._delete_logfile_locker:
            if len(self._existing_files) < self.config.log_file_maxcount:
                return
            while True:
                # sorted by value(the log file flag number)
                for flag, fipath in sorted(self._existing_files.items()):
                    try:
                        if len(self._existing_files
                               ) <= self.config.log_file_maxcount:
                            return
                        if not os.path.exists(fipath):
                            continue
                        os.remove(fipath)
                        self._existing_files.pop(flag)
                    except Exception as ex:
                        print(ex)
