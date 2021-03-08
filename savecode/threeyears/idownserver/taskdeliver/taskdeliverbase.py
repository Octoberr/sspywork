"""task deliver"""

# -*- coding:utf-8 -*-

import queue
import threading
import time
import traceback
from abc import ABCMeta, abstractmethod

from datacontract import Client, ECommandStatus, Task, TaskBack, TaskBatchBack
from outputmanagement import OutputManagement

from ..dbmanager import DbManager, EDBAutomic, SqlCondition, SqlConditions
from ..servicemanager import MicroService
from ..statusmantainer import StatusMantainer
from .taskdeliverconfig import TaskDeliverConfig


class TaskDeliverBase(MicroService):
    """Read task from database, 
    and handle tasks to clients.\n
    从数据库读取任务信息并分发，分发失败时需要将数据库
    中此条任务标记为分发失败，并生成回馈数据。
    当前模块为 任务发送管理器，负责 等待发送的任务及其状态管理。"""

    __metaclass = ABCMeta

    _static_initialed: bool = False
    _static_init_locker = threading.RLock()

    _config: TaskDeliverConfig = None

    @classmethod
    def static_init(cls, cfg: TaskDeliverConfig):
        with cls._static_init_locker:
            if cls._static_initialed:
                return
            if not isinstance(cfg, TaskDeliverConfig):
                raise Exception("Invalid param 'cfg' for TaskDeliver")
            cls._config = cfg

            cls._static_initialed = True

    def __init__(self):
        MicroService.__init__(self)

        self._dbmanager: DbManager = DbManager()

        self._started: bool = False
        self._started_locker = threading.Lock()

        # 发送队列
        self._send_queue = queue.Queue()

        self.__t_scan = threading.Thread(
            target=self._scan_new_tasks, name="scan_task", daemon=True)
        self.__t_deal = threading.Thread(
            target=self._deliver_tasks, name="deliver_task", daemon=True)

    def start(self):
        """启动处理"""
        if self._started:
            return
        with self._started_locker:
            if self._started:
                return
            self.__t_scan.start()
            self.__t_deal.start()
            self._started = True

    def _scan_new_tasks(self):
        """扫数据库，发命令"""
        #####
        # 1. 要有执行超时重发机制。
        #####
        while True:
            try:
                for task in self._get_deliverable_task():
                    if task is None:
                        continue

                    # 此处是从batchtask表拿的所有待下发的子任务，
                    # 必有platform, clientid, taskid, batchid
                    if self._is_task_in_deal_queue(task):
                        continue

                    self._add_task_to_deal_queue(task)
                    self._send_queue.put(task)

            except Exception:
                self._logger.error(
                    f"Scan new tasks from db error: {traceback.format_exc()}")
            finally:
                time.sleep(1)

    @abstractmethod
    def _get_deliverable_task(self) -> iter:
        raise NotImplementedError()

    @abstractmethod
    def _is_task_in_deal_queue(self, task) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def _add_task_to_deal_queue(self, task: Task):
        """将任务添加到处理中队列"""
        raise NotImplementedError()

    @abstractmethod
    def _remove_task_from_deal_queue(self, task):
        raise NotImplementedError()

    def _deliver_tasks(self):
        """将命令发走"""
        gotnew: bool = False
        while True:
            try:
                gotnew = False
                task = self._send_queue.get(timeout=3)
                gotnew = True

                self._to_deliver(task)
            except queue.Empty:
                continue
            except Exception:
                self._logger.error(
                    f"Deliver new tasks to clients error: {traceback.format_exc()}"
                )
            finally:
                if gotnew:
                    self._send_queue.task_done()
                    self._remove_task_from_deal_queue(task)

    @abstractmethod
    def _to_deliver(self, task):
        raise NotImplementedError()

    def stop(self):
        pass

    def reload(self):
        pass
