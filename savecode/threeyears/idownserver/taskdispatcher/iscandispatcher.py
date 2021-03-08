"""cmd dispatcher"""

# -*- coding:utf-8 -*-

import time
import traceback
from typing import Tuple

from datacontract import (Client, CmdFeedBack, DataMatcher, ECommandStatus,
                          EScanType, ETaskStatus, IscanTask, IscanTaskBack)
from outputmanagement import OutputManagement

from ..statusmantainer import StatusMantainer
from .dispatcherbase import DispatcherBase


class IScanDispatcher(DispatcherBase):
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

    def _output_taskback(self, scantask: IscanTask, status: ECommandStatus,
                         msg: str):
        if not isinstance(scantask, IscanTask):
            self._logger.error(
                "Invalid IscanTask object for output ScanTaskBack: {}".format(
                    type(scantask)))
            return

        scantask: IscanTask = scantask
        scanback: IscanTaskBack = IscanTaskBack.create_from_task(
            scantask, status, msg)
        if not OutputManagement.output(scanback):
            self._logger.error(
                "Output IscanTaskBack failed:\ntaskid={}\ndata={}".format(
                    scantask.taskid, scantask.inputdata._source))

    def _output_batch_task_back(self, scantask: IscanTask,
                                status: ECommandStatus, msg: str):
        pass

    def _dispatch_task(self, scantask: IscanTask) -> Tuple[bool, str]:
        """
        dispatch IScanTask
        """
        succ: bool = True
        msg: str = None
        try:
            if not isinstance(scantask, IscanTask):
                self._logger.error("Invalid IscanTask: {}".format(
                    type(scantask)))
                return (succ, msg)

            if scantask.scantype == EScanType.ScanSearch:
                succ, msg = self._dispatch_scansearch(scantask)
            elif scantask.scantype == EScanType.Scan:
                succ, msg = self._dispatch_scansearch(scantask)
            else:
                succ = False
                msg = "不支持的任务类型"
                self._logger.error("Unknow IscanTask({}): {}".format(
                    scantask.scantype.name, type(scantask)))

        except Exception as ex:
            succ = False
            msg = "内部错误: {}".format(ex.args)
        return (succ, msg)

    def _dispatch_scansearch(self, scantask: IscanTask) -> Tuple[bool, str]:
        """分发扫描搜索任务"""
        try:

            succ, needdispatch, client, msg = self._choose_client(scantask)
            if not succ:
                return (succ, msg)

            # 先选client,当选好了client再去把任务存放在数据库
            # 存入数据库
            if needdispatch:
                if not self._save_task_to_db(scantask, client):
                    succ = False
            else:
                self._logger.info(
                    "Reduplicated IScanTask already dispatched and is currently on dealing:\ntaskid:{}\nbatchid:{}\nclient:{}\t{}"
                        .format(scantask.taskid, scantask.batchid,
                                client._statusbasic._clientid,
                                client._statusbasic.ip))

        except Exception as ex:
            if not isinstance(msg, str):
                msg = "内部分发扫描任务错误: {}".format(ex.args)
            self._log_error_task(
                scantask,
                "Dispatch IScantask scansearch error: {}".format(ex.args))
        return (succ, msg)

    def _choose_client(self, scantask: IscanTask) -> Tuple[bool, bool, Client, str]:
        """
        选择一个client
        """
        succ: bool = True
        msg: str = None
        res: Client = None
        msg: str = None
        needdispatch: bool = True
        try:
            currentclients: dict = StatusMantainer.get_clientstatus_id_sorted()
            # 检查任务，如果是完全重复的taskid（直接手动重新搞的），则找到已经被分配过的采集端
            existtask: IscanTask = self._dbmanager.get_iscantask(
                scantask._platform, scantask.taskid)

            if not isinstance(existtask, IscanTask) or not isinstance(
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
                    scantask, currentclients)
            else:
                # 走到这里，目标采集端必然存在并在线
                # 如果已存在的任务状态为正在执行等状态，则直接返回一个回馈文件说正在执行
                # 否则重新下发到目标采集端
                # 这里做一个修改，因为有暂停周期这个功能，那么无论如何都要将任务发过去，但是如果本身被暂停了，也可以不用发过去，等待那边执行完成
                # 这边必须要给前端回一个已经收到任务，modify by judy 2020/07/24
                res = currentclients[existtask._clientid]
                # if existtask.cmdstatus == ECommandStatus.Failed or \
                #     existtask.cmdstatus == ECommandStatus.Succeed or \
                #     existtask.cmdstatus == ECommandStatus.Cancelled or \
                #     existtask.cmdstatus == ECommandStatus.Timeout:
                # 重新下发, 没毛病这里做的是对的
                # 周期任务都需要继承周期，by judy 2020/09/10
                if scantask._is_period:
                    # 如果是周期任务，对于新任务重新下发时则需要将其周期数+1
                    # 但是如果是需要暂停任务，则直接就把这个暂停命令发过去了就行了
                    # if scantask.cmd.switch_control.download_switch == 1:
                    scantask.periodnum = existtask.periodnum
                    # else:
                    # 如果不是暂停任务也需要继承目前有的周期
                    # scantask.periodnum = existtask.periodnum
                # else:
                # 返回回馈数据，说正在执行
                # needdispatch = False
                # 这种情况暂时不返回任何回馈数据
                # tb: TaskBatchBack = TaskBatchBack.create_from_task(
                #     task, ECommandStatus.Progress, '任务正在执行')
                # if not OutputManagement.output(tb):
                #     self._logger.error(
                #         "Return TaskBatchBack of reduplicated task already running failed:\ntaskid:{}\nbatchid:{}\nclientid:{}".
                #         format(task.taskid, task.batchid,
                #                existtask._clientid))

        except Exception as ex:
            self._logger.error("Choose iscantask client error: %s" %
                               traceback.format_exc())
            res = None
            succ = False
            msg = "内部错误: {}".format(ex.args)
        return (succ, needdispatch, res, msg)

    def _save_task_to_db(self, scantask: IscanTask, client: Client) -> bool:
        """"""
        res: bool = False
        try:
            res = self._dbmanager.save_new_iscantask(
                client, scantask, ECommandStatus.WaitForSend)
            if res:
                self._logger.debug(
                    "Save IScanTask OK: {} {} {} -> {} {}".format(
                        scantask.taskid, scantask.batchid,
                        scantask.scantype.name, client._statusbasic._clientid,
                        client._statusbasic.ip))
            else:
                # 如果存入失败了，
                # 对于当前子任务来说，需要返回一个子任务回馈文件
                # 对于总任务，需要判断是否其所有子任务都失败了，并返回回馈数据
                self._logger.debug(
                    "Save IScanTask Failed: {} {} {} -> {} {}".format(
                        scantask.taskid, scantask.batchid,
                        scantask.scantype.name, client._statusbasic._clientid,
                        client._statusbasic.ip))

                ## 返回回馈数据
                scanback: IscanTaskBack = IscanTaskBack.create_from_task(
                    scantask, ECommandStatus.Failed, '保存任务信息出错')
                if not OutputManagement.output(scanback):
                    self._logger.error(
                        'Output IScanTaskBack failed:\ntaskid={}\nbatchid={}'.
                            format(scanback.taskid, scanback.batchid))

        except Exception as ex:
            msg = "内部错误，存储扫描任务失败:{}".format(ex.args)
            res = False
            self._log_error_task(
                scantask,
                "Dispatch IScantask scansearch error: {}".format(ex.args))

        return res

    def _log_error_task(self, task: IscanTask, msg: str = 'error'):
        """打印错误任务的日志信息"""
        try:
            task: IscanTask = task
            if msg is None:
                msg = 'error'
            self._logger.info(f"""{msg}:
segline:{task.segline}
segindex:{task.segindex}
taskid:{task.taskid}
batchid:{task.batchid}
scantype:{task.scantype.name}""")

        except Exception:
            self._logger.error(
                "Output error task to error folder error:\ntaskid=%s\nerror:%s"
                % (task.taskid, traceback.format_exc()))
