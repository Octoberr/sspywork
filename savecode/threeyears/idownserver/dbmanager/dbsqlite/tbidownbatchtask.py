"""table idownbatchtask"""

# -*- coding:utf-8 -*-

import time
import traceback
from typing import Tuple

from commonbaby.helpers import helper_str, helper_time
from commonbaby.sql import (SqlConn, SqliteColumn, SqliteConn,
                            SqliteConnManager, SqliteIndex, SqliteTable,
                            table_locker)

from datacontract import Client, ECommandStatus, Task, TaskBatchBack

from ..sqlcondition import SqlCondition, SqlConditions
from .sqlite_config import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbIDownBatchTask(TbSqliteBase):
    """Task表及相关操作"""

    __tb_IDownBatchTask: SqliteTable = SqliteTable(
        'IDownBatchTask',
        True,
        SqliteColumn(colname='Id',
                     coltype='INTEGER',
                     nullable=False,
                     is_primary_key=True,
                     is_auto_increament=True,
                     is_unique=True).set_index_new(),
        SqliteColumn(colname='Platform', nullable=False).set_index_new(),
        SqliteColumn(colname='TaskId', nullable=False).set_index_new(),
        SqliteColumn(colname='BatchId', nullable=False).set_index_new(),
        SqliteColumn(colname='ParentBatchId', nullable=True).set_index_new(),
        SqliteColumn(colname='ClientId', nullable=False).set_index_new(),
        SqliteColumn(colname='TokenId', coltype='INTEGER',
                     nullable=False).set_index_new(),
        SqliteColumn(colname='AppType', coltype='INTEGER').set_index_new(),
        SqliteColumn(colname='ForceDownload', coltype='INTEGER', defaultval=0).set_index_new(),
        SqliteColumn(colname='CmdRcvMsg'),
        SqliteColumn(colname='Result'),
        SqliteColumn(colname='CmdStatus', coltype='INTEGER',
                     nullable=False).set_index_new(),
        SqliteColumn(
            colname='Progress',  #0~1浮点数表百分比
            coltype='REAL',
            defaultval=0).set_index_new(),
        SqliteColumn(colname='Sequence', coltype='INTEGER',
                     defaultval=0).set_index_new(),
        SqliteColumn(colname='OtherFields').set_index_new(),
        SqliteColumn(colname='CreateTime',
                     coltype='DATETIME',
                     defaultval=helper_time.ts_since_1970_tz()),
        SqliteColumn(colname='UpdateTime', coltype='REAL',
                     nullable=False).set_index_new(),
        SqliteColumn(
            # 此字段仅在查询 或 操作IDownTask表的 BatchCompleteCount 字段时使用，
            # 其他时候不要使用
            colname='IsBatchCompleteCountIncreased',
            coltype='BOOLEAN',
            nullable=False,
            defaultval=0),
        SqliteColumn(colname="Source"),  # 新增
        SqliteColumn(colname="CmdId"),  #cmdid字段要更新
    )

    # 所有列，复制粘贴用...：
    # Platform,
    # TaskId,
    # Batchid,
    # ParentBatchId,
    # ClientId,
    # TokenId,
    # AppType,
    # ForceDownload,
    # CmdRcvMsg,
    # Result,
    # CmdStatus,
    # Progress,
    # Sequence,
    # OtherFields,
    # CreateTime,
    # UpdateTime,
    # IsBatchCompleteCountIncreased,
    # Source,
    # CmdId

    def __init__(self, dbcfg: SqliteConfig):
        """"""
        TbSqliteBase.__init__(self,
                              TbIDownBatchTask.__tb_IDownBatchTask._tbname,
                              dbcfg)

    def _append_tables(self):
        self._conn_mngr.append_table(TbIDownBatchTask.__tb_IDownBatchTask)

    @table_locker(__tb_IDownBatchTask._tbname)
    def save_new_idownbatchtask(
            self,
            task: Task,
            client: Client,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend
    ) -> Tuple[bool, bool]:
        """保存新的批处理任务的子任务\n
        task: 任务对象\n
        tokenid：当前批处理子任务对应的登陆令牌存储在IDownBatchTokens表中的tokenid，关联存储\n
        client: 当前批处理子任务被分配到的client\n
        cmdstatus: 指定当前批处理子任务的命令状态\n
        return: （bool是否成功，bool是否为新增(用于计算batchtotalcount)）"""
        res: bool = False
        isnew: bool = False
        conn: SqliteConn = None
        cursor = None
        client: Client = client
        task: Task = task
        try:
            if not isinstance(task.tokenid, str) or task.tokenid == "":
                raise Exception(
                    "Invalid tokenid while save new idownbatchtask:\ntaskid:{}"
                    .format(task.taskid))
            # 搜索每个库，看有没有 taskid和clientid一样，且时间更新
            # 的，一样就更新其他所有字段
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE 
            Platform=? and TaskId=? and BatchId=? and ClientId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        task._platform,
                        task.taskid,
                        task.batchid,
                        client._statusbasic._clientid,
                    ))
                    result = cursor.fetchall()

                    if result[0][0] > 0:
                        res = True
                        # 只根据TaskId、ParentTaskId和ClientId关联，
                        # 不考虑 任务文件产生时间与现有数据库中已存在任务的时间，每次直接覆盖，以符合用户操作。
                        # 若来了TaskId一样的数据，则必然分配给同一个ClientId
                        cmd = f'''UPDATE {self._tbname} set
                            TokenId=?,
                            AppType=?,
                            ForceDownload=?,
                            CmdRcvMsg=?,
                            Result=?,
                            CmdStatus=?,
                            Progress=?,
                            Sequence=?,
                            OtherFields=?,
                            CreateTime=?,
                            UpdateTime=?,
                            Source=?,
                            CmdId=? 
                            WHERE Platform=? and TaskId=? and BatchId=? and ClientId=? and CreateTime<=?;'''

                        result = cursor.execute(
                            cmd,
                            (
                                task.tokenid,
                                task.apptype,
                                task.forcedownload,
                                task._cmdrcvmsg,
                                task._result,
                                cmdstatus.value,
                                # 进度置零
                                0,
                                #批量任务完成数也要重置，因为重置了任务下发状态，变为新任务，需要重新执行
                                0,  #sequence重置
                                task.other_fields_json,
                                task.timestr,
                                helper_time.get_time_sec_tz(),
                                task.source,
                                task.cmd_id,
                                # 0 此字段在其他地方重置 #是否总任务已提升batchcompletecount置零，
                                task._platform,
                                task.taskid,
                                task.batchid,
                                client._statusbasic._clientid,
                                task.timestr,
                            ))

                        # 这句没用，就是调试看看结果..
                        if result is None or result.rowcount < 1:  # or len(result) < 1:
                            pass

                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

            # 若没找到，则insert一条到最新的库
            # res==True表示至少有一个库里面有一条符合条件的任务，且已更新其字段
            if not res:
                isnew = True
                conn = self.connect_write(5)
                try:
                    # insert
                    # Platform,
                    # TaskId,
                    # Batchid,
                    # ParentBatchId,
                    # ClientId,
                    # TokenId,
                    # AppType,
                    # ForceDownload,
                    # CmdRcvMsg,
                    # Result,
                    # CmdStatus,
                    # Progress,
                    # Sequence,
                    # OtherFields,
                    # CreateTime,
                    # UpdateTime
                    # IsBatchCompleteCountIncreased
                    cmd = f'''INSERT INTO {self._tbname}(
                        Platform,
                        TaskId,
                        Batchid,
                        ParentBatchId,
                        ClientId,
                        TokenId,
                        AppType,
                        ForceDownload,
                        CmdRcvMsg,
                        Result,
                        CmdStatus,
                        Progress,
                        Sequence,
                        OtherFields,
                        CreateTime,
                        UpdateTime,
                        Source,
                        CmdId) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                    # 有几个属于TaskBack的字段在此不更新
                    cursor = conn.cursor
                    result = cursor.execute(
                        cmd,
                        (
                            task._platform,
                            task.taskid,
                            task.batchid,
                            task.parentbatchid,
                            client._statusbasic._clientid,
                            task.tokenid,
                            task.apptype,
                            task.forcedownload,
                            task._cmdrcvmsg,
                            task._result,
                            cmdstatus.value,
                            0,  # progress初始化为0
                            0,  #sequence初始化为0
                            task.other_fields_json,
                            task.timestr,
                            helper_time.get_time_sec_tz(),
                            task.source,
                            task.cmd_id))

                    if result is None or result.rowcount < 1:  # or len(result) < 1:
                        res = False
                    else:
                        res = True
                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error("save_new_idownbatchtask error: %s" %
                               traceback.format_exc())

        return (res, isnew)

    @table_locker(__tb_IDownBatchTask._tbname)
    def get_parent_clientid_of_task(self, task: Task) -> str:
        """获取 指定task的被分配到的采集端 Client对象"""
        res: str = None
        conn: SqliteConn = None
        cursor = None
        task: Task = task
        try:
            if helper_str.is_none_or_empty(task.parenttaskid):
                raise Exception(
                    "Invalid task parent_taskid for task, taskid={} batchid={}"
                    .format(task.taskid, task.batchid))
            if helper_str.is_none_or_empty(task.parentbatchid):
                raise Exception(
                    "Invalid task parent_batchid for task, taskid={} batchid={}"
                    .format(task.taskid, task.batchid))

            # 搜索每个库，看有没有 taskid和clientid一样，且时间更新
            # 的，一样就更新其他所有字段
            cmd = f'''SELECT ClientId FROM {self._tbname} WHERE 
            Platform=? and TaskId=? and BatchId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        task._platform,
                        task.parenttaskid,
                        task.parentbatchid,
                    ))
                    result = cursor.fetchall()

                    if result is None or len(result) < 1 or len(result[0]) < 1:
                        continue
                    else:
                        res = result[0][0]
                        break

                except Exception:
                    self._logger.error(
                        "get_parent_client_of_task error: {}".format(
                            traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()
                    if not res is None:
                        break

        except Exception:
            self._logger.error("get_parent_client_of_task error: %s" %
                               traceback.format_exc())

        return res

    @table_locker(__tb_IDownBatchTask._tbname)
    def get_batch_task(self, conds: SqlConditions) -> dict:
        """按条件搜索指定的一个任务，返回数据行转换成的字段字典迭代器"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            cmd = f'''SELECT 
                    Platform,
                    TaskId,
                    Batchid,
                    ParentBatchId,
                    ClientId,
                    TokenId,
                    AppType,
                    ForceDownload,
                    CmdRcvMsg,
                    Result,
                    CmdStatus,
                    Progress,
                    Sequence,
                    OtherFields,
                    CreateTime,
                    UpdateTime,
                    IsBatchCompleteCountIncreased,
                    Source,
                    CmdId FROM {self._tbname} WHERE {conds.text_normal}'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                conn._conn.row_factory = self._dict_factory
                # conn._conn.text_factory = self._text_factory
                try:
                    cursor = conn.cursor
                    cursor = cursor.execute(cmd, conds.params)

                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    fields: dict = {}
                    for i in range(len(result[0])):
                        fields[cursor.description[i][0].lower()] = result[0][i]
                    return fields

                except Exception:
                    self._logger.error(
                        "Get BatchTask from {} error: {}".format(
                            self._tbname, traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error("Get BatchTask {} error: {}".format(
                self._tbname, traceback.format_exc()))

    @table_locker(__tb_IDownBatchTask._tbname)
    def get_batch_tasks(self, conds: SqlConditions) -> iter:
        """按条件搜索任务，返回数据行转换成的字段字典迭代器"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            cmd = f'''SELECT 
                    Platform,
                    TaskId,
                    Batchid,
                    ParentBatchId,
                    ClientId,
                    TokenId,
                    AppType,
                    ForceDownload,
                    CmdRcvMsg,
                    Result,
                    CmdStatus,
                    Progress,
                    Sequence,
                    OtherFields,
                    CreateTime,
                    UpdateTime,
                    IsBatchCompleteCountIncreased,
                    Source,
                    CmdId FROM {self._tbname} WHERE {conds.text_normal}'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                conn._conn.row_factory = self._dict_factory
                # conn._conn.text_factory = self._text_factory
                try:
                    cursor = conn.cursor
                    cursor = cursor.execute(cmd, conds.params)

                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    for row in result:
                        # if len(row) != 15:
                        #     continue
                        fields: dict = {}
                        for i in range(len(row)):
                            fields[cursor.description[i][0].lower()] = row[i]

                        yield fields

                except Exception:
                    self._logger.error(
                        "Get BatchTasks from {} error: {}".format(
                            self._tbname, traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error("Get BatchTasks {} error: {}".format(
                self._tbname, traceback.format_exc()))

    @table_locker(__tb_IDownBatchTask._tbname)
    def get_batch_task_count_by_cmdstatus(self, task: Task,
                                          cmdstatus: ECommandStatus) -> int:
        """查询指定总任务taskid下的所有 为指定命令状态的子任务 的数量"""
        res: int = 0  #总数量
        conn: SqliteConn = None
        cursor = None
        try:
            cmd = f'''SELECT COUNT() FROM {self._tbname} WHERE Platform=? and TaskId=? and CmdStatus=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        task._platform,
                        task.taskid,
                        cmdstatus.value,
                    ))
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    tmp = result[0][0]

                    res = res + tmp

                except Exception:
                    self._logger.error("Select {} error: {}".format(
                        self._tbname, traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error("Save new {} error: {}".format(
                self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IDownBatchTask._tbname)
    def update_batchtask(self, task: Task) -> bool:
        """使用指定task对象更新IDownBatchTask表，
        不更新 isbatchcompletecountincreased\n
        task: 表示一个子任务对象"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        try:
            task._cmdstatus
            cmd = f'''UPDATE {self._tbname} set
                    ClientId=?,
                    ParentBatchId=?,
                    TokenId=?,
                    AppType=?,
                    ForceDownload=?,
                    CmdRcvMsg=?,
                    Result=?,
                    CmdStatus=?,
                    Progress=?,
                    Sequence=?,
                    OtherFields=?,
                    CreateTime=?,
                    UpdateTime=?,
                    Source=?,
                    CmdId=? 
                    WHERE Platform=? and TaskId=? and BatchId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    # task:Task = task
                    result = cursor.execute(cmd, (
                        task._clientid,
                        task.parentbatchid,
                        task.tokenid,
                        task.apptype,
                        task.forcedownload,
                        task._cmdrcvmsg,
                        task._result,
                        task._cmdstatus.value,
                        task.progress,
                        task._sequence,
                        task.other_fields_json,
                        task.timestr,
                        helper_time.get_time_sec_tz(),
                        task.source,
                        task.cmd_id,
                        task._platform,
                        task.taskid,
                        task.batchid,
                    ))
                    if not result is None and result.rowcount > 0:
                        res = True  # 一定只有一个子任务
                        break

                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

        except Exception:
            self._logger.error("update {} error: {}".format(
                self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IDownBatchTask._tbname)
    def update_batchtask_status(self, platform: str, taskid: str, batchid: str,
                                cmdstatus: ECommandStatus) -> bool:
        """使用指定task对象更新IDownBatchTask表，
        不更新 isbatchcompletecountincreased\n
        task: 表示一个子任务对象"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        try:
            cmd = f'''UPDATE {self._tbname} set
                    CmdStatus=? 
                    WHERE Platform=? and TaskId=? and BatchId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    # task:Task = task
                    result = cursor.execute(cmd, (
                        cmdstatus.value,
                        platform,
                        taskid,
                        batchid,
                    ))
                    if not result is None and result.rowcount > 0:
                        res = True  # 一定只有一个子任务
                        break

                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

        except Exception:
            self._logger.error("update {} error: {}".format(
                self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IDownBatchTask._tbname)
    def update_batchtask_client(self, platform: str, taskid: str, batchid: str,
                                clientid: str) -> bool:
        """更新batchtask被分配到的采集端"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        try:
            if not isinstance(clientid, str) or clientid == "":
                raise Exception(
                    "Invalid clientid for update_batchtask_clientid")
            cmd = f'''UPDATE {self._tbname} set
                    ClientId=? 
                    WHERE Platform=? and TaskId=? and BatchId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    # task:Task = task
                    result = cursor.execute(cmd, (
                        clientid,
                        platform,
                        taskid,
                        batchid,
                    ))
                    if not result is None and result.rowcount > 0:
                        res = True  # 一定只有一个子任务
                        break

                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

        except Exception:
            self._logger.error(
                "update batchtask client to {} error: {}".format(
                    self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IDownBatchTask._tbname)
    def update_batchtask_back(self, tb: TaskBatchBack) -> bool:
        """使用指定 TaskBatchBack 对象更新IDownBatchTask表，
        不更新 isbatchcompletecountincreased\n"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        tb: TaskBatchBack = tb
        try:
            if not isinstance(tb, TaskBatchBack):
                self._logger.error(
                    "Invalid param TaskBatchBack: {}".format(tb))
                return res

            # Platform
            # TaskId,
            # Batchid,
            # ClientId,
            # TokenId,
            # AppType,
            # CmdRcvMsg,
            # Result,
            # CmdStatus,
            # Progress,
            # Sequence,
            # OtherFields,
            # CreateTime,
            # UpdateTime,
            # IsBatchCompleteCountIncreased
            # CmdId
            # 更新策略，先搜一下有没有，并把sequence搜出来，如果
            # 本地sequence和新来的任务的sequence一样，则说明
            # 采集端的sequence出错了，打一句日志并返回False
            cmd = f'''SELECT Sequence FROM {self._tbname} WHERE Platform=? and TaskId=? and BatchId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:

                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        tb._platform,
                        tb._taskid,
                        tb._batchid,
                    ))
                    result = cursor.fetchall()

                    if result is None or len(result) < 1:
                        continue

                    oldseq = result[0][0]
                    if oldseq >= tb._sequence:
                        self._logger.error(
                            "The comming TaskBatchBack.sequence is {}, but which in local db is {}:\ntaskid:{}\nbatchid:{}\nsequence:{}"
                            .format(tb._sequence, oldseq, tb._taskid,
                                    tb._batchid, oldseq))
                        break

                    cmd = f'''UPDATE {self._tbname} set
                            CmdRcvMsg=?,
                            Result=?,
                            CmdStatus=?,
                            Progress=?,
                            Sequence=?,
                            UpdateTime=? 
                            WHERE Platform=? and TaskId=? and BatchId=? and Sequence<?;'''
                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        tb._cmdrcvmsg,
                        tb._result,
                        tb._cmdstatus.value,
                        tb._progress,
                        tb._sequence,
                        helper_time.get_time_sec_tz(),
                        tb._platform,
                        tb._taskid,
                        tb._batchid,
                        tb._sequence,
                    ))

                    if not result is None and result.rowcount > 0:
                        res = True  # 一定只有一个子任务
                        break

                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

        except Exception:
            self._logger.error("update {} error: {}".format(
                self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IDownBatchTask._tbname)
    def is_batch_complete_count_increaced(self, platform: str, taskid: str,
                                          batchid: str) -> bool:
        """返回 指定的子任务完成情况 是否已更新到 总任务表的 batchcompletecount 字段"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        try:
            # IsBatchCompleteCountIncreased
            cmd = f'''SELECT IsBatchCompleteCountIncreased FROM {self._tbname} 
            WHERE Platform=? and TaskId=? and BatchId=?'''
            found = False
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        platform,
                        taskid,
                        batchid,
                    ))
                    result = cursor.fetchall()
                    if not result is None and len(result) > 0:
                        tmp = result[0][0]
                        res = bool(tmp)  # 一定只有一个子任务
                        found = True
                        break

                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()
                    if found:
                        break

        except Exception:
            self._logger.error("update {} error: {}".format(
                self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IDownBatchTask._tbname)
    def update_batch_complete_count_increaced_flag(
            self, platform: str, taskid: str, batchid: str,
            isbatchcompletecountincreased: bool) -> bool:
        """使用指定 TaskBatchBack 对象的 isbatchcompletecountincreased 字段\n"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        try:

            # Platform
            # TaskId,
            # Batchid,
            # ClientId,
            # TokenId,
            # AppType,
            # CmdRcvMsg,
            # Result,
            # CmdStatus,
            # Sequence,
            # OtherFields,
            # CreateTime,
            # UpdateTime,
            # IsBatchCompleteCountIncreased
            cmd = f'''UPDATE {self._tbname} set
                    IsBatchCompleteCountIncreased=? 
                    WHERE Platform=? and TaskId=? and BatchId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:

                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        1 if isbatchcompletecountincreased else 0,
                        platform,
                        taskid,
                        batchid,
                    ))

                    if not result is None and result.rowcount > 0:
                        res = True  # 一定只有一个子任务
                        break

                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

        except Exception:
            self._logger.error("update {} error: {}".format(
                self._tbname, traceback.format_exc()))

        return res
