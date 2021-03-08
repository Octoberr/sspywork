"""
autotask download manager
create by judy 2019/07/27
"""
import threading
import time
import traceback
from queue import Queue
from datetime import datetime
import pytz

from datacontract import ETaskStatus, ECommandStatus
from datacontract.automateddataset import AutomatedTask, EAutoType
from idownclient.automated import Exploit, GeoName
from idownclient.config_task import clienttaskconfig
from .automanagebase import AutoManagenBase
from ..clientdbmanager.sqlcondition import (ESqlComb, SqlCondition,
                                            SqlConditions)


class AutoTaskDownloadManager(AutoManagenBase):
    def __init__(self):
        AutoManagenBase.__init__(self)
        # 新任务队列
        self._new_autotask_queue = Queue()
        # 正在处理的任务队列
        self._dealing_queue: dict = {}
        # 正在处理新任务队列,如果有新任务是不会执行循环下载任务的
        self._dealing_queue_locker = threading.Lock()
        # 并发队列任务数
        self._concur_num = clienttaskconfig.concurrent_number
        # 自动化插件字典,目前只有两个
        self._autotask_dic = {
            EAutoType.EXPDB: Exploit,
            EAutoType.DBIP: None,
            EAutoType.GEONAME: GeoName
        }

    def on_task_complete(self, task: AutomatedTask):
        """Task对象处理完毕的回调"""
        with self._dealing_queue_locker:
            if self._dealing_queue.__contains__(task.batchid):
                self._dealing_queue.pop(task.batchid, None)

    def _get_new_autotask(self):
        """
        目前先不考虑设置，不太清楚需不需要做循环下载
        modify by judy 2019/08/06
        不用循环下载，控制都在server端
        :return:
        """
        new_task_list = []
        new_task = self._sqlfunc.query_auto_task(
            SqlConditions(
                SqlCondition(
                    colname='taskstatus',
                    val=ETaskStatus.New.value,
                    comb=ESqlComb.Or),
                SqlCondition(
                    colname='taskstatus',
                    val=ETaskStatus.WaitForDeal.value,
                    comb=ESqlComb.Or),
                # SqlCondition(
                #     colname='taskstatus',
                #     val=ETaskStatus.Logining.value,
                #     comb=ESqlComb.Or),
                # SqlCondition(
                #     colname='taskstatus',
                #     val=ETaskStatus.Downloading.value,
                #     comb=ESqlComb.Or),
            ))
        # if len(new_task) != 0:
        for el in new_task:
            # 这里可以做一些筛选
            # 你预测对了
            batchid = el.get('batchid')
            if self._dealing_queue.__contains__(batchid):
                continue
            new_task_list.append(el)
        return new_task_list

    def _put_task_to_queue(self, filedata: dict, queue: Queue):
        """
        将任务放进队列的通用方法，
        这里不用去判断设置，设置能用的话直接用吧
        :param filedata:
        :param queue:
        :return:
        """
        tsk: AutomatedTask = AutomatedTask.create_from_dict(filedata)
        if self._dealing_queue.__contains__(tsk.batchid):
            return
        tsk.on_complete = self.on_task_complete
        # 同时进行的最大的下载任务数,优先级高的任务直接处理
        # 正在下载的任务可能需要很久，所以每次sleep5秒即可
        # while len(self._dealing_queue) >= self._concur_num:
        #     time.sleep(5)
        with self._dealing_queue_locker:
            self._dealing_queue[tsk.batchid] = tsk
        # 修改任务状态为正在处理到对列
        tsk.taskstatus = ETaskStatus.WaitForDeal
        # 修改数据库中的任务状态
        self._sqlfunc.update_auto_status('taskstatus', tsk.taskstatus.value, tsk.batchid, tsk.taskid)
        queue.put(tsk)
        return

    def put_new_autotask(self):
        """
        将新的autotask放入队列
        :return:
        """
        while True:

            new_tasks = self._get_new_autotask()
            if len(new_tasks) == 0:
                # 3秒钟扫描一次数据库
                time.sleep(1)
                continue
            try:
                for filedata in new_tasks:
                    self._put_task_to_queue(filedata,
                                            self._new_autotask_queue)
            except:
                self._logger.error(
                    f"Make the task from sqlite wrong, err:{traceback.format_exc()}"
                )
            finally:
                time.sleep(0.5)

    def __after_end(self, task: AutomatedTask):
        """
        在任务执行完成后干的一些事情
        :return:
        """
        # 第一个是更新任务状态
        self._sqlfunc.update_auto_status('taskstatus', ETaskStatus.DownloadSucceed.value, task.batchid, task.taskid)
        # 然后是给个任务执行完成的时间
        task.lastendtime = int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp())
        # 最后输出回馈
        self._logger.info(f"Automated task download complete, mission acomplished.")
        self.write_autotaskback(task, ECommandStatus.Succeed, "Mission acomplished")
        # 将完成的任务移出队列
        time.sleep(1)
        if task is not None:
            if callable(task.on_complete):
                task.on_complete(task)
        return

    def execute_new_autotask(self):
        """
        不断的从新任务中取出任务,下载数据
        :return:
        """
        got = False
        while True:
            if self._new_autotask_queue.empty():
                time.sleep(1)
                continue
            got = False
            tsk: AutomatedTask = self._new_autotask_queue.get()
            got = True

            self._logger.info(f"Task start: {tsk.batchid}, tasktype:{tsk.autotasktype.value}")

            try:
                # 根据tasktype的值实例化不同的插件，然后执行最后销毁,销毁的时候需要给server一个状态
                plug_info = self._autotask_dic.get(tsk.autotasktype, None)
                if plug_info is not None:
                    plug = plug_info()
                    plug.start()
                    # 最后执行完成后删除
                    del plug
                    self.__after_end(tsk)
            except:
                self._logger.error(
                    f"Execute autotask error, err:{traceback.format_exc()}")
            finally:
                time.sleep(1)  # 等待线程状态回执
                if got:
                    self._new_autotask_queue.task_done()

    def start(self):
        """
        多线程开启任务执行
        :return:
        """
        thread1 = threading.Thread(target=self.put_new_autotask, name="autotaskscan")
        thread2 = threading.Thread(target=self.execute_new_autotask, name="autotaskexecute")
        thread1.start()
        thread2.start()
