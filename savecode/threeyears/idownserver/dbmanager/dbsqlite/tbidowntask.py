"""table task"""

# -*- coding:utf-8 -*-

import time
import traceback

from commonbaby.helpers import helper_time
from commonbaby.sql import (SqlConn, SqliteColumn, SqliteConn,
                            SqliteConnManager, SqliteIndex, SqliteTable,
                            table_locker)

from datacontract import Client, ECommandStatus, Task

from ..sqlcondition import SqlCondition, SqlConditions
from .sqlite_config import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbIDownTask(TbSqliteBase):
    """Task表及相关操作"""

    __tb_IDownTask: SqliteTable = SqliteTable(
        'IDownTask',
        True,
        SqliteColumn(
            colname='Id',
            coltype='INTEGER',
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True).set_index_new(),
        # SqliteColumn(colname='ClientId', nullable=False).set_index_new(),
        SqliteColumn(
            colname='CmdStatus',
            coltype='INTEGER',
            nullable=False,
            description='采集端执行命令的状态，要反给中心的').set_index_new(),
        SqliteColumn(colname='Platform', nullable=False),
        SqliteColumn(colname='TaskId', nullable=False).set_index_new(),
        SqliteColumn(
            colname='TaskStatus',
            coltype='INTEGER',
            nullable=False,
            description='采集端执行任务的状态（下载状态等），跟CmdStatus不一样').set_index_new(),
        SqliteColumn(colname='ParentTaskId').set_index_new(),
        SqliteColumn(colname='BatchTotalCount', coltype='INTEGER'),
        SqliteColumn(colname='BatchCompleteCount',
                     coltype='INTEGER').set_index_new(),
        SqliteColumn(colname='TaskType', coltype='INTEGER', nullable=False),
        SqliteColumn(
            colname='Progress',  #0~1浮点数表百分比
            coltype='REAL',
            nullable=True),
        SqliteColumn(colname='CmdRcvMsg'),
        SqliteColumn(colname='Result'),
        SqliteColumn(colname='Sequence', coltype='INTEGER',
                     defaultval=0).set_index_new(),
        SqliteColumn(colname='OtherFields').set_index_new(),
        SqliteColumn(
            colname='CreateTime',
            coltype='DATETIME',
            defaultval=helper_time.ts_since_1970_tz()),
        SqliteColumn(colname='UpdateTime', coltype='REAL',
                     nullable=False).set_index_new(),
    )

    # 所有列，复制粘贴用...：
    # CmdStatus,
    # Platform
    # TaskId,
    # ParentTaskId,
    # BatchTotalCount,
    # BatchCompleteCount,
    # TaskType,
    # Progress,
    # TaskStatus,
    # CmdRcvMsg,
    # Result,
    # Sequence,
    # OtherFields,
    # CreateTime,
    # UpdateTime

    def __init__(self, dbcfg: SqliteConfig):
        """"""
        TbSqliteBase.__init__(self, TbIDownTask.__tb_IDownTask._tbname, dbcfg)

    def _append_tables(self):
        self._conn_mngr.append_table(TbIDownTask.__tb_IDownTask)

    @table_locker(__tb_IDownTask._tbname)
    def save_new_idown_task(
            self,
            task: Task,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend) -> bool:
        """保存/插入新来的任务"""
        res = False
        conn: SqliteConn = None
        cursor = None
        task: Task = task
        try:
            # 搜索每个库，看有没有 taskid和platform一样，且时间更新
            # 的，一样就更新其他所有字段
            # 若库中已有taskid一样的任务，说明是重新下发的，需要更新任务状态为等待下发，要重新下发执行
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE TaskId=? and Platform=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        task.taskid,
                        task._platform,
                    ))
                    result = cursor.fetchall()

                    if result[0][0] > 0:
                        res = True
                        # 只根据TaskId、platform作为条件，
                        # 不考虑 任务文件产生时间与现有数据库中已存在任务的时间，每次直接覆盖，以符合用户操作。
                        # 若来了TaskId一样的数据，则必然分配给同一个ClientId
                        cmd = f'''UPDATE {self._tbname} set
                            CmdStatus=?,
                            ParentTaskId=?,
                            BatchTotalCount=?,
                            BatchCompleteCount=?,
                            TaskType=?,
                            Progress=?,
                            TaskStatus=?,
                            CmdRcvMsg=?,
                            Result=?,
                            Sequence=?,
                            OtherFields=?,
                            CreateTime=?,
                            UpdateTime=? WHERE TaskId=? and Platform=? and CreateTime<=?;'''

                        result = cursor.execute(
                            cmd,
                            (
                                cmdstatus.value,
                                task.parenttaskid,
                                task.batchtotalcount,
                                #批量任务完成数也要重置，因为重置了任务下发状态，变为新任务，需要重新执行
                                task.batchcompletecount,
                                task.tasktype.value,
                                task.progress,
                                task.taskstatus.value,
                                task._cmdrcvmsg,
                                task._result,
                                0,  #sequence重置
                                task.other_fields_json,
                                task.timestr,
                                helper_time.get_time_sec_tz(),
                                task.taskid,
                                task.platform,
                                task.timestr,
                            ))
                        # 这句没用，就是调试看看结果..
                        if result is None or result.rowcount < 1:  # or len(result) < 1:
                            pass

                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    pass  # conn.commit()
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

            # 若没找到，则insert一条到最新的库
            # res==True表示至少有一个库里面有一条符合条件的任务，且已更新其字段
            if not res:
                conn = self.connect_write(5)
                try:
                    # insert
                    cmd = f'''INSERT INTO {self._tbname}(
                        CmdStatus,
                        Platform,
                        TaskId,
                        ParentTaskId,
                        BatchTotalCount,
                        BatchCompleteCount,
                        TaskType,
                        Progress,
                        TaskStatus,
                        CmdRcvMsg,
                        Result,
                        Progress,
                        Sequence,
                        OtherFields,
                        CreateTime,
                        UpdateTime) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                    # 有几个属于TaskBack的字段在此不更新
                    cursor = conn.cursor
                    result = cursor.execute(
                        cmd,
                        (
                            cmdstatus.value,
                            task.platform,
                            task.taskid,
                            task.parenttaskid,
                            task.batchtotalcount,
                            task.batchcompletecount,
                            task.tasktype.value,
                            task.progress,
                            task.taskstatus.value,
                            task._cmdrcvmsg,
                            task._result,
                            0,  #Progress初始化为0，其实总任务的Progress通过batchcompletecount计算得到更好
                            0,  #sequence初始化为0
                            task.other_fields_json,
                            task.timestr,
                            helper_time.ts_since_1970_tz(),
                        ))

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
            self._logger.error(
                "Save new idown_task error: %s" % traceback.format_exc())

        return res

    @table_locker(__tb_IDownTask._tbname)
    def update_idown_task(
            self,
            task: Task,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend) -> bool:
        """更新IDownTask表，根据platform,taskid更新其他所有字段，并重置task.sequence序列"""
        res = False
        conn: SqliteConn = None
        cursor = None
        task: Task = task
        try:
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE Platform=? and TaskId=? and CreateTime=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (task.taskid, task.timestr))
                    result = cursor.fetchall()

                    if result[0][0] > 0:
                        # 只根据TaskId、platform作为条件，
                        # 不考虑 任务文件产生时间与现有数据库中已存在任务的时间，每次直接覆盖，以符合用户操作。
                        # 若来了TaskId一样的数据，则必然分配给同一个ClientId
                        cmd = f'''UPDATE {self._tbname} set
                            CmdStatus=?,
                            ParentTaskId=?,
                            BatchTotalCount=?,
                            BatchCompleteCount=?,
                            TaskType=?,
                            Progress=?,
                            TaskStatus=?,
                            CmdRcvMsg=?,
                            Result=?,
                            Sequence=?,
                            OtherFields=?,
                            CreateTime=?,
                            UpdateTime=? WHERE TaskId=? and Platform=?;'''

                        result = cursor.execute(
                            cmd,
                            (
                                cmdstatus.value,
                                task.parenttaskid,
                                task.batchtotalcount,
                                #批量任务完成数也要重置，因为重置了任务下发状态，变为新任务，需要重新执行
                                task.batchcompletecount,
                                task.taskstatus.value,
                                task.tasktype.value,
                                task.progress,
                                task.taskstatus.value,
                                task._cmdrcvmsg,
                                task._result,
                                0,  #sequence重置
                                task.other_fields_json,
                                task.timestr,
                                helper_time.get_time_sec_tz(),
                                task.taskid,
                                task.platform,
                            ))

                        if result is None or result.rowcount < 1:  # or len(result) < 1:
                            continue
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
                    if res:
                        break

        except Exception:
            self._logger.error(
                "Save new idown_task error: %s" % traceback.format_exc())

        return res

    @table_locker(__tb_IDownTask._tbname)
    def update_idown_task2(self, task: Task) -> bool:
        """更新IDownTask表，根据platform,taskid更新其他所有字段"""
        res = False
        conn: SqliteConn = None
        cursor = None
        task: Task = task
        try:
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE Platform=? and TaskId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (task._platform, task.taskid))
                    result = cursor.fetchall()

                    if result[0][0] > 0:
                        # 只根据TaskId、platform作为条件，
                        # 不考虑 任务文件产生时间与现有数据库中已存在任务的时间，每次直接覆盖，以符合用户操作。
                        # 若来了TaskId一样的数据，则必然分配给同一个ClientId
                        cmd = f'''UPDATE {self._tbname} set
                            CmdStatus=?,
                            ParentTaskId=?,
                            BatchTotalCount=?,
                            BatchCompleteCount=?,
                            TaskType=?,
                            Progress=?,
                            TaskStatus=?,
                            CmdRcvMsg=?,
                            Result=?,
                            Sequence=?,
                            OtherFields=?,
                            CreateTime=?,
                            UpdateTime=? WHERE TaskId=? and Platform=?;'''

                        result = cursor.execute(
                            cmd,
                            (
                                task.cmdstatus.value,
                                task.parenttaskid,
                                task.batchtotalcount,
                                #批量任务完成数也要重置，因为重置了任务下发状态，变为新任务，需要重新执行
                                task.batchcompletecount,
                                task.tasktype.value,
                                task.progress,
                                task.taskstatus.value,
                                task._cmdrcvmsg,
                                task._result,
                                task.sequence,
                                task.other_fields_json,
                                task.timestr,
                                helper_time.get_time_sec_tz(),
                                task.taskid,
                                task.platform,
                            ))

                        if result is None or result.rowcount < 1:  # or len(result) < 1:
                            continue
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
                    if res:
                        break

        except Exception:
            self._logger.error(
                "Update idown_task error: %s" % traceback.format_exc())
        return res

    @table_locker(__tb_IDownTask._tbname)
    def get_task(self, conds: SqlConditions) -> dict:
        """按条件搜索，并返回第一个匹配的IDownTask表数据行"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            cmd = f'''SELECT 
                    CmdStatus,
                    Platform,
                    TaskId,
                    ParentTaskId,
                    BatchTotalCount,
                    BatchCompleteCount,
                    TaskType,
                    Progress,
                    TaskStatus,
                    CmdRcvMsg,
                    Result,
                    Sequence,
                    OtherFields,
                    CreateTime,
                    UpdateTime FROM {self._tbname} WHERE {conds.text_normal}'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, conds.params)
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    for row in result:
                        fields: dict = {}
                        for i in range(len(row)):
                            fields[cursor.description[i][0].lower()] = row[i]

                        return fields

                except Exception:
                    self._logger.error("save_idown_task error: {}".format(
                        traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error(
                "Get idown_task error: %s" % traceback.format_exc())

    @table_locker(__tb_IDownTask._tbname)
    def get_tasks(self, conds: SqlConditions) -> iter:
        """按条件搜索任务，返回数据行转换成的字段字典迭代器"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            cmd = f'''SELECT 
                    CmdStatus,
                    Platform,
                    TaskId,
                    ParentTaskId,
                    BatchTotalCount,
                    BatchCompleteCount,
                    TaskType,
                    Progress,
                    TaskStatus,
                    CmdRcvMsg,
                    Result,
                    Sequence,
                    OtherFields,
                    CreateTime,
                    UpdateTime FROM {self._tbname} WHERE {conds.text_normal}'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, conds.params)
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    for row in result:
                        fields: dict = {}
                        for i in range(len(row)):
                            fields[cursor.description[i][0].lower()] = row[i]

                        yield fields

                except Exception:
                    self._logger.error("save_idown_task error: {}".format(
                        traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error(
                "Get idown_tasks error: %s" % traceback.format_exc())

    @table_locker(__tb_IDownTask._tbname)
    def update_task_batch_total_count(self, task: Task) -> bool:
        """更新指定task的batchtotalcount字段，返回bool指示是否成功"""
        res: bool = False
        conn: SqliteConn = None
        cursor = None
        try:
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE Platform=? and TaskId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        task._platform,
                        task.taskid,
                    ))
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    cmd = f'''UPDATE {self._tbname} set BatchTotalCount=? WHERE TaskId=? and Platform=?;'''
                    result = cursor.execute(cmd, (
                        task.batchtotalcount,
                        task.taskid,
                        task._platform,
                    ))

                    if result is None or result.rowcount < 1:  # or len(result) < 1:
                        continue

                    res = True

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
            self._logger.error("Update idown task batch total count error: %s"
                               % traceback.format_exc())
        return res

    @table_locker(__tb_IDownTask._tbname)
    def get_task_batch_total_count(self, task: Task) -> int:
        """查询指定task的batchtotalcount，返回-1表示没找到指定的task"""
        res: int = -1  #返回-1表示没找到指定的task
        conn: SqliteConn = None
        cursor = None
        try:
            cmd = f'''SELECT BatchTotalCount FROM {self._tbname} WHERE Platform=? and TaskId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        task._platform,
                        task.taskid,
                    ))
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    res = result[0][0]

                except Exception:
                    self._logger.error(
                        "Get IDownTask batchtotalcount error: {}".format(
                            traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

        except Exception:
            self._logger.error("Get IDownTask batchtotalcount error: %s" %
                               traceback.format_exc())
        return res

    @table_locker(__tb_IDownTask._tbname)
    def get_task_batch_complete_count(self, task: Task) -> int:
        """查询指定task的batchcompletecount，返回-1表示没找到指定的task"""
        res: int = -1  #返回-1表示没找到指定的task
        conn: SqliteConn = None
        cursor = None
        try:
            cmd = f'''SELECT BatchCompleteCount FROM {self._tbname} WHERE Platform=? and TaskId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        task._platform,
                        task.taskid,
                    ))
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    res = result[0][0]

                except Exception:
                    self._logger.error(
                        "Get task_batch_complete_count error: {}".format(
                            traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

        except Exception:
            self._logger.error("Get task_batch_complete_count error: %s" %
                               traceback.format_exc())
        return res

    @table_locker(__tb_IDownTask._tbname)
    def get_task_cmdstatus(self, task: Task) -> ECommandStatus:
        """获取指定总任务id的命令状态"""
        res: ECommandStatus = None
        conn: SqliteConn = None
        cursor = None
        try:

            cmd = f'''SELECT CmdStatus FROM {self._tbname} WHERE Platform=? and TaskId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        task._platform,
                        task.taskid,
                    ))
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    tmp = result[0][0]
                    res = ECommandStatus(int(tmp))

                    break

                except Exception as ex:
                    # conn._conn.rollback()
                    # 此为纯 select 方法，不用 rollback
                    raise ex
                else:
                    # conn.commit()
                    # 此为纯 select 方法，不用 commit
                    pass
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

        except Exception:
            self._logger.error(
                "Save new idown_task error: %s" % traceback.format_exc())
        return res

    @table_locker(__tb_IDownTask._tbname)
    def increace_task_batch_complete_count(self,
                                           platform: str,
                                           taskid: str,
                                           increment: int = 1) -> int:
        """原子操作，提升指定Task的batchcompletecount数量。
        task:任务对象\n
        increment:在原有基础上要增加多少，默认为1，可以为负数"""
        res: bool = False
        conn: SqliteConn = None
        cursor = None
        try:
            if not isinstance(increment, int):  # 可以为负数
                raise Exception(
                    "Invalid increment count for task batch complete count")

            cmd = f'''SELECT BatchCompleteCount FROM {self._tbname} WHERE Platform=? and TaskId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        platform,
                        taskid,
                    ))
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    src = result[0][0]

                    target = src + increment
                    cmd = f'''UPDATE {self._tbname} set BatchCompleteCount=? 
                    WHERE Platform=? and TaskId=?;'''

                    result = cursor.execute(cmd, (
                        target,
                        platform,
                        taskid,
                    ))

                    if result is None or result.rowcount < 1:
                        continue

                    res = True

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
            self._logger.error("increace_task_batch_complete_count error: %s" %
                               traceback.format_exc())
        return res

    @table_locker(__tb_IDownTask._tbname)
    def update_idown_task_status(self, task: Task,
                                 cmdstatus: ECommandStatus) -> bool:
        """更新指定task的总任务状态"""
        res: bool = False
        conn: SqliteConn = None
        cursor = None
        try:
            if not isinstance(task, Task):
                self._logger.error("Invalid task object: {}".format(task))
                return res
            if not isinstance(cmdstatus, ECommandStatus):
                self._logger.error("Invalid task status: {}".format(cmdstatus))
                return res

            cmd = f'''UPDATE {self._tbname} set CmdStatus=? WHERE Platform=? and TaskId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        cmdstatus.value,
                        task._platform,
                        task.taskid,
                    ))
                    if result is None or result.rowcount < 1:
                        continue

                    res = True

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
                "Save new idown_task error: %s" % traceback.format_exc())
        return res
