"""cmd deliver"""

# -*- coding:utf-8 -*-

import queue
import threading
import time
import traceback

from datacontract import Client, ECommandStatus, IdownCmd, CmdFeedBack
from outputmanagement import OutputManagement

from ..dbmanager import DbManager, EDBAutomic, SqlCondition, SqlConditions
from .taskdeliverbase import TaskDeliverBase
from ..statusmantainer import StatusMantainer


class CmdDeliver(TaskDeliverBase):
    """deliver cmd"""

    def __init__(self):
        TaskDeliverBase.__init__(self)
        # <platform, <clientid, <cmdid, cmdobj>>>
        self._deal_queue: dict = {}
        self._deal_queue_locker = threading.RLock()

    def _get_deliverable_task(self) -> iter:
        for cmd in self._dbmanager.get_deliverable_cmd():
            cmd: IdownCmd = cmd
            if not isinstance(cmd, IdownCmd):
                self._logger.warn(
                    "Invalid cmd from database for delivering: {}".format(cmd))
                continue

            yield cmd

    def _is_task_in_deal_queue(self, cmd: IdownCmd) -> False:
        """查询某任务是否正在下发过程中，返回True是/False否"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(cmd.platform):
                return False

            if not self._deal_queue[cmd.platform].__contains__(cmd.cmd_id):
                return False

            return True

    def _add_task_to_deal_queue(self, cmd: IdownCmd):
        """将任务添加到处理中队列"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(cmd.platform):
                self._deal_queue[cmd.platform] = {}

            if not self._deal_queue[cmd.platform].__contains__(cmd.cmd_id):
                self._deal_queue[cmd.platform][cmd.cmd_id] = cmd

            return True

    def _remove_task_from_deal_queue(self, cmd: IdownCmd):
        """从处理队列移除指定taskid的任务，使放开数据库新任务查询"""
        with self._deal_queue_locker:
            if not self._deal_queue.__contains__(cmd.platform):
                return

            if not self._deal_queue[cmd.platform].__contains__(cmd.cmd_id):
                return

        self._deal_queue[cmd.platform].pop(cmd.cmd_id, None)

    def _to_deliver(self, cmd: IdownCmd):
        try:
            succ: bool = False
            try:
                if not isinstance(cmd, IdownCmd):
                    self._logger.error("Invalid cmd to_deliver: {}".format(
                        type(cmd).__name__))
                    return

                if not isinstance(cmd._clientid, str) or cmd._clientid == "":
                    self._logger.error(
                        "Invalid clientid in cmd object while delivering task:\ncmdid:{}\nclientid:{}"
                        .format(cmd.cmd_id, cmd._clientid))
                    return

                # 拿一下ip
                tmpclients = StatusMantainer.get_clientstatus_id_sorted()
                targetclient: Client = tmpclients.get(cmd._clientid, None)
                if not isinstance(targetclient, Client):
                    self._logger.error(
                        "Unknown client for cmd deliver:\ncmdid:{}\nclientid:{}"
                        .format(cmd.cmd_id, cmd._clientid))

                # 传输分配
                if not self._config._ipdir.__contains__(
                        targetclient._statusbasic.ip):
                    self._logger.error(
                        "Client transfer folder not configured: clientip={}".
                        format(targetclient._statusbasic.ip))
                else:
                    targetdir = self._config._ipdir[
                        targetclient._statusbasic.ip]
                    succ = OutputManagement.output_to_file(cmd, targetdir)

            finally:
                with self._dbmanager.get_automic_locker(
                        EDBAutomic.ReduplicateTask):
                    self._update_to_db(cmd, targetclient, succ)

        except Exception as ex:
            self._logger.error(
                "Deliver IDownCmd err:\ncmdid:{}\nerr:{}".format(
                    cmd.cmd_id, ex))

    def _update_to_db(self, cmd: IdownCmd, targetclient: Client, succ: bool):
        try:
            if not succ:
                cmd.cmdstatus = ECommandStatus.Failed
                cmd.cmdrcvmsg = "发送任务到采集端失败"
                # 失败，返回回馈数据
                cmdback: CmdFeedBack = CmdFeedBack.create_from_cmd(cmd, cmd.cmdstatus,
                                                   cmd.cmdrcvmsg)
                if not OutputManagement.output(cmdback):
                    self._logger.error(
                        "Write idown_cmd_back failed:\ncmdid:{}".format(
                            cmd.cmd_id))
            else:
                # 成功，状态置为 处理中
                cmd.cmdstatus = ECommandStatus.Dealing
                self._logger.info(
                    "Send idown_cmd_back succeed\t{}:\ncmdid:{}\nclient:{}\t{}"
                    .format(cmd.target, cmd.cmd_id, cmd._clientid,
                            targetclient._statusbasic.ip))

            if not self._dbmanager.update_cmd_status(
                    cmd._platform, cmd.cmd_id,
                    targetclient._statusbasic._clientid, cmd.cmdstatus):
                self._logger.error(
                    "Update cmd cmdstatus failed:\ncmdid:{}\ncmdstatus:{}".
                    format(cmd.cmd_id, cmd.cmdstatus.name))
                return

        except Exception:
            self._logger.error(
                "Update IDownCmd cmdstatus to db error: {}".format(
                    traceback.format_exc()))

    def stop(self):
        pass

    def reload(self):
        pass
