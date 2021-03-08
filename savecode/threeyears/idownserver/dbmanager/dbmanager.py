"""database manager"""

# -*- coding:utf-8 -*-

import enum
import threading

from datacontract import (AutomatedTask, AutotaskBack, AutotaskBatchBack,
                          Client, CmdFeedBack, EAutoType, ECommandStatus,
                          ETaskStatus, ETokenType, IdownCmd, IscanTask,
                          IscanTaskBack, IscoutBtaskBack, IscoutTask,
                          IscoutTaskBack, StatusBasic, StatusTask,
                          StatusTaskInfo, Task, TaskBatchBack)

from ..config_db import sqlitecfg
from .dbsqlite.dbsqlite import DbSqlite
from .sqlcondition import SqlCondition, SqlConditions
from .sqlconn import SqlConn


class EDBAutomic(enum.Enum):
    """数据库原子操作锁枚举，用于外部调用方控制全局业务原子性操作"""
    # 用于重复任务在数据库合并时的原子操作锁
    ReduplicateTask = 0
    ReduplicateIScoutTask = 1
    ReduplicateIScanTask = 2
    ReduplicateAutoTask = 3
    ReduplicateCmd = 4


class DbManager:
    """数据库接口"""

    _currdb = DbSqlite
    _static_initialed: bool = False
    _static_init_locker = threading.Lock()

    # 各业务原子操作锁(暂时就这么取名字吧..)
    # 由于可能存在情况：会来完全重复的任务，有可能是故意重新下发的。
    # 所以为了符合用户操作，特此加锁避免出现用户乱搞（大量重复任务过来）的情况
    # 但这种情况必然是特例，且不应该在生产环境出现。
    # 所以仅考虑非常可能导致数据库混乱的接口进行加锁，
    # dbmanager对外提供锁获取接口，外部调用方自行进行业务原子性操控。
    __automic_lockers: dict = {}
    __automic_lockers_lock = threading.RLock()

    def __init__(self):
        if DbManager._static_initialed:
            return
        with DbManager._static_init_locker:
            if DbManager._static_initialed:
                return

            DbManager._currdb.static_init(sqlitecfg)
            DbManager._static_initialed = True

    @classmethod
    def get_automic_locker(cls, lock: EDBAutomic):
        """获取业务原子操作锁，外部自行控制业务原子性"""
        if not isinstance(lock, EDBAutomic):
            raise Exception("Invalid automic locke")
        if cls.__automic_lockers.__contains__(lock):
            return cls.__automic_lockers[lock]
        with cls.__automic_lockers_lock:
            if cls.__automic_lockers.__contains__(lock):
                return cls.__automic_lockers[lock]
            cls.__automic_lockers[lock] = threading.RLock()
            return cls.__automic_lockers[lock]

    @classmethod
    def connect_write(cls, tbname: str, timeout=None) -> SqlConn:
        """返回一个可以用于增删改操作的数据库连接"""
        return DbManager._currdb.connect_write(tbname, timeout)

    @classmethod
    def connect_all(cls, tbname: str, timeout=None) -> iter:
        """返回所有可用于查询操作的数据库连接"""
        return DbManager._currdb.connect_all(tbname, timeout)

    @classmethod
    def execute_search_one(cls, tbname: str, sql: str,
                           params: tuple = None) -> object:
        """执行查询语句"""
        return DbManager._currdb.execute_search_one(tbname, sql, params)

    @classmethod
    def execute_search_all(cls,
                           tbname: str,
                           sql: str,
                           return_with_conn: bool = False,
                           params: tuple = None) -> iter:
        """执行查询语句\n
        return_with_conn: 是否将结果与对应的数据库链接一并返回，默认为False"""
        return DbManager._currdb.execute_search_all(tbname, sql,
                                                    return_with_conn, params)

    @classmethod
    def execute_modify(cls, tbname: str, sql: str,
                       params: tuple = None) -> bool:
        """执行写增删改操作"""
        return DbManager._currdb.execute_modify(tbname, sql, params)

