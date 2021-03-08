"""dispatcher base"""

# -*- coding:utf-8 -*-

import os
import queue
import shutil
import threading
import time
import traceback
from typing import Tuple

from commonbaby.helpers import helper_file
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import (Client, DataMatcher, ECommandStatus, ETaskStatus,
                          InputData)
from outputmanagement import OutputManagement

from ..config_stdconvert import stdconvertconfig
from ..dbmanager.dbmanager import (DbManager, EDBAutomic, SqlCondition,
                                   SqlConditions)
from ..servicemanager.dealerbase import DealerBase
from ..statusmantainer import StatusMantainer
from ..stdconvertmanagement.stdconvertmanagement import \
    StandardConvertManagement
from .strategy.strategymanager import StrategyManager
from abc import ABCMeta, abstractmethod


class DispatcherBase(DealerBase):
    """"""

    __metaclass = ABCMeta

    def __init__(
            self,
            uniquename: str,
            datamatcher: DataMatcher,
            maxwaitcount: int = 1,
            maxwaittime: float = 3,
            relation_inputer_src: list = None,
    ):
        DealerBase.__init__(self, datamatcher)

        if not isinstance(uniquename, str) or uniquename == "":
            raise Exception("Task dispatcher uniquename cannot be None")

        self._strategymngr = StrategyManager()

        self._uniquename = uniquename

        self._logger: MsLogger = MsLogManager.get_logger(
            "dispatcher_%s" % uniquename)

        # 各字段
        self._relation_inputer_src = relation_inputer_src

        self._maxwaitcount: int = 1
        if isinstance(maxwaitcount, int) and maxwaitcount > 0:
            self._maxwaitcount = maxwaitcount

        self._maxwaittime: float = 3
        if type(maxwaittime) in [int, float] and maxwaittime > 0:
            self._maxwaittime = maxwaittime

        # 增时睡眠时间
        self._increace_sleep_sec: int = 1

        # 各执行器
        self._stdconvert = StandardConvertManagement(stdconvertconfig)

        # 处理队列，线程
        self._task_queue = queue.Queue()
        self._dispatch_queue: dict = {}
        self._dispatch_queue_locker = threading.RLock()
        # 用于存放data->tasks映射关系，方便根据任务处理结果处理文件
        self._data_map: list = []
        self._data_map_locker = threading.RLock()

        self._t_task_allocate = threading.Thread(
            target=self._task_allocate,
            name="taskallocate_{}".format(self._uniquename),
            daemon=True)
        self._t_task_ok_judge = threading.Thread(
            target=self._task_ok_judge,
            name="taskokjudge_{}".format(self._uniquename),
            daemon=True)
        self._timeok: bool = False
        self._timeok_locker = threading.Lock()
        self._t_timer = threading.Thread(
            target=self._timer_thread, name="tasktimer", daemon=True)

    def _start(self):
        """开启各种处理线程"""
        if not self._t_task_allocate._started._flag:
            self._t_task_allocate.start()
        if not self._t_task_ok_judge._started._flag:
            self._t_task_ok_judge.start()
        if not self._t_timer._started._flag:
            self._t_timer.start()

        self._start_sub()

    @abstractmethod
    def _start_sub(self):
        pass

    def _timer_thread(self, intervalsec: float = 0.1):
        """
        定时器，定时分配任务。\n
        intervalsec: 轮询间隔，单位秒，默认0.1
        """
        if not type(intervalsec) in [int, float]:
            raise Exception("Timer param inverval sec type wrong.")
        if intervalsec < 0 or intervalsec > 10:
            intervalsec = 0.1
        elapsed: float = 0
        while True:
            try:
                if elapsed >= self._maxwaittime:
                    with self._timeok_locker:
                        self._timeok = True
                        elapsed = 0
            except Exception:
                self._logger.error(
                    "Task dispatcher timer error: %s" % traceback.format_exc())
            finally:
                time.sleep(intervalsec)
                # 当timeok为True时，表示自上次将timeok设置为true到现在都
                # 还没完成一次分配，所以逝去时间elapsed不涨
                if not self._timeok:
                    elapsed += intervalsec

    def _task_ok_judge(self):
        """
        根据子任务处理结果，对InputData进行处理，并根据情况返回总任务执行回馈数据
        """
        # 只要有一个任务成功，整个data就算成功
        # 全部失败才算失败

        tmplist: list = []  # 临时列表，用于存储处理完的data集
        while True:
            try:
                tmplist.clear()
                with self._data_map_locker:
                    for data in self._data_map:
                        data: InputData = data
                        if not data.tasksparsedok:
                            continue

                        # 数据没有解析出任何任务
                        if len(data.tasks) < 1:
                            tmplist.append(data)
                            continue

                        # 当前数据还有未分配完成的task就先不要慌，这个线程不需要实时，根本就不要慌
                        if any([t.deliverok is None for t in data.tasks]):
                            continue

                        # inputdata数据和总任务判断
                        try:
                            if all([not t.deliverok for t in data.tasks]):
                                # 全部失败则data算作失败，并返回总任务失败回馈数据
                                self._logger.error(
                                    "All tasks in data dispatch client failed: {}"
                                    .format(data._source))
                                data.on_complete(False)
                                task = data.tasks[0]  #随便取一个task，要它的taskid
                                self._output_taskback(task,
                                                      ECommandStatus.Failed,
                                                      '内部错误：任务分配采集端失败')
                            else:
                                data.on_complete(True)
                        finally:
                            # 只要下来，整个data和其解析出来的子任务就都处理完成了
                            tmplist.append(data)

                    # data从队列移除
                    for data in tmplist:
                        self._data_map.remove(data)

            except Exception:
                self._logger.error(
                    "Task complete status judge thread error: %s" %
                    traceback.format_exc())
            finally:
                time.sleep(1)

    def _deal_data(self, data: InputData) -> bool:
        """分配任务到采集端，返回bool成功与否"""
        # res需要永远返回None，表示此dealer内部自行处理data完成情况
        res: bool = None
        try:
            # 这里解出来的每个数据段（task），都是一个子任务
            # 其必然带有apptype

            data.tasks = []  #记录当前数据中解析出来的所有task
            data.tasksparsedok = False  #记录当前文件是否已经解析完成

            for tsk in self._stdconvert.convert(data):

                tsk.deliverok = None
                data.tasks.append(tsk)

                self._task_queue.put(tsk)
                with self._data_map_locker:
                    self._data_map.append(data)

                self._logger.debug("New task: %s %s" % (tsk, type(tsk)))

            # 只要有一个任务成功，整个data就算成功
            data.tasksparsedok = True

        except Exception:
            self._logger.error("Dispatch task error:\ndata:%s\nerror:%s" %
                               (data._source, traceback.format_exc()))
            data.on_complete(False)

        return res

    def _increace_sleep(self, msg: str = None):
        """增时睡眠"""
        if not self._increace_sleep_sec >= 60:
            self._increace_sleep_sec *= 2

        if msg is None:
            msg = ""
        self._logger.info(
            "%s, sleep %s seconds..." % (msg, self._increace_sleep_sec))
        time.sleep(self._increace_sleep_sec)

    def _task_allocate(self):
        """任务分配器，从queue读取任务，并分配到采集端"""
        # 用于存储一次分配中，分配成功的任务
        got: bool = False
        currentclients = 0
        while True:
            try:
                try:
                    got = False
                    task = self._task_queue.get(timeout=0.5)
                    got = True
                    if task is None:
                        continue

                    currentclients: dict = StatusMantainer.get_clientstatus_ip_sorted(
                    )
                    with self._dispatch_queue_locker:
                        self._dispatch_queue[task] = None

                        # 看有没有可用采集端
                        if len(currentclients) < 1:
                            self._increace_sleep(
                                "No available client, %s task(s) waiting for allocation"
                                % len(self._dispatch_queue))
                            continue
                        else:
                            self._increace_sleep_sec = 1

                        # 数量阈值和时间阈值任何一个达到上限则分配一次
                        if len(self._dispatch_queue
                               ) < self._maxwaitcount and not self._timeok:
                            continue

                except queue.Empty:
                    with self._dispatch_queue_locker:
                        # 看有没有可用采集端
                        if len(self._dispatch_queue) > 0 and len(
                                currentclients) < 1:
                            self._increace_sleep(
                                "No available client, %s task(s) waiting for allocation"
                                % len(self._dispatch_queue))
                            continue
                        else:
                            if self._increace_sleep_sec > 1:
                                self._increace_sleep_sec = 1

                        # 数量阈值和时间阈值任何一个达到上限则分配一次
                        if len(self._dispatch_queue
                               ) < self._maxwaitcount and not self._timeok:
                            continue
                finally:
                    if got:
                        self._task_queue.task_done()

                with self._timeok_locker:
                    if self._timeok:
                        self._timeok = False
                if len(self._dispatch_queue) < 1:
                    continue

                # 子类进行分配
                self.__dispatch_task()

            except queue.Empty:
                pass
            except Exception:
                self._logger.error("Task status monitor thread error: %s" %
                                   traceback.format_exc())
            finally:
                pass

    @abstractmethod
    def _dispatch_task(self, task) -> Tuple[bool, str]:
        """子类实现据体分配业务"""
        raise NotImplementedError()

    @abstractmethod
    def __dispatch_task(self):
        # 子类实现分配任务
        # 使用 self._dispatch_queue
        # 注意使用 self._dispatch_queue_locker 加锁处理

        completelist: list = []
        with self._dispatch_queue_locker:
            for item in self._dispatch_queue.items():
                # item[0]是task对象，item[1]是预留的额外参数
                task = item[0]
                try:
                    # obj = item[1]
                    msg: str = None
                    # 重试3次，每次失败睡眠一段时间，避免时间差
                    for i in range(4):
                        succ, msg = self._dispatch_task(task)
                        if not succ:
                            # 重试3次，每次失败睡眠一段时间，避免时间差
                            if i < 3:
                                self._logger.warn(
                                    "Dispatch task failed: taskid={}\nmsg:{}\nsleep {}s and retry..."
                                    .format(task.taskid, msg, 3))
                                time.sleep(3)
                                continue
                            else:
                                # 若没有选择到任何采集端ip，则输出任务到error目录
                                self._log_error_task(task,
                                                     'No client suites task')
                                task.deliverok = False
                                break
                        # 退出重试循环
                        task.deliverok = True
                        break

                    # 分配失败的任务返回子任务回馈
                    if not task.deliverok:
                        if msg is None:
                            msg = '内部错误：任务分配采集端失败，存入本地数据库失败'
                        self._output_batch_task_back(
                            task, ECommandStatus.Failed, msg)

                except Exception:
                    # 有任何异常则输出到error目录
                    task.deal_sucdeliverokceed = False
                    self._log_error_task(task, 'Dispatch task error')
                finally:
                    completelist.append(task)

            # 将分配完成的任务剔除队列
            with self._dispatch_queue_locker:
                for task in completelist:
                    if self._dispatch_queue.__contains__(task):
                        self._dispatch_queue.pop(task, None)

    @abstractmethod
    def _output_taskback(self, task, status: ECommandStatus, msg: str):
        """子类返回总任务回馈"""
        raise NotImplementedError()

    @abstractmethod
    def _output_batch_task_back(self, task, status: ECommandStatus, msg: str):
        """子类返回子任务回馈（若存在子任务）"""
        pass

    @abstractmethod
    def _log_error_task(self, task, msg: str):
        """信息较全的，统一的，格式化打日志"""
        pass