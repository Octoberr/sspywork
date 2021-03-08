"""task feedback data dealerbase"""

# -*- coding:utf-8 -*-

import math
import queue
import threading
import time
import traceback
from abc import ABCMeta, abstractmethod

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import (DataMatcher, DataSeg, ECommandStatus, InputData,
                          TaskBackBase)
from dataparser import DataParser
from outputmanagement import OutputManagement

from ..dbmanager import EDBAutomic
from ..servicemanager.dealerbase import DealerBase


class TaskBackDealerBase(DealerBase):
    """deal task feedback data"""

    __metaclass = ABCMeta

    def __init__(
            self,
            uniquename: str,
            datamatcher: DataMatcher,
            relation_inputer_src: list = None,
    ):
        DealerBase.__init__(self, datamatcher)

        if not isinstance(uniquename, str) or uniquename == "":
            raise Exception("Task dispatcher uniquename cannot be None")

        self._uniquename = uniquename
        self._logger: MsLogger = MsLogManager.get_logger(uniquename)

        # 各字段
        self._relation_inputer_src = relation_inputer_src

        self._started: bool = False
        self._startedlocker = threading.RLock()

        # InputData与其中解析出来的TaskBatchBack的关联字典，
        # 用于判定一个 InputData 解析出来的 TaskBatchBack
        # 对象是否已经全部处理完成
        # <data, <tb, bool>>
        self._datas: list = []
        self._datas_locker = threading.RLock()

        # TaskBatchBack 处理队列
        self._tbbqueue: queue.Queue = queue.Queue()

        # 各种线程
        self._t_taskback_timeout_check: threading.Thread = threading.Thread(
            target=self.taskback_timeout_check,
            name='taskbacktimeoutcheck',
            daemon=True)
        self._t_deal_taskback = threading.Thread(
            target=self._deal_taskbback, name='deal_taskback', daemon=True)

        self._t_data_complete_judge = threading.Thread(
            target=self._data_complete_judge,
            name='data_complete_judge',
            daemon=True)

    def _start(self):
        """开一个线程循环检测是否有已发送的任务
        长时间未收到任务回馈响应，若有，则尝试重新发送任务。"""
        if self._started:
            return
        with self._startedlocker:
            if self._started:
                return

            # 任务超时判断线程暂时不起
            # if not self._t_taskback_timeout_check._started._flag:
            # self._t_taskback_timeout_check.start()
            if not self._t_deal_taskback._started._flag:
                self._t_deal_taskback.start()
            if not self._t_data_complete_judge._started._flag:
                self._t_data_complete_judge.start()

            self._startsub()
            self._started = True

    @abstractmethod
    def _startsub(self):
        pass

    def taskback_timeout_check(self):
        """开一个线程循环检测是否有已发送的任务
        长时间未收到任务回馈响应，若有，则尝试重新发送任务。"""
        # self._logger.info("Taskback timeout check not implemented")
        while True:
            try:
                # 暂不检查超时，直接一直等待
                time.sleep(10)
            except Exception:
                self._logger.error("Taskback timeout check error: {}".format(
                    traceback.format_exc()))
            finally:
                time.sleep(10)

    def _deal_data(self, data: InputData) -> bool:
        """处理采集端的任务回馈数据，返回是否处理成功。
        回来的必然是idown_btask_back数据类型"""
        try:
            # Taskback数据需要解析，并根据数据内容，更新控制端本地数据库
            # 然后根据platform回传中心

            with self._datas_locker:
                self._datas.append(data)
                # 动态加个属性记录解析出来的所有TaskBatchBack对象。。
                data.tbs: list = []
                data.tbslocker = threading.RLock()

            for tb in self._parse_data_back(data):
                try:

                    if not isinstance(tb, TaskBackBase):
                        raise Exception("Invalid {} for taskbackdeal".format(
                            type(TaskBackBase).__name__))

                    # 动态加个属性标记是否处理成功
                    # None：正在处理
                    # False: 处理失败
                    # True: 处理成功
                    tb.ok: bool = None
                    tb.failedtimes: int = 0  # 失败重试次数
                    tb.errbackgenerated: bool = False

                    with data.tbslocker:
                        data.tbs.append(tb)

                    self._tbbqueue.put(tb)

                except Exception:
                    self._logger.error(
                        "Save and judge TaskBatchBack error: {}".format(
                            traceback.format_exc()))
                    data.on_complete(False)

        except Exception:
            self._logger.error(
                "Deal data error:\nplatform:{}\ndata:{}\nerror:{}".format(
                    data._platform, data._source, data._source))
        finally:
            pass

    @abstractmethod
    def _parse_data_back(self, data: InputData) -> iter:
        raise NotImplementedError()

    def _deal_taskbback(self):
        """根据采集端回传任务状态数据，更新数据库，并回传任务回馈数据。
        """
        got: bool = False
        while True:
            try:

                got = False
                tb: TaskBackBase = self._tbbqueue.get(timeout=3)
                got = True

                if not self._deal_data_back(tb):
                    tb.ok = False
                else:
                    tb.ok = True

            except queue.Empty:
                pass
            except Exception as ex:
                # if got:
                #     tb._cmdrcvmsg = ','.join(ex.args)
                #     self._on_deal_err(tb, traceback.format_exc())
                # else:
                tb.ok = False
                tb._cmdrcvmsg = ex.args
                self._logger.error("Deal TaskBatchBack error: {}".format(
                    traceback.format_exc()))
            finally:
                if got:
                    self._tbbqueue.task_done()

    @abstractmethod
    def _deal_data_back(self, tb):
        """处理回馈数据"""
        raise NotImplementedError()

    # @abstractmethod
    # def _on_deal_err(self, tb, msg: str):
    #     self._logger.error("Deal FeedBack error:\ndata:{}\nerror:{}".format(
    #         tb.inputdata.name, msg))

    def _data_complete_judge(self):
        '''数据处理完成判定'''
        completed: list = []
        while True:
            try:
                completed.clear()

                with self._datas_locker:
                    for data in self._datas:
                        data: InputData = data

                        # None：正在处理
                        # False: 处理失败
                        # True: 处理成功
                        with data.tbslocker:
                            allok = True
                            for tb in data.tbs:
                                tb: TaskBackBase = tb
                                if not isinstance(tb.ok, bool):
                                    allok = False
                                elif not tb.ok:
                                    # 如果是进度状态数据，则忽略错误，
                                    if tb._cmdstatus == ECommandStatus.Progress:
                                        tb.ok = True  # 当作成功数据处理
                                        continue
                                    # 内部处理错误或任务回馈文件错误则反回错误状态信息到中心
                                    self._output_taskback(
                                        tb, ECommandStatus.Failed,
                                        '处理出错：{}'.format(tb.cmdrcvmsg))

                            if not allok:
                                continue

                            if any([tb.ok is None for tb in data.tbs]):
                                continue

                        with data.tbslocker:
                            if any([not tb.ok for tb in data.tbs]):
                                data.on_complete(False)
                            else:
                                data.on_complete(True)

                        # data完成
                        completed.append(data)

                    for d in completed:
                        self._datas.remove(d)

            except Exception:
                self._logger.error(
                    "TaskBatchBack complete judge error: {}".format(
                        traceback.format_exc()))
            finally:
                time.sleep(1)

    @abstractmethod
    def _output_taskback(self, task, status: ECommandStatus, msg: str):
        """子类返回总任务回馈"""
        raise NotImplementedError()