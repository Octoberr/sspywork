"""automated task dispatcher"""

# -*- coding:utf-8 -*-

import json
import threading
import time
import traceback
import uuid

from commonbaby.helpers import helper_time

from ..dbmanager import EDBAutomic
from datacontract import (AutomatedTask, AutotaskBack, AutotaskBatchBack,
                          Client, DataMatcher, EAutoType, ECommandStatus,
                          ETaskStatus)
from outputmanagement import OutputManagement

from ..config_autotask import autotaskconfigs
from ..statusmantainer import StatusMantainer
from .autotaskdispatchconfig import AutoTaskConfig
from .dispatcherbase import DispatcherBase


class AutoTaskDispatcher(DispatcherBase):
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

        # 任务生成线程
        self._dispatching_tasks: dict = {}
        self._dispatching_tasks_locker = threading.RLock()
        self._t_task = threading.Thread(target=self._task_generate)

    def _start_sub(self):
        if not self._t_task._started._flag:
            self._t_task.start()

    def _output_taskback(self, task: AutomatedTask, status: ECommandStatus,
                         msg: str):
        if not isinstance(task, AutomatedTask):
            self._logger.error(
                "Invalid AutomatedTask object for output AutoTaskBack: {}".
                format(type(task)))
            return

        task: AutomatedTask = task
        taskback: AutotaskBack = AutotaskBack.create_from_task(
            task, status, msg, helper_time.ts_since_1970_tz())
        if not OutputManagement.output(taskback):
            self._logger.error("Output AutoTaskBack failed: taskid={}".format(
                task.taskid))

    def _output_batch_task_back(self, task: AutomatedTask,
                                status: ECommandStatus, msg: str):
        if not isinstance(task, AutomatedTask):
            self._logger.error(
                "Invalid AutomatedTask object for output AutoTaskBack: {}".
                format(type(task)))
            return

        task: AutomatedTask = task
        taskbback: AutotaskBatchBack = AutotaskBatchBack.create_from_task(
            task, status, msg, helper_time.ts_since_1970_tz())
        if not OutputManagement.output(taskbback):
            self._logger.error(
                "Output AutoBatchTaskBack failed:\ntaskid={}".format(
                    task.taskid))

    def _add_to_dispatching_list(self, task: AutomatedTask):
        with self._dispatching_tasks_locker:
            if not self._dispatching_tasks.__contains__(task.autotasktype):
                self._dispatching_tasks[task.autotasktype] = {}

            if not self._dispatching_tasks[task.autotasktype].__contains__(
                    task._platform):
                self._dispatching_tasks[task.autotasktype][task._platform] = []

            self._dispatching_tasks[task.autotasktype][task._platform].append(
                task)

    def _remove_from_dispatching_list(self, task: AutomatedTask):
        with self._dispatching_tasks_locker:
            if not self._dispatching_tasks.__contains__(task.autotasktype):
                return
            if not self._dispatching_tasks[task.autotasktype].__contains__(
                    task._platform):
                return

            if not task in self._dispatching_tasks[task.autotasktype][
                    task._platform]:
                return

            self._dispatching_tasks[task.autotasktype][task._platform].remove(
                task)

    def _is_task_on_dispatcing(self, platform: str,
                               tasktype: EAutoType) -> bool:
        with self._dispatching_tasks_locker:
            if not self._dispatching_tasks.__contains__(tasktype):
                return False

            if not self._dispatching_tasks[tasktype].__contains__(platform):
                return False

            if len(self._dispatching_tasks[tasktype][platform]) < 1:
                return False

            return True

