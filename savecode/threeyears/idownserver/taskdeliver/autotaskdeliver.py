"""AutomatedTask deliver"""

# -*- coding:utf-8 -*-

import json
import queue
import threading
import time
import datetime
import traceback

from commonbaby.helpers import helper_time

from datacontract import (Client, CmdFeedBack, ECommandStatus, IdownCmd,
                          AutomatedTask, AutotaskBack, AutotaskBatchBack)
from outputmanagement import OutputManagement

from ..dbmanager import DbManager, EDBAutomic, SqlCondition, SqlConditions
from ..statusmantainer import StatusMantainer
from .taskdeliverbase import TaskDeliverBase


class AutoTaskDeliver(TaskDeliverBase):
    """deliver automatedtask"""

    def __init__(self):
        TaskDeliverBase.__init__(self)
        # <platform, <clientid, <AutomatedTaskid, AutomatedTaskobj>>>
        self._deal_queue: dict = {}
        self._deal_queue_locker = threading.RLock()

    def _get_deliverable_task(self) -> iter:
        """从数据库读取扫描任务并分发"""
        try:
            # 下发普通任务
            for task in self._get_waitforsend_task():
                yield task

            # # 下发周期任务的除第一次周期外的后续周期
            # for task in self._get_periodic_task():
            #     yield task
        except Exception:
            self._logger.error(
                "Get deliverable AutomatedTask error: {}".format(
                    traceback.format_exc()))

    def _get_waitforsend_task(self) -> iter:
        try:
            for task in self._dbmanager.get_deliverable_autotask():
                task: AutomatedTask = task
                if not isinstance(task, AutomatedTask):
                    self._logger.warn(
                        "Invalid AutomatedTask from database for delivering: {}"
                        .format(task))
                    continue

                # 判断指定的开始时间
                if isinstance(task.cmd.stratagy.time_start,
                              str) and not task.cmd.stratagy.time_start == "":
                    # 这个cmd里来的time_start就是东8区时间
                    tstart: float = time.mktime(
                        time.strptime(task.cmd.stratagy.time_start,
                                      "%Y-%m-%d %H:%M:%S"))
                    if tstart > helper_time.ts_since_1970_tz():
                        continue

                yield task
        except Exception:
            self._logger.error("Get wait for send task error: {}".format(
                traceback.format_exc()))

    def _is_task_in_deal_queue(self, task: AutomatedTask) -> False:
        """查询某任务是否正在下发过程中，返回True是/False否"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(task._platform):
                return False

            if not self._deal_queue[task._platform].__contains__(task.taskid):
                return False

            if not self._deal_queue[task._platform][task.taskid].__contains__(
                    task.batchid):
                return False

            return True

    def _add_task_to_deal_queue(self, task: AutomatedTask):
        """将任务添加到处理中队列"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(task._platform):
                self._deal_queue[task._platform] = {}

            if not self._deal_queue[task._platform].__contains__(task.taskid):
                self._deal_queue[task._platform][task.taskid] = {}

            if not self._deal_queue[task._platform][task.taskid].__contains__(
                    task.batchid):
                self._deal_queue[task._platform][task.taskid][
                    task.batchid] = task

            return True

    def _remove_task_from_deal_queue(self, task: AutomatedTask):
        """从处理队列移除指定taskid的任务，使放开数据库新任务查询"""
        with self._deal_queue_locker:
            if not self._is_task_in_deal_queue(task):
                return

            self._deal_queue[task._platform][task.taskid].pop(
                task.batchid, None)

    def _to_deliver(self, task: AutomatedTask):
        try:
            succ: bool = False
            try:
                if not isinstance(task, AutomatedTask):
                    self._logger.error(
                        "Invalid AutomatedTask to_deliver: {}".format(
                            type(task).__name__))
                    return

                if not isinstance(task._clientid, str) or task._clientid == "":
                    self._logger.error(
                        "Invalid clientid in AutomatedTask object while delivering task:\nAutomatedTaskid:{}\nclientid:{}"
                        .format(task.taskid, task._clientid))
                    return

                # 拿一下ip
                tmpclients = StatusMantainer.get_clientstatus_id_sorted()
                targetclient: Client = tmpclients.get(task._clientid, None)
                if not isinstance(targetclient, Client):
                    # 这里要做失败重新分配采集端机制
                    self._logger.error(
                        "Invalid client for AutomatedTask deliver:\nAutomatedTaskid:{}\nclientid:{}"
                        .format(task.taskid, task._clientid))

                # 传输分配
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
                        EDBAutomic.ReduplicateAutoTask):
                    self._update_to_db(task, targetclient, succ)
                    self._merge_task_status(task)

        except Exception as ex:
            self._logger.error(
                "Deliver IscanTask err:\nAutomatedTaskid:{}\nerr:{}".format(
                    task.taskid, ex))

    def _update_to_db(self, task: AutomatedTask, targetclient: Client,
                      succ: bool):
        """同步任务下发状态到数据库。这里来的永远是子任务"""
        try:
            task.laststarttime = helper_time.ts_since_1970_tz()
            updatefields: dict = {}
            if not succ:
                # 失败，返回回馈数据
                task.periodnum += 1
                updatefields['PeriodNum'] = task.periodnum
                task.lastendtime = helper_time.ts_since_1970_tz()
                updatefields['LastEndTime'] = task.lastendtime

                task.cmdstatus = ECommandStatus.Failed
                task.cmdrcvmsg = "发送任务到采集端失败"

                tb: AutotaskBatchBack = AutotaskBatchBack.create_from_task(
                    task, cmdstatus=task.cmdstatus, recvmsg=task.cmdrcvmsg)
                if not OutputManagement.output(tb):
                    self._logger.error(
                        "Write IscoutBtaskBack failed:\ntaskid:{}".format(
                            task.taskid))

                # 自动化任务暂不回传cmdback
                # if isinstance(task.cmd, IdownCmd):
                #     task.cmd.cmdstatus = ECommandStatus.Failed
                #     task.cmd.cmdrcvmsg = task.cmdrcvmsg
                #     cmdback: CmdFeedBack = CmdFeedBack.create_from_cmd(
                #         task.cmd, task.cmd.cmdstatus, task.cmd.cmdrcvmsg)
                #     if not OutputManagement.output(cmdback):
                #         self._logger.error(
                #             "Write IDownCmdBack failed:\nplatform:{}\ncmdid:{}"
                #             .format(task._platform, task.cmd_id))
            else:
                # 成功
                task.cmdstatus = ECommandStatus.Dealing
                if isinstance(task.cmd, IdownCmd):
                    task.cmd.cmdstatus = ECommandStatus.Dealing
                # 返回 子任务开始回馈
                task.cmdstatus = ECommandStatus.Dealing
                task.cmdrcvmsg = "任务开始执行"
                if task.periodnum > 1:
                    task.cmdrcvmsg += ",周期{}".format(task.periodnum)
                tb: AutotaskBatchBack = AutotaskBatchBack.create_from_task(
                    task, cmdstatus=task.cmdstatus, recvmsg=task.cmdrcvmsg)
                if not OutputManagement.output(tb):
                    self._logger.error(
                        "Write IscoutBtaskBack failed:\ntaskid:{}".format(
                            task.taskid))
                self._logger.info(
                    "Send AutomatedTask succeed [{}]:\ntaskid:{}\nbatchid:{}\nperiod:{}\nclient:{}\t{}"
                    .format(task.autotasktype.name, task.taskid, task.batchid,
                            task.periodnum, task._clientid,
                            targetclient._statusbasic.ip))

            with self._dbmanager.get_automic_locker(
                    EDBAutomic.ReduplicateAutoTask):

                # 更新数据库当前子任务状态
                updatefields['Status'] = task.cmdstatus.value
                updatefields['LastStartTime'] = task.laststarttime
                if not self._dbmanager.update_automated_batch_task(
                        task._platform, task.taskid, task.batchid,
                        updatefields):
                    # 这里如果更新数据库状态失败了，那发送线程可能会重新发送当前子任务。
                    # 此时需要采集端支持 冥等性（任务去重，保证多次收到同一条任务只会处理一条）
                    self._logger.error(
                        "Update AutomatedTask failed:\ntaskid:{}\ncmdstatus:{}"
                        .format(task.taskid, task.cmdstatus.name))
                # 更新总任务开始时间
                if not self._dbmanager.update_automated_task(
                        task._platform,
                        task.taskid,
                        updatefields={
                            'LastStartTime': helper_time.ts_since_1970_tz()
                        }):
                    self._logger.error(
                        "Update IScouttask LastStartTime failed:\ntaskid:{}\ncmdstatus:{}"
                        .format(task.taskid, task.cmdstatus.name))
                # 如果带cmd，更新cmd状态
                if isinstance(
                        task.cmd,
                        IdownCmd) and not self._dbmanager.update_cmd_status(
                            task.cmd.platform, task.cmd.cmd_id,
                            targetclient._statusbasic._clientid,
                            task.cmd.cmdstatus):
                    self._logger.error(
                        "Update cmd cmdstatus failed:\ntaskid:{}\ncmdstatus:{}"
                        .format(task.taskid, task.cmdstatus.name))

                # 返回 总任务开始回馈
                task.cmdstatus = ECommandStatus.Dealing
                task.cmdrcvmsg = "任务开始执行，周期{}".format(task.periodnum)
                tb: AutotaskBack = AutotaskBack.create_from_task(
                    task,
                    cmdstatus=task.cmdstatus,
                    recvmsg=task.cmdrcvmsg,
                    batchcompletecount=task.batchcompletecount,
                    periodnum=task.periodnum)
                if not OutputManagement.output(tb):
                    self._logger.error(
                        "Write IscoutBtaskBack failed:\ntaskid:{}".format(
                            task.taskid))
        except Exception:
            self._logger.error("Update task cmdstatus to db error: {}".format(
                traceback.format_exc()))
            self._dbmanager.update_autotask_status(task._platform, task.taskid,
                                                   ECommandStatus.Failed)
            if isinstance(task.cmd, IdownCmd):
                self._dbmanager.update_cmd_status(task._platform, task.cmd_id,
                                                  task.cmd._clientid,
                                                  ECommandStatus.Failed)

    def _merge_task_status(self, task: AutomatedTask):
        """合并处理子任务状态"""
        try:
            # 当前模块为 任务发送管理器，只负责 等待发送的任务及其状态管理。
            # 合并子任务状态，并将总任务状态从 等待发送更新为正在执行。
            # 只要有一个子任务发送成功，则总任务更新为发送成功
            # 若全部子任务发送失败，整个任务才算发送失败，
            # 貌似这样才能在非实时性的任务状态中没什么错

            ## 先看是否还有尚未发送的子任务，有的话先不要乱动。。
            waitforsendcount: int = self._dbmanager.get_autobtask_count_by_cmdstatus(
                task._platform, task.taskid, ECommandStatus.WaitForSend)
            if waitforsendcount > 0:
                return

            ## 再看有没有发送成功的，有的话直接总任务发送成功，正在执行
            sendsucccount: int = self._dbmanager.get_autobtask_count_by_cmdstatus(
                task._platform, task.taskid, ECommandStatus.Dealing)
            if sendsucccount > 0:
                task.cmdstatus = ECommandStatus.Dealing
                self._logger.info("AutomatedTask all sent, taskid={}".format(
                    task.taskid))
                # 只要有一个子任务发送成功，则更新总任务为正在执行（不需要返回回馈数据）
                if not self._dbmanager.update_autotask_status(
                        task._platform, task.taskid, ECommandStatus.Dealing):
                    self._logger.error(
                        "Update AutomatedTask cmdstatus to {} faled: taskid:{}"
                        .format(ECommandStatus.Dealing.name, task.taskid))
            else:
                task.cmdstatus = ECommandStatus.Failed
                self._logger.error(
                    "AutomatedTask all sent failed, taskid={} tasktype={}".
                    format(task.taskid, task.tasktype))
                # 若全部子任务都已发送（不管发成功还是失败），且子任务没有发送成功的，
                # 则更新总任务为失败，并返回回馈数据
                if not self._dbmanager.update_autotask_status(
                        task._platform, task.taskid, ECommandStatus.Failed):
                    self._logger.error(
                        "Update AutomatedTask cmdstatus to {} faled: taskid:{}"
                        .format(ECommandStatus.Failed.name, task.taskid))
                # 失败，返回总任务回馈数据
                tb: AutotaskBack = AutotaskBack.create_from_task(
                    task, ECommandStatus.Failed, "任务执行失败，发送到采集端失败")
                if not OutputManagement.output(tb):
                    self._logger.error(
                        "Write AutotaskBack failed:\ntaskid:{}".format(
                            task.taskid))

        except Exception as ex:
            self._logger.error(
                "Merge AutomatedTask status error:\nplatform:{}\ntaskid:{}\nerror:{}"
                .format(task._platform, task.taskid, ex.args))
            self._dbmanager.update_autotask_status(task._platform, task.taskid,
                                                   ECommandStatus.Failed)

    def stop(self):
        pass

    def reload(self):
        pass