######################################################
# ClientStatus

    @classmethod
    def save_client_status_basic(cls, client: StatusBasic) -> bool:
        """保存采集端基础状态"""
        return DbManager._currdb.save_client_status_basic(client)

    @classmethod
    def save_client_status_task(cls, client: StatusTask) -> bool:
        """保存采集端基础状态数据"""
        return DbManager._currdb.save_client_status_task(client)

    @classmethod
    def get_client_status(cls, clientid: str) -> Client:
        """保存采集端任务状态数据"""
        return DbManager._currdb.get_client_status(clientid)

    @classmethod
    def get_client_status_all(cls, heartbeat: float = 15) -> iter:
        """获取所有采集端任务状态数据。\n
        interval: 指定心跳间隔，即只读取最近n秒内更新的采集端状态，单位秒。"""
        return DbManager._currdb.get_client_status_all(heartbeat)

    @classmethod
    def get_client_by_search_token(
            cls,
            platform: str,
            apptype: int,
            tokentype: ETokenType = None,
            input_: str = None,
            preglobaltelcode: str = None,
            preaccount: str = None,
            globaltelcode: str = None,
            phone: str = None,
            account: str = None,
            password: str = None,
            url: str = None,
            host: str = None,
            cookie: str = None,
    ) -> Client:
        """查询附带指定token的task被分配到的clientid"""
        # 由于相同的令牌资源在分配时将会分配到固定的一个采集端，
        # 所以在根据令牌资源搜索采集端时将只会有一个结果。
        return DbManager._currdb.get_client_by_search_token(
            platform=platform,
            apptype=apptype,
            tokentype=tokentype,
            input_=input_,
            preglobaltelcode=preglobaltelcode,
            preaccount=preaccount,
            globaltelcode=globaltelcode,
            phone=phone,
            account=account,
            password=password,
            url=url,
            host=host,
            cookie=cookie,
        )

######################################################
# IDownTask

    @classmethod
    def save_new_idown_task(
            cls,
            task: Task,
            client: Client,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend) -> bool:
        """保存/插入新来的任务"""
        return DbManager._currdb.save_new_idown_task(task, client, cmdstatus)

    @classmethod
    def get_parent_clientid_of_task(cls, task: Task) -> str:
        """获取 指定task的父任务被分配到的采集端 clientid"""
        return DbManager._currdb.get_parent_clientid_of_task(task)

    @classmethod
    def get_parent_client_of_task(cls, task: Task) -> Client:
        """获取 指定task的父任务被分配到的采集端 Client对象"""
        return DbManager._currdb.get_parent_client_of_task(task)

    @classmethod
    def get_deliverable_task(cls, ):
        """获取待分配的任务"""
        return DbManager._currdb.get_deliverable_task()

    @classmethod
    def update_idown_task_status(cls, task: Task,
                                 cmdstatus: ECommandStatus) -> bool:
        """更新指定的task，Task表总任务状态"""
        return DbManager._currdb.update_idown_task_status(task, cmdstatus)

    @classmethod
    def get_task_by_taskid(cls, taskid: str) -> Task:
        """查询并返回指定taskid的总任务Task对象"""
        return DbManager._currdb.get_task_by_taskid(taskid)

    @classmethod
    def update_idown_task(cls, task: Task) -> bool:
        """更新IDownTask表，根据platform,taskid更新其他所有字段，并重置task.sequence序列"""
        return DbManager._currdb.update_idown_task(task)

    @classmethod
    def update_idown_task2(cls, task: Task) -> bool:
        """更新指定的task，IDownTask表总任务所有字段"""
        return DbManager._currdb.update_idown_task2(task)

    @classmethod
    def increace_task_batch_complete_count(cls, platform: str, taskid: str,
                                           batchid: str) -> bool:
        """原子操作，提升指定Task的batchcompletecount数量1。
        task:任务对象"""
        return DbManager._currdb.increace_task_batch_complete_count(
            platform, taskid, batchid)

