"""db sqlite"""

# -*- coding:utf-8 -*-

import math
import os
import sqlite3
import threading
import time
import traceback

from commonbaby.helpers import helper_time
from commonbaby.mslog import MsLogger, MsLogManager
from commonbaby.sql import (SqlConn, SqliteColumn, SqliteConn,
                            SqliteConnManager, SqliteIndex, SqliteTable,
                            table_locker)

from datacontract import (AutomatedTask, AutotaskBack, AutotaskBatchBack,
                          Client, CmdFeedBack, EAutoType, ECommandStatus,
                          ETaskStatus, ETokenType, IdownCmd, IscanTask,
                          IscanTaskBack, IscoutBtaskBack, IscoutTask,
                          IscoutTaskBack, StatusBasic, StatusTask,
                          StatusTaskInfo, Task, TaskBatchBack)

from ..sqlcondition import ESqlComb, ESqlOper, SqlCondition, SqlConditions
from .sqlite_config import SqliteConfig
from .tbautomatedbatchtask import TbAutomatedBatchTask
from .tbautomatedtask import TbAutomatedTask
from .tbclient import TbClient
from .tbidownbatchtask import TbIDownBatchTask
from .tbidownbatchtoken import TbIDownBatchToken
from .tbidowncmd import TbIDownCmd
from .tbidowntask import TbIDownTask
from .tbiscantask import TbIScanTask
from .tbiscoutbatchtask import TbIScoutBatchTask
from .tbiscouttask import TbIScoutTask
from .tbsqlitebase import TbSqliteBase

__sqlite_initialed_locker = threading.RLock()
__sqlite_initialed = lambda: False


def _check_static_initial(func):
    """"""
    def check(*args, **kwargs):
        """"""

        if not callable(__sqlite_initialed):
            return func(*args, **kwargs)

        if not __sqlite_initialed():
            with __sqlite_initialed_locker:
                if not __sqlite_initialed():
                    raise Exception("需要先调用DbSqlite.static_init()后才能开始操作数据库")
        return func(*args, **kwargs)

    check.__doc__ = func.__doc__
    return check


class DbSqlite:
    """Sqlite operator"""

    _logger: MsLogger = MsLogManager.get_logger("DbSqlite")

    _static_initialed = False
    _init_locker = threading.Lock()
    _config: SqliteConfig = None

    # 各表
    __tables: dict = {}
    _tbclient: TbClient = None
    _tbidowntask: TbIDownTask = None
    _tbidownbatchtask: TbIDownBatchTask = None
    _tbidownbatchtoken: TbIDownBatchToken = None
    _tbidowncmd: TbIDownCmd = None
    _tbiscantask: TbIScanTask = None
    _tbiscouttask: TbIScoutTask = None
    _tbiscoutbatchtask: TbIScoutBatchTask = None
    _tbautotask: TbAutomatedTask = None
    _tbautobatchtask: TbAutomatedBatchTask = None

    def __init__(self):
        pass

    @staticmethod
    def static_init(cfg: SqliteConfig):
        """初始化数据库，在对数据库进行任何操作前调用。"""
        if DbSqlite._static_initialed:
            return

        with DbSqlite._init_locker:
            if DbSqlite._static_initialed:
                return
            DbSqlite._config: SqliteConfig = cfg

            # Client
            DbSqlite._tbclient = TbClient(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbclient._tbname] = DbSqlite._tbclient

            # Cmd
            DbSqlite._tbidowncmd = TbIDownCmd(DbSqlite._config)
            DbSqlite.__tables[
                DbSqlite._tbidowncmd._tbname] = DbSqlite._tbidowncmd

            # IDownTask
            DbSqlite._tbidowntask = TbIDownTask(DbSqlite._config)
            DbSqlite.__tables[
                DbSqlite._tbidowntask._tbname] = DbSqlite._tbidowntask

            DbSqlite._tbidownbatchtask = TbIDownBatchTask(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbidownbatchtask.
                              _tbname] = DbSqlite._tbidownbatchtask

            DbSqlite._tbidownbatchtoken = TbIDownBatchToken(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbidownbatchtoken.
                              _tbname] = DbSqlite._tbidownbatchtoken

            # IScanTask
            DbSqlite._tbiscantask = TbIScanTask(DbSqlite._config)
            DbSqlite.__tables[
                DbSqlite._tbiscantask._tbname] = DbSqlite._tbiscantask

            # IScoutTask
            DbSqlite._tbiscouttask = TbIScoutTask(DbSqlite._config)
            DbSqlite.__tables[
                DbSqlite._tbiscouttask._tbname] = DbSqlite._tbiscouttask

            DbSqlite._tbiscoutbatchtask = TbIScoutBatchTask(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbiscoutbatchtask.
                              _tbname] = DbSqlite._tbiscoutbatchtask

            # AutomatedTask
            DbSqlite._tbautotask = TbAutomatedTask(DbSqlite._config)
            DbSqlite.__tables[
                DbSqlite._tbautotask._tbname] = DbSqlite._tbautotask

            DbSqlite._tbautobatchtask = TbAutomatedBatchTask(DbSqlite._config)
            DbSqlite.__tables[
                DbSqlite._tbautobatchtask._tbname] = DbSqlite._tbautobatchtask

            DbSqlite._static_initialed = True

    @staticmethod
    @_check_static_initial
    def _get_table_manager(tbname: str) -> TbSqliteBase:
        """根据tbname查找sqliteconnmanager"""
        if not isinstance(
                tbname, str
        ) or tbname == "" or not DbSqlite.__tables.__contains__(tbname):
            raise Exception("Invalid table name: {}".format(tbname))
        return DbSqlite.__tables[tbname]

    @staticmethod
    @_check_static_initial
    def connect_write(tbname: str, timeout=None) -> SqlConn:
        """获取sqlite可用于增删改的链接"""
        conn_mngr = DbSqlite._get_table_manager(tbname)
        return conn_mngr.connect_write(timeout)

    @staticmethod
    @_check_static_initial
    def connect_all(tbname: str, timeout=None) -> iter:
        """获取sqlite所有数据库链接"""
        conn_mngr = DbSqlite._get_table_manager(tbname)
        return conn_mngr.connect_all(timeout)

    @staticmethod
    @_check_static_initial
    def execute_search_one(tbname: str, sql: str,
                           params: tuple = None) -> sqlite3.Row:
        """执行增删改这种修改操作"""
        conn_mngr = DbSqlite._get_table_manager(tbname)
        return conn_mngr.execute_search_one(tbname, sql, params)

    @staticmethod
    @_check_static_initial
    def execute_search_all(self,
                           tbname: str,
                           sql: str,
                           return_with_conn: bool = False,
                           params: tuple = None) -> iter:
        """执行增删改这种修改操作\n
        return_with_conn: 是否将结果与对应的数据库链接一并返回，默认为False"""
        conn_mngr = DbSqlite._get_table_manager(tbname)
        return conn_mngr.execute_search_all(tbname, sql, return_with_conn,
                                            params)

    @staticmethod
    @_check_static_initial
    def execute_modify(tbname: str, sql: str, params: tuple = None) -> bool:
        """执行增删改这种修改操作"""
        conn_mngr = DbSqlite._get_table_manager(tbname)
        return conn_mngr.execute_modify(tbname, sql, params)