###########################################################
# generate automate task

    def _task_generate(self):
        """生成任务"""
        # 睡2秒再开始分配。不然太快了，采集端状态数据库还么读出来
        time.sleep(2)
        while True:
            try:
                for task in self._generate_tasks():
                    if not isinstance(task, AutomatedTask):
                        self._logger.error(
                            "Invalid AutomatedTask: {}".format(task))
                        continue

                    # filter dispatching task
                    if self._is_task_on_dispatcing(task._platform,
                                                   task.autotasktype):
                        continue
                    self._add_to_dispatching_list(task)

                    # TODO: dispatch to clients
                    self._logger.info(
                        "New AutomatedTask [{} periodnum={}]".format(
                            task.autotasktype.name, task.periodnum))
                    self._task_queue.put(task)
                    self._logger.debug("New task: {} {}".format(
                        task, type(task)))
                    # self._dispatch_task(task)

            except Exception:
                self._logger.error("Generate automated task error: {}".format(
                    traceback.format_exc()))
            finally:
                time.sleep(2)

    def _generate_tasks(self) -> iter:
        """调度所有task生成器"""
        try:
            for taskconfig in autotaskconfigs:
                if not isinstance(taskconfig, AutoTaskConfig):
                    self._logger.error("Invalid {}: {}".format(
                        type(taskconfig), taskconfig))
                    continue

                taskconfig: AutoTaskConfig = taskconfig
                if not taskconfig._enable:
                    continue

                for task in self._generate_task_by_config(taskconfig):
                    yield task

        except Exception:
            self._logger.error("Generate tasks error: {}".format(
                traceback.format_exc()))

    def _generate_task_by_config(self, autotaskconfig: AutoTaskConfig) -> iter:
        """generate出来是多个子任务"""
        lastendtime: str = None
        periodnum: int = None
        # 从库中找
        # 1. 查询最晚的一条总任务
        # 2. 条件1：若有，则判断其完成时间是否超过周期循环间隔时间 或
        # 3. 条件2：若无
        # 4. 则下发一条全新的、周期数+1的任务
        # 这样才能记录每一次任务的每个子任务被分发到的ClientId
        got: bool = False
        task: AutomatedTask = self._dbmanager.get_last_automatedtask(
            autotaskconfig._platform, autotaskconfig._tasktype)

        if isinstance(task, AutomatedTask):
            got = True
            lastendtime = task.lastendtime
            periodnum = task.periodnum

        do: bool = False
        if got and lastendtime is None:
            # 已经有任务，但是还么执行完过
            return
        elif not got:
            # 新部署的，还没有过任务
            periodnum = 0
            do = True
        else:
            # got and lastendtime is not None的情况
            # tend = time.mktime(
            #     time.strptime(task.lastendtime, "%Y-%m-%d %H:%M:%S"))
            tend = task.lastendtime
            tstart = tend + task.cmd.stratagy.interval
            tnow = helper_time.ts_since_1970_tz()
            if tnow > tstart:
                do = True

        if not do:
            return

        # 造任务
        taskid: str = str(uuid.uuid1())

        count: int = 1
        if autotaskconfig._seperatetask:
            count = len(StatusMantainer.get_clientstatus_id_sorted())

        for i in range(count):
            fields: dict = {
                "platform":
                autotaskconfig._platform,
                "source":
                autotaskconfig._source,
                "periodnum":
                periodnum + 1,
                "taskid":
                taskid,
                "batchid":
                str(uuid.uuid1()),
                "autotasktype":
                autotaskconfig._tasktype.value,
                "createtime":
                helper_time.ts_since_1970_tz(),
                "cmdid":
                str(uuid.uuid1()),
                "cmd":
                json.dumps({
                    "stratagy": {
                        "circulation_mode": 2,
                        "interval": autotaskconfig._interval,
                    },
                    "stratagyauto": {
                        "section": "1/{}".format(count),
                        "index": i
                    }
                }),
            }
            task: AutomatedTask = AutomatedTask.create_from_dict(
                fields, autotaskconfig._platform)

            yield task

    def _construct_batch_task(self, taskid: str,
                              otherfields: dict = None) -> iter:
        """根据配置是否拆分任务，构造并返回AutomatedTask"""
        yield None