######################################################
# IDownBatchTask

    @classmethod
    def get_task_by_search_token(
            cls,
            platform: str,
            apptype: int,
            tokentype: ETokenType = None,
            input_: str = None,
            preglobaltelcode: str = None,
            preaccount: str = None,
            globaltelcode: str = None,
            phone: str = None,
            account: str = None,
            password: str = None,
            url: str = None,
            host: str = None,
            cookie: str = None,
    ) -> Task:
        """查询附带指定token的task"""
        # 此功能可能存在问题：
        # 当程序同时用于不同平台时，给过来的条件查询出来的子任务
        # 可能有多个，且属于不同平台，此时若全部选中并下发对应任务
        # 可能造成意外的结果，即平台A的命令下发到平台B去了。
        # 但有时候又需要不指定platform进行查询，即本身就是想要将任务
        # 下发到所有当前程序正在运行于的平台。
        # 所以此处后面可能需要加上platform为参数，platform可以为空。
        # 当platform不为空时，只查询到当前platform下的任务，并下发到特指
        # 的平台。当platform为空时，下发任务到所有匹配的平台下。

        # 由于相同的令牌资源在分配时将会分配到固定的一个采集端，
        # 所以在根据令牌资源搜索采集端时将只会有一个结果。
        return DbManager._currdb.get_task_by_search_token(
            platform=platform,
            apptype=apptype,
            tokentype=tokentype,
            input_=input_,
            preglobaltelcode=preglobaltelcode,
            preaccount=preaccount,
            globaltelcode=globaltelcode,
            phone=phone,
            account=account,
            password=password,
            url=url,
            host=host,
            cookie=cookie,
        )

    @classmethod
    def get_task_cmdstatus(cls, task: Task) -> ECommandStatus:
        """获取指定总任务id的命令状态"""
        return DbManager._currdb.get_task_cmdstatus(task)

    @classmethod
    def get_task_batch_complete_count(cls, task: Task) -> int:
        """获取指定（子）任务的taskid对应的任务的
        batchcompletecount（子任务已完成数量），
        此方法为原子操作。"""
        return DbManager._currdb.get_task_batch_complete_count(task)

    @classmethod
    def get_batch_task_count_by_cmdstatus(cls, task: Task,
                                          cmdstatus: ECommandStatus) -> int:
        """查询指定任务的所有 为指定命令状态的子任务 的数量"""
        return DbManager._currdb.get_batch_task_count_by_cmdstatus(
            task, cmdstatus)

    @classmethod
    def get_batch_tasks(cls, platform: str, taskid: str) -> iter:
        """查询并返回指定总任务taskid下的所有子任务BatchTask对象"""
        return DbManager._currdb.get_batch_tasks(platform, taskid)

    @classmethod
    def get_batch_task(cls, platform: str, taskid: str, batchid: str) -> Task:
        """根据taskid、batchid、platform查询并返回指定的"""
        return DbManager._currdb.get_batch_task(platform, taskid, batchid)

    @classmethod
    def update_batchtask_status(cls, platform: str, taskid: str, batchid: str,
                                cmdstatus: ECommandStatus) -> bool:
        """更新task及batchtask命令状态"""
        return DbManager._currdb.update_batchtask_status(
            platform, taskid, batchid, cmdstatus)

    @classmethod
    def update_batchtask_client(cls, platform: str, taskid: str, batchid: str,
                                clientid: str) -> bool:
        """更新batchtask被分配到的采集端"""
        return DbManager._currdb.update_batchtask_client(
            platform, taskid, batchid, clientid)

    @classmethod
    def update_batchtask_back(cls, tb: TaskBatchBack) -> bool:
        """根据给予的采集端子任务状态数据 TaskBatchBack 更新数据库子任务状态。
        不会更新 IDownBatchTask 表的 IsBatchTaskCompleteCountIncreased 字段"""
        return DbManager._currdb.update_batchtask_back(tb)

    @classmethod
    def is_batch_complete_count_increaced(cls, platform: str, taskid: str,
                                          batchid: str) -> bool:
        """返回 指定的子任务完成情况 是否已更新到 总任务表的 batchcompletecount 字段"""
        return DbManager._currdb.is_batch_complete_count_increaced(
            platform, taskid, batchid)

