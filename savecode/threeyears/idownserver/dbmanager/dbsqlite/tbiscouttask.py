"""table iscantask"""

# -*- coding:utf-8 -*-

import time
import traceback

from commonbaby.helpers import helper_time
from commonbaby.sql import (SqlConn, SqliteColumn, SqliteConn,
                            SqliteConnManager, SqliteIndex, SqliteTable,
                            table_locker)

from datacontract import Client, ECommandStatus, IscoutTask, IscoutTaskBack

from ..sqlcondition import SqlCondition, SqlConditions
from .sqlite_config import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbIScoutTask(TbSqliteBase):
    """Task表及相关操作"""

    __tb_IScoutTask: SqliteTable = SqliteTable(
        'IScoutTask',
        True,
        SqliteColumn(colname='Id',
                     coltype='INTEGER',
                     nullable=False,
                     is_primary_key=True,
                     is_auto_increament=True,
                     is_unique=True).set_index_new(),
        SqliteColumn(colname='Platform', nullable=False),
        SqliteColumn(colname='TaskId', nullable=False).set_index_new(),
        SqliteColumn(colname='IsPeriod',
                     coltype='INTEGER',
                     nullable=False,
                     defaultval=0).set_index_new(),
        SqliteColumn(colname='PeriodNum',
                     coltype='INTEGER',
                     nullable=False,
                     defaultval=0).set_index_new(),
        SqliteColumn(colname='StartTime', coltype='DATETIME'),
        SqliteColumn(colname='EndTime', coltype='DATETIME'),
        SqliteColumn(colname='Interval', coltype='REAL'),
        SqliteColumn(colname='LastStartTime', coltype='DATETIME'),
        SqliteColumn(colname='LastEndTime', coltype='DATETIME'),
        SqliteColumn(colname='Status',
                     coltype='INTEGER',
                     nullable=False,
                     description='采集端执行命令的状态，要反给中心的').set_index_new(),
        SqliteColumn(
            colname='TaskStatus',
            coltype='INTEGER',
            nullable=False,
            description='采集端执行任务的状态（下载状态等），跟CmdStatus不一样').set_index_new(),
        SqliteColumn(colname='BatchTotalCount', coltype='INTEGER'),
        SqliteColumn(colname='BatchCompleteCount',
                     coltype='INTEGER').set_index_new(),
        SqliteColumn(
            colname='Progress',  #0~1浮点数表百分比
            coltype='REAL',
            nullable=True),
        SqliteColumn(
            colname='Elapsed',  #0~1浮点数表百分比
            coltype='REAL',
            nullable=True),
        SqliteColumn(colname='Source'),
        SqliteColumn(colname='CmdRcvMsg'),
        SqliteColumn(colname='CreateTime',
                     coltype='DATETIME',
                     defaultval='1970-01-01 00:00:00'),
        SqliteColumn(colname='UpdateTime', coltype='REAL',
                     nullable=False).set_index_new(),
        SqliteColumn(colname='Sequence', coltype='INTEGER',
                     defaultval=0).set_index_new(),
    )

    # scantype=scansearch 主键  TaskId
    # scantype=scan       主键  TaskId+BatchId
    # 所有列，复制粘贴用...：
    # Platform,
    # TaskId,
    # IsPeriod,
    # PeriodNum,
    # StartTime,
    # EndTime,
    # Interval,
    # LastStartTime,
    # LastEndTime,
    # Status,
    # TaskStatus,
    # BatchTotalCount,
    # BatchCompleteCount,
    # Progress,
    # Elapsed,
    # Source,
    # CmdRcvMsg,
    # CreateTime,
    # UpdateTime,
    # Sequence,

    def __init__(self, dbcfg: SqliteConfig):
        """"""
        TbSqliteBase.__init__(self, TbIScoutTask.__tb_IScoutTask._tbname,
                              dbcfg)

    def _append_tables(self):
        self._conn_mngr.append_table(TbIScoutTask.__tb_IScoutTask)

    @table_locker(__tb_IScoutTask._tbname)
    def save_new_iscouttask(
            self,
            task: IscoutTask,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
    ) -> bool:
        """保存新的批处理任务的令牌资源\n
        task:任务对象"""
        res = False
        conn: SqliteConn = None
        cursor = None
        task: IscoutTask = task
        try:
            # 搜索每个库，看有没有 TokenId一样的，且时间更新
            # 的，一样就更新其他所有字段
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE 
            TaskId=? and Platform=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        task.taskid,
                        task._platform,
                    ))
                    result = cursor.fetchall()

                    # IsPeriod,
                    # PeriodNum,
                    # StartTime,
                    # EndTime,
                    # Interval,
                    if result[0][0] > 0:
                        res = True
                        cmd = f'''UPDATE {self._tbname} set
                            IsPeriod=?,
                            PeriodNum=?,
                            StartTime=?,
                            EndTime=?,
                            Interval=?,
                            LastStartTime=?,
                            LastEndTime=?,
                            Status=?,
                            TaskStatus=?,
                            BatchTotalCount=?,
                            BatchCompleteCount=?,
                            Progress=?,
                            Elapsed=?,
                            Source=?,
                            CmdRcvMsg=?,
                            CreateTime=?,
                            UpdateTime=?,
                            Sequence=? 
                            WHERE TaskId=? and Platform=? and CreateTime<=?;'''

                        result = cursor.execute(
                            cmd,
                            (
                                1 if task._is_period else 0,
                                task.periodnum,
                                task.cmd.stratagy.time_start,
                                task.cmd.stratagy.time_end,
                                task.cmd.stratagy.interval,
                                task.laststarttime,
                                task.lastendtime,
                                task.cmdstatus.value,
                                task.taskstatus.value,
                                task.batchtotalcount,
                                task.batchcompletecount,
                                task.progress,
                                0,  # 重置消耗时间
                                task.source,
                                task.cmdrcvmsg,
                                task.createtimestr,
                                helper_time.get_time_sec_tz(),
                                0,  #重置sequence
                                task.taskid,
                                task._platform,
                                task.createtimestr,
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
                conn = self.connect_write(5)
                try:
                    # Platform,
                    # TaskId,
                    # IsPeriod,
                    # PeriodNum,
                    # StartTime,
                    # EndTime,
                    # Interval,
                    # LastStartTime,
                    # LastEndTime,
                    # Status,
                    # TaskStatus,
                    # BatchTotalCount,
                    # BatchCompleteCount,
                    # Progress,
                    # Elapsed，
                    # Source,
                    # CmdRcvMsg,
                    # CreateTime,
                    # UpdateTime,
                    # Sequence,

                    # insert
                    cmd = f'''INSERT INTO {self._tbname}(
                        Platform,
                        TaskId,
                        IsPeriod,
                        PeriodNum,
                        StartTime,
                        EndTime,
                        Interval,
                        LastStartTime,
                        LastEndTime,
                        Status,
                        TaskStatus,
                        BatchTotalCount,
                        BatchCompleteCount,
                        Progress,
                        Elapsed,
                        Source,
                        CmdRcvMsg,
                        CreateTime,
                        UpdateTime,
                        Sequence) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                    # 有几个属于TaskBack的字段在此不更新
                    cursor = conn.cursor
                    result = cursor.execute(
                        cmd,
                        (
                            task._platform,
                            task.taskid,
                            1 if task._is_period else 0,
                            task.periodnum,
                            task.cmd.stratagy.time_start,
                            task.cmd.stratagy.time_end,
                            task.cmd.stratagy.interval,
                            task.laststarttime,
                            task.lastendtime,
                            task.cmdstatus.value,
                            task.taskstatus.value,
                            task.batchtotalcount,
                            task.batchcompletecount,
                            0,  # progress
                            0,  # elapsed
                            task.source,
                            '',
                            task.createtimestr,
                            helper_time.get_time_sec_tz(),
                            0,
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
            self._logger.error("save new IScoutTask error: %s" %
                               traceback.format_exc())

        return res

    @table_locker(__tb_IScoutTask._tbname)
    def select_iscouttask(self, conds: SqlConditions) -> dict:
        """按条件搜索任务，返回数据行转换成的字段字典"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            cmd = f'''SELECT 
                    Platform,
                    TaskId,
                    IsPeriod,
                    PeriodNum,
                    StartTime,
                    EndTime,
                    Interval,
                    LastStartTime,
                    LastEndTime,
                    Status,
                    TaskStatus,
                    BatchTotalCount,
                    BatchCompleteCount,
                    Progress,
                    Elapsed,
                    Source,
                    CmdRcvMsg,
                    CreateTime,
                    UpdateTime,
                    Sequence 
                    FROM {self._tbname} WHERE {conds.text_normal}'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                conn._conn.row_factory = self._dict_factory
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, conds.params)
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    fields: dict = {}
                    for i in range(len(result[0])):
                        fields[cursor.description[i][0].lower()] = result[0][i]

                    return fields

                except Exception:
                    self._logger.error("Get IScoutTask error: {}".format(
                        traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error("Get IScanTask error: %s" %
                               traceback.format_exc())

    @table_locker(__tb_IScoutTask._tbname)
    def select_iscouttasks(self, conds: SqlConditions) -> iter:
        """按条件搜索任务，返回数据行转换成的字段字典迭代器"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            # Platform,
            # TaskId,
            # IsPeriod,
            # PeriodNum,
            # StartTime,
            # EndTime,
            # Interval,
            # LastStartTime,
            # LastEndTime,
            # Status,
            # TaskStatus,
            # BatchTotalCount,
            # BatchCompleteCount,
            # Progress,
            # Elapsed,
            # Source,
            # CmdRcvMsg,
            # CreateTime,
            # UpdateTime,
            # Sequence,
            cmd = f'''SELECT 
                    Platform,
                    TaskId,
                    IsPeriod,
                    PeriodNum,
                    StartTime,
                    EndTime,
                    Interval,
                    LastStartTime,
                    LastEndTime,
                    Status,
                    TaskStatus,
                    BatchTotalCount,
                    BatchCompleteCount,
                    Progress,
                    Elapsed,
                    Source,
                    CmdRcvMsg,
                    CreateTime,
                    UpdateTime,
                    Sequence 
                    FROM {self._tbname} WHERE {conds.text_normal}'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                conn._conn.row_factory = self._dict_factory
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
                    self._logger.error("Get IScoutTask error: {}".format(
                        traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error("Get IScoutTask error: %s" %
                               traceback.format_exc())

    @table_locker(__tb_IScoutTask._tbname)
    def update_iscouttask_status(
            self,
            platform: str,
            taskid: str,
            cmdstatus: ECommandStatus,
    ) -> bool:
        """更新task的Status状态字段"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        try:
            cmd = f'''UPDATE {self._tbname} set
                    Status=? 
                    WHERE Platform=? and Taskid=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        cmdstatus.value,
                        platform,
                        taskid,
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
            self._logger.error("update {} Status error: {}".format(
                self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IScoutTask._tbname)
    def update_iscouttask2(self, task: IscoutTask) -> bool:
        """更新IScoutTask表，根据platform,taskid更新其他所有字段"""
        res = False
        conn: SqliteConn = None
        cursor = None
        task: IscoutTask = task
        try:
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE Platform=? and TaskId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (task._platform, task.taskid))
                    result = cursor.fetchall()

                    # Platform,
                    # TaskId,
                    # IsPeriod,
                    # PeriodNum,
                    # StartTime,
                    # EndTime,
                    # Interval,
                    # LastStartTime,
                    # LastEndTime,
                    # Status,
                    # TaskStatus,
                    # BatchTotalCount,
                    # BatchCompleteCount,
                    # Progress,
                    # Elapsed,
                    # Source,
                    # CmdRcvMsg,
                    # CreateTime,
                    # UpdateTime,
                    # Sequence,
                    if result[0][0] > 0:
                        # 只根据TaskId、platform作为条件，
                        # 不考虑 任务文件产生时间与现有数据库中已存在任务的时间，每次直接覆盖，以符合用户操作。
                        # 若来了TaskId一样的数据，则必然分配给同一个ClientId
                        cmd = f'''UPDATE {self._tbname} set
                            IsPeriod=?,
                            PeriodNum=?,
                            StartTime=?,
                            EndTime=?,
                            Interval=?,
                            LastStartTime=?,
                            LastEndTime=?,
                            Status=?,
                            TaskStatus=?,
                            BatchTotalCount=?,
                            BatchCompleteCount=?,
                            Progress=?,
                            Elapsed=?,
                            Source=?,
                            CmdRcvMsg=?,
                            Sequence=?,
                            CreateTime=?,
                            UpdateTime=? WHERE TaskId=? and Platform=?;'''

                        result = cursor.execute(cmd, (
                            1 if task._is_period else 0,
                            task.periodnum,
                            task.cmd.stratagy.time_start,
                            task.cmd.stratagy.time_end,
                            task.cmd.stratagy.interval,
                            task.laststarttime,
                            task.lastendtime,
                            task.cmdstatus.value,
                            task.taskstatus.value,
                            task.batchtotalcount,
                            task.batchcompletecount,
                            task.progress,
                            task.elapsed,
                            task.source,
                            task.cmdrcvmsg,
                            task.sequence,
                            task.createtimestr,
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
            self._logger.error("Update IScoutTask error: %s" %
                               traceback.format_exc())
        return res

    @table_locker(__tb_IScoutTask._tbname)
    def update_iscouttask3(self, platform: str, taskid: str,
                           updatefields: dict) -> bool:
        """更新IScoutTask表，根据platform,taskid更新指定字段"""
        res = False
        conn: SqliteConn = None
        cursor = None
        try:
            if not isinstance(updatefields, dict) or len(updatefields) < 1:
                return True
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE Platform=? and TaskId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (platform, taskid))
                    result = cursor.fetchall()

                    if result[0][0] > 0:
                        # 只根据TaskId、platform作为条件，
                        # 不考虑 任务文件产生时间与现有数据库中已存在任务的时间，每次直接覆盖，以符合用户操作。
                        # 若来了TaskId一样的数据，则必然分配给同一个ClientId
                        sqlset = ''
                        for k in updatefields.keys():
                            sqlset = sqlset + '{}=?,'.format(k)
                        sqlset = sqlset.rstrip(',')
                        cmd = f'''UPDATE {self._tbname} set {sqlset} WHERE TaskId=? and Platform=?;'''
                        params = [v for v in updatefields.values()]
                        params.append(taskid)
                        params.append(platform)
                        result = cursor.execute(cmd, params)

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
            self._logger.error("Update IScoutTask error: %s" %
                               traceback.format_exc())
        return res

    @table_locker(__tb_IScoutTask._tbname)
    def get_iscouttask_batch_total_count(self, platform: str,
                                         taskid: str) -> int:
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
                        platform,
                        taskid,
                    ))
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    res = result[0][0]

                except Exception:
                    self._logger.error(
                        "Get IScoutTask batchtotalcount error: {}".format(
                            traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

        except Exception:
            self._logger.error("Get IScoutTask batchtotalcount error: %s" %
                               traceback.format_exc())
        return res

    @table_locker(__tb_IScoutTask._tbname)
    def get_iscouttask_batch_complete_count(self, platform: str,
                                            taskid: str) -> int:
        """查询指定task的batchtotalcount，返回-1表示没找到指定的task"""
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
                        platform,
                        taskid,
                    ))
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    res = result[0][0]

                except Exception:
                    self._logger.error(
                        "Get IScoutTask batchcompletecount error: {}".format(
                            traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

        except Exception:
            self._logger.error("Get IScoutTask batchcompletecount error: %s" %
                               traceback.format_exc())
        return res

    @table_locker(__tb_IScoutTask._tbname)
    def update_iscouttask_batch_total_count(self, task: IscoutTask) -> bool:
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
            self._logger.error(
                "Update iscout task batch total count error: %s" %
                traceback.format_exc())
        return res

    @table_locker(__tb_IScoutTask._tbname)
    def increace_iscouttask_batch_complete_count(self,
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
            self._logger.error(
                "increace_iscouttask_batch_complete_count error: %s" %
                traceback.format_exc())
        return res

    @table_locker(__tb_IScoutTask._tbname)
    def get_iscouttask_sequence(self, platform: str, taskid: str) -> int:
        """获取指定的总任务的sequence"""
        res: int = 0
        conn: SqliteConn = None
        cursor = None
        try:
            cmd = f'''SELECT Sequence FROM {self._tbname} WHERE Platform=? and TaskId=?'''
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

                    res = result[0][0]
                    if not isinstance(res, int):
                        res = int(res)

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
            self._logger.error("get_iscouttask_sequence error: %s" %
                               traceback.format_exc())
        return res

    @table_locker(__tb_IScoutTask._tbname)
    def get_iscouttask_elapsed(self, platform: str, taskid: str) -> float:
        """获取指定的总任务的 elapsed"""
        res: float = 0
        conn: SqliteConn = None
        cursor = None
        try:
            cmd = f'''SELECT Elapsed FROM {self._tbname} WHERE Platform=? and TaskId=?'''
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

                    res = result[0][0]
                    if type(res) in [int, float]:
                        res = float(res)

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
            self._logger.error("Get iscouttask elapsed error: %s" %
                               traceback.format_exc())
        return res
