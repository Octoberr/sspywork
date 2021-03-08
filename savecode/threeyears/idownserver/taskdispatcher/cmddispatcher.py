"""cmd dispatcher"""

# -*- coding:utf-8 -*-

import time
import traceback

from commonbaby.helpers import helper_time

from datacontract import (Client, CmdFeedBack, DataMatcher, ECommandStatus,
                          ETaskStatus, IdownCmd, Task)
from outputmanagement import OutputManagement

from ..statusmantainer import StatusMantainer
from .dispatcherbase import DispatcherBase


class CmdDispatcher(DispatcherBase):
    """"""

    def __init__(
            self,
            uniquename: str,
            datamatcher: DataMatcher,
            maxwaitcount: int = 1,
            maxwaittime: float = 3,
            relation_inputer_src: list = None,
    ):
        DispatcherBase.__init__(self, uniquename, datamatcher, maxwaitcount,
                                maxwaittime, relation_inputer_src)

    def _output_taskback(self, cmd: IdownCmd, status: ECommandStatus,
                         msg: str):
        if not isinstance(cmd, IdownCmd):
            self._logger.error(
                "Invalid IDownCmd object for output CmdFeedBack: {}".format(
                    type(cmd)))
            return

        cmd: IdownCmd = cmd
        cmdback: CmdFeedBack = CmdFeedBack.create_from_cmd(cmd, status, msg)
        if not OutputManagement.output(cmdback):
            self._logger.error(
                "Output CmdFeedBack failed:\ncmdid={}\ndata={}".format(
                    cmd.cmd_id, cmd.inputdata._source))

    def _output_batch_task_back(self, cmd: IdownCmd, status: ECommandStatus,
                                msg: str):
        pass

    def _dispatch_task(self, cmd: IdownCmd) -> (bool, str):
        """分配Cmd"""
        succ = True
        msg = None
        try:
            if not isinstance(cmd, IdownCmd):
                msg = "错误的Cmd类型: {}".format(type(cmd))
                return (succ, msg)
            if not cmd.target is None and len(cmd.target) > 0:
                succ, msg = self._dispatch_by_target(cmd)
            else:
                succ, msg = self._dispatch_to_all_clients(cmd)
        except Exception:
            self._logger.error("Dispatch IDownCmd to clients error: {}".format(
                traceback.format_exc()))

        return (succ, msg)

    def _dispatch_by_target(self, cmd: IdownCmd) -> (bool, str):
        '''dispatch by cmd target'''
        # cmd.target.
        succ: bool = True
        msg: str = None
        try:
            if not isinstance(cmd, IdownCmd):
                self._logger.error(
                    "Invalid IDownCmd for dispatch by target: {}".format(
                        type(cmd)))
                return (succ, msg)
            task: Task = self._dbmanager.search_task_by_cmd_target(cmd)

            if not isinstance(task, Task):
                succ = False
                msg = '未找到指定的target'
                return (succ, msg)

            if not isinstance(task._clientid, str):
                succ = False
                msg = '指定的target任务未下发到任何采集端'
                return (succ, msg)

            currentclients: dict = StatusMantainer.get_clientstatus_id_sorted()
            if not currentclients.__contains__(task._clientid):
                succ = False
                msg = '指定的target任务所在的采集端未上线'
                return (succ, msg)

            clients: dict = {task._clientid: currentclients[task._clientid]}
            if not self._dbmanager.save_new_idown_cmd(
                    cmd.platform, clients, cmd, helper_time.ts_since_1970_tz(),
                    ECommandStatus.WaitForSend, None, None, 0):
                succ = False
                msg = '分配命令到所有采集端失败'

        except Exception as ex:
            succ = False
            msg = "内部错误: {}".format(ex.args)
        return (succ, msg)

    def _dispatch_to_all_clients(self, cmd: IdownCmd) -> (bool, str):
        '''dispatch to all clients'''
        succ: bool = True
        msg: str = None
        try:
            currentclients: dict = StatusMantainer.get_clientstatus_id_sorted()
            # 每个ClientId存一份cmd
            if not self._dbmanager.save_new_idown_cmd(
                    cmd.platform, currentclients, cmd,
                    helper_time.ts_since_1970_tz(), ECommandStatus.WaitForSend,
                    None, None, 0):
                succ = False
                msg = '分配命令到所有采集端失败'

        except Exception as ex:
            self._logger.error(
                "Dispatch IDownCmd to all clients error: {}".format(ex.args))
            succ = False
            msg = "内部错误: {}".format(ex.args)
        return (succ, msg)
