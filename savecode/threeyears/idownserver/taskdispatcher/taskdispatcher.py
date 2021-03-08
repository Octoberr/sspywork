"""task dispathcer"""

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
                          InputData, Task, TaskBack, TaskBatchBack)
from outputmanagement import OutputManagement

from ..config_stdconvert import stdconvertconfig
from ..dbmanager.dbmanager import (DbManager, EDBAutomic, SqlCondition,
                                   SqlConditions)
from ..statusmantainer import StatusMantainer
from ..stdconvertmanagement.stdconvertmanagement import \
    StandardConvertManagement
from .dispatcherbase import DispatcherBase
from .strategy.strategymanager import StrategyManager


class TaskDispatcher(DispatcherBase):
    """任务分配器。\n
    uniquename:当前任务分配器唯一标识，为了区分处理不同任务类型的处理器\n
    statusreadinterval: 指定心跳间隔，即只读取最近n秒内更新的采集端状态，单位秒。\n
    maxwaitcount: 为了给采集端状态信息缓冲时间，设置任务堆积数量处理阈值，达到数量上限分配一次\n
    maxwaittime: 为了给采集端状态信息缓冲时间，设置任务堆积时间处理阈值，达到时间上限分配一次\n
    relation_inputer_src: 当前处理器关联的输入器，不为空时仅从关联的输入器输入数据\n
    datamatcher: 当前任务分发器的数据匹配器"""
    def __init__(
            self,
            uniquename: str,
            datamatcher: DataMatcher = None,
            maxwaitcount: int = 1,
            maxwaittime: float = 3,
            relation_inputer_src: list = None,
    ):
        # 这两个目录字段暂时弃用，统一仅对InputData进行错误目录移动等操作。
        #  tmpdir: str = './_servertmp',
        #  errordir: str = r'./_servererror'):

        DispatcherBase.__init__(self, uniquename, datamatcher, maxwaitcount,
                                maxwaittime, relation_inputer_src)

    def _output_taskback(self, task, status: ECommandStatus, msg: str):
        """返回总任务回馈"""
        if not isinstance(task, Task):
            self._logger.error(
                "Invalid task object for output taskback: {}".format(
                    type(task)))
            return

        task: Task = task
        taskback: TaskBack = TaskBack(task, status, msg)
        if not OutputManagement.output(taskback):
            self._logger.error(
                "Output TaskBack failed:\ntaskid={}\ndata={}".format(
                    task.taskid, task.inputdata._source))

    def _output_batch_task_back(self, task, status: ECommandStatus, msg: str):
        """返回子任务回馈"""
        if not isinstance(task, Task):
            self._logger.error(
                "Invalid task object for output taskback: {}".format(
                    type(task)))
            return

        task: Task = task
        taskbatchback: TaskBatchBack = TaskBatchBack.create_from_task(
            task, status, msg)
        if not OutputManagement.output(taskbatchback):
            self._logger.error(
                'Output TaskBatchBack failed:\ntaskid={}\nbatchid={}'.format(
                    task.taskid, task.batchid))

    def _dispatch_task(self, task: Task) -> Tuple[bool, str]:
        """分配Task"""
        if not isinstance(task, Task):
            return (False, "错误的Task类型: {}".format(type(task)))

        succ, needdispatch, client, msg = self._choose_client(task)
        if not succ:
            return (succ, msg)

        # 存入数据库
        if needdispatch:
            if not self._save_task_to_db(task, client):
                succ = False
        else:
            self._logger.info(
                "Reduplicated task already dispatched and is currently on dealing:\ntaskid:{}\nbatchid:{}\nclient:{}\t{}"
                .format(task.taskid, task.batchid,
                        client._statusbasic._clientid, client._statusbasic.ip))

        return (succ, msg)

    def _save_task_to_db(self, task: Task, client: Client) -> bool:
        """存储新任务，来的肯定是子任务\n
        task: 任务对象\n
        client: 任务被分配到的采集端对象"""
        res: bool = True
        try:
            ############
            # 1. 同一个账号测试N个app
            # 2. N个账号测试1个app
            # 3. N个账号测试N个app，他非要对每个账号选apptype
            # 4. 同一批次任务反复测试（同一个批处理任务需要反复测了10次那种）

            #
            # 任务必有taskid+batchid

            # 所有任务来了都存入3张表
            with DbManager.get_automic_locker(EDBAutomic.ReduplicateTask):
                res = DbManager.save_new_idown_task(task, client)
            if res:
                self._logger.debug("Save task OK: {} {} {} -> {} {}".format(
                    task.taskid, task.batchid, task.tasktype.name,
                    client._statusbasic._clientid, client._statusbasic.ip))
            else:
                # 如果存入失败了，
                # 对于当前子任务来说，需要返回一个子任务回馈文件
                # 对于总任务，需要判断是否其所有子任务都失败了，并返回回馈数据
                self._logger.debug("Save task Faild: {} {} {} -> {} {}".format(
                    task.taskid, task.batchid, task.tasktype.name,
                    client._statusbasic._clientid, client._statusbasic.ip))

                ## 返回回馈数据
                taskbatchback: TaskBatchBack = TaskBatchBack.create_from_task(
                    task, ECommandStatus.Failed, '内部错误：任务分配采集端失败，存入本地数据库失败')
                if not OutputManagement.output(taskbatchback):
                    self._logger.error(
                        'Output TaskBatchBack failed:\ntaskid={}\nbatchid={}'.
                        format(task.taskid, task.batchid))

        except Exception:
            res = False
            self._logger.error(
                "save new task to db error:\ntaskid:{}\nerror:{}".format(
                    task.taskid, traceback.format_exc()))

        return res

    def _choose_client(self, task: Task) -> Tuple[bool, bool, Client, str]:
        """选择最优采集端，返回配置的采集端ip。
        返回<是否选择采集端成功，是否更新到数据库，选择的采集端>"""
        succ: bool = True
        needdispatch: bool = True
        res: Client = None
        msg: str = None
        try:

            currentclients: dict = StatusMantainer.get_clientstatus_id_sorted()
            # 检查任务，如果是完全重复的taskid+batchid（直接手动重新搞的），则找到已经被分配过的采集端
            existtask: Task = DbManager.get_batch_task(task._platform,
                                                       task.taskid,
                                                       task.batchid)

            if not isinstance(existtask, Task) or not isinstance(
                    existtask._clientid, str
            ) or existtask._clientid == "" or not currentclients.__contains__(
                    existtask._clientid):
                # 如果目标采集端未上线，或查询到任务未分配过采集端，则新分配一个，并需要更新到数据库。
                # 这种情况会导致同一个账号分布在不同的采集端，将导致退出登陆等任务无法兼顾到所有
                # 采集端。所以如果在任务分配到新的采集端后，旧的采集端又上限了，那么在更新到数据库
                # 之前，需要搞一个零时任务，后台有一个线程循环执行，
                # 当收到任何来自此账号所属的原采集端的关于此账号的任何信息时，触发零时任务，并用此零时
                # 任务告知原有采集端取消此账号的自动下载，并将此账号下线（删除即可，不注销）（触发性重分配告知）。
                succ, res, msg = self._strategymngr.dispatch(
                    task, currentclients)
            else:
                # 改为全部重新下发
                # 但这样可能会出现任务错乱的问题。
                # 比如来了task1下发了，然后client执行到一半，又来了一个task1，改了策略，下发了，
                # 这时client的任务回馈过来了，导致这个回馈把第二次下发的任务给完成了，但实际上
                # client还没有收到这个任务。
                # 先这样吧，后面数据库提出来就好了，分布式事务做好。
                res = currentclients.get(existtask._clientid)
                if res is None:
                    raise Exception(
                        "Get client for dispatched task failed: taskid={}, batchid={}, clientid={}"
                        .format(task.taskid, task.batchid, task._clientid))
                needdispatch = True

                # # 走到这里，目标采集端必然存在并在线
                # # 如果已存在的任务状态为正在执行等状态，则直接返回一个回馈文件说正在执行
                # # 否则重新下发到目标采集端
                # res = currentclients[existtask._clientid]
                # if existtask.cmdstatus == ECommandStatus.Failed or \
                #     existtask.cmdstatus == ECommandStatus.Succeed or \
                #     existtask.cmdstatus == ECommandStatus.Cancelled or \
                #     existtask.cmdstatus == ECommandStatus.Timeout:
                #     # 重新下发
                #     pass
                # else:
                #     # 返回回馈数据，说正在执行
                #     needdispatch = False
                #     # 这种情况暂时不返回任何回馈数据
                #     # tb: TaskBatchBack = TaskBatchBack.create_from_task(
                #     #     task, ECommandStatus.Progress, '任务正在执行')
                #     # if not OutputManagement.output(tb):
                #     #     self._logger.error(
                #     #         "Return TaskBatchBack of reduplicated task already running failed:\ntaskid:{}\nbatchid:{}\nclientid:{}".
                #     #         format(task.taskid, task.batchid,
                #     #                existtask._clientid))

        except Exception:
            self._logger.error("Choose idowntask client error: %s" %
                               traceback.format_exc())
            res = None
            succ = False
            msg = '内部错误500'

        return (succ, needdispatch, res, msg)

    def _log_error_task(self, task: Task, msg: str = 'error'):
        """打印错误任务的日志信息"""
        try:
            if msg is None:
                msg = 'error'
            self._logger.info(f"""{msg}:
segline:{task.segline}
segindex:{task.segindex}
taskid:{task.taskid}
batchid:{task.batchid}
tasktype:{task.tasktype.name}
apptype:{task.apptype}""")

        except Exception:
            self._logger.error(
                "Output error task to error folder error:\ntaskid=%s\nerror:%s"
                % (task.taskid, traceback.format_exc()))