######################################################
# ClientStatus

    @staticmethod
    @_check_static_initial
    def save_client_status_basic(client: StatusBasic) -> bool:
        """保存采集端基础状态"""
        return DbSqlite._tbclient.save_client_status_basic(client)

    @staticmethod
    @_check_static_initial
    def save_client_status_task(client: StatusTask):
        """保存采集端基础状态数据"""
        return DbSqlite._tbclient.save_client_status_task(client)

    @staticmethod
    @_check_static_initial
    def get_client_status(clientid: str) -> Client:
        """获取指定采集端任务状态数据"""
        fields: dict = DbSqlite._tbclient.get_client_status(clientid)
        if not isinstance(fields, dict) or len(fields) < 1:
            return None
        res: Client = Client(StatusBasic(fields), StatusTask(fields))
        return res

    @staticmethod
    def get_client_status_all(interval: float = 15) -> iter:
        """获取所有采集端任务状态数据。\n
        interval: 指定心跳间隔，即只读取最近n秒内更新的采集端状态，单位秒。"""
        return DbSqlite._tbclient.get_client_status_all(interval=interval)

    @staticmethod
    @_check_static_initial
    def get_client_by_search_token(
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
        res: Client = None
        conds: SqlConditions = SqlConditions()
        DbSqlite._apend_conds(
            conds, 'TokenType',
            None if not isinstance(tokentype, ETokenType) else tokentype.value)
        DbSqlite._apend_conds(conds, 'Input', input_)
        DbSqlite._apend_conds(conds, 'PreGlobalTelCode', preglobaltelcode)
        DbSqlite._apend_conds(conds, 'PreAccount', preaccount)
        DbSqlite._apend_conds(conds, 'GlobalTelCode', globaltelcode)
        DbSqlite._apend_conds(conds, 'Phone', phone)
        DbSqlite._apend_conds(conds, 'Account', account)
        DbSqlite._apend_conds(conds, 'Password', password)
        DbSqlite._apend_conds(conds, 'Url', url)
        DbSqlite._apend_conds(conds, 'Host', host)
        DbSqlite._apend_conds(conds, 'Cookie', cookie)
        if conds.cond_count < 1:
            return res

        for tfields in DbSqlite._tbidownbatchtoken.select_token(conds):
            tokenid: str = tfields['tokenid']
            bfields: dict = DbSqlite._tbidownbatchtask.get_batch_task(
                SqlConditions(
                    SqlCondition('Platform', platform),
                    SqlCondition('Apptype', apptype),
                    SqlCondition('TokenId', tokenid),
                ))
            if not isinstance(bfields, dict) or len(
                    bfields) < 1 or not bfields.__contains__('clientid'):
                continue
            res: Client = DbSqlite.get_client_status(bfields['clientid'])
            if not isinstance(res, Client):
                res = None
                return res
            return res

######################################################
# IDownTask

    @staticmethod
    @_check_static_initial
    def save_new_idown_task(
            task: Task,
            client: Client,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend) -> bool:
        """保存/插入新来的任务"""
        if not isinstance(task, Task):
            DbSqlite._logger.error("Invalid task object: {}".format(task))
            return False

        if not isinstance(task.batchid, str) or task.batchid == "":
            DbSqlite._logger.error("Invalid task batchid: {}".format(task))
            return False

        if not isinstance(task.tokenid, str) or task.batchid == "":
            DbSqlite._logger.error("Invalid task tokenid: {}".format(task))
            return False

        isnewtask: bool = False
        # 查询已存在task的总任务数，
        bcount: int = DbSqlite._tbidowntask.get_task_batch_total_count(task)
        if bcount == -1:
            isnewtask = True
            # -1表示没找到指定Task，表示是新来的任务，令其拥有一个子任务
            task.batchtotalcount = 1
        else:
            # 否则其子任务数等于库中任务数
            task.batchtotalcount = bcount

        # 先存入token
        if not DbSqlite._tbidownbatchtoken.save_new_idownbatchtoken(task):
            DbSqlite._logger.error(
                "Save task token failed:\ntaskid:{}\ntokenid:{}".format(
                    task.taskid, task.tokenid))
            return False

        # 然后存 cmd
        if isinstance(
                task.cmd,
                IdownCmd) and not DbSqlite._tbidowncmd.save_new_idowncmd(
                    task.platform, client, task.cmd, task.time,
                    ECommandStatus.WaitForSend, task.taskid, task.batchid, 1):
            return False

        # 有了tokenid再存 batchid
        succ, isnewbatchtask = DbSqlite._tbidownbatchtask.save_new_idownbatchtask(
            task, client)
        if not succ:
            DbSqlite._logger.error(
                "Save task batch task failed:\ntaskid:{}\nbatchid:{}".format(
                    task.taskid, task.batchid))
            return False

        # 如果是新增的子任务，那么batchtotalcount要加1
        if not isnewtask and isnewbatchtask:
            task.batchtotalcount += 1

        # 最后存入IDownTask表，
        if isnewtask:
            # 新任务插入
            if not DbSqlite._tbidowntask.save_new_idown_task(task):
                DbSqlite._logger.error(
                    "Save idown task failed, insert new task failed:\ntaskid:{}"
                    .format(task.taskid))
                return False
        else:
            # 已有任务更新batchtotalcount
            if not DbSqlite._tbidowntask.update_task_batch_total_count(task):
                DbSqlite._logger.error(
                    "Save idown task failed, update batchtotalcount failed:\ntaskid:{}"
                    .format(task.taskid))
                return False
            # 如果不是新的子任务，需要做重置处理，因为要符合用户操作，他可能来完全相同的重复任务
            if not isnewbatchtask:
                task: Task = task
                # 根据情况，将 batchcompletecount-1，并重置batch_complete_count_increaced_flag标记
                if DbSqlite._tbidownbatchtask.is_batch_complete_count_increaced(
                        task._platform, task.taskid, task.batchid):
                    if not DbSqlite._tbidowntask.increace_task_batch_complete_count(
                            task._platform, task.taskid, -1):
                        DbSqlite._logger.error(
                            "Decreace task batch_complete_count failed:\ntaskid:{}"
                            .format(task.taskid))
                        return False
                    if not DbSqlite._tbidownbatchtask.update_batch_complete_count_increaced_flag(
                            task._platform, task.taskid, task.batchid, False):
                        DbSqlite._logger.error(
                            "Set task batch_complete_count_increaced_flag failed:\ntaskid:{}\nbatchid:{}"
                            .format(task.taskid, task.batchid))
                        return False
                # 计算 并更新 Task 表当前Task的Progress等字段？
                oldtaskfields: dict = DbSqlite._tbidowntask.get_task(
                    SqlConditions(SqlCondition('TaskId', task.taskid),
                                  SqlCondition('Platform', task._platform)))
                if not isinstance(oldtaskfields,
                                  dict) or len(oldtaskfields) < 1:
                    DbSqlite._logger.error(
                        "Get exist Task failed:\ntaskid:{}\nbatchid:{}".format(
                            task.taskid, task.batchid))
                    return False
                oldtask: Task = Task(oldtaskfields)
                oldtask.progress = math.floor(
                    oldtask.batchcompletecount / oldtask.batchtotalcount *
                    100) / 100
                oldtask.cmdrcvmsg = ''
                oldtask.sequence_reset()
                oldtask.cmdstatus = ECommandStatus.WaitForSend
                if not DbSqlite.update_idown_task2(oldtask):
                    DbSqlite._logger.error(
                        "Update exist Task failed:\ntaskid:{}\nbatchid:{}".
                        format(task.taskid, task.batchid))
                    return False

        return True

    @staticmethod
    @_check_static_initial
    def get_parent_clientid_of_task(task: Task) -> Client:
        """获取 指定task的父任务被分配到的采集端 Client对象"""
        res: str = DbSqlite._tbidownbatchtask.get_parent_clientid_of_task(task)
        return res

    @staticmethod
    @_check_static_initial
    def get_parent_client_of_task(task: Task) -> Client:
        """获取 指定task的父任务被分配到的采集端 Client对象"""
        res: Client = None
        clientid: str = DbSqlite._tbidownbatchtask.get_parent_clientid_of_task(
            task)
        if clientid is None:
            return res
        fields = DbSqlite._tbclient.get_client_status(clientid)
        if not isinstance(fields, dict) or len(fields) < 1:
            return res

        res: Client = Client(StatusBasic(fields), StatusTask(fields))
        return res

    @staticmethod
    @_check_static_initial
    def get_task_cmdstatus(task: Task) -> ECommandStatus:
        """获取指定总任务id的命令状态"""
        return DbSqlite._tbidowntask.get_task_cmdstatus(task)

    @staticmethod
    @_check_static_initial
    def get_task_by_taskid(taskid: str) -> Task:
        """获取指定任务id的命令状态"""
        for fields in DbSqlite._tbidowntask.get_tasks(
                SqlConditions(SqlCondition('TaskId', taskid))):
            try:
                task: Task = Task(fields)
                return task
            except Exception as ex:
                raise ex
        return None

    @staticmethod
    @_check_static_initial
    def get_task_by_search_token(
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
        conds: SqlConditions = SqlConditions()
        DbSqlite._apend_conds(
            conds, 'TokenType',
            None if not isinstance(tokentype, ETokenType) else tokentype.value)
        DbSqlite._apend_conds(conds, 'Input', input_)
        DbSqlite._apend_conds(conds, 'PreGlobalTelCode', preglobaltelcode)
        DbSqlite._apend_conds(conds, 'PreAccount', preaccount)
        DbSqlite._apend_conds(conds, 'GlobalTelCode', globaltelcode)
        DbSqlite._apend_conds(conds, 'Phone', phone)
        DbSqlite._apend_conds(conds, 'Account', account)
        DbSqlite._apend_conds(conds, 'Password', password)
        DbSqlite._apend_conds(conds, 'Url', url)
        DbSqlite._apend_conds(conds, 'Host', host)
        DbSqlite._apend_conds(conds, 'Cookie', cookie)
        if conds.cond_count < 1:
            return

        for tfields in DbSqlite._tbidownbatchtoken.select_token(conds):
            tokenid: str = tfields['tokenid']
            bfields: dict = DbSqlite._tbidownbatchtask.get_batch_task(
                SqlConditions(
                    SqlCondition('Platform', platform),
                    SqlCondition('Apptype', apptype),
                    SqlCondition('TokenId', tokenid),
                ))
            if not isinstance(bfields, dict) or len(bfields) < 1:
                continue

            tafields: dict = DbSqlite._tbidowntask.get_task(
                SqlConditions(SqlCondition('TaskId', bfields['taskid']),
                              SqlCondition('Platform', bfields['platform'])))
            if not isinstance(tafields, dict) or len(tafields) < 1:
                continue

            tafields.update(bfields)
            tafields.update(tfields)
            res = Task(tafields)
            return res

    @staticmethod
    @_check_static_initial
    def get_deliverable_task() -> iter:
        """查询所有待分配的任务"""
        # IDownTask表
        for fieldstask in DbSqlite._tbidowntask.get_tasks(
                SqlConditions(
                    SqlCondition('CmdStatus',
                                 ECommandStatus.WaitForSend.value))):
            if not isinstance(fieldstask, dict) or len(fieldstask) < 1:
                continue

            taskid = fieldstask['taskid']
            platform = fieldstask['platform']

            # IDownBatchTask表
            for fieldsbtask in DbSqlite._tbidownbatchtask.get_batch_tasks(
                    SqlConditions(
                        SqlCondition('TaskId', taskid),
                        SqlCondition('Platform', platform),
                        SqlCondition('CmdStatus',
                                     ECommandStatus.WaitForSend.value))):

                if not isinstance(fieldsbtask, dict) or len(fieldsbtask) < 1:
                    continue

                fieldsbtask.update(fieldstask)
                tokenid = fieldsbtask['tokenid']
                cmdid = fieldsbtask['cmdid']

                # IDownBatchToken表，此处只取第一个结果
                for fieldstoken in DbSqlite._tbidownbatchtoken.select_token(
                        SqlConditions(SqlCondition('TokenId', tokenid))):

                    if not isinstance(fieldstoken,
                                      dict) or len(fieldstoken) < 1:
                        continue

                    fieldstoken: dict = fieldstoken
                    fieldsbtask.update(fieldstoken)

                    #这里只取第一行数据，所以直接break
                    break

                # IDownCmd表，取第一条
                if not cmdid is None:
                    fieldscmd = DbSqlite._tbidowncmd.select_cmd(
                        SqlConditions(SqlCondition("CmdId", cmdid),
                                      SqlCondition("Platform", platform)))
                    fieldscmd: dict = fieldscmd
                    if isinstance(fieldscmd,dict) and len(fieldscmd)>0:
                        isre = fieldscmd.get("isrelative")
                        if not isre is None and isre == 1:
                            fieldsbtask.update(fieldscmd)

                tsk: Task = Task(fieldsbtask)

                yield tsk

    @staticmethod
    @_check_static_initial
    def get_batch_task_count_by_cmdstatus(task: Task,
                                          cmdstatus: ECommandStatus) -> int:
        """查询指定任务的所有 为指定命令状态的子任务 的数量"""
        return DbSqlite._tbidownbatchtask.get_batch_task_count_by_cmdstatus(
            task, cmdstatus)

    @staticmethod
    @_check_static_initial
    def update_idown_task(task: Task) -> bool:
        """更新IDownTask表，根据platform,taskid更新其他所有字段，并重置task.sequence序列"""
        return DbSqlite._tbidowntask.update_idown_task(task)

    @staticmethod
    @_check_static_initial
    def update_idown_task2(task: Task) -> bool:
        """更新指定的task，IDownTask表总任务的其他所有字段"""
        return DbSqlite._tbidowntask.update_idown_task2(task)

    @staticmethod
    @_check_static_initial
    def update_idown_task_status(task: Task,
                                 cmdstatus: ECommandStatus) -> bool:
        """更新指定的task，IDownTask表总任务状态"""
        return DbSqlite._tbidowntask.update_idown_task_status(task, cmdstatus)

    @staticmethod
    @_check_static_initial
    def increace_task_batch_complete_count(platform: str, taskid: str,
                                           batchid: str) -> bool:
        """原子操作，提升指定Task的batchcompletecount数量1。
        task:任务对象"""
        res: bool = True
        try:
            # 暂时先这么写了，
            # 后面如果需要实现原子操作，需要：
            # 1. 查询原 batchcompletecount 值并记录
            # 2. 尝试 加1，失败返回False
            # 3. 尝试 设置update_batch_complete_count_increaced_flag为True，
            #   失败需要将 batchcompletecount 回滚-1，并返回False
            # 4. 都成功，返回True
            if not DbSqlite._tbidowntask.increace_task_batch_complete_count(
                    platform, taskid, 1):
                res = False
                return res

            if not DbSqlite._tbidownbatchtask.update_batch_complete_count_increaced_flag(
                    platform, taskid, batchid, True):
                res = False
                return res

        except Exception as ex:
            res = False
            raise ex
        return res

######################################################
# IDownBatchTask

    @staticmethod
    @_check_static_initial
    def get_batch_tasks(platform: str, taskid: str) -> iter:
        """搜索指定TaskId下的所有子任务，返回Task任务对象典迭代器"""
        for tfields in DbSqlite._tbidowntask.get_tasks(
                SqlConditions(SqlCondition('Platform', platform),
                              SqlCondition('TaskId', taskid))):
            if not isinstance(tfields, dict) or len(tfields) < 1:
                continue

            for bfields in DbSqlite._tbidownbatchtask.get_batch_tasks(
                    SqlConditions(SqlCondition('TaskId', taskid))):
                tfields.update(bfields)
                tb: TaskBatchBack = TaskBatchBack.create_from_dict(tfields)
                yield tb

    @staticmethod
    @_check_static_initial
    def get_batch_task(platform: str, taskid: str, batchid: str) -> Task:
        """根据taskid、batchid、platform查询并返回第一个匹配的Task对象"""
        res: Task = None
        tfields: dict = DbSqlite._tbidowntask.get_task(
            SqlConditions(SqlCondition('Platform', platform),
                          SqlCondition('TaskId', taskid)))
        if not isinstance(tfields, dict) or len(tfields) < 1:
            return res
        bfields = DbSqlite._tbidownbatchtask.get_batch_task(
            SqlConditions(
                SqlCondition('Platform', platform),
                SqlCondition('TaskId', taskid),
                SqlCondition('BatchId', batchid),
            ))
        if not isinstance(bfields, dict) or len(bfields) < 1:
            return res
        tfields.update(bfields)
        res = Task(tfields)
        return res

    @staticmethod
    @_check_static_initial
    def update_batchtask_status(platform: str, taskid: str, batchid: str,
                                cmdstatus: ECommandStatus) -> bool:
        """更新batchtask命令状态"""
        # 来的必然是子任务，先更新 BatchTask表
        if not DbSqlite._tbidownbatchtask.update_batchtask_status(
                platform, taskid, batchid, cmdstatus):
            return False
        return True

    @staticmethod
    @_check_static_initial
    def update_batchtask_client(platform: str, taskid: str, batchid: str,
                                clientid: str) -> bool:
        """更新batchtask被分配到的采集端"""
        # 来的必然是子任务，先更新 BatchTask表
        if not DbSqlite._tbidownbatchtask.update_batchtask_client(
                platform, taskid, batchid, clientid):
            return False
        return True

    @staticmethod
    @_check_static_initial
    def update_batchtask_back(tb: TaskBatchBack) -> bool:
        """根据给予的采集端子任务状态数据 TaskBatchBack 更新数据库子任务状态"""
        return DbSqlite._tbidownbatchtask.update_batchtask_back(tb)

    @staticmethod
    @_check_static_initial
    def get_task_batch_complete_count(task: Task) -> bool:
        """获取指定（子）任务的taskid对应的任务的
        batchcompletecount（子任务已完成数量），
        此方法为原子操作。"""
        return DbSqlite._tbidowntask.get_task_batch_complete_count(task)

    @staticmethod
    @_check_static_initial
    def is_batch_complete_count_increaced(platform: str, taskid: str,
                                          batchid: str) -> bool:
        """返回 指定的子任务完成情况 是否已更新到 总任务表的 batchcompletecount 字段"""
        return DbSqlite._tbidownbatchtask.is_batch_complete_count_increaced(
            platform, taskid, batchid)

######################################################
# IDownCmd

    @staticmethod
    @_check_static_initial
    def save_new_idown_cmd(
            platform: str,
            clients: list,
            cmd: IdownCmd,
            cmdtime: float,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
            taskid: str = None,
            batchid: str = None,
            isrelative: int = 1,
    ) -> bool:
        res: bool = True
        # platform: str,
        # client: Client,
        # command: IdownCmd,
        # cmdtime: float,
        # cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
        # taskid: str = None,
        # batchid: str = None
        for client in clients.values():
            if not isinstance(client, Client):
                continue

            if not DbSqlite._tbidowncmd.save_new_idowncmd(
                    cmd.platform, client, cmd, cmdtime, cmdstatus, taskid,
                    batchid, isrelative):
                res = False

        return res

    @staticmethod
    @_check_static_initial
    def get_deliverable_cmd() -> iter:
        """获取需要下发的，独立的，非绑定到task一起的cmd任务"""
        for fieldscmd in DbSqlite._tbidowncmd.select_cmds(
                SqlConditions(
                    SqlCondition(colname="Status",
                                 val=ECommandStatus.WaitForSend.value),
                    SqlCondition(colname='IsRelative', val=0),
                )):
            if not isinstance(fieldscmd, dict) or len(fieldscmd) < 1:
                continue

            # 查看是否有task绑定了当前cmd，若绑定了则continue，
            # 没绑定的才返回
            cmdid = fieldscmd['cmdid']
            btaskfields: dict = DbSqlite._tbidownbatchtask.get_batch_task(
                SqlConditions(SqlCondition("CmdId", cmdid)))
            if not btaskfields is None and not len(btaskfields) > 0:
                continue

            # 返回独立的cmd
            cmd: IdownCmd = IdownCmd.parse_from_dict(fieldscmd)

            yield cmd

    @staticmethod
    @_check_static_initial
    def update_cmd(cmd: IdownCmd, taskid: str = None,
                   batchid: str = None) -> bool:
        return DbSqlite._tbidowncmd.update_cmd(cmd, taskid, batchid)

    @staticmethod
    @_check_static_initial
    def update_cmd_status(platform: str, cmdid: str, clientid: str,
                          cmdstatus: ECommandStatus) -> bool:
        return DbSqlite._tbidowncmd.update_cmd_status(platform, cmdid,
                                                      clientid, cmdstatus)

    @staticmethod
    @_check_static_initial
    def update_cmdback(cmdback: CmdFeedBack) -> bool:
        return DbSqlite._tbidowncmd.update_cmdback(cmdback)

    @staticmethod
    @_check_static_initial
    def get_cmd_merge_status(cmdid: str, platform: str) -> ECommandStatus:
        """返回合并的cmd执行状态，返回None表示没有搜索到目标Cmd"""
        res: ECommandStatus = None

        cmds: list = []
        succount = 0
        for cmd in DbSqlite._tbidowncmd.select_cmds(
                SqlConditions(
                    SqlCondition(colname='CmdId', val=cmdid),
                    SqlCondition(colname='Platform', val=platform),
                )):
            cmd: IdownCmd = IdownCmd.parse_from_dict(cmd)
            cmds.append(cmd)

            if cmd.cmdstatus == ECommandStatus.Failed or \
                cmd.cmdstatus == ECommandStatus.Timeout:
                # 有一个失败算全失败
                res = ECommandStatus.Failed
                break
            elif cmd.cmdstatus == ECommandStatus.Dealing or \
                cmd.cmdstatus == ECommandStatus.Progress:
                res = ECommandStatus.Dealing
            elif cmd.cmdstatus == ECommandStatus.Succeed:
                succount = succount + 1

        if succount >= len(cmds):
            res = ECommandStatus.Succeed

        return res

    @staticmethod
    def search_task_by_cmd_target(cmd: IdownCmd) -> object:
        """
        搜索目标target所在的任务（idownbatchtask/iscantask/iscouttask），没找到返回None
        """
        res: Task = None

        cmd: IdownCmd = cmd
        if cmd is None or cmd.target is None or len(cmd.target) < 1:
            return res

        # tasktype不为空时
        if isinstance(cmd.target.tasktype, int):
            # IDownTask任务
            if cmd.target.tasktype == 1:
                if cmd.target.taskid is None or cmd.target.batchid is None:
                    return res

                fields = DbSqlite._tbidownbatchtask.get_batch_task(
                    SqlConditions(
                        SqlCondition(colname='Platform', val=cmd.platform),
                        SqlCondition(colname='TaskId', val=cmd.target.taskid),
                        SqlCondition(colname='BatchId',
                                     val=cmd.target.batchid)))
                if not isinstance(
                        fields,
                        dict) or len(fields) < 1 or not fields.__contains__(
                            'tokenid') or not isinstance(
                                fields['tokenid'], str):
                    return res
                tokenid = fields['tokenid']
                fieldstoken = DbSqlite._tbidownbatchtoken.select_token_one(
                    SqlConditions(SqlCondition(colname='TokenId',
                                               val=tokenid)))
                if not isinstance(fieldstoken, dict) or len(fieldstoken) < 1:
                    return res
                fields.update(fieldstoken)
                fieldsbtask: dict = DbSqlite._tbidowntask.get_task(
                    SqlConditions(
                        SqlCondition(colname='TaskId', val=cmd.target.taskid)))
                if not isinstance(fieldsbtask, dict) or len(fieldsbtask) < 1:
                    return res
                fields.update(fieldsbtask)
                res = Task(fields)
            # IScanTask任务
            elif cmd.target.tasktype == 2:
                return res
            # IScoutTask任务
            elif cmd.target.tasktype == 3:
                return res
        # apptype不为空时，是对某个账号设置
        elif isinstance(cmd.target.apptype, int):
            fieldstoken: dict = None
            if isinstance(cmd.target.account, str):
                fieldstoken = DbSqlite._tbidownbatchtoken.select_token_one(
                    SqlConditions(
                        SqlCondition(colname='Account',
                                     val=cmd.target.account), ))
            elif isinstance(cmd.target.phone, str):
                fieldstoken = DbSqlite._tbidownbatchtoken.select_token_one(
                    SqlConditions(
                        SqlCondition(colname='Phone', val=cmd.target.phone), ))

            if fieldstoken is None or not fieldstoken.__contains__('tokenid'):
                return res
            tokenid = fieldstoken['tokenid']
            fieldsbtask = DbSqlite._tbidownbatchtask.get_batch_task(
                SqlConditions(
                    SqlCondition(colname='AppType', val=cmd.target.apptype),
                    SqlCondition(colname='Platform', val=cmd.platform),
                    SqlCondition(colname='TokenId', val=tokenid)))
            if fieldsbtask is None or len(fieldsbtask) < 1:
                return res
            fieldsbtask.update(fieldstoken)

            taskid: str = fieldsbtask['taskid']
            fieldstask: dict = DbSqlite._tbidowntask.get_task(
                SqlConditions(SqlCondition(colname='TaskId', val=taskid)))
            if not isinstance(fieldstask, dict) or len(fieldstask) < 1:
                return res
            fieldsbtask.update(fieldstask)
            res = Task(fieldsbtask)
        return res

######################################################
# IScanTask

    @staticmethod
    @_check_static_initial
    def get_deliverable_iscantask() -> bool:
        '''获取代分发的IScanTask'''
        for fieldsscan in DbSqlite._tbiscantask.execute_search_all(
                tablename="IScanTask",
                sql='''select * from IScanTask where 
        Status=2 and (EndTime is Null or EndTime>?)''',
                params=(helper_time.ts_since_1970_tz(), )):

            if not isinstance(fieldsscan, dict) or len(fieldsscan) < 1:
                continue

            # 拿cmd
            cmdid = fieldsscan['cmdid']
            cmdfields: dict = DbSqlite._tbidowncmd.select_cmd(
                SqlConditions(SqlCondition(colname="CmdId", val=cmdid)))
            if not isinstance(cmdfields, dict) or len(cmdfields) < 1:
                # raise Exception(
                #     "Cmd for IScanTask not found: scantaskid:{}".format(
                #         fieldsscan['taskid']))
                continue

            fieldsscan.update(cmdfields)
            scantask: IscanTask = IscanTask(fieldsscan)

            yield scantask

    @staticmethod
    @_check_static_initial
    def get_deliverable_iscantask2() -> bool:
        '''获取代分发的IScanTask'''
        for fieldsscan in DbSqlite._tbiscantask.execute_search_all(
                tablename="IScanTask",
                sql='''select * from IScanTask where 
                        IsPeriod=1 and PeriodNum>=1 and 
                        (Status!=3 and Status!=4) and 
                        (EndTime is Null or EndTime>?)''',
                params=(helper_time.ts_since_1970_tz(), )):

            if not isinstance(fieldsscan, dict) or len(fieldsscan) < 1:
                continue

            # taskid = fieldsscan['taskid']
            platform = fieldsscan['platform']

            # 拿cmd
            cmdid = fieldsscan['cmdid']
            cmdfields: dict = DbSqlite._tbidowncmd.select_cmd(
                SqlConditions(
                    SqlCondition(colname="CmdId", val=cmdid),
                    SqlCondition("Platform", platform),
                    SqlCondition("IsRelative", 1),
                ))
            if isinstance(cmdfields, dict) and len(cmdfields) > 1:
                fieldsscan.update(cmdfields)

            scantask: IscanTask = IscanTask(fieldsscan)

            yield scantask

    @staticmethod
    @_check_static_initial
    def save_new_iscantask(
            client: Client,
            scantask: IscanTask,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
    ) -> bool:
        """"""
        if not isinstance(scantask, IscanTask):
            raise Exception("Invalid IScanTask for saving to db:{}".format(
                type(scantask).__name__))
        if not isinstance(scantask.cmd_id, str) or not isinstance(
                scantask.cmd, IdownCmd):
            raise Exception(
                "Invalid IDownCmd in IScanTask for saving to db:{}".format(
                    scantask.cmd))

        res: bool = DbSqlite._tbiscantask.save_new_iscantask(
            client, scantask, cmdstatus)
        if not res:
            return res

        scantask: IscanTask = scantask
        res = DbSqlite._tbidowncmd.save_new_idowncmd(
            scantask._platform, client, scantask.cmd, scantask.createtime,
            ECommandStatus.WaitForSend, scantask.taskid)
        return res

    @staticmethod
    @_check_static_initial
    def get_iscantask(platform: str, taskid: str) -> IscanTask:
        if not isinstance(platform, str):
            raise Exception("Condition Platform cannot be None")
        if not isinstance(taskid, str):
            raise Exception("Condition TaskId cannot be None")
        scantaskfields: dict = DbSqlite._tbiscantask.select_iscantask(
            SqlConditions(
                SqlCondition(colname='Platform', val=platform),
                SqlCondition(colname='TaskId', val=taskid),
            ))
        if not isinstance(scantaskfields, dict) or len(scantaskfields) < 1:
            return None

        cmdid: str = scantaskfields['cmdid']
        if isinstance(cmdid, str) and not cmdid == "":
            cmdfields: dict = DbSqlite._tbidowncmd.select_cmd(
                SqlConditions(
                    SqlCondition(colname="CmdId", val=cmdid),
                    SqlCondition("Platform", platform),
                    SqlCondition("IsRelative", 1),
                ))
            if isinstance(cmdfields, dict) and len(cmdfields) > 1:
                # status不要被覆盖了
                cmdfields.update(scantaskfields)
                # taskstatus = scantaskfields.get("status")
                # sequence = scantaskfields.get("sequence")
                # scantaskfields.update(cmdfields)
                # scantaskfields["status"] = taskstatus
                # 就知道status不能被覆盖了，那TM sequence也不能被覆盖了3
                # scantaskfields["sequence"] = sequence

        task: IscanTask = IscanTask(cmdfields, platform)
        return task

    @staticmethod
    @_check_static_initial
    def get_iscantasks(conds: SqlConditions) -> IscanTask:
        for scantaskfields in DbSqlite._tbiscantask.select_iscantasks(conds):
            if not isinstance(scantaskfields, dict) or len(scantaskfields) < 1:
                return None
            cmdid: str = scantaskfields['cmdid']
            platform: str = scantaskfields['platform']
            if isinstance(cmdid, str) and not cmdid == "":
                cmdfields: dict = DbSqlite._tbidowncmd.select_cmd(
                    SqlConditions(
                        SqlCondition(colname="CmdId", val=cmdid),
                        SqlCondition("Platform", platform),
                        SqlCondition("IsRelative", 1),
                    ))
                if isinstance(cmdfields, dict) and len(cmdfields) > 1:
                    scantaskfields.update(cmdfields)

            task: IscanTask = IscanTask(scantaskfields)
            yield task

    @staticmethod
    @_check_static_initial
    def update_iscantask_status(
            platform: str,
            taskid: str,
            cmdstatus: ECommandStatus,
    ):
        return DbSqlite._tbiscantask.update_iscantask_status(
            platform, taskid, cmdstatus)

    @staticmethod
    @_check_static_initial
    def update_iscantask(scantask: IscanTask):
        return DbSqlite._tbiscantask.update_iscantask(scantask)

    @staticmethod
    @_check_static_initial
    def update_iscantask2(platform: str, taskid: str, updatefields: dict):
        return DbSqlite._tbiscantask.update_iscantask2(platform, taskid,
                                                       updatefields)

    @staticmethod
    @_check_static_initial
    def update_iscantask_back(scantaskback: IscanTaskBack):
        return DbSqlite._tbiscantask.update_iscantask_back(scantaskback)

######################################################
# IScoutTask/IScoutBatchTask

    @staticmethod
    @_check_static_initial
    def save_new_iscouttask(task: IscoutTask, client: Client):
        '''存IScoutTask，到IScoutTask表和IScoutBatchTask表'''
        if not isinstance(task, IscoutTask):
            raise Exception(
                "Invalid IScoutTask for saving to db:{}".format(task))

        isnewtask: bool = False
        # 查询已存在task的总任务数，
        bcount: int = DbSqlite._tbiscouttask.get_iscouttask_batch_total_count(
            task._platform, task.taskid)
        if bcount == -1:
            isnewtask = True
            # -1表示没找到指定Task，表示是新来的任务，令其拥有一个子任务
            task.batchtotalcount = 1
        else:
            # 否则其子任务数等于库中任务数
            task.batchtotalcount = bcount

        # 然后存 cmd
        if isinstance(task.cmd_id,
                      str) and not task.cmd_id is None and isinstance(
                          task.cmd, IdownCmd):
            if not DbSqlite._tbidowncmd.save_new_idowncmd(
                    task.platform, client, task.cmd, task.createtime,
                    ECommandStatus.WaitForSend, task.taskid, task.batchid, 1):
                return False

        # 同步子任务的周期数为总任务的周期数
        taskfields: dict = DbSqlite._tbiscouttask.select_iscouttask(
            SqlConditions(SqlCondition('TaskId', task.taskid),
                          SqlCondition('Platform', task._platform)))
        periodnum: int = 1
        if isinstance(taskfields,
                      dict) and taskfields.__contains__("periodnum"):
            periodnum = taskfields["periodnum"]
        task.periodnum = periodnum
        succ, isnewbatchtask = DbSqlite._tbiscoutbatchtask.save_new_iscoutbtask(
            task, client, ECommandStatus.WaitForSend)
        if not succ:
            DbSqlite._logger.error(
                "Save iscout batch task failed:\ntaskid:{}\nbatchid:{}".format(
                    task.taskid, task.batchid))
            return False

        # 如果是新增的子任务，那么batchtotalcount要加1
        if not isnewtask and isnewbatchtask:
            task.batchtotalcount += 1

        # 最后存入IDownTask表，
        if isnewtask:
            # 新任务插入
            if not DbSqlite._tbiscouttask.save_new_iscouttask(
                    task, ECommandStatus.WaitForSend):
                DbSqlite._logger.error(
                    "Save iscout task failed, insert new task failed:\ntaskid:{}"
                    .format(task.taskid))
                return False
        else:
            bcompletecount: int = DbSqlite._tbiscouttask.get_iscouttask_batch_complete_count(
                task._platform, task.taskid)
            if not DbSqlite._tbiscouttask.update_iscouttask3(
                    task._platform,
                    task.taskid,
                {
                    'Status': ECommandStatus.WaitForSend.value,
                    'BatchTotalCount': task.batchtotalcount,
                    'BatchCompleteCount': 0,
                    # 现在是直接重置idowntask的进度，因为要全部重新下发
                    'Progress': 0,  # bcompletecount / task.batchtotalcount,
                    'CmdRcvMsg': '',
                }):
                DbSqlite._logger.error(
                    "Save iscout task failed, update iscouttask failed:\ntaskid:{}"
                    .format(task.taskid))
                return False

            # DbSqlite._tbiscouttask.update_iscouttask2()
            # 如果不是新的子任务，需要做重置处理，因为要符合用户操作，他可能来完全相同的重复任务
            if not isnewbatchtask:
                task: IscoutTask = task
                # 根据情况，将 batchcompletecount-1，并重置batch_complete_count_increaced_flag标记
                if DbSqlite._tbiscoutbatchtask.is_iscoutbatch_complete_count_increaced(
                        task._platform, task.taskid, task.batchid):
                    if not DbSqlite._tbiscouttask.increace_iscouttask_batch_complete_count(
                            task._platform, task.taskid, -1):
                        DbSqlite._logger.error(
                            "Decreace iscouttask batch_complete_count failed:\ntaskid:{}"
                            .format(task.taskid))
                        return False
                    if not DbSqlite._tbiscoutbatchtask.update_batch_complete_count_increaced_flag(
                            task._platform, task.taskid, task.batchid, False):
                        DbSqlite._logger.error(
                            "Set iscouttask batch_complete_count_increaced_flag failed:\ntaskid:{}\nbatchid:{}"
                            .format(task.taskid, task.batchid))
                        return False
                # 计算 并更新 Task 表当前Task的Progress等字段？
                oldtaskfields: dict = DbSqlite._tbiscouttask.select_iscouttask(
                    SqlConditions(SqlCondition('TaskId', task.taskid),
                                  SqlCondition('Platform', task._platform)))
                if not isinstance(oldtaskfields,
                                  dict) or len(oldtaskfields) < 1:
                    DbSqlite._logger.error(
                        "Get exist IScoutTask failed:\ntaskid:{}\nbatchid:{}".
                        format(task.taskid, task.batchid))
                    return False
                oldtaskfields.update(task._iscout_dict)
                oldtask: IscoutTask = IscoutTask.create_from_dict(
                    oldtaskfields, task._platform)
                # oldtask.progress = math.floor(
                #     oldtask.batchcompletecount / oldtask.batchtotalcount *
                #     100) / 100
                # 此处改为重置progress，因为要重新下发
                oldtask.progress = 0
                oldtask.cmdrcvmsg = ''
                oldtask.sequence_reset()
                oldtask.cmdstatus = ECommandStatus.WaitForSend
                if not DbSqlite._tbiscouttask.update_iscouttask2(oldtask):
                    DbSqlite._logger.error(
                        "Update exist IScoutTask failed:\ntaskid:{}\nbatchid:{}"
                        .format(task.taskid, task.batchid))
                    return False

        return True

    @staticmethod
    @_check_static_initial
    def get_iscout_task_periodnum(platform: str, taskid: str) -> int:
        taskfields = DbSqlite._tbiscouttask.select_iscouttask(
            SqlConditions(
                SqlCondition(colname='Platform', val=platform),
                SqlCondition(colname='TaskId', val=taskid),
            ))
        if not isinstance(taskfields,
                          dict) or not taskfields.__contains__("periodnum"):
            return -1
        return int(taskfields["periodnum"])

    # @staticmethod
    # @_check_static_initial
    # def get_iscout_task(platform: str, taskid: str) -> IscoutTask:
    #     taskfields = DbSqlite._tbiscouttask.select_iscouttask(
    #         SqlConditions(
    #             SqlCondition(colname='Platform', val=platform),
    #             SqlCondition(colname='TaskId', val=taskid),
    #         ))
    #     res:IscoutTask = IscoutTask.create_from_dict(taskfields)
    #     return res

    # @staticmethod
    # @_check_static_initial
    # def get_iscout_tasks(platform: str, taskid: str) -> IscoutTask:
    #     for taskfields in DbSqlite._tbiscouttask.select_iscouttasks(
    #             SqlConditions(
    #                 SqlCondition(colname='Platform', val=platform),
    #                 SqlCondition(colname='TaskId', val=taskid),
    #             )):
    #         if not isinstance(taskfields,dict) or len(taskfields)<1:
    #             continue
    #         # 搞cmd字段
    #         cmdid: str = btaskfields.get('cmdid', None)
    #         if not cmdid is None:
    #             cmdfields: dict = DbSqlite._tbidowncmd.select_cmd(
    #                 SqlConditions(
    #                     SqlCondition(colname='CmdId', val=cmdid),
    #                     SqlCondition(colname='Platform', val=platform)))
    #             if not cmdfields is None:
    #                 cmdfields.update(taskfields)

    @staticmethod
    @_check_static_initial
    def get_iscout_batch_task(platform: str, taskid: str, batchid: str):
        # 搞batchtask字段
        btaskfields: dict = DbSqlite._tbiscoutbatchtask.select_iscoutbtask(
            SqlConditions(
                SqlCondition(colname='Platform', val=platform),
                SqlCondition(colname='TaskId', val=taskid),
                SqlCondition(colname='BatchId', val=batchid),
            ))
        if not isinstance(btaskfields, dict) or len(btaskfields) < 1:
            return None
        # 搞task.batchcomplete等字段
        taskfields: dict = DbSqlite._tbiscouttask.select_iscouttask(
            SqlConditions(
                SqlCondition(colname='Platform', val=platform),
                SqlCondition(colname='TaskId', val=taskid),
            ))
        if not isinstance(taskfields, dict) or len(taskfields) < 1:
            return None

        # 这个接口是获取batchtask，要用batchtask的字段
        taskfields.update(btaskfields)

        # 搞cmd字段
        cmdid: str = btaskfields.get('cmdid', None)
        if not cmdid is None:
            cmdfields: dict = DbSqlite._tbidowncmd.select_cmd(
                SqlConditions(SqlCondition(colname='CmdId', val=cmdid),
                              SqlCondition(colname='Platform', val=platform)))
            if not cmdfields is None:
                cmdfields.update(taskfields)
                # 这波反向更新的操作属实秀到我了 by judy 20201019
        res: IscoutTask = IscoutTask.create_from_dict(cmdfields, platform)
        return res

    @staticmethod
    @_check_static_initial
    def get_iscout_batch_tasks(platform: str, taskid: str) -> iter:
        # 搞batchtask字段
        for btaskfields in DbSqlite._tbiscoutbatchtask.select_iscoutbtasks(
                SqlConditions(
                    SqlCondition(colname='Platform', val=platform),
                    SqlCondition(colname='TaskId', val=taskid),
                )):
            if not isinstance(btaskfields, dict) or len(btaskfields) < 1:
                continue
            # 搞task.batchcomplete等字段
            taskfields: dict = DbSqlite._tbiscouttask.select_iscouttask(
                SqlConditions(
                    SqlCondition(colname='Platform', val=platform),
                    SqlCondition(colname='TaskId', val=taskid),
                ))
            if not isinstance(taskfields, dict) or len(taskfields) < 1:
                return None

            # 这个接口是获取batchtask，要用batchtask的字段
            taskfields.update(btaskfields)

            # 搞cmd字段
            cmdid: str = btaskfields.get('cmdid', None)
            if not cmdid is None:
                cmdfields: dict = DbSqlite._tbidowncmd.select_cmd(
                    SqlConditions(
                        SqlCondition(colname='CmdId', val=cmdid),
                        SqlCondition(colname='Platform', val=platform)))
                if not cmdfields is None:
                    cmdfields.update(taskfields)
            res: IscoutTask = IscoutTask.create_from_dict(cmdfields, platform)
            yield res

    @staticmethod
    @_check_static_initial
    def is_iscoutbatch_complete_count_increaced(platform: str, taskid: str,
                                                batchid: str) -> bool:
        """返回 指定的子任务完成情况 是否已更新到 总任务表的 batchcompletecount 字段"""
        return DbSqlite._tbiscoutbatchtask.is_iscoutbatch_complete_count_increaced(
            platform, taskid, batchid)

    @staticmethod
    @_check_static_initial
    def increace_iscouttask_batch_complete_count(platform: str, taskid: str,
                                                 batchid: str) -> bool:
        """原子操作，提升指定Task的batchcompletecount数量1。
        task:任务对象"""
        res: bool = True
        try:
            # 暂时先这么写了，
            # 后面如果需要实现原子操作，需要：
            # 1. 查询原 batchcompletecount 值并记录
            # 2. 尝试 加1，失败返回False
            # 3. 尝试 设置update_batch_complete_count_increaced_flag为True，
            #   失败需要将 batchcompletecount 回滚-1，并返回False
            # 4. 都成功，返回True
            if not DbSqlite._tbiscouttask.increace_iscouttask_batch_complete_count(
                    platform, taskid, 1):
                res = False
                return res

            if not DbSqlite._tbiscoutbatchtask.update_batch_complete_count_increaced_flag(
                    platform, taskid, batchid, True):
                res = False
                return res

        except Exception as ex:
            res = False
            raise ex
        return res

    @staticmethod
    @_check_static_initial
    def decreace_iscouttask_batch_complete_count(platform: str, taskid: str,
                                                 batchid: str) -> bool:
        """原子操作，提升指定Task的batchcompletecount数量1。
        task:任务对象"""
        res: bool = True
        try:
            # 暂时先这么写了，
            # 后面如果需要实现原子操作，需要：
            # 1. 查询原 batchcompletecount 值并记录
            # 2. 尝试 加1，失败返回False
            # 3. 尝试 设置update_batch_complete_count_increaced_flag为True，
            #   失败需要将 batchcompletecount 回滚-1，并返回False
            # 4. 都成功，返回True
            if not DbSqlite._tbiscoutbatchtask.is_iscoutbatch_complete_count_increaced(
                    platform, taskid, batchid):
                return res

            if not DbSqlite._tbiscouttask.increace_iscouttask_batch_complete_count(
                    platform, taskid, -1):
                res = False
                return res

            if not DbSqlite._tbiscoutbatchtask.update_batch_complete_count_increaced_flag(
                    platform, taskid, batchid, False):
                res = False
                return res

        except Exception as ex:
            res = False
            raise ex
        return res

    @staticmethod
    @_check_static_initial
    def get_deliverable_iscouttask() -> iter:
        """查询所有待分配的iscouttask任务"""
        # IDownTask表
        for fieldstask in DbSqlite._tbiscouttask.execute_search_all(
                tablename="IScoutTask",
                sql='''select * from IScoutTask where 
        Status=2 and (EndTime is Null or EndTime>?)''',
                params=(helper_time.ts_since_1970_tz(), )):
            # for fieldstask in DbSqlite._tbiscouttask.select_iscouttasks(
            #         SqlConditions(
            #             SqlCondition('Status', ECommandStatus.WaitForSend.value),
            #             SqlCondition('EndTime', ),
            #         )):
            if not isinstance(fieldstask, dict) or len(fieldstask) < 1:
                continue

            taskid = fieldstask['taskid']
            platform = fieldstask['platform']

            # IDownBatchTask表
            for fieldsbtask in DbSqlite._tbiscoutbatchtask.select_iscoutbtasks(
                    SqlConditions(
                        SqlCondition('TaskId', taskid),
                        SqlCondition('Platform', platform),
                        SqlCondition('Status',
                                     ECommandStatus.WaitForSend.value))):

                if not isinstance(fieldsbtask, dict) or len(fieldsbtask) < 1:
                    continue

                fieldsbtask.update(fieldstask)
                cmdid = fieldsbtask['cmdid']

                # IDownCmd表，取第一条
                if not cmdid is None:
                    fieldscmd = DbSqlite._tbidowncmd.select_cmd(
                        SqlConditions(SqlCondition("CmdId", cmdid),
                                      SqlCondition("Platform", platform),
                                      SqlCondition("IsRelative", 1)))
                    fieldscmd: dict = fieldscmd
                    fieldsbtask.update(fieldscmd)

                tsk: IscoutTask = IscoutTask(fieldsbtask)

                yield tsk

    @staticmethod
    @_check_static_initial
    def get_deliverable_iscouttask2() -> iter:
        """获取所有 周期循环任务，返回 子任务字段为主"""
        for fieldstask in DbSqlite._tbiscouttask.execute_search_all(
                tablename="IScoutTask",
                sql='''select * from IScoutTask where 
                        IsPeriod=1 and PeriodNum>=1 and 
                        (Status!=3 and Status!=4) and 
                        (EndTime is Null or EndTime>?)''',
                params=(helper_time.ts_since_1970_tz(), )):
                # 
            # for fieldstask in DbSqlite._tbiscouttask.select_iscouttasks(
            #         SqlConditions(
            #             SqlCondition('IsPeriod', 1),
            #             SqlCondition('PeriodNum', 2, ESqlOper.GreaterEquals),
            #             SqlCondition('Status', ECommandStatus.Failed.value),
            #             SqlCondition('Status', ECommandStatus.Succeed.value),
            #             SqlCondition('Status', ECommandStatus.Cancelled.value),
            #             SqlCondition('Status', ECommandStatus.Timeout.value),
            #         )):
            if not isinstance(fieldstask, dict) or len(fieldstask) < 1:
                continue

            taskid = fieldstask['taskid']
            platform = fieldstask['platform']

            # IDownBatchTask表
            for fieldsbtask in DbSqlite._tbiscoutbatchtask.select_iscoutbtasks(
                    SqlConditions(
                        SqlCondition('TaskId', taskid),
                        SqlCondition('Platform', platform),
                        SqlCondition('IsPeriod', 1),
                        SqlCondition('Status', 3, ESqlOper.NotEquals),
                    )):

                if not isinstance(fieldsbtask, dict) or len(fieldsbtask) < 1:
                    continue

                fieldstask.update(fieldsbtask)
                cmdid = fieldsbtask['cmdid']

                # IDownCmd表，取第一条
                if not cmdid is None:
                    fieldscmd = DbSqlite._tbidowncmd.select_cmd(
                        SqlConditions(SqlCondition("CmdId", cmdid),
                                      SqlCondition("Platform", platform),
                                      SqlCondition("IsRelative", 1)))
                    fieldscmd: dict = fieldscmd
                    fieldstask.update(fieldscmd)

                tsk: IscoutTask = IscoutTask(fieldstask)

                yield tsk

    @staticmethod
    @_check_static_initial
    def update_iscouttask_status(
            platform: str,
            taskid: str,
            cmdstatus: ECommandStatus,
    ):
        return DbSqlite._tbiscouttask.update_iscouttask_status(
            platform, taskid, cmdstatus)

    @staticmethod
    @_check_static_initial
    def update_iscoutbtask_status(
            platform: str,
            taskid: str,
            batchid: str,
            cmdstatus: ECommandStatus,
    ):
        return DbSqlite._tbiscoutbatchtask.update_iscoutbtask_status(
            platform, taskid, batchid, cmdstatus)

    @staticmethod
    @_check_static_initial
    def update_iscoutbtask_back(btaskback: IscoutBtaskBack) -> bool:
        return DbSqlite._tbiscoutbatchtask.update_iscoutbtask_back(btaskback)

    @staticmethod
    @_check_static_initial
    def update_iscoutbtask(platform: str, taskid: str, batchid: str,
                           updatefields: dict) -> bool:
        return DbSqlite._tbiscoutbatchtask.update_iscoutbtask(
            platform, taskid, batchid, updatefields)

    @staticmethod
    @_check_static_initial
    def get_iscoutbtask_count_by_cmdstatus(platform: str, taskid: str,
                                           status: ECommandStatus) -> int:
        return DbSqlite._tbiscoutbatchtask.get_batch_task_count_by_cmdstatus(
            platform, taskid, status)

    @staticmethod
    @_check_static_initial
    def update_iscout_task(platform: str, taskid: str,
                           updatefields: dict) -> bool:
        """更新指定的task，IDownTask表总任务的其他所有字段"""
        return DbSqlite._tbiscouttask.update_iscouttask3(
            platform, taskid, updatefields)

    @staticmethod
    @_check_static_initial
    def update_iscout_task2(task: IscoutTask) -> bool:
        """更新指定的task，IDownTask表总任务的其他所有字段"""
        return DbSqlite._tbiscouttask.update_iscouttask2(task)

    @staticmethod
    @_check_static_initial
    def get_iscouttask_sequence(platform: str, taskid: str) -> int:
        """更新指定的task，IDownTask表总任务的其他所有字段"""
        return DbSqlite._tbiscouttask.get_iscouttask_sequence(platform, taskid)

    @staticmethod
    @_check_static_initial
    def get_iscouttask_elapsed(platform: str, taskid: str) -> int:
        """更新指定的task，IDownTask表总任务的其他所有字段"""
        return DbSqlite._tbiscouttask.get_iscouttask_elapsed(platform, taskid)

######################################################
# Automated task

    @staticmethod
    @_check_static_initial
    def get_last_automatedtask(platform: str,
                               autotasktype: EAutoType) -> AutomatedTask:
        """查询最晚的一条总任务"""
        fields: dict = DbSqlite._tbautotask.execute_search_one(
            tablename="AutomatedTask",
            sql="""SELECT * FROM AutomatedTask where 
            LastEndTime is Null and 
            Platform=? and 
            AutoTaskType=?;""",
            params=(
                platform,
                autotasktype.value,
            ))
        if not isinstance(fields, dict) or len(fields) < 1:
            fields = DbSqlite._tbautotask.execute_search_one(
                tablename="AutomatedTask",
                sql="""SELECT * FROM AutomatedTask where 
            LastEndTime=(SELECT max(LastEndTime) FROM AutomatedTask) and 
            Platform=? and 
            AutoTaskType=?;""",
                params=(
                    platform,
                    autotasktype.value,
                ))
        if not isinstance(fields, dict) or len(fields) < 1:
            return None

        # 随便查一条子任务出来 填空
        taskid: str = fields['taskid']

        fieldsbtask: dict = DbSqlite._tbautobatchtask.select_autobtask(
            SqlConditions(SqlCondition(colname="TaskId", val=taskid)))
        if not isinstance(fieldsbtask, dict) or len(fieldsbtask) < 1:
            raise Exception(
                "Automated batch task not found by taskid={}".format(taskid))

        fields.update(fieldsbtask)

        # 查对应的cmd
        if fields.__contains__('cmdid') and isinstance(
                fields['cmdid'], str) and not fields['cmdid'] == "":
            fieldscmd: dict = DbSqlite._tbidowncmd.select_cmd(
                SqlConditions(
                    SqlCondition(colname="CmdId", val=fields["cmdid"])))
            if isinstance(fieldscmd, dict) and len(fieldscmd) > 0:
                fields.update(fieldscmd)
        task: AutomatedTask = AutomatedTask.create_from_dict(fields, platform)
        return task

    @staticmethod
    @_check_static_initial
    def save_new_autotask(task: AutomatedTask, client: Client):
        '''存AutomatedTask，到AutomatedTask表和AutomatedBatchTask表'''
        if not isinstance(task, AutomatedTask):
            raise Exception(
                "Invalid AutomatedTask for saving to db:{}".format(task))

        isnewtask: bool = False
        # 查询已存在task的总任务数，
        bcount: int = DbSqlite._tbautotask.get_automatedtask_batch_total_count(
            task._platform, task.taskid)
        if bcount == -1:
            isnewtask = True
            # -1表示没找到指定Task，表示是新来的任务，令其拥有一个子任务
            task.batchtotalcount = 1
        else:
            # 否则其子任务数等于库中任务数
            task.batchtotalcount = bcount

        # 然后存 cmd
        task: AutomatedTask = task
        if isinstance(task.cmd_id,
                      str) and not task.cmd_id is None and isinstance(
                          task.cmd, IdownCmd):
            if not DbSqlite._tbidowncmd.save_new_idowncmd(
                    task._platform, client, task.cmd, task.createtime,
                    ECommandStatus.WaitForSend, task.taskid, task.batchid, 1):
                return False

        # 同步子任务的周期数为总任务的周期数
        taskfields: dict = DbSqlite._tbautotask.select_automatedtask(
            SqlConditions(SqlCondition('TaskId', task.taskid),
                          SqlCondition('Platform', task._platform)))
        periodnum: int = 1
        if isinstance(taskfields,
                      dict) and taskfields.__contains__("periodnum"):
            periodnum = taskfields["periodnum"]
        task.periodnum = periodnum
        succ, isnewbatchtask = DbSqlite._tbautobatchtask.save_new_autobtask(
            task, client, ECommandStatus.WaitForSend)
        if not succ:
            DbSqlite._logger.error(
                "Save automated batch task failed:\ntaskid:{}\nbatchid:{}".
                format(task.taskid, task.batchid))
            return False

        # 如果是新增的子任务，那么batchtotalcount要加1
        if not isnewtask and isnewbatchtask:
            task.batchtotalcount += 1

        # 最后存入IDownTask表，
        if isnewtask:
            # 新任务插入
            if not DbSqlite._tbautotask.save_new_automatedtask(
                    task, ECommandStatus.WaitForSend):
                DbSqlite._logger.error(
                    "Save automated task failed, insert new task failed:\ntaskid:{}"
                    .format(task.taskid))
                return False
        else:
            bcompletecount: int = DbSqlite._tbautotask.get_automatedtask_batch_complete_count(
                task._platform, task.taskid)
            if not DbSqlite._tbautotask.update_automatedtask3(
                    task._platform, task.taskid, {
                        'Status': ECommandStatus.WaitForSend.value,
                        'BatchTotalCount': task.batchtotalcount,
                        'Progress': bcompletecount / task.batchtotalcount,
                        'CmdRcvMsg': '',
                    }):
                DbSqlite._logger.error(
                    "Save AutomatedTask task failed, update AutomatedTask failed:\ntaskid:{}"
                    .format(task.taskid))
                return False

            # 如果不是新的子任务，需要做重置处理，因为要符合用户操作，他可能来完全相同的重复任务
            if not isnewbatchtask:
                task: AutomatedTask = task
                # 根据情况，将 batchcompletecount-1，并重置batch_complete_count_increaced_flag标记
                if DbSqlite._tbautobatchtask.is_autotaskbatch_complete_count_increaced(
                        task._platform, task.taskid, task.batchid):
                    if not DbSqlite._tbautotask.increace_automatedtask_batch_complete_count(
                            task._platform, task.taskid, -1):
                        DbSqlite._logger.error(
                            "Decreace AutomatedTask batch_complete_count failed:\ntaskid:{}"
                            .format(task.taskid))
                        return False
                    if not DbSqlite._tbautobatchtask.update_batch_complete_count_increaced_flag(
                            task._platform, task.taskid, task.batchid, False):
                        DbSqlite._logger.error(
                            "Set AutomatedBTask batch_complete_count_increaced_flag failed:\ntaskid:{}\nbatchid:{}"
                            .format(task.taskid, task.batchid))
                        return False
                # 计算 并更新 Task 表当前Task的Progress等字段？
                oldtaskfields: dict = DbSqlite._tbautotask.select_automatedtask(
                    SqlConditions(SqlCondition('TaskId', task.taskid),
                                  SqlCondition('Platform', task._platform)))
                if not isinstance(oldtaskfields,
                                  dict) or len(oldtaskfields) < 1:
                    DbSqlite._logger.error(
                        "Get exist Automated failed:\ntaskid:{}\nbatchid:{}".
                        format(task.taskid, task.batchid))
                    return False
                oldtaskfields.update(task._auto_dict)
                oldtask: AutomatedTask = AutomatedTask.create_from_dict(
                    oldtaskfields, task._platform)
                oldtask.progress = math.floor(
                    oldtask.batchcompletecount / oldtask.batchtotalcount *
                    100) / 100
                oldtask.cmdrcvmsg = ''
                oldtask.sequence_reset()
                oldtask.cmdstatus = ECommandStatus.WaitForSend
                if not DbSqlite._tbautotask.update_automatedtask2(oldtask):
                    DbSqlite._logger.error(
                        "Update exist AutomatedTask failed:\ntaskid:{}\nbatchid:{}"
                        .format(task.taskid, task.batchid))
                    return False

        return True

    @staticmethod
    @_check_static_initial
    def get_auto_batch_task(platform: str, taskid: str, batchid: str):
        # 搞batchtask字段
        btaskfields: dict = DbSqlite._tbautobatchtask.select_autobtask(
            SqlConditions(
                SqlCondition(colname='Platform', val=platform),
                SqlCondition(colname='TaskId', val=taskid),
                SqlCondition(colname='BatchId', val=batchid),
            ))
        if not isinstance(btaskfields, dict) or len(btaskfields) < 1:
            return None
        # 搞task.batchcomplete等字段
        taskfields: dict = DbSqlite._tbautotask.select_automatedtask(
            SqlConditions(
                SqlCondition(colname='Platform', val=platform),
                SqlCondition(colname='TaskId', val=taskid),
            ))
        if not isinstance(taskfields, dict) or len(taskfields) < 1:
            return None

        # 这个接口是获取batchtask，要用batchtask的字段
        taskfields.update(btaskfields)

        # 搞cmd字段
        cmdid: str = btaskfields.get('cmdid', None)
        if not cmdid is None:
            cmdfields: dict = DbSqlite._tbidowncmd.select_cmd(
                SqlConditions(SqlCondition(colname='CmdId', val=cmdid),
                              SqlCondition(colname='Platform', val=platform)))
            if not cmdfields is None:
                cmdfields.update(taskfields)
        res: AutomatedTask = AutomatedTask.create_from_dict(
            cmdfields, platform)
        return res

    @staticmethod
    @_check_static_initial
    def get_deliverable_autotask() -> iter:
        """查询所有待分配的autotask任务"""
        # IDownTask表
        for fieldstask in DbSqlite._tbautotask.select_automatedtasks(
                SqlConditions(
                    SqlCondition(colname="Status",
                                 val=ECommandStatus.WaitForSend.value), )):
            if not isinstance(fieldstask, dict) or len(fieldstask) < 1:
                continue

            taskid = fieldstask['taskid']
            platform = fieldstask['platform']

            # IDownBatchTask表
            for fieldsbtask in DbSqlite._tbautobatchtask.select_autobtasks(
                    SqlConditions(
                        SqlCondition('TaskId', taskid),
                        SqlCondition('Platform', platform),
                        SqlCondition('Status',
                                     ECommandStatus.WaitForSend.value))):

                if not isinstance(fieldsbtask, dict) or len(fieldsbtask) < 1:
                    continue

                fieldsbtask.update(fieldstask)
                cmdid = fieldsbtask['cmdid']

                # IDownCmd表，取第一条
                if not cmdid is None:
                    fieldscmd = DbSqlite._tbidowncmd.select_cmd(
                        SqlConditions(SqlCondition("CmdId", cmdid),
                                      SqlCondition("Platform", platform),
                                      SqlCondition("IsRelative", 1)))
                    fieldscmd: dict = fieldscmd
                    fieldsbtask.update(fieldscmd)

                tsk: AutomatedTask = AutomatedTask.create_from_dict(
                    fieldsbtask, platform)

                yield tsk

    @staticmethod
    @_check_static_initial
    def update_automated_task(platform: str, taskid: str,
                              updatefields: dict) -> bool:
        """更新指定的task，IDownTask表总任务的其他所有字段"""
        return DbSqlite._tbautotask.update_automatedtask3(
            platform, taskid, updatefields)

    @staticmethod
    @_check_static_initial
    def update_automated_task2(task: IscoutTask) -> bool:
        """更新指定的task，IDownTask表总任务的其他所有字段"""
        return DbSqlite._tbautotask.update_automatedtask2(task)

    @staticmethod
    @_check_static_initial
    def update_automated_batch_task(platform: str, taskid: str, batchid: str,
                                    updatefields: dict) -> bool:
        """更新指定的task，IDownTask表总任务的其他所有字段"""
        return DbSqlite._tbautobatchtask.update_autobtask(
            platform, taskid, batchid, updatefields)

    @staticmethod
    @_check_static_initial
    def update_autotask_status(
            platform: str,
            taskid: str,
            cmdstatus: ECommandStatus,
    ):
        return DbSqlite._tbautotask.update_autotask_status(
            platform, taskid, cmdstatus)

    @staticmethod
    @_check_static_initial
    def get_autobtask_count_by_cmdstatus(platform: str, taskid: str,
                                         status: ECommandStatus) -> int:
        return DbSqlite._tbautobatchtask.get_batch_task_count_by_cmdstatus(
            platform, taskid, status)

    @staticmethod
    @_check_static_initial
    def is_autobatch_complete_count_increaced(platform: str, taskid: str,
                                              batchid: str) -> bool:
        """返回 指定的子任务完成情况 是否已更新到 总任务表的 batchcompletecount 字段"""
        return DbSqlite._tbautobatchtask.is_autotaskbatch_complete_count_increaced(
            platform, taskid, batchid)

    @staticmethod
    @_check_static_initial
    def increace_autotask_batch_complete_count(platform: str, taskid: str,
                                               batchid: str) -> bool:
        """原子操作，提升指定Task的batchcompletecount数量1。
        task:任务对象"""
        res: bool = True
        try:
            # 暂时先这么写了，
            # 后面如果需要实现原子操作，需要：
            # 1. 查询原 batchcompletecount 值并记录
            # 2. 尝试 加1，失败返回False
            # 3. 尝试 设置update_batch_complete_count_increaced_flag为True，
            #   失败需要将 batchcompletecount 回滚-1，并返回False
            # 4. 都成功，返回True
            if not DbSqlite._tbautotask.increace_automatedtask_batch_complete_count(
                    platform, taskid, 1):
                res = False
                return res

            if not DbSqlite._tbautobatchtask.update_batch_complete_count_increaced_flag(
                    platform, taskid, batchid, True):
                res = False
                return res

        except Exception as ex:
            res = False
            raise ex
        return res

    @staticmethod
    @_check_static_initial
    def get_autotask_sequence(platform: str, taskid: str) -> int:
        """更新指定的task，IDownTask表总任务的其他所有字段"""
        return DbSqlite._tbautotask.get_automatedtask_sequence(
            platform, taskid)


######################################################
# Others

    @staticmethod
    def _apend_conds(conds: SqlConditions, colname, colval):
        if not colval is None:
            conds.append_conditions(SqlCondition(colname, colval))


def __get_sqlite_initailed():
    return DbSqlite._static_initialed


__sqlite_initialed = __get_sqlite_initailed
