"""table iscouttask"""

# -*- coding:utf-8 -*-

import time
import traceback
from typing import Tuple

from commonbaby.helpers import helper_time
from commonbaby.sql import (SqlConn, SqliteColumn, SqliteConn,
                            SqliteConnManager, SqliteIndex, SqliteTable,
                            table_locker)

from datacontract import Client, ECommandStatus, IscoutTask, IscoutBtaskBack

from ..sqlcondition import SqlCondition, SqlConditions
from .sqlite_config import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbIScoutBatchTask(TbSqliteBase):
    """Task表及相关操作"""

    __tb_IScoutBTask: SqliteTable = SqliteTable(
        'IScoutBatchTask',
        True,
        SqliteColumn(colname='Id',
                     coltype='INTEGER',
                     nullable=False,
                     is_primary_key=True,
                     is_auto_increament=True,
                     is_unique=True).set_index_new(),
        SqliteColumn(colname='ClientId', nullable=False).set_index_new(),
        SqliteColumn(colname='Platform', nullable=False).set_index_new(),
        SqliteColumn(colname='Source', nullable=False).set_index_new(),
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
        SqliteColumn(colname='TaskId', nullable=False).set_index_new(),
        SqliteColumn(colname='BatchId', nullable=False).set_index_new(),
        SqliteColumn(colname='CmdId').set_index_new(),
        SqliteColumn(colname='Status',
                     coltype='INTEGER',
                     nullable=False,
                     description='采集端执行命令的状态，要反给中心的').set_index_new(),
        SqliteColumn(colname='ObjectType', coltype='INTEGER').set_index_new(),
        SqliteColumn(colname='Object', ).set_index_new(),
        SqliteColumn(
            colname='Progress',  #0~1浮点数表百分比
            coltype='REAL',
            nullable=True),
        SqliteColumn(
            colname='Elapsed',  #0~1浮点数表百分比
            coltype='REAL',
            nullable=True),
        SqliteColumn(colname='CmdRcvMsg'),
        SqliteColumn(colname='IsBatchCompleteCountIncreased',
                     coltype='BOOLEAN').set_index_new(),
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
    # ClientId,
    # Platform,
    # Source,
    # IsPeriod,
    # PeriodNum,
    # StartTime,
    # EndTime,
    # Interval,
    # LastStartTime,
    # LastEndTime
    # TaskId,
    # BatchId,
    # CmdId,
    # Status,
    # ObjectType,
    # Object,
    # Progress,
    # Elapsed,
    # CmdRcvMsg,
    # IsBatchCompleteCountIncreased,
    # CreateTime,
    # UpdateTime,
    # Sequence,

    def __init__(self, dbcfg: SqliteConfig):
        """"""
        TbSqliteBase.__init__(self, TbIScoutBatchTask.__tb_IScoutBTask._tbname,
                              dbcfg)

    def _append_tables(self):
        self._conn_mngr.append_table(TbIScoutBatchTask.__tb_IScoutBTask)

    @table_locker(__tb_IScoutBTask._tbname)
    def save_new_iscoutbtask(
            self,
            task: IscoutTask,
            client: Client,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
    ) -> Tuple[bool, bool]:
        """保存新的批处理任务的令牌资源\n
        task:任务对象"""
        res = False
        isnew: bool = False
        conn: SqliteConn = None
        cursor = None
        task: IscoutTask = task
        try:
            # 搜索每个库，看有没有 TokenId一样的，且时间更新
            # 的，一样就更新其他所有字段
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE 
            TaskId=? and BatchId=? and Platform=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        task.taskid,
                        task.batchid,
                        task._platform,
                    ))
                    result = cursor.fetchall()
                    if result[0][0] > 0:
                        res = True
                        cmd = f'''UPDATE {self._tbname} set
                            ClientId=?,
                            CmdId=?,
                            Source=?,
                            IsPeriod=?,
                            PeriodNum=?,
                            StartTime=?,
                            EndTime=?,
                            Interval=?,
                            LastStartTime=?,
                            LastEndTime=?,
                            Status=?,
                            ObjectType=?,
                            Object=?,
                            Progress=?,
                            Elapsed=?,
                            CmdRcvMsg=?,
                            IsBatchCompleteCountIncreased=?,
                            UpdateTime=?,
                            CreateTime=?,
                            Sequence=? 
                            WHERE TaskId=? and BatchId=? and Platform=? and CreateTime<=?;'''

                        result = cursor.execute(
                            cmd,
                            (
                                client._statusbasic._clientid,
                                task.cmd_id,
                                task.source,
                                1 if task._is_period else 0,
                                # 这里的update是来了新的任务文件，需要直接覆盖periodnum
                                task.periodnum,
                                task.cmd.stratagy.time_start,
                                task.cmd.stratagy.time_end,
                                task.cmd.stratagy.interval,
                                task.laststarttime,
                                task.lastendtime,
                                cmdstatus.value,
                                task._objecttype.value,
                                task._object,
                                task.progress,
                                0,  # elapsed
                                task.cmdrcvmsg,
                                task.isbatchcompletecountincreased,
                                helper_time.get_time_sec_tz(),
                                task.createtimestr,
                                0,  #重置sequence
                                task.taskid,
                                task.batchid,
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
                isnew = True
                conn = self.connect_write(5)
                try:
                    # insert
                    cmd = f'''INSERT INTO {self._tbname}(
                        ClientId,
                        Platform,
                        Source,
                        IsPeriod,
                        PeriodNum,
                        StartTime,
                        EndTime,
                        Interval,
                        LastStartTime,
                        LastEndTime,
                        TaskId,
                        BatchId,
                        CmdId,
                        Status,
                        ObjectType,
                        Object,
                        Progress,
                        Elapsed,
                        CmdRcvMsg,
                        IsBatchCompleteCountIncreased,
                        CreateTime,
                        UpdateTime,
                        Sequence) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                    # 有几个属于TaskBack的字段在此不更新
                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        client._statusbasic._clientid,
                        task._platform,
                        task.source,
                        1 if task._is_period else 0,
                        task.periodnum,
                        task.cmd.stratagy.time_start,
                        task.cmd.stratagy.time_end,
                        task.cmd.stratagy.interval,
                        task.laststarttime,
                        task.lastendtime,
                        task.taskid,
                        task.batchid,
                        task.cmd_id,
                        cmdstatus.value,
                        task._objecttype.value,
                        task._object,
                        task.progress,
                        0,
                        '',
                        task.isbatchcompletecountincreased,
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

        return (res, isnew)

    @table_locker(__tb_IScoutBTask._tbname)
    def select_iscoutbtask(self, conds: SqlConditions) -> dict:
        """按条件搜索任务，返回数据行转换成的字段字典"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            # ClientId,
            # Platform,
            # Source,
            # IsPeriod,
            # PeriodNum,
            # StartTime,
            # EndTime,
            # Interval,
            # LastStartTime,
            # LastEndTime
            # TaskId,
            # BatchId,
            # CmdId,
            # Status,
            # ObjectType,
            # Object,
            # Progress,
            # Elapsed,
            # CmdRcvMsg,
            # IsBatchCompleteCountIncreased,
            # CreateTime,
            # UpdateTime,
            # Sequence,
            cmd = f'''select 
                    ClientId,
                    Platform,
                    Source,
                    IsPeriod,
                    PeriodNum,
                    StartTime,
                    EndTime,
                    Interval,
                    LastStartTime,
                    LastEndTime,
                    TaskId,
                    BatchId,
                    CmdId,
                    Status,
                    ObjectType,
                    Object,
                    Progress,
                    Elapsed,
                    CmdRcvMsg,
                    IsBatchCompleteCountIncreased,
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
            self._logger.error("Get IScoutTask error: %s" %
                               traceback.format_exc())

    @table_locker(__tb_IScoutBTask._tbname)
    def select_iscoutbtasks(self, conds: SqlConditions) -> iter:
        """按条件搜索任务，返回数据行转换成的字段字典迭代器"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            # ClientId,
            # Platform,
            # Source,
            # IsPeriod,
            # PeriodNum,
            # StartTime,
            # EndTime,
            # Interval,
            # LastStartTime,
            # LastEndTime,
            # TaskId,
            # BatchId,
            # CmdId,
            # Status,
            # ObjectType,
            # Object,
            # Progress,
            # Elapsed,
            # CmdRcvMsg,
            # IsBatchCompleteCountIncreased,
            # CreateTime,
            # UpdateTime,
            # Sequence,
            cmd = f'''SELECT 
                    ClientId,
                    Platform,
                    Source,
                    IsPeriod,
                    PeriodNum,
                    StartTime,
                    EndTime,
                    Interval,
                    LastStartTime,
                    LastEndTime,
                    TaskId,
                    BatchId,
                    CmdId,
                    Status,
                    ObjectType,
                    Object,
                    Progress,
                    Elapsed,
                    CmdRcvMsg,
                    IsBatchCompleteCountIncreased,
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
                        for i in range(len(result[0])):
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

    @table_locker(__tb_IScoutBTask._tbname)
    def update_iscoutbtask(self, platform: str, taskid: str, batchid: str,
                           updatefields: dict) -> Tuple[bool, bool]:
        """根据taskid+batchid+platform更新其他字段\n
        task:任务对象"""
        res = False
        conn: SqliteConn = None
        cursor = None
        try:
            # 搜索每个库，看有没有 TokenId一样的，且时间更新
            # 的，一样就更新其他所有字段
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE 
            TaskId=? and BatchId=? and Platform=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (taskid, batchid, platform))
                    result = cursor.fetchall()

                    if result[0][0] > 0:
                        # 只根据TaskId、platform作为条件，
                        # 不考虑 任务文件产生时间与现有数据库中已存在任务的时间，每次直接覆盖，以符合用户操作。
                        # 若来了TaskId一样的数据，则必然分配给同一个ClientId
                        sqlset = ''
                        for k in updatefields.keys():
                            sqlset = sqlset + '{}=?,'.format(k)
                        sqlset = sqlset.rstrip(',')
                        cmd = f'''UPDATE {self._tbname} set {sqlset} WHERE TaskId=? and BatchId=? and Platform=?;'''
                        params = [v for v in updatefields.values()]
                        params.append(taskid)
                        params.append(batchid)
                        params.append(platform)
                        result = cursor.execute(cmd, params)

                        if result is None or result.rowcount < 1:  # or len(result) < 1:
                            continue
                        else:
                            res = True

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
            self._logger.error("save new IScoutTask error: %s" %
                               traceback.format_exc())

        return res

    @table_locker(__tb_IScoutBTask._tbname)
    def update_iscoutbtask_status(
            self,
            platform: str,
            taskid: str,
            batchid: str,
            cmdstatus: ECommandStatus,
    ) -> bool:
        """更新task的Status状态字段"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        try:
            cmd = f'''UPDATE {self._tbname} set
                    Status=? 
                    WHERE Platform=? and Taskid=? and BatchId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
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
            self._logger.error("update {} Status error: {}".format(
                self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IScoutBTask._tbname)
    def update_batch_complete_count_increaced_flag(
            self, platform: str, taskid: str, batchid: str,
            isbatchcompletecountincreased: bool) -> bool:
        """增加指定iscout子任务isbatchcompletecountincreased 字段\n"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        try:
            cmd = f'''UPDATE {self._tbname} set
                    IsBatchCompleteCountIncreased=? 
                    WHERE Platform=? and TaskId=? and BatchId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:

                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        isbatchcompletecountincreased,
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
                "batch {} batch complete count increaced flag error: {}".
                format(self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IScoutBTask._tbname)
    def update_iscoutbtask_back(
            self,
            tb: IscoutBtaskBack,
    ) -> bool:
        """更新iscoutbtask_back"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        tb: IscoutBtaskBack = tb
        try:
            if not isinstance(tb, IscoutBtaskBack):
                self._logger.error(
                    "Invalid param IscoutBtaskBack: {}".format(tb))
                return res

            # 更新策略，先搜一下有没有，并把sequence搜出来，如果
            # 本地sequence和新来的任务的sequence一样，则说明
            # 采集端的sequence出错了，打一句日志并返回False
            cmd = f'''SELECT Sequence FROM {self._tbname} WHERE Platform=? and TaskId=? and BatchId=? and PeriodNum<=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:

                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        tb._platform,
                        tb._taskid,
                        tb._batchid,
                        tb.periodnum,
                    ))
                    result = cursor.fetchall()

                    if result is None or len(result) < 1:
                        continue

                    oldseq = result[0][0]
                    if oldseq >= tb._sequence:
                        self._logger.error(
                            "The comming IscoutBtaskBack.sequence is {}, but which in local db is {}:\ntaskid:{}\nbatchid:{}\nsequence:{}"
                            .format(tb._sequence, oldseq, tb._taskid,
                                    tb._batchid, oldseq))
                        break

                    # ClientId,
                    # Platform,
                    # Source,
                    # IsPeriod,
                    # PeriodNum,
                    # StartTime,
                    # EndTime,
                    # Interval,
                    # TaskId,
                    # BatchId,
                    # CmdId,
                    # Status,
                    # ObjectType,
                    # Object,
                    # Progress,
                    # Elapsed,
                    # CmdRcvMsg,
                    # IsBatchCompleteCountIncreased,
                    # CreateTime,
                    # Sequence,
                    cmd = f'''UPDATE {self._tbname} set
                            PeriodNum=?,
                            Status=?,
                            Progress=?,
                            Elapsed=?,
                            CmdRcvMsg=?,
                            Sequence=?,
                            WHERE Platform=? and TaskId=? and BatchId=? and Sequence<?;'''
                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        tb.periodnum,
                        tb._cmdstatus.value,
                        tb._progress,
                        tb.elapsed,
                        tb._cmdrcvmsg,
                        tb._sequence,
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
            self._logger.error(
                "update IScoutBatchTaskBack to {} error: {}".format(
                    self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IScoutBTask._tbname)
    def get_batch_task_count_by_cmdstatus(self, platform: str, taskid: str,
                                          cmdstatus: ECommandStatus) -> int:
        """查询指定总任务taskid下的所有 为指定命令状态的子任务 的数量"""
        res: int = 0  #总数量
        conn: SqliteConn = None
        cursor = None
        try:
            cmd = f'''SELECT COUNT() FROM {self._tbname} WHERE Platform=? and TaskId=? and Status=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        platform,
                        taskid,
                        cmdstatus.value,
                    ))
                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    tmp = result[0][0]

                    res = res + tmp

                except Exception:
                    self._logger.error(
                        "Select iscoutbtask count by status in {} error: {}".
                        format(self._tbname, traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error(
                "Select iscoutbtask count by status in {} error: {}".format(
                    self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IScoutBTask._tbname)
    def is_iscoutbatch_complete_count_increaced(self, platform: str,
                                                taskid: str,
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
            self._logger.error(
                "Check {} if IsBatchCompleteCountIncreased error: {}".format(
                    self._tbname, traceback.format_exc()))

        return res
