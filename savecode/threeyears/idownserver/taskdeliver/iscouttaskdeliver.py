"""iscouttask deliver"""

import threading
import datetime
import traceback
from dateutil import parser
import pytz
from datetime import datetime

from commonbaby.helpers import helper_time

from datacontract import (
    Client,
    CmdFeedBack,
    ECommandStatus,
    IdownCmd,
    IscoutBtaskBack,
    IscoutTask,
    IscoutTaskBack,
)
from outputmanagement import OutputManagement

from ..dbmanager import DbManager, EDBAutomic, SqlCondition, SqlConditions
from ..statusmantainer import StatusMantainer
from .taskdeliverbase import TaskDeliverBase


class IScoutTaskDeliver(TaskDeliverBase):
    """deliver iscouttask"""

    def __init__(self):
        TaskDeliverBase.__init__(self)
        # <platform, <clientid, <iscouttaskid, iscouttaskobj>>>
        self._deal_queue: dict = {}
        self._deal_queue_locker = threading.RLock()

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
                "Get deliverable iscouttask error: {}".format(traceback.format_exc())
            )

    def _get_waitforsend_task(self) -> iter:
        try:
            for task in self._dbmanager.get_deliverable_iscouttask():
                task: IscoutTask = task
                if not isinstance(task, IscoutTask):
                    self._logger.warn(
                        "Invalid IscoutTask from database for delivering: {}".format(
                            task
                        )
                    )
                    continue

                # 判断指定的开始时间
                if (
                    isinstance(task.cmd.stratagy.time_start, str)
                    and not task.cmd.stratagy.time_start == ""
                ):
                    # 这里cmd里来的就是东8区时间
                    # tstart: float = time.mktime(
                    #     time.strptime(task.cmd.stratagy.time_start,
                    #                   "%Y-%m-%d %H:%M:%S"))
                    tstart = parser.parse(task.cmd.stratagy.time_start)
                    tstart = tstart.timestamp()
                    if tstart > helper_time.ts_since_1970_tz():
                        continue

                yield task
        except Exception:
            self._logger.error(
                "Get wait for send task error: {}".format(traceback.format_exc())
            )

    def _get_periodic_task(self) -> iter:
        try:
            for task in self._dbmanager.get_deliverable_iscouttask2():
                task: IscoutTask = task
                if not isinstance(task, IscoutTask):
                    self._logger.warn(
                        "Invalid IscoutTask from database for delivering: {}".format(
                            task
                        )
                    )
                    continue

                # 如果不在指定时间内那么就不下发
                if not self._process_task_execution_time(task):
                    continue

                if not self._filter_deliverable_task(task):
                    continue

                yield task
        except Exception:
            self._logger.error(
                "Get periodic task error: {}".format(traceback.format_exc())
            )

    def _process_task_execution_time(self, task: IscoutTask) -> bool:
        """
        处理刚从数据库查出数据，检测任务是否在有效期
        和任务是否满足在执行时间段
        :param q_task:
        :return:
        """
        is_effective = True
        # iscout task也没有继续下载的功能，所以暂停也是相当于将这个任务结束并且不再下载，这个周期的处理和iscan相似modify by judy 20200722
        if int(task.cmd.switch_control.download_switch) != 1:
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

    def _filter_deliverable_task(self, task: IscoutTask) -> bool:
        res: bool = False
        try:
            # 这里task.lastendtime就是东8区时间
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
            # 只有在周期任务下发的时候才+1其他任何时候都不增加周期，不然就会出错
            task.periodnum += 1
        except Exception:
            self._logger.error(
                "Check if task is deliverable error:\ntaskid={}\nbatchid={}\nerror:{}".format(
                    task.taskid, task.batchid, traceback.format_exc()
                )
            )
        return res

    def _is_task_in_deal_queue(self, task: IscoutTask) -> False:
        """查询某任务是否正在下发过程中，返回True是/False否"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(task._platform):
                return False

            if not self._deal_queue[task._platform].__contains__(task.taskid):
                return False

            if not self._deal_queue[task._platform][task.taskid].__contains__(
                task.batchid
            ):
                return False

            return True

    def _add_task_to_deal_queue(self, task: IscoutTask):
        """将任务添加到处理中队列"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(task._platform):
                self._deal_queue[task._platform] = {}

            if not self._deal_queue[task._platform].__contains__(task.taskid):
                self._deal_queue[task._platform][task.taskid] = {}

            if not self._deal_queue[task._platform][task.taskid].__contains__(
                task.batchid
            ):
                self._deal_queue[task._platform][task.taskid][task.batchid] = task

            return True

    def _remove_task_from_deal_queue(self, task: IscoutTask):
        """从处理队列移除指定taskid的任务，使放开数据库新任务查询"""
        with self._deal_queue_locker:
            if not self._is_task_in_deal_queue(task):
                return

            self._deal_queue[task._platform][task.taskid].pop(task.batchid, None)

    def _to_deliver(self, task: IscoutTask):
        try:
            succ: bool = False
            targetclient = None
            try:
                if not isinstance(task, IscoutTask):
                    self._logger.error(
                        "Invalid iscouttask to_deliver: {}".format(type(task).__name__)
                    )
                    return

                if not isinstance(task._clientid, str) or task._clientid == "":
                    self._logger.error(
                        "Invalid clientid in IScanTask object while delivering task:\niscouttaskid:{}\nclientid:{}".format(
                            task.taskid, task._clientid
                        )
                    )
                    return

                # 拿一下ip
                tmpclients = StatusMantainer.get_clientstatus_id_sorted()
                targetclient: Client = tmpclients.get(task._clientid, None)
                if not isinstance(targetclient, Client):
                    self._logger.error(
                        "Client may DOWN, periodic IScoutTask deliver failed:\niscouttaskid:{}\nclientid:{}".format(
                            task.taskid, task._clientid
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
                    succ = OutputManagement.output_to_file(task, targetdir)

            finally:
                with self._dbmanager.get_automic_locker(
                    EDBAutomic.ReduplicateIScoutTask
                ):
                    self._update_to_db(task, targetclient, succ)
                    self._merge_task_status(task)

        except Exception as ex:
            self._logger.error(
                "Deliver IscanTask err:\niscouttaskid:{}\nerr:{}".format(
                    task.taskid, ex
                )
            )

    def _update_to_db(self, task: IscoutTask, targetclient: Client, succ: bool):
        """同步任务下发状态到数据库。这里来的永远是子任务"""
        try:
            task.laststarttime = helper_time.ts_since_1970_tz()
            updatefields: dict = {}
            updatefields["PeriodNum"] = task.periodnum
            if not succ:
                # 失败，返回回馈数据
                task.lastendtime = helper_time.ts_since_1970_tz()
                updatefields["LastEndTime"] = task.lastendtime

                task.cmdstatus = ECommandStatus.Failed
                task.cmdrcvmsg = "发送任务到采集端失败"
                tb: IscoutBtaskBack = IscoutBtaskBack.create_from_task(
                    task, cmdstatus=task.cmdstatus, recvmsg=task.cmdrcvmsg
                )
                if not OutputManagement.output(tb):
                    self._logger.error(
                        "Write IscoutBtaskBack failed:\ntaskid:{}".format(task.taskid)
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
                # 成功
                task.cmdstatus = ECommandStatus.Dealing
                if isinstance(task.cmd, IdownCmd):
                    task.cmd.cmdstatus = ECommandStatus.Dealing
                # 返回 子任务开始回馈
                task.cmdstatus = ECommandStatus.Dealing
                task.cmdrcvmsg = "任务开始执行"
                if task.periodnum > 1:
                    task.cmdrcvmsg += ",周期{}".format(task.periodnum)
                tb: IscoutBtaskBack = IscoutBtaskBack.create_from_task(
                    task, cmdstatus=task.cmdstatus, recvmsg=task.cmdrcvmsg
                )
                if not OutputManagement.output(tb):
                    self._logger.error(
                        "Write IscoutBtaskBack failed:\ntaskid:{}".format(task.taskid)
                    )
                self._logger.info(
                    "Send IScoutTask succeed [{}: {}]:\ntaskid:{}\nbatchid:{}\nperiod:{}\nclient:{}\t{}".format(
                        task._objecttype.name,
                        task._object,
                        task.taskid,
                        task.batchid,
                        task.periodnum,
                        task._clientid,
                        targetclient._statusbasic.ip,
                    )
                )

            with self._dbmanager.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
                # 总任务batchcompletecount -1
                # 子任务isbatchcompletecountincreaced 置0
                self._dbmanager.decreace_iscouttask_batch_complete_count(
                    task._platform, task.taskid, task.batchid
                )
                task.batchcompletecount -= 1
                # 更新数据库当前子任务状态
                updatefields["Status"] = task.cmdstatus.value
                updatefields["LastStartTime"] = task.laststarttime
                if not self._dbmanager.update_iscoutbtask(
                    task._platform, task.taskid, task.batchid, updatefields
                ):
                    # 这里如果更新数据库状态失败了，那发送线程可能会重新发送当前子任务。
                    # 此时需要采集端支持 冥等性（任务去重，保证多次收到同一条任务只会处理一条）
                    self._logger.error(
                        "Update IScoutBatchTask cmdstatus failed:\ntaskid:{}\ncmdstatus:{}".format(
                            task.taskid, task.cmdstatus.name
                        )
                    )
                # 更新总任务开始时间
                if not self._dbmanager.update_iscout_task(
                    task._platform,
                    task.taskid,
                    updatefields={
                        "LastStartTime": helper_time.ts_since_1970_tz(),
                        "PeriodNum": task.periodnum,
                    },
                ):
                    self._logger.error(
                        "Update IScouttask LastStartTime failed:\ntaskid:{}\ncmdstatus:{}".format(
                            task.taskid, task.cmdstatus.name
                        )
                    )
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

                # 返回 总任务开始回馈
                task.cmdstatus = ECommandStatus.Dealing
                task.cmdrcvmsg = "任务开始执行，周期{}".format(task.periodnum)
                tb: IscoutTaskBack = IscoutTaskBack.create_from_task(
                    task,
                    cmdstatus=task.cmdstatus,
                    recvmsg=task.cmdrcvmsg,
                    batchcompletecount=task.batchcompletecount,
                    periodnum=task.periodnum,
                )
                if not OutputManagement.output(tb):
                    self._logger.error(
                        "Write IscoutBtaskBack failed:\ntaskid:{}".format(task.taskid)
                    )
        except Exception:
            self._logger.error(
                "Update task cmdstatus to db error: {}".format(traceback.format_exc())
            )
            self._dbmanager.update_iscouttask_status(
                task._platform, task.taskid, ECommandStatus.Failed
            )
            if isinstance(task.cmd, IdownCmd):
                self._dbmanager.update_cmd_status(
                    task._platform,
                    task.cmd_id,
                    task.cmd._clientid,
                    ECommandStatus.Failed,
                )

    def _merge_task_status(self, task: IscoutTask):
        """合并处理子任务状态"""
        try:
            # 当前模块为 任务发送管理器，只负责 等待发送的任务及其状态管理。
            # 合并子任务状态，并将总任务状态从 等待发送更新为正在执行。
            # 只要有一个子任务发送成功，则总任务更新为发送成功
            # 若全部子任务发送失败，整个任务才算发送失败，
            # 貌似这样才能在非实时性的任务状态中没什么错

            ## 先看是否还有尚未发送的子任务，有的话先不要乱动。。
            waitforsendcount: int = self._dbmanager.get_iscoutbtask_count_by_cmdstatus(
                task._platform, task.taskid, ECommandStatus.WaitForSend
            )
            if waitforsendcount > 0:
                return

            ## 再看有没有发送成功的，有的话直接总任务发送成功，正在执行
            sendsucccount: int = self._dbmanager.get_iscoutbtask_count_by_cmdstatus(
                task._platform, task.taskid, ECommandStatus.Dealing
            )
            if sendsucccount > 0:
                task.cmdstatus = ECommandStatus.Dealing
                self._logger.info("IScoutTask all sent, taskid={}".format(task.taskid))
                # 只要有一个子任务发送成功，则更新总任务为正在执行（不需要返回回馈数据）
                if not self._dbmanager.update_iscouttask_status(
                    task._platform, task.taskid, ECommandStatus.Dealing
                ):
                    self._logger.error(
                        "Update IScoutTask cmdstatus to {} faled: taskid:{}".format(
                            ECommandStatus.Dealing.name, task.taskid
                        )
                    )
            else:
                task.cmdstatus = ECommandStatus.Failed
                self._logger.error(
                    "IScoutTask all sent failed, taskid={} objtype={} obj={}".format(
                        task.taskid, task._objecttype, task._object
                    )
                )
                # 若全部子任务都已发送（不管发成功还是失败），且子任务没有发送成功的，
                # 则更新总任务为失败，并返回回馈数据
                if not self._dbmanager.update_iscouttask_status(
                    task._platform, task.taskid, ECommandStatus.Failed
                ):
                    self._logger.error(
                        "Update IScoutTask cmdstatus to {} faled: taskid:{}".format(
                            ECommandStatus.Failed.name, task.taskid
                        )
                    )
                # 失败，返回总任务回馈数据
                tb: IscoutTaskBack = IscoutTaskBack.create_from_task(
                    task, ECommandStatus.Failed, "任务执行失败，发送到采集端失败"
                )
                if not OutputManagement.output(tb):
                    self._logger.error(
                        "Write IscoutTaskBack failed:\ntaskid:{}".format(task.taskid)
                    )

        except Exception as ex:
            self._logger.error(
                "Merge IScoutTask status error:\nplatform:{}\ntaskid:{}\nerror:{}".format(
                    task._platform, task.taskid, ex.args
                )
            )
            self._dbmanager.update_iscouttask_status(
                task._platform, task.taskid, ECommandStatus.Failed
            )

    def stop(self):
        pass

    def reload(self):
        pass