######################################################
# IDownCmd

    @classmethod
    def get_deliverable_cmd(cls, ):
        """获取待分配的任务"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateCmd):
            return DbManager._currdb.get_deliverable_cmd()

    @classmethod
    def save_new_idown_cmd(
            cls,
            platform: str,
            clients: list,
            cmd: IdownCmd,
            cmdtime: float,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
            taskid: str = None,
            batchid: str = None,
            isrelative: int = 1,
    ) -> bool:
        """保存/插入新来的任务"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateCmd):
            return DbManager._currdb.save_new_idown_cmd(
                cmd.platform, clients, cmd, cmdtime, cmdstatus, taskid,
                batchid, isrelative)

    @classmethod
    def update_cmd(cls, cmd: IdownCmd, taskid: str = None,
                   batchid: str = None) -> bool:
        with cls.get_automic_locker(EDBAutomic.ReduplicateCmd):
            return DbManager._currdb.update_cmd(cmd, taskid, batchid)

    @classmethod
    def update_cmd_status(cls, platform: str, cmdid: str, clientid: str,
                          cmdstatus: ECommandStatus) -> bool:
        with cls.get_automic_locker(EDBAutomic.ReduplicateCmd):
            return DbManager._currdb.update_cmd_status(platform, cmdid,
                                                       clientid, cmdstatus)

    @classmethod
    def update_cmdback(cls, cmdback: CmdFeedBack) -> bool:
        with cls.get_automic_locker(EDBAutomic.ReduplicateCmd):
            return DbManager._currdb.update_cmdback(cmdback)

    @classmethod
    def get_cmd_merge_status(cls, cmdid: str, platform: str) -> ECommandStatus:
        """返回合并的cmd执行状态，返回None表示没有搜索到目标Cmd"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateCmd):
            return DbManager._currdb.get_cmd_merge_status(cmdid, platform)

    @classmethod
    def search_task_by_cmd_target(cls, cmd: IdownCmd) -> object:
        """返回合并的cmd执行状态，返回None表示没有搜索到目标Cmd"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateCmd):
            return DbManager._currdb.search_task_by_cmd_target(cmd)

######################################################
# IScanTask

    @classmethod
    def get_deliverable_iscantask(cls) -> iter:
        """获取待分配的任务"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScanTask):
            return DbManager._currdb.get_deliverable_iscantask()

    @classmethod
    def get_deliverable_iscantask2(cls) -> iter:
        """获取待分配的任务"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScanTask):
            return DbManager._currdb.get_deliverable_iscantask2()

    @classmethod
    def save_new_iscantask(
            cls,
            client: Client,
            scantask: IscanTask,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
    ) -> bool:
        '''存新的扫描任务'''
        # 加锁避免任务正在更新时把更新了一半的任务读出来下发了...
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScanTask):
            return DbManager._currdb.save_new_iscantask(
                client, scantask, cmdstatus)

    @classmethod
    def get_iscantask(cls, platform: str, taskid: str) -> IscanTask:
        """根据taskid+platform搜iscantask"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScanTask):
            return DbManager._currdb.get_iscantask(platform, taskid)

    @classmethod
    def get_iscantasks(cls, conds: SqlConditions) -> IscanTask:
        """根据taskid+platform搜iscantask"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScanTask):
            return DbManager._currdb.get_iscantasks(conds)

    @classmethod
    def update_iscantask_status(cls, platform: str, scantaskid: str,
                                cmdstatus: ECommandStatus) -> bool:
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScanTask):
            return DbManager._currdb.update_iscantask_status(
                platform, scantaskid, cmdstatus)

    @classmethod
    def update_iscantask_back(cls, scantaskback: IscanTaskBack) -> bool:
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScanTask):
            return DbManager._currdb.update_iscantask_back(scantaskback)

    @classmethod
    def update_iscantask(cls, task: IscanTask) -> bool:
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScanTask):
            return DbManager._currdb.update_iscantask(task)

    @classmethod
    def update_iscantask2(cls, platform: str, taskid: str,
                          updatefields: dict) -> bool:
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScanTask):
            return DbManager._currdb.update_iscantask2(platform, taskid,
                                                       updatefields)

