"""cmd dispatcher"""

# -*- coding:utf-8 -*-

import time
import traceback
from typing import Tuple

from datacontract import (Client, CmdFeedBack, DataMatcher, ECommandStatus,
                          EScanType, ETaskStatus, IscoutBtaskBack, IscoutTask,
                          IscoutTaskBack)
from outputmanagement import OutputManagement
from ..dbmanager import EDBAutomic
from ..statusmantainer import StatusMantainer
from .dispatcherbase import DispatcherBase


class IScoutDispatcher(DispatcherBase):
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

    def _output_taskback(self, scouttask: IscoutTask, status: ECommandStatus,
                         msg: str):
        if not isinstance(scouttask, IscoutTask):
            self._logger.error(
                "Invalid IscoutTask object for output ScanTaskBack: {}".format(
                    type(scouttask)))
            return

        scouttask: IscoutTask = scouttask
        scouttask: IscoutTaskBack = IscoutTaskBack.create_from_task(
            scouttask, status, msg)
        if not OutputManagement.output(scouttask):
            self._logger.error(
                "Output IscoutTaskBack failed:\ntaskid={}\ndata={}".format(
                    scouttask.taskid, scouttask.inputdata._source))

    def _output_batch_task_back(self, scouttask: IscoutTask,
                                status: ECommandStatus, msg: str):
        if not isinstance(scouttask, IscoutTask):
            self._logger.error(
                "Invalid IscoutTask object for output ScanTaskBack: {}".format(
                    type(scouttask)))
            return

        scouttask: IscoutTask = scouttask
        scouttask: IscoutBtaskBack = IscoutBtaskBack.create_from_task(
            scouttask, status, msg)
        if not OutputManagement.output(scouttask):
            self._logger.error(
                "Output IscoutBTaskBack failed:\ntaskid={}\ndata={}".format(
                    scouttask.taskid, scouttask.inputdata._source))

    def _dispatch_task(self, task: IscoutTask) -> Tuple[bool, str]:
        '''dispatch IScoutTask'''
        succ: bool = True
        msg: str = None
        try:
            if not isinstance(task, IscoutTask):
                self._logger.error("Invalid IScoutTask: {}".format(type(task)))
                return (succ, msg)

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
                            client._statusbasic._clientid,
                            client._statusbasic.ip))

            return (succ, msg)
        except Exception as ex:
            succ = False
            msg = "内部错误: {}".format(ex.args)
        return (succ, msg)

    def _choose_client(self,
                       task: IscoutTask) -> Tuple[bool, bool, Client, str]:
        """选择最优采集端，返回配置的采集端ip。
        返回<是否选择采集端成功，是否更新到数据库，选择的采集端>"""
        succ: bool = True
        needdispatch: bool = True
        res: Client = None
        msg: str = None
        try:

            currentclients: dict = StatusMantainer.get_clientstatus_id_sorted()
            # 检查是否存在已有的子任务，如果是完全重复的taskid+batchid（直接手动重新搞的），则找到已经被分配过的采集端
            existtask: IscoutTask = self._dbmanager.get_iscout_batch_task(
                task._platform, task.taskid, task.batchid)

            if not isinstance(existtask, IscoutTask) or not isinstance(
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
                # 这里的周期可能会有问题by judy 2020/09/1
                # 走到这里，目标采集端必然存在并在线
                # 如果已存在的任务状态为正在执行等状态，则直接返回一个回馈文件说正在执行
                # 否则重新下发到目标采集端
                res = currentclients[existtask._clientid]
                if existtask.cmdstatus == ECommandStatus.Failed or \
                    existtask.cmdstatus == ECommandStatus.Succeed or \
                    existtask.cmdstatus == ECommandStatus.Cancelled or \
                    existtask.cmdstatus == ECommandStatus.Timeout:
                    # 重新下发
                    if task._is_period:
                        task.periodnum = existtask.periodnum
                else:
                    # 返回回馈数据，说正在执行
                    needdispatch = False
                    # 这种情况暂时不返回任何回馈数据

        except Exception:
            self._logger.error("Choose IScoutTask client error: %s" %
                               traceback.format_exc())
            res = None
            succ = False
            msg = '内部错误500'

        return (succ, needdispatch, res, msg)

    def _save_task_to_db(self, task: IscoutTask, client: Client) -> bool:
        """存储新任务，来的肯定是子任务\n
        task: 任务对象\n
        client: 任务被分配到的采集端对象"""
        res: bool = True
        try:
            ############
            # 1. 不同任务下发多次
            # 2. 同一批次任务反复测试（同一个批处理任务需要反复测了10次那种）

            #
            # 任务必有taskid+batchid

            # 所有任务来了都存入3张表
            with self._dbmanager.get_automic_locker(
                    EDBAutomic.ReduplicateIScoutTask):
                res = self._dbmanager.save_new_iscouttask(task, client)
            if res:
                self._logger.debug(
                    "Save IScoutTask OK: {} {} {} {} -> {} {}".format(
                        task.taskid, task.batchid, task._objecttype.name,
                        task._object, client._statusbasic._clientid,
                        client._statusbasic.ip))
            else:
                # 如果存入失败了，
                # 对于当前子任务来说，需要返回一个子任务回馈文件
                # 对于总任务，需要判断是否其所有子任务都失败了，并返回回馈数据
                self._logger.debug(
                    "Save IScoutTask Failed: {} {} {} {} -> {} {}".format(
                        task.taskid, task.batchid, task._objecttype.name,
                        task._object, client._statusbasic._clientid,
                        client._statusbasic.ip))

                ## 返回回馈数据
                taskbatchback: IscoutBtaskBack = IscoutBtaskBack.create_from_task(
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

    def _log_error_task(self, task: IscoutTask, msg: str = 'error'):
        """打印错误任务的日志信息"""
        try:
            task: IscoutTask = task
            if msg is None:
                msg = 'error'
            self._logger.info(f"""{msg}:
segline:{task.segline}
segindex:{task.segindex}
taskid:{task.taskid}
batchid:{task.batchid}
objtype:{task._objecttype.name}
obj:{task._object}""")

        except Exception:
            self._logger.error(
                "Output error task to error folder error:\ntaskid=%s\nerror:%s"
                % (task.taskid, traceback.format_exc()))
