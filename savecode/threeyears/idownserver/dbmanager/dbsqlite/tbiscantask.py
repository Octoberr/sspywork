"""table iscantask"""

# -*- coding:utf-8 -*-

import time
import traceback

from commonbaby.helpers import helper_time
from commonbaby.sql import (SqlConn, SqliteColumn, SqliteConn,
                            SqliteConnManager, SqliteIndex, SqliteTable,
                            table_locker)

from datacontract import Client, ECommandStatus, IscanTask, IscanTaskBack, IscanBtaskBack

from ..sqlcondition import SqlCondition, SqlConditions
from .sqlite_config import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbIScanTask(TbSqliteBase):
    """Task表及相关操作"""

    __tb_IScanTask: SqliteTable = SqliteTable(
        'IScanTask',
        True,
        SqliteColumn(
            colname='Id',
            coltype='INTEGER',
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True).set_index_new(),
        SqliteColumn(colname='ClientId').set_index_new(),
        SqliteColumn(colname='TaskId', nullable=False).set_index_new(),
        SqliteColumn(colname='CmdId', nullable=False).set_index_new(),
        SqliteColumn(colname='Platform', nullable=False).set_index_new(),
        SqliteColumn(
            colname='Status',
            coltype='INTEGER',
            nullable=False,
            defaultval=ECommandStatus.WaitForSend.value).set_index_new(),
        SqliteColumn(
            colname='Progress',  #0~1浮点数表百分比
            coltype='REAL',
            nullable=True),
        SqliteColumn(colname='ScanType', coltype='INTEGER',
                     defaultval=1).set_index_new(),
        SqliteColumn(
            colname='IsPeriod',
            coltype='INTEGER',
            nullable=False,
            defaultval=0).set_index_new(),
        SqliteColumn(
            colname='PeriodNum',
            coltype='INTEGER',
            nullable=False,
            defaultval=0).set_index_new(),
        SqliteColumn(colname='StartTime', coltype='DATETIME'),
        SqliteColumn(colname='EndTime', coltype='DATETIME'),
        SqliteColumn(colname='Interval', coltype='REAL'),
        SqliteColumn(colname='LastStartTime', coltype='DATETIME'),
        SqliteColumn(colname='LastEndTime', coltype='DATETIME'),
        SqliteColumn(colname='Source').set_index_new(),
        SqliteColumn(colname='CmdRcvMsg'),
        SqliteColumn(
            colname='CreateTime',
            coltype='DATETIME',
            defaultval=helper_time.get_time_sec_tz()),
        SqliteColumn(colname='UpdateTime', coltype='REAL',
                     nullable=False).set_index_new(),
        SqliteColumn(
            colname='Sequence',
            nullable=False,
            coltype='INTEGER',
            defaultval=0).set_index_new(),
    )

    # scantype=scansearch 主键  TaskId
    # scantype=scan       主键  TaskId+BatchId
    # 所有列，复制粘贴用...：
    # ClientId
    # TaskId,
    # CmdId,
    # Platform,
    # Status,
    # Progress,
    # ScanType,
    # IsPeriod,
    # PeriodNum,
    # StartTime,
    # EndTime,
    # Interval,
    # LastStartTime,
    # LastEndTime,
    # Source,
    # CmdRcvMsg,
    # CreateTime,
    # UpdateTime,
    # Sequence,

    def __init__(self, dbcfg: SqliteConfig):
        """"""
        TbSqliteBase.__init__(self, TbIScanTask.__tb_IScanTask._tbname, dbcfg)

    def _append_tables(self):
        self._conn_mngr.append_table(TbIScanTask.__tb_IScanTask)

    @table_locker(__tb_IScanTask._tbname)
    def save_new_iscantask(
            self,
            client: Client,
            scantask: IscanTask,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
    ) -> bool:
        """保存新的批处理任务的令牌资源\n
        task:任务对象"""
        res = False
        conn: SqliteConn = None
        cursor = None
        client: Client = client
        scantask: IscanTask = scantask
        try:
            # 搜索每个库，看有没有 TokenId一样的，且时间更新
            # 的，一样就更新其他所有字段
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE 
            ClientId=? and TaskId=? and Platform=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        client._statusbasic._clientid,
                        scantask.taskid,
                        scantask._platform,
                    ))
                    result = cursor.fetchall()

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
                            CmdId=?,
                            Status=?,
                            Progress=?,
                            ScanType=?,
                            Source=?,
                            UpdateTime=?,
                            Sequence=? 
                            WHERE ClientId=? and TaskId=? and Platform=?;'''
                        # and UpdateTime<=? 暂时不判断时间了。因为server端自己也会更新
                        # 这个UpdateTime字段，中心也会更新这个字段，无法保证任务重新下发的
                        # 时候的UpdateTime > 当前server更新过的这个UpdateTime，否则会
                        # 导致明明重新下发了，但server由于任务的UpdateTime小于当前数据库
                        # 中的UpdateTime而更新任务状态失败。

                        result = cursor.execute(
                            cmd,
                            (
                                1 if scantask._is_period else 0,
                                scantask.periodnum,
                                scantask.cmd.stratagy.time_start,
                                scantask.cmd.stratagy.time_end,
                                scantask.cmd.stratagy.interval,
                                scantask.laststarttime,
                                scantask.lastendtime,
                                scantask.cmd_id,
                                cmdstatus.value,
                                scantask.progress,
                                scantask.scantype.value,
                                scantask.source,
                                helper_time.get_time_sec_tz(),
                                0,
                                client._statusbasic._clientid,
                                scantask.taskid,
                                scantask._platform,
                                # scantask.createtime,
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
                    # ClientId
                    # TaskId,
                    # CmdId,
                    # Platform,
                    # Status,
                    # Progress,
                    # ScanType,
                    # IsPeriod,
                    # PeriodNum,
                    # StartTime,
                    # EndTime,
                    # Interval,
                    # LastStartTime,
                    # LastEndTime,
                    # Source,
                    # CmdRcvMsg,
                    # CreateTime,
                    # UpdateTime,
                    # Sequence,

                    # insert
                    cmd = f'''INSERT INTO {self._tbname}(
                        ClientId,
                        TaskId,
                        CmdId,
                        Platform,
                        Status,
                        Progress,
                        ScanType,
                        IsPeriod,
                        PeriodNum,
                        StartTime,
                        EndTime,
                        Interval,
                        LastStartTime,
                        LastEndTime,
                        Source,
                        CmdRcvMsg,
                        CreateTime,
                        UpdateTime,
                        Sequence) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                    # 有几个属于TaskBack的字段在此不更新
                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        client._statusbasic._clientid,
                        scantask.taskid,
                        scantask.cmd_id,
                        scantask._platform,
                        cmdstatus.value,
                        scantask.progress,
                        scantask.scantype.value,
                        1 if scantask._is_period else 0,
                        scantask.periodnum,
                        scantask.cmd.stratagy.time_start,
                        scantask.cmd.stratagy.time_end,
                        scantask.cmd.stratagy.interval,
                        scantask.laststarttime,
                        scantask.lastendtime,
                        scantask.source,
                        '',
                        helper_time.get_time_sec_tz(),
                        scantask.createtimestr,
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
            self._logger.error(
                "save new iscantask error: %s" % traceback.format_exc())

        return res

    @table_locker(__tb_IScanTask._tbname)
    def select_iscantask(self, conds: SqlConditions) -> IscanTask:
        """按条件搜索任务，返回数据行转换成的字段字典"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            # ClientId
            # TaskId,
            # CmdId,
            # Platform,
            # Status,
            # Progress,
            # ScanType,
            # IsPeriod,
            # PeriodNum,
            # StartTime,
            # EndTime,
            # Interval,
            # LastStartTime,
            # LastEndTime,
            # Source,
            # CmdRcvMsg,
            # CreateTime,
            # UpdateTime,
            # Sequence,
            cmd = f'''SELECT 
                    ClientId,
                    TaskId,
                    CmdId,
                    Platform,
                    Status,
                    Progress,
                    ScanType,
                    IsPeriod,
                    PeriodNum,
                    StartTime,
                    EndTime,
                    Interval,
                    LastStartTime,
                    LastEndTime,
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
                    self._logger.error("Get IDownCmd error: {}".format(
                        traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error(
                "Get IScanTask error: %s" % traceback.format_exc())

    @table_locker(__tb_IScanTask._tbname)
    def select_iscantasks(self, conds: SqlConditions) -> iter:
        """按条件搜索任务，返回数据行转换成的字段字典迭代器"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            # ClientId
            # TaskId,
            # CmdId,
            # Platform,
            # Status,
            # Progress,
            # ScanType,
            # IsPeriod,
            # PeriodNum,
            # StartTime,
            # EndTime,
            # Interval,
            # LastStartTime,
            # LastEndTime,
            # Source,
            # CmdRcvMsg,
            # CreateTime,
            # UpdateTime,
            # Sequence,
            cmd = f'''SELECT 
                    ClientId,
                    TaskId,
                    CmdId,
                    Platform,
                    Status,
                    Progress,
                    ScanType,
                    IsPeriod,
                    PeriodNum,
                    StartTime,
                    EndTime,
                    Interval,
                    LastStartTime,
                    LastEndTime,
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
                        for i in range(len(result[0])):
                            fields[cursor.description[i][0].lower()] = row[i]

                        yield fields

                except Exception:
                    self._logger.error("Get IScanTask error: {}".format(
                        traceback.format_exc()))
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error(
                "Get IScanTask error: %s" % traceback.format_exc())

    @table_locker(__tb_IScanTask._tbname)
    def update_iscantask_status(
            self,
            platform: str,
            taskid: str,
            cmdstatus: ECommandStatus,
    ) -> bool:
        """更新cmd的Status状态字段"""
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

    @table_locker(__tb_IScanTask._tbname)
    def update_iscantask(
            self,
            scantask: IscanTask,
    ) -> bool:
        """更新iscantask，条件为platform+taskid，更新其他可更新字段"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        scantask: IscanTask = scantask
        try:
            # ClientId
            # TaskId,
            # CmdId,
            # Platform,
            # Status,
            # Progress,
            # ScanType,
            # IsPeriod,
            # PeriodNum,
            # StartTime,
            # EndTime,
            # Interval,
            # LastStartTime,
            # LastEndTime,
            # Source,
            # CmdRcvMsg,
            # CreateTime,
            # UpdateTime,
            # Sequence,

            cmd = f'''UPDATE {self._tbname} set 
                    Progress=?,
                    IsPeriod=?,
                    PeriodNum=?,
                    StartTime=?,
                    EndTime=?,
                    Interval=?,
                    LastStartTime=?,
                    LastEndTime=?,
                    CmdId=?,
                    Source=?,
                    CreateTime=?,
                    UpdateTime=? 
                    WHERE Platform=? and TaskId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        scantask.progress,
                        1 if scantask._is_period else 0,
                        scantask.periodnum,
                        scantask.cmd.stratagy.time_start,
                        scantask.cmd.stratagy.time_end,
                        scantask.cmd.stratagy.interval,
                        scantask.laststarttime,
                        scantask.lastendtime,
                        scantask.cmd_id,
                        scantask.source,
                        scantask.createtimestr,
                        helper_time.get_time_sec_tz(),
                        scantask._platform,
                        scantask.taskid,
                    ))
                    if not result is None and result.rowcount > 0:
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
            self._logger.error("update {} error: {}".format(
                self._tbname, traceback.format_exc()))

        return res

    @table_locker(__tb_IScanTask._tbname)
    def update_iscantask2(self, platform: str, taskid: str,
                          updatefields: dict) -> bool:
        """根据taskid+platform更新其他字段\n
        task:任务对象"""
        res = False
        conn: SqliteConn = None
        cursor = None
        try:
            # 搜索每个库，看有没有 TokenId一样的，且时间更新
            # 的，一样就更新其他所有字段
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE 
            TaskId=? and Platform=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (taskid, platform))
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
                "save new IScanTask error: %s" % traceback.format_exc())

        return res

    @table_locker(__tb_IScanTask._tbname)
    def update_iscantask_back(self, scantaskback: IscanTaskBack) -> bool:
        """更新iscantaskback到数据库，条件为platform+taskid，更新其他可更新字段"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        scantaskback: IscanTaskBack = scantaskback
        try:
            if not isinstance(scantaskback,
                              IscanTaskBack) or scantaskback._platform is None:
                raise Exception("Invalid IScanTaskBack obj")

            # ClientId
            # TaskId,
            # CmdId,
            # Platform,
            # Status,
            # Progress,
            # ScanType,
            # IsPeriod,
            # PeriodNum,
            # StartTime,
            # EndTime,
            # Interval,
            # LastStartTime,
            # LastEndTime,
            # Source,
            # CmdRcvMsg,
            # CreateTime,
            # UpdateTime,
            # Sequence,
            cmd = f'''UPDATE {self._tbname} set 
                    PeriodNum=?,
                    Status=?,
                    Progress=?,
                    CmdRcvMsg=?,
                    UpdateTime=?,
                    Sequence=? 
                    WHERE Platform=? and TaskId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    # task:Task = task
                    result = cursor.execute(cmd, (
                        scantaskback.periodnum,
                        scantaskback._cmdstatus.value,
                        scantaskback.progress,
                        scantaskback.cmdrcvmsg,
                        helper_time.get_time_sec_tz(),
                        scantaskback._sequence,
                        scantaskback._platform,
                        scantaskback._taskid,
                    ))
                    if not result is None and result.rowcount > 0:
                        res = True
                        break
                    else:
                        self._logger.error(
                            "IScanTask not found in db:\nplatform={}\ntaskid={}"
                            .format(scantaskback._platform,
                                    scantaskback.taskid))

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
            self._logger.error("update CmdFeedBack to db {} error: {}".format(
                self._tbname, traceback.format_exc()))

        return res