######################################################
# IScoutTask/IScoutBatchTask

    @classmethod
    def save_new_iscouttask(cls, task: IscoutTask, client: Client):
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.save_new_iscouttask(task, client)

    @classmethod
    def get_iscout_task_periodnum(cls, platform: str, taskid: str):
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.get_iscout_task_periodnum(
                platform, taskid)

    # @classmethod
    # def get_iscout_task(cls,platform,taskid:str):
    #     with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
    #         return DbManager._currdb.get_iscout_task(
    #             platform, taskid)

    @classmethod
    def get_iscout_batch_task(cls, platform: str, taskid: str, batchid: str):
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.get_iscout_batch_task(
                platform, taskid, batchid)

    @classmethod
    def get_iscout_batch_tasks(cls, platform: str, taskid: str) -> iter:
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.get_iscout_batch_tasks(platform, taskid)

    @classmethod
    def get_deliverable_iscouttask(cls) -> iter:
        """获取待分配的任务"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.get_deliverable_iscouttask()

    @classmethod
    def get_deliverable_iscouttask2(cls) -> iter:
        """获取待分配的任务。走新的业务，server端控制下发"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.get_deliverable_iscouttask2()

    @classmethod
    def update_iscouttask_status(cls, platform: str, taskid: str,
                                 cmdstatus: ECommandStatus) -> bool:
        """更新指定的task，Task表总任务状态"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.update_iscouttask_status(
                platform, taskid, cmdstatus)

    @classmethod
    def update_iscoutbtask_status(cls, platform: str, taskid: str,
                                  batchid: str,
                                  cmdstatus: ECommandStatus) -> bool:
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.update_iscoutbtask_status(
                platform, taskid, batchid, cmdstatus)

    @classmethod
    def update_iscoutbtask_back(cls, scoutbtaskback: IscoutBtaskBack) -> bool:
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.update_iscoutbtask_back(scoutbtaskback)

    @classmethod
    def update_iscoutbtask(cls, platform: str, taskid: str, batchid: str,
                           updatefields: dict) -> bool:
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.update_iscoutbtask(
                platform, taskid, batchid, updatefields)

    @classmethod
    def get_iscoutbtask_count_by_cmdstatus(cls, platform: str, taskid: str,
                                           cmdstatus: ECommandStatus) -> int:
        """查询指定任务的所有 为指定命令状态的子任务 的数量"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.get_iscoutbtask_count_by_cmdstatus(
                platform, taskid, cmdstatus)

    @classmethod
    def is_iscoutbtask_batchcompletecount_increaced(cls, platform: str,
                                                    taskid: str, batchid: str):
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.is_iscoutbatch_complete_count_increaced(
                platform, taskid, batchid)

    @classmethod
    def increace_iscouttask_batch_complete_count(cls, platform: str,
                                                 taskid: str,
                                                 batchid: str) -> bool:
        """原子操作，提升指定Task的batchcompletecount数量-1。
        task:任务对象"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.increace_iscouttask_batch_complete_count(
                platform, taskid, batchid)

    @classmethod
    def decreace_iscouttask_batch_complete_count(cls, platform: str,
                                                 taskid: str,
                                                 batchid: str) -> bool:
        """原子操作，提升指定Task的batchcompletecount数量1。
        task:任务对象"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.decreace_iscouttask_batch_complete_count(
                platform, taskid, batchid)

    @classmethod
    def update_iscout_task(cls, platform: str, taskid: str,
                           updatefields: dict) -> bool:
        """更新指定的task，IscoutTask表总任务所有字段"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.update_iscout_task(
                platform, taskid, updatefields)

    @classmethod
    def update_iscout_task2(cls, task: IscoutTask) -> bool:
        """更新指定的task，IscoutTask表总任务所有字段"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.update_iscout_task2(task)

    @classmethod
    def get_iscouttask_sequence(cls, platform: str, taskid: str) -> int:
        """查询指定任务的所有 为指定命令状态的子任务 的数量"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.get_iscouttask_sequence(platform, taskid)

    @classmethod
    def get_iscouttask_elapsed(cls, platform: str, taskid: str) -> int:
        """查询指定任务的所有 为指定命令状态的子任务 的数量"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateIScoutTask):
            return DbManager._currdb.get_iscouttask_elapsed(platform, taskid)


