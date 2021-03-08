"""input file"""

# -*- coding:utf-8 -*-

import io
import os
import queue
import shutil
import threading
import time
import traceback
import uuid
import datetime
import pytz

from commonbaby import charsets, helper_file

from datacontract.inputdata import InputData

from ..inputerbase import InputerBase
from .inputfiledata import InputFileData


class InputerFile(InputerBase):
    """文件输入监视器Inputer。
    uniqueName:当前Inputer的唯一限定名，各Inputer对象的uniqueName不能重复，以免多个监视器监视同一目录。\n
    inputdir:当前Inputer要监视的文件夹路径。\n
    platform:当前Inputer监视的文件夹所属平台。\n
    clasifiers:当前Inputer监视的文件数据的类型分类（令牌类型/目标网站类型等），以字典dict形式传入。\n
    maxDealingQueue:当前Inputer的最大处理队列长度，正在处理的文件数量超过此数量则停止继续读取文件。\n
    encoding:当前Inputer读取文件时使用的字符集\n
    succ_file_delete:处理成功的数据是否删除，默认True\n
    succdir:处理成功的文件若不删除，则移动存放到此目录\n
    succfilekeepcount:处理成功的文件存储后，定时删除，只保留此参数指定个数，0表示全部删除，负数表示全部保留。\n
    succfilekeepdays:处理成功后的文件存储后，定时删除，只保留此参数指定的天数，0表示全部删除，负数表示全部保留。\n
    error_file_delete:处理失败的数据是否删除，默认False\n
    errordir: 处理失败的数据若不删除，则移动存放到此目录\n
    errorfilekeepcount: 处理失败的文件存储后，定时删除，只保留此参数指定个数，0表示全部删除，负数表示全部保留。\n
    errorfilekeepdays:处理失败后的文件存储后，定时删除，只保留此参数指定的天数，0表示全部删除，负数表示全部保留。"""

    @property
    def _succdir(self):
        """按时间分割的已完成目录"""
        if datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() - self._last_succ_dir_time < 86400:  # 24*60*60秒
            return self.__succdir
        with self._succdir_locker:
            if datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() - self._last_succ_dir_time < 86400:
                return self.__succdir
            self._last_succ_dir_time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
            self.__succdir = os.path.join(self._succdirroot, self._get_date())
        return self.__succdir

    @property
    def _errordir(self):
        """按时间分割的已完成目录"""
        if datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() - self._last_error_dir_time < 86400:  # 24*60*60秒
            return self.__errordir
        with self._errordir_locker:
            if datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() - self._last_error_dir_time < 86400:
                return self.__errordir
            self._last_error_dir_time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
            self.__errordir = os.path.join(self._errordirroot,
                                           self._get_date())
        return self.__errordir

    @property
    def _is_stoped(self) -> bool:
        """指示文件监视线程是否停止"""
        return self._stoped

    def __init__(self,
                 uniqueName: str,
                 inputdir: str,
                 platform: str,
                 clasifiers: dict = None,
                 maxDealingQueue: int = 20,
                 encoding='utf-8',
                 succ_file_delete: bool = True,
                 succdir: str = './_serversucc',
                 succfilekeepcount: int = 1000,
                 succfilekeepdays: int = 3,
                 error_file_delete: bool = False,
                 errordir: str = './_servererror',
                 errorfilekeepcount: int = 1000,
                 errorfilekeepdays: int = 3):
        InputerBase.__init__(self, uniqueName, inputdir, platform, clasifiers,
                             error_file_delete, succ_file_delete)

        # 输入器属性
        self._inputdir = os.path.abspath(inputdir)
        os.makedirs(self._inputdir, exist_ok=True)
        if not isinstance(
                maxDealingQueue,
                int) or maxDealingQueue < 1 or maxDealingQueue > 99999:
            raise Exception("Param maxDealingQueue is incorrect.")
        self._max_dealing_queue_count = maxDealingQueue
        # 读取文件时使用的字符集
        self._encoding = 'utf-8'
        if not isinstance(encoding,
                          str) or not charsets.contains_charset(encoding):
            self._logger.warn(
                "Specified charset is invalid: '%s', will use 'utf-8' instead."
                % encoding)
        else:
            self._encoding = encoding

        # 完成目录
        self._succdirroot = os.path.abspath('./_servercomplete')
        if isinstance(succdir, str) and not succdir == "":
            self._succdirroot = os.path.abspath(succdir)
        self.__succdir = os.path.join(self._succdirroot, self._get_date())
        self._last_succ_dir_time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
        self._succdir_locker = threading.RLock()

        self._succfile_keepcount: int = 1000
        if isinstance(succfilekeepcount, int):
            self._succfile_keepcount = succfilekeepcount
        self._succfile_keepdays: int = 3
        if type(succfilekeepdays) in [int, float]:
            self._succfile_keepdays = succfilekeepdays
        self._t_completefi_reduce: threading.Thread = helper_file.directory_file_reduce(
            self._succdirroot, self._succfile_keepcount,
            self._succfile_keepdays, self._complete_file_reduce_log)

        # 错误目录
        self._errordirroot = os.path.abspath('./_servererror')
        if isinstance(errordir, str) and not errordir == "":
            self._errordirroot = os.path.abspath(errordir)
        self.__errordir = os.path.join(self._errordirroot, self._get_date())
        self._last_error_dir_time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
        self._errordir_locker = threading.RLock()

        self._errorfile_keepcount: int = 1000
        if isinstance(errorfilekeepcount, int):
            self._errorfile_keepcount = errorfilekeepcount
        self._errorfile_keepdays: int = 3
        if type(errorfilekeepdays) in [int, float]:
            self._errorfile_keepdays = errorfilekeepdays
        self._t_errorfi_reduce: threading.Thread = helper_file.directory_file_reduce(
            self._errordirroot, self._errorfile_keepcount,
            self._errorfile_keepdays, self._error_file_reduce_log)

        # 文件监视线程相关
        # 指示文件监视线程是否停止
        self._stoped = True
        self._stopedLocker = threading.Lock()
        self._tmonitor = threading.Thread(
            target=self._monitor, name=self._uniquename)
        self._dealing_queue: dict = {}
        self._dealing_queue_locker = threading.Lock()

    def _get_date(self, utc: bool = True):
        ct = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
        if utc:
            ct = datetime.datetime.utcnow().timestamp()
        local_time = time.localtime(ct)
        data_head = time.strftime("%Y-%m-%d", local_time)
        return data_head

    def _complete_file_reduce_log(self, msg):
        if not msg is None:
            self._logger.info("Complete file reduce: %s" % msg)

    def _error_file_reduce_log(self, msg):
        if not msg is None:
            self._logger.info("Error file reduce: %s" % msg)

    def _start(self):
        """若后面此函数在其他Inputer内部可重用，则提到InputerBase中"""
        if self._tmonitor is None:
            self._tmonitor = threading.Thread(
                target=self._monitor, name=self._uniquename, daemon=True)

        if not self._tmonitor.is_alive():
            self._tmonitor.start()

        if not self._t_errorfi_reduce.is_alive():
            self._t_errorfi_reduce.start()

        if self._stoped == False:
            return
        with self._stopedLocker:
            if self._stoped == False:
                return
            self._stoped = False

    def _stop(self):
        """若后面此函数在其他Inputer内部可重用，则提到InputerBase中"""
        if self._stoped:
            return
        with self._stopedLocker:
            if self._stoped:
                return
            self._stoped = True

    def _monitor(self):
        """监视输入目录线程"""
        while True:
            try:
                while self._stoped:
                    time.sleep(1)

                for p in os.listdir(self._inputdir):
                    path: str = os.path.join(self._inputdir, p)
                    if os.path.isdir(path):
                        continue

                    with self._dealing_queue_locker:
                        if self._dealing_queue.__contains__(
                                path) or not os.path.exists(path):
                            continue

                    data: InputData = self._load_data(path)
                    if data is None or not issubclass(data.__class__,
                                                      InputData):
                        continue

                    with self._dealing_queue_locker:
                        if self._dealing_queue.__contains__(
                                data._source) or not os.path.exists(path):
                            continue
                        self._dealing_queue[data._source] = data

                    self._logger.info("New data: %s" % data.name)
                    self._on_data_in_wrapper(data)

            except Exception:
                self._logger.error(
                    "Inputer thread error: %s" % traceback.format_exc())
            finally:
                time.sleep(1)

    def _load_data(self, path: str) -> InputData:
        """加载文件数据，返回一个 InputData对象"""
        data: InputData = None
        try:
            if not isinstance(path, str) or path == "":
                raise Exception("Given input data path is invalid")

            data = InputFileData(path, self._paltform, self._on_complete,
                                 self._uniquename, self._encoding)

            data.fullname = path
            data.name = os.path.split(path)[1]
            data.extension = os.path.splitext(data.name)[1].strip('.').strip()

        except Exception:
            self._logger.error("Load file error:\npath:%s\nerror:%s" %
                               (path, traceback.format_exc()))
        return data

    def _on_complete(self, data: InputData, succ: bool,
                     finaldeal: bool = True):
        """文件数据处理完成后应调用的回调函数 
        data.on_complete(self, issucc:bool=True, finaldeal:bool=True)\n
        succ:指示当前数据是否处理成功\n
        finaldeal:指示当前数据是否需要做最终处理"""
        try:

            if not finaldeal:
                return

            if data is None or data.fullname is None or data.fullname == "":
                return

            if not data.stream is None and not data.stream.closed:
                data.stream.close()

            if succ:
                self._succ_data_deal(data)
            else:
                self._error_data_deal(data)

        except Exception:
            self._logger.error(
                "Complete deal data file error:\ndata:%s\nerror:%s" %
                (data._source, traceback.format_exc()))
        finally:
            with self._dealing_queue_locker:
                if self._dealing_queue.__contains__(data._source):
                    self._dealing_queue.pop(data._source, None)

    def _error_data_deal(self, data: InputData):
        """出错数据收尾处理"""
        try:
            if data is None or data.fullname is None or data.fullname == "":
                return

            if self._error_data_delete:
                self._data_delete(data)
            else:
                self._data_move(data, self._errordir)

            self._logger.info("Data FAILED: %s" % data.name)
            # self._logger.debug(data.)

        except Exception:
            self._logger.error("Error data deal error:\ndata:%s\nerror:%s" %
                               (data.fullname, traceback.format_exc()))

    def _succ_data_deal(self, data: InputData):
        """成功数据收尾处理"""
        try:
            if data is None or data.fullname is None or data.fullname == "":
                return

            if self._succ_data_delete:
                self._data_delete(data)
            else:
                self._data_move(data, self._succdir)

            self._logger.info("Data OK: {}".format(data.name))

        except Exception:
            self._logger.error("Succ data deal error:\ndata:%s\nerror:%s" %
                               (data.fullname, traceback.format_exc()))

    def _data_move(self, data: InputData, targetdir: str):
        """移动数据"""
        try:
            if data is None or data.fullname is None or data.fullname == "":
                return

            if not os.path.exists(targetdir) or not os.path.isdir(targetdir):
                os.makedirs(targetdir)

            newfi = os.path.join(targetdir, data.name)
            while os.path.exists(newfi):
                newfi = os.path.join(targetdir,
                                     '%s.%s' % (str(uuid.uuid1()),
                                                data.extension.strip('.')))

            shutil.move(data.fullname, newfi)

        except Exception:
            self._logger.error("Move data error:\ndata:%s\nerror:%s" %
                               (data.fullname, traceback.format_exc()))

    def _data_delete(self, data: InputData):
        """删除数据"""
        try:
            if data is None or data.fullname is None or data.fullname == "":
                return

            if os.path.exists(data.fullname) and os.path.isfile(data.fullname):
                os.remove(data.fullname)
        except Exception:
            self._logger.error("Delete data error:\ndata:%s\nerror:%s" %
                               (data.fullname, traceback.format_exc()))