###########################################################
# dispatch task

    def _dispatch_task(self, task: AutomatedTask) -> (bool, str):
        '''dispatch AutomatedTask'''
        succ: bool = True
        msg: str = None
        try:
            if not isinstance(task, AutomatedTask):
                self._logger.error("Invalid AutomatedTask: {}".format(
                    type(task)))
                return (succ, msg)

            succ, needdispatch, client, msg = self._choose_client(task)
            if not succ:
                return (succ, msg)

            # 存入数据库
            if needdispatch:
                if not self._save_task_to_db(task, client):
                    self._logger.info(
                        "AutomatedTask dispatch failed [{} periodnum={}]:\ntaskid:{}\nbatchid:{}\nclient:{}\t{}"
                        .format(task.autotasktype.name, task.periodnum,
                                task.taskid, task.batchid,
                                client._statusbasic._clientid,
                                client._statusbasic.ip))
                    succ = False
                else:
                    self._logger.info(
                        "AutomatedTask dispatch OK [{} periodnum={}]:\ntaskid:{}\nbatchid:{}\nclient:{}\t{}"
                        .format(task.autotasktype.name, task.periodnum,
                                task.taskid, task.batchid,
                                client._statusbasic._clientid,
                                client._statusbasic.ip))
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
        finally:
            self._remove_from_dispatching_list(task)

        return (succ, msg)

    def _choose_client(self, task: AutomatedTask) -> (bool, bool, Client, str):
        """选择最优采集端，返回配置的采集端ip。
        返回<是否选择采集端成功，是否更新到数据库，选择的采集端>"""
        succ: bool = True
        needdispatch: bool = True
        res: Client = None
        msg: str = None
        try:

            currentclients: dict = StatusMantainer.get_clientstatus_id_sorted()
            # 检查是否存在已有的子任务，如果是完全重复的taskid+batchid（直接手动重新搞的），则找到已经被分配过的采集端
            existtask: AutomatedTask = self._dbmanager.get_auto_batch_task(
                task._platform, task.taskid, task.batchid)

            if not isinstance(existtask, AutomatedTask) or not isinstance(
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
                # 走到这里，目标采集端必然存在并在线
                # 如果已存在的任务状态为正在执行等状态，则直接返回一个回馈文件说正在执行
                # 否则重新下发到目标采集端
                res = currentclients[existtask._clientid]
                if existtask.cmdstatus == ECommandStatus.Failed or \
                    existtask.cmdstatus == ECommandStatus.Succeed or \
                    existtask.cmdstatus == ECommandStatus.Cancelled or \
                    existtask.cmdstatus == ECommandStatus.Timeout:
                    # 重新下发
                    pass
                else:
                    # 返回回馈数据，说正在执行
                    needdispatch = False
                    # 这种情况暂时不返回任何回馈数据

        except Exception:
            self._logger.error(
                "Choose IScoutTask client error: %s" % traceback.format_exc())
            res = None
            succ = False
            msg = '内部错误500'

        return (succ, needdispatch, res, msg)

    def _save_task_to_db(self, task: AutomatedTask, client: Client) -> bool:
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
                    EDBAutomic.ReduplicateAutoTask):
                res = self._dbmanager.save_new_autotask(task, client)
            if res:
                self._logger.debug(
                    "Save AutomatedTask OK: {} {} {} -> {} {}".format(
                        task.taskid, task.batchid, task.autotasktype.name,
                        client._statusbasic._clientid, client._statusbasic.ip))
            else:
                # 如果存入失败了，
                # 对于当前子任务来说，需要返回一个子任务回馈文件
                # 对于总任务，需要判断是否其所有子任务都失败了，并返回回馈数据
                self._logger.debug(
                    "Save AutomatedTask Failed: {} {} {} -> {} {}".format(
                        task.taskid, task.batchid, task.autotasktype.name,
                        client._statusbasic._clientid, client._statusbasic.ip))

                ## 返回回馈数据
                taskbatchback: AutotaskBatchBack = AutotaskBatchBack.create_from_task(
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

    def _log_error_task(self, task: AutomatedTask, msg: str = 'error'):
        """打印错误任务的日志信息"""
        try:
            task: AutomatedTask = task
            if msg is None:
                msg = 'error'
            self._logger.info(f"""{msg}:
segline:{task.segline}
segindex:{task.segindex}
taskid:{task.taskid}
batchid:{task.batchid}
autotasktype:{task.autotasktype}""")

        except Exception:
            self._logger.error(
                "Output error task to error folder error:\ntaskid=%s\nerror:%s"
                % (task.taskid, traceback.format_exc()))