######################################################
# Automated task

    @classmethod
    def get_last_automatedtask(cls, platform: str,
                               autotasktype: EAutoType) -> AutomatedTask:
        """"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.get_last_automatedtask(
                platform, autotasktype)

    @classmethod
    def save_new_autotask(cls, autotask: AutomatedTask,
                          client: Client) -> bool:
        '''存新的扫描任务'''
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.save_new_autotask(autotask, client)

    @classmethod
    def get_auto_batch_task(cls, platform: str, taskid: str, batchid: str):
        """get auto batch task"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.get_auto_batch_task(
                platform, taskid, batchid)

    @classmethod
    def get_deliverable_autotask(cls) -> iter:
        """获取待分配的任务"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.get_deliverable_autotask()

    @classmethod
    def update_automated_task(cls, platform: str, taskid: str,
                              updatefields: dict) -> bool:
        """更新指定的task，AutomatedTask表总任务所有字段"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.update_automated_task(
                platform, taskid, updatefields)

    @classmethod
    def update_automated_batch_task(cls, platform: str, taskid: str,
                                    batchid: str, updatefields: dict) -> bool:
        """更新指定的task，AutomatedTask表总任务所有字段"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.update_automated_batch_task(
                platform, taskid, batchid, updatefields)

    @classmethod
    def update_automated_task2(cls, task: IscoutTask) -> bool:
        """更新指定的task，IscoutTask表总任务所有字段"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.update_automated_task2(task)

    @classmethod
    def update_autotask_status(cls, platform: str, taskid: str,
                               cmdstatus: ECommandStatus) -> bool:
        """更新指定的task，Task表总任务状态"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.update_autotask_status(
                platform, taskid, cmdstatus)

    @classmethod
    def get_autobtask_count_by_cmdstatus(cls, platform: str, taskid: str,
                                         cmdstatus: ECommandStatus) -> int:
        """查询指定任务的所有 为指定命令状态的子任务 的数量"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.get_autobtask_count_by_cmdstatus(
                platform, taskid, cmdstatus)

    @classmethod
    def is_autobtask_batchcompletecount_increaced(cls, platform: str,
                                                  taskid: str, batchid: str):
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.is_autobatch_complete_count_increaced(
                platform, taskid, batchid)

    @classmethod
    def increace_autotask_batch_complete_count(cls, platform: str, taskid: str,
                                               batchid: str) -> bool:
        """原子操作，提升指定Task的batchcompletecount数量-1。
        task:任务对象"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.increace_autotask_batch_complete_count(
                platform, taskid, batchid)

    @classmethod
    def get_autotask_sequence(cls, platform: str, taskid: str) -> int:
        """查询指定任务的所有 为指定命令状态的子任务 的数量"""
        with cls.get_automic_locker(EDBAutomic.ReduplicateAutoTask):
            return DbManager._currdb.get_autotask_sequence(platform, taskid)
