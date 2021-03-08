"""task deliver"""

# -*- coding:utf-8 -*-

import queue
import threading
import time
import traceback

from datacontract import (Client, CmdFeedBack, ECommandStatus, IdownCmd, Task,
                          TaskBack, TaskBatchBack)
from outputmanagement import OutputManagement

from ..dbmanager import DbManager, EDBAutomic, SqlCondition, SqlConditions
from ..statusmantainer import StatusMantainer
from .taskdeliverbase import TaskDeliverBase
from .taskdeliverconfig import TaskDeliverConfig


class TaskDeliver(TaskDeliverBase):
    """Read task from database, 
    and handle tasks to clients.\n
    从数据库读取任务信息并分发，分发失败时需要将数据库
    中此条任务标记为分发失败，并生成回馈数据。
    当前模块为 任务发送管理器，负责 等待发送的任务及其状态管理。"""

    def __init__(self):
        TaskDeliverBase.__init__(self)

        # 任务处理中字典，用于过滤正在处理下发的任务又被查出来了
        # 如果来了一个任务id=1，添加到处理队列拿去下发，下发过程
        # 中又来了一个任务id=1（用户手动重复拷贝），此时算做同一个
        # 任务。除非下发完毕更新了数据库任务状态为'已下发，正在执行中'后，
        # 又来了同taskid的任务，此时才需要重新下发一次。
        # 这是一个 4层的 字典，结构为：
        # <platform, <clientid, <taskid, <batchid, taskobj>>>>
        self._deal_queue: dict = {}
        self._deal_queue_locker = threading.RLock()

    def _get_deliverable_task(self) -> iter:
        for task in self._dbmanager.get_deliverable_task():
            task: Task = task
            if not isinstance(task, Task):
                self._logger.warn(
                    "Invalid task from database for delivering: {}".format(
                        task))
                continue
            yield task

    def _is_task_in_deal_queue(self, task: Task):
        """查询某任务是否正在下发过程中，返回True是/False否"""
        res: bool = False
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(task._platform):
                return res

            if not self._deal_queue[task._platform].__contains__(
                    task._clientid):
                return res

            if not self._deal_queue[task._platform][
                    task._clientid].__contains__(task.taskid):
                return res

            if not self._deal_queue[task._platform][task._clientid][
                    task.taskid].__contains__(task.batchid):
                return res

            res = True
            return res

    def _add_task_to_deal_queue(self, task: Task):
        """将任务添加到处理中队列"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(task._platform):
                self._deal_queue[task._platform]: dict = {}

            if not self._deal_queue[task._platform].__contains__(
                    task._clientid):
                self._deal_queue[task._platform][task._clientid]: dict = {}

            if not self._deal_queue[task._platform][
                    task._clientid].__contains__(task.taskid):
                self._deal_queue[task._platform][task._clientid][
                    task.taskid]: dict = {}

            if not self._deal_queue[task._platform][task._clientid][
                    task.taskid].__contains__(task.batchid):
                self._deal_queue[task._platform][task._clientid][task.taskid][
                    task.batchid] = task

    def _remove_task_from_deal_queue(self, task: Task):
        """从处理队列移除指定taskid的任务，使放开数据库新任务查询"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(task._platform):
                return

            if not self._deal_queue[task._platform].__contains__(
                    task._clientid):
                return

            if not self._deal_queue[task._platform][
                    task._clientid].__contains__(task.taskid):
                return

            if not self._deal_queue[task._platform][task._clientid][
                    task.taskid].__contains__(task.batchid):
                return

            self._deal_queue[task._platform][task._clientid][task.taskid].pop(
                task.batchid, None)

    def _to_deliver(self, task: Task):
        """任务分类，分给各传输器"""
        try:
            succ: bool = False
            try:

                if not isinstance(task, Task):
                    self._logger.error("Invalid task to_deliver")
                    return

                if not isinstance(task._clientid, str) or task._clientid == "":
                    self._logger.error(
                        "Invalid clientid in task object while delivering task:\ntaskid:{}\nclientid:{}"
                        .format(task.taskid, task._clientid))
                    return

                # 拿一下ip
                tmpclients = StatusMantainer.get_clientstatus_id_sorted()
                targetclient: Client = tmpclients.get(task._clientid, None)
                if not isinstance(targetclient, Client):
                    self._logger.error(
                        "Unknown client for task deliver:\nclientid:{}\ntaskid:{}\ntasktype:{}"
                        .format(task._clientid, task.taskid,
                                task.tasktype.name))
                    return

                # 传输给client
                ##########
                # 逻辑为：
                # 1. 事先并不知道分配给哪个采集端。
                # 2. 从数据库读取一条子任务，task任务对象有其被分配到的采集端的clientid。
                # 3. 根据task的clientid，和StatusMantainer的clients对象，找到目标client的clientip
                # 4. 根据clientip和当前TaskDeliver中配置的ip->目录配置，将任务task对象发送到
                #    指定目录（走文件）
                # 5. 或根据配置若走直连传输，则通过clientid找到对应采集端的地址并发送。
                ##########

                if not self._config._ipdir.__contains__(
                        targetclient._statusbasic.ip):
                    self._logger.error(
                        "Client transfer folder not configured: clientip={}".
                        format(targetclient._statusbasic.ip))
                else:
                    targetdir = self._config._ipdir[
                        targetclient._statusbasic.ip]
                    succ = OutputManagement.output_to_file(task, targetdir)

            finally:
                with self._dbmanager.get_automic_locker(
                        EDBAutomic.ReduplicateTask):
                    self._update_to_db(task, targetclient, succ)
                    self._merge_task_status(task)

        except Exception:
            self._logger.error("to_deliver error: taskid:{} error:{}".format(
                task.taskid, traceback.format_exc()))

    def _update_to_db(self, task: Task, targetclient: Client, succ: bool):
        """同步任务下发状态到数据库。这里来的永远是子任务"""
        try:
            if not succ:
                # 失败，返回回馈数据
                task.cmdstatus = ECommandStatus.Failed
                task.cmdrcvmsg = "发送任务到采集端失败"
                tb: TaskBatchBack = TaskBatchBack.create_from_task(
                    task, cmdrcvmsg=task.cmdrcvmsg)
                if not OutputManagement.output(tb):
                    self._logger.error(
                        "Write idown_task_back failed:\ntaskid:{}".format(
                            task.taskid))
                if isinstance(task.cmd, IdownCmd):
                    task.cmd.cmdstatus = ECommandStatus.Failed
                    task.cmd.cmdrcvmsg = task.cmdrcvmsg
                    cmdback: CmdFeedBack = CmdFeedBack.create_from_cmd(
                        task.cmd, task.cmd.cmdstatus, task.cmd.cmdrcvmsg)
                    if not OutputManagement.output(cmdback):
                        self._logger.error(
                            "Write IDownCmdBack failed:\nplatform:{}\ncmdid:{}"
                            .format(task._platform, task.cmd_id))
            else:
                # 成功
                task.cmdstatus = ECommandStatus.Dealing
                if isinstance(task.cmd, IdownCmd):
                    task.cmd.cmdstatus = ECommandStatus.Dealing
                self._logger.info(
                    "Send task succeed\t{}:\ntaskid:{}\nbatchid:{}\nclient:{}\t{}"
                    .format(task.tasktype.name, task.taskid, task.batchid,
                            task._clientid, targetclient._statusbasic.ip))

            # 更新数据库当前子任务状态
            if not self._dbmanager.update_batchtask_status(
                    task._platform, task.taskid, task.batchid, task.cmdstatus):
                # 这里如果更新数据库状态失败了，那发送线程可能会重新发送当前子任务。
                # 此时需要采集端支持 冥等性（任务去重，保证多次收到同一条任务只会处理一条）
                self._logger.error(
                    "Update task cmdstatus failed:\ntaskid:{}\ncmdstatus:{}".
                    format(task.taskid, task.cmdstatus.name))
            # 如果带cmd，更新cmd状态
            elif isinstance(
                    task.cmd,
                    IdownCmd) and not self._dbmanager.update_cmd_status(
                        task.cmd.platform, task.cmd.cmd_id,
                        targetclient._statusbasic._clientid,
                        task.cmd.cmdstatus):
                self._logger.error(
                    "Update cmd cmdstatus failed:\ntaskid:{}\ncmdstatus:{}".
                    format(task.taskid, task.cmdstatus.name))

        except Exception:
            self._logger.error("Update task cmdstatus to db error: {}".format(
                traceback.format_exc()))
            self._dbmanager.update_idown_task_status(task,
                                                     ECommandStatus.Failed)
            if isinstance(task.cmd, IdownCmd):
                self._dbmanager.update_cmd_status(task._platform, task.cmd_id,
                                                  task.cmd._clientid,
                                                  ECommandStatus.Failed)

    def _merge_task_status(self, task: Task):
        """合并处理子任务状态"""
        try:
            # 当前模块为 任务发送管理器，只负责 等待发送的任务及其状态管理。
            # 合并子任务状态，并将总任务状态从 等待发送更新为正在执行。
            # 只要有一个子任务发送成功，则总任务更新为发送成功
            # 若全部子任务发送失败，整个任务才算发送失败，
            # 貌似这样才能在非实时性的任务状态中没什么错

            ## 先看是否还有尚未发送的子任务，有的话先不要乱动。。
            waitforsendcount: int = self._dbmanager.get_batch_task_count_by_cmdstatus(
                task, ECommandStatus.WaitForSend)
            if waitforsendcount > 0:
                return

            ## 再看有没有发送成功的，有的话直接总任务发送成功，正在执行
            sendsucccount: int = self._dbmanager.get_batch_task_count_by_cmdstatus(
                task, ECommandStatus.Dealing)
            if sendsucccount > 0:
                task.cmdstatus = ECommandStatus.Dealing
                self._logger.info(
                    "Task all sent, taskid={} tasktype={}".format(
                        task.taskid, task.tasktype))
                # 只要有一个子任务发送成功，则更新总任务为正在执行（不需要返回回馈数据）
                if not self._dbmanager.update_idown_task_status(
                        task, ECommandStatus.Dealing):
                    self._logger.error(
                        "Update task cmdstatus to {} faled: taskid:{}".format(
                            ECommandStatus.Dealing.name, task.taskid))
            else:
                task.cmdstatus = ECommandStatus.Failed
                self._logger.error(
                    "Task all sent failed, taskid={} tasktype={}".format(
                        task.taskid, task.tasktype))
                # 若全部子任务都已发送（不管发成功还是失败），且子任务没有发送成功的，
                # 则更新总任务为失败，并返回回馈数据
                if not self._dbmanager.update_idown_task_status(
                        task, ECommandStatus.Failed):
                    self._logger.error(
                        "Update task cmdstatus to {} faled: taskid:{}".format(
                            ECommandStatus.Failed.name, task.taskid))
                # 失败，返回回馈数据
                tb: TaskBack = TaskBack(task, ECommandStatus.Failed,
                                        "任务执行失败，发送到采集端失败")
                if not OutputManagement.output(tb):
                    self._logger.error(
                        "Write idown_task_back failed:\ntaskid:{}".format(
                            task.taskid))

        except Exception as ex:
            self._logger.error(
                "Merge IDownTask status error:\nplatform:{}\ntaskid:{}\nerror:{}"
                .format(task._platformm, task.taskid, ex.args))
            self._dbmanager.update_idown_task_status(task,
                                                     ECommandStatus.Failed)

    def stop(self):
        pass

    def reload(self):
        pass
