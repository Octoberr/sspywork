"""iscantask deliver"""

# -*- coding:utf-8 -*-

import threading
import traceback
import pytz
from datetime import datetime

from commonbaby.helpers import helper_time

from datacontract import (
    Client,
    CmdFeedBack,
    ECommandStatus,
    IdownCmd,
    IscanTask,
    IscanTaskBack,
)
from outputmanagement import OutputManagement

from ..dbmanager import DbManager, EDBAutomic, SqlCondition, SqlConditions
from ..statusmantainer import StatusMantainer
from .taskdeliverbase import TaskDeliverBase


class IScanTaskDeliver(TaskDeliverBase):
    """deliver scantask"""

    def __init__(self):
        TaskDeliverBase.__init__(self)
        # <platform, <clientid, <scantaskid, scantaskobj>>>
        self._deal_queue: dict = {}
        self._deal_queue_locker = threading.RLock()

    # def _get_deliverable_task(self) -> iter:
    #     """从数据库读取扫描任务并分发"""
    #     for scantask in self._dbmanager.get_deliverable_iscantask():
    #         scantask: IscanTask = scantask
    #         if not isinstance(scantask, IscanTask):
    #             self._logger.warn(
    #                 "Invalid IScanTask from database for delivering: {}".
    #                 format(scantask))
    #             continue

    #         yield scantask

    def _get_deliverable_task(self) -> iter:
        """从数据库读取扫描任务并分发"""
        try:
            # 下发普通任务
            for task in self._get_waitforsend_task():
                yield task

            # 下发周期任务的除第一次周期外的后续周期
            for task in self._get_periodic_task():
                yield task

        except Exception:
            self._logger.error(
                "Get deliverable iscantask error: {}".format(traceback.format_exc())
            )

    def _get_waitforsend_task(self) -> iter:
        try:
            for task in self._dbmanager.get_deliverable_iscantask():
                task: IscanTask = task
                if not isinstance(task, IscanTask):
                    self._logger.warn(
                        "Invalid IscanTask from database for delivering: {}".format(
                            task
                        )
                    )
                    continue

                yield task
        except Exception:
            self._logger.error(
                "Get wait for send task error: {}".format(traceback.format_exc())
            )

    def _get_periodic_task(self) -> iter:
        try:
            for task in self._dbmanager.get_deliverable_iscantask2():
                task: IscanTask = task
                if not isinstance(task, IscanTask):
                    self._logger.warn(
                        "Invalid IscanTask from database for delivering: {}".format(
                            task
                        )
                    )
                    continue

                # 这里不进行处理，如果是被暂停的任务，那么client会回相关的信息
                # if task.cmd.switch_control.download_switch == 0:
                #     task.cmdstatus = 1
                #     if not DbManager.update_iscantask_status(task.platform, task.taskid, task.cmdstatus):
                #         task.cmdstatus = 0
                #         ## 返回回馈数据
                #         scanback: IscanTaskBack = IscanTaskBack.create_from_task(
                #             task, ECommandStatus.Failed, '更新任务状态失败')
                #         if not OutputManagement.output(scanback):
                #             self._logger.error(
                #                 'Output IScanTaskBack failed:\ntaskid={}'.
                #                     format(scanback._taskid))
                #     else:
                #         ## 返回回馈数据
                #         scanback: IscanTaskBack = IscanTaskBack.create_from_task(
                #             task, ECommandStatus.Succeed, '任务执行成功')
                #         if not OutputManagement.output(scanback):
                #             self._logger.error(
                #                 'Output IScanTaskBack failed:\ntaskid={}'.
                #                     format(scanback._taskid))
                #     # 周期任务没有开下载那么就不再进行过滤，直接跳过
                #     continue
                # 如果任务不在执行时间内那么就不再下发
                if not self._process_task_execution_time(task):
                    continue
                if not self._filter_deliverable_task(task):
                    continue

                yield task
        except Exception:
            self._logger.error(
                "Get periodic task error: {}".format(traceback.format_exc())
            )

    def _process_task_execution_time(self, task: IscanTask) -> bool:
        """
        处理刚从数据库查出数据，检测任务是否在有效期
        和任务是否满足在执行时间段
        :param q_task:
        :return:
        """
        is_effective = True
        # iscantask也是支持周期执行的，但是同时也支持周期暂停，但是扫描程序不会有继续下载的功能，所以暂停不仅是将当前下载暂停了，更是把这个周期暂停了
        # 所以如果发现字段是被暂停了的，那么就不再进行下载modify by judy 2020/07/23
        if int(task.cmd.switch_control.download_switch) != 1:
            # 暂停的任务不需要再执行，但是需要更新下数据库状态，并且将状态回馈给server
            return False
        # 统一使用东8区的时间
        beijing = pytz.timezone("Asia/Shanghai")
        now_datetime = datetime.now(beijing)
        now_time = now_datetime.time()
        try:
            if task.cmd.stratagy.time_start is not None:
                task_time_start = datetime.strptime(
                    task.cmd.stratagy.time_start, "%Y-%m-%d %H:%M:%S"
                )
                if now_datetime >= beijing.localize(task_time_start):
                    is_effective = True
                else:
                    return False
            if task.cmd.stratagy.time_end is not None:
                task_time_end = datetime.strptime(
                    task.cmd.stratagy.time_end, "%Y-%m-%d %H:%M:%S"
                )
                if now_datetime <= beijing.localize(task_time_end):
                    is_effective = True
                else:
                    return False
            # ----------------------------------------------上面的判断为任务是否在有效时间

        except:
            self._logger.error(
                f"Determine the effective and execution time of the task error\nerr:{traceback.format_exc()}"
            )
            is_effective = False
        return is_effective

    def _filter_deliverable_task(self, task: IscanTask) -> bool:
        res: bool = False
        try:
            # 这里task.lastendtime就是东8区时间
            # tend = time.mktime(
            #     time.strptime(task.lastendtime, "%Y-%m-%d %H:%M:%S"))
            tend = task.lastendtime
            if tend is None or tend == "":
                return res
            if task.cmd.stratagy.interval is None:
                raise Exception(f"Period task interval is None: taskid={task.taskid}")
            tstart = tend + task.cmd.stratagy.interval
            tnow = helper_time.ts_since_1970_tz()

            if tnow < tstart:
                return res

            # 走到这，就是周期任务达到 循环间隔，需要下发
            res = True
            self._logger.info(
                f"Periodtask:{task.taskid}\nlaster execute time:{tend}\ninterval:{task.cmd.stratagy.interval}\ntime_now:{tnow}"
            )
            # 只有在周期任务下发的时候才+1其他任何时候都不增加周期，不然就会出错
            task.periodnum += 1
        except Exception:
            self._logger.error(
                "Check if task is deliverable error:\ntaskid={}\nbatchid={}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()
                )
            )
        return res

    def _is_task_in_deal_queue(self, scantask: IscanTask) -> False:
        """查询某任务是否正在下发过程中，返回True是/False否"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(scantask._platform):
                return False

            if not self._deal_queue[scantask._platform].__contains__(scantask.taskid):
                return False

            return True

    def _add_task_to_deal_queue(self, scantask: IscanTask):
        """将任务添加到处理中队列"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(scantask._platform):
                self._deal_queue[scantask._platform] = {}

            if not self._deal_queue[scantask._platform].__contains__(scantask.taskid):
                self._deal_queue[scantask._platform][scantask.taskid] = scantask

            return True

    def _remove_task_from_deal_queue(self, scantask: IscanTask):
        """从处理队列移除指定taskid的任务，使放开数据库新任务查询"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(scantask._platform):
                return

            if not self._deal_queue[scantask._platform].__contains__(scantask.taskid):
                return

        self._deal_queue[scantask._platform].pop(scantask.taskid, None)

    def _to_deliver(self, scantask: IscanTask):
        try:
            succ: bool = False
            targetclient = None
            try:
                if not isinstance(scantask, IscanTask):
                    self._logger.error(
                        "Invalid scantask to_deliver: {}".format(
                            type(scantask).__name__
                        )
                    )
                    return

                if not isinstance(scantask._clientid, str) or scantask._clientid == "":
                    self._logger.error(
                        "Invalid clientid in IScanTask object while delivering task:\nscantaskid:{}\nclientid:{}".format(
                            scantask.taskid, scantask._clientid
                        )
                    )
                    return

                # 拿一下ip
                tmpclients = StatusMantainer.get_clientstatus_id_sorted()
                targetclient: Client = tmpclients.get(scantask._clientid, None)
                if not isinstance(targetclient, Client):
                    self._logger.error(
                        "Client may DOWN, periodic IScanTask deliver failed:\nscantaskid:{}\nclientid:{}".format(
                            scantask.taskid, scantask._clientid
                        )
                    )
                    return succ

                # 传输分配
                if not self._config._ipdir.__contains__(targetclient._statusbasic.ip):
                    self._logger.error(
                        "Client transfer folder not configured: clientip={}".format(
                            targetclient._statusbasic.ip
                        )
                    )
                else:
                    targetdir = self._config._ipdir[targetclient._statusbasic.ip]
                    succ = OutputManagement.output_to_file(scantask, targetdir)

            finally:
                with self._dbmanager.get_automic_locker(
                    EDBAutomic.ReduplicateIScanTask
                ):
                    self._update_to_db(scantask, targetclient, succ)

        except Exception as ex:
            self._logger.error(
                "Deliver IscanTask err:\nscantaskid:{}\nerr:{}".format(
                    scantask.taskid, ex
                )
            )

    def _update_to_db(self, task: IscanTask, targetclient: Client, succ: bool):
        try:
            task.laststarttime = helper_time.ts_since_1970_tz()
            updatefields: dict = {}
            # 每次下发去更新周期，只有在下发的时候才更新周期其他任何时候都不更新
            updatefields["PeriodNum"] = task.periodnum
            if not succ:
                task.lastendtime = helper_time.ts_since_1970_tz()
                updatefields["LastEndTime"] = task.lastendtime

                # 失败，返回回馈数据
                task.cmdstatus = ECommandStatus.Failed
                task.cmdrcvmsg = "发送任务到采集端失败"
                scantaskback: IscanTaskBack = IscanTaskBack.create_from_task(
                    task, task.cmdstatus, task.cmdrcvmsg
                )
                if not OutputManagement.output(scantaskback):
                    self._logger.error(
                        "Write idown_scantask_back failed:\nscantaskid:{}\nperiodnum:{}".format(
                            task.taskid, task.periodnum
                        )
                    )
                if isinstance(task.cmd, IdownCmd):
                    task.cmd.cmdstatus = ECommandStatus.Failed
                    task.cmd.cmdrcvmsg = task.cmdrcvmsg
                    cmdback: CmdFeedBack = CmdFeedBack.create_from_cmd(
                        task.cmd, task.cmd.cmdstatus, task.cmd.cmdrcvmsg
                    )
                    if not OutputManagement.output(cmdback):
                        self._logger.error(
                            "Write IDownCmdBack failed:\nplatform:{}\ncmdid:{}".format(
                                task._platform, task.cmd_id
                            )
                        )
            else:
                # 成功，状态置为 处理中
                task.cmdstatus = ECommandStatus.Dealing
                if isinstance(task.cmd, IdownCmd):
                    task.cmd.cmdstatus = ECommandStatus.Dealing
                task.cmdrcvmsg = "任务开始执行"
                if task.periodnum > 1:
                    task.cmdrcvmsg += ",周期{}".format(task.periodnum)
                tb: IscanTaskBack = IscanTaskBack.create_from_task(
                    task, cmdstatus=task.cmdstatus, scanrecvmsg=task.cmdrcvmsg
                )
                if not OutputManagement.output(tb):
                    self._logger.error(
                        "Write IScanTaskBack failed:\ntaskid:{}\nperiodnum:{}".format(
                            task.taskid, task.periodnum
                        )
                    )
                self._logger.info(
                    "Send IScanTask succeed:\nscantaskid:{}\nperiodnum:{}\nclient:{}\t{}".format(
                        task.taskid,
                        task.periodnum,
                        task._clientid,
                        targetclient._statusbasic.ip,
                    )
                )

            updatefields["Status"] = task.cmdstatus.value
            updatefields["LastStartTime"] = task.laststarttime

            with self._dbmanager.get_automic_locker(EDBAutomic.ReduplicateIScanTask):
                if not self._dbmanager.update_iscantask2(
                    task._platform, task.taskid, updatefields
                ):
                    self._logger.error(
                        "Update IScanTask cmdstatus failed:\ntaskid:{}\ncmdstatus:{}".format(
                            task.taskid, task.cmdstatus.name
                        )
                    )
                    return
                # 如果带cmd，更新cmd状态
                if isinstance(
                    task.cmd, IdownCmd
                ) and not self._dbmanager.update_cmd_status(
                    task.cmd.platform,
                    task.cmd.cmd_id,
                    targetclient._statusbasic._clientid
                    if not targetclient is None
                    else task._clientid,
                    task.cmd.cmdstatus,
                ):
                    self._logger.error(
                        "Update cmd cmdstatus failed:\ntaskid:{}\ncmdstatus:{}".format(
                            task.taskid, task.cmdstatus.name
                        )
                    )
            # if not self._dbmanager.update_iscantask_status(
            #         scantask._platform, scantask.taskid, scantask.cmdstatus):
            #     self._logger.error(
            #         "Update IScanTask status failed:\nscantaskid:{}\ntaskstatus:{}"
            #         .format(scantask.taskid, scantask.cmdstatus.name))
            #     return

        except Exception:
            self._logger.error(
                "Update IscanTask status to db error: {}".format(traceback.format_exc())
            )

    def stop(self):
        pass

    def reload(self):
        pass
