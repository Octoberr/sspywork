"""table idowncmd"""

# -*- coding:utf-8 -*-

import time
import traceback

from commonbaby.helpers import helper_time
from commonbaby.sql import (SqlConn, SqliteColumn, SqliteConn,
                            SqliteConnManager, SqliteIndex, SqliteTable,
                            table_locker)

from datacontract import Client, ECommandStatus, IdownCmd, Task, CmdFeedBack

from ..sqlcondition import SqlCondition, SqlConditions
from .sqlite_config import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbIDownCmd(TbSqliteBase):
    """Task表及相关操作"""

    __tb_IDownCmd: SqliteTable = SqliteTable(
        'IDownCmd',
        True,
        SqliteColumn(colname='Id',
                     coltype='INTEGER',
                     nullable=False,
                     is_primary_key=True,
                     is_auto_increament=True,
                     is_unique=True).set_index_new(),
        SqliteColumn(colname='ClientId').set_index_new(),
        SqliteColumn(colname='CmdId', nullable=False).set_index_new(),
        SqliteColumn(colname='Platform', nullable=False).set_index_new(),
        SqliteColumn(colname='TaskId').set_index_new(),
        SqliteColumn(colname='BatchId').set_index_new(),
        SqliteColumn(colname='Cmd', nullable=False).set_index_new(),
        SqliteColumn(colname='Status', coltype='INTEGER',
                     nullable=False).set_index_new(),
        SqliteColumn(colname='Source').set_index_new(),
        SqliteColumn(colname='CmdRcvMsg'),
        SqliteColumn(colname='CreateTime',
                     coltype='DATETIME',
                     defaultval=helper_time.ts_since_1970_tz()),
        SqliteColumn(colname='UpdateTime', coltype='REAL',
                     nullable=False).set_index_new(),
        SqliteColumn(colname='Sequence',
                     nullable=False,
                     coltype='INTEGER',
                     defaultval=0).set_index_new(),
        SqliteColumn(
            # 指示当前cmd是否是与任何task关联的，0独立的/1关联的
            colname='IsRelative',
            nullable=False,
            coltype='INTEGER',
            defaultval=1).set_index_new(),
    )

    # 主键  ClientId+CmdId
    # 所有列，复制粘贴用...：
    # ClientId
    # CmdId,
    # Platform,
    # TaskId,
    # BatchId,
    # Cmd,
    # Status,
    # Source,
    # CmdRcvMsg,
    # CreateTime,
    # UpdateTime,
    # Sequence,
    # IsRelative

    def __init__(self, dbcfg: SqliteConfig):
        """"""
        TbSqliteBase.__init__(self, TbIDownCmd.__tb_IDownCmd._tbname, dbcfg)

    def _append_tables(self):
        self._conn_mngr.append_table(TbIDownCmd.__tb_IDownCmd)

    @table_locker(__tb_IDownCmd._tbname)
    def save_new_idowncmd(
            self,
            platform: str,
            client: Client,
            command: IdownCmd,
            cmdtime: float,
            cmdstatus: ECommandStatus = ECommandStatus.WaitForSend,
            taskid: str = None,
            batchid: str = None,
            isrelative: int = 1,
    ) -> bool:
        """保存新的批处理任务的令牌资源\n
        task:任务对象"""
        res = False
        conn: SqliteConn = None
        cursor = None
        client: Client = client
        command: IdownCmd = command
        try:
            # 搜索每个库，看有没有 TokenId一样的，且时间更新
            # 的，一样就更新其他所有字段
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE 
            ClientId=? and CmdId=? and Platform=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (
                        client._statusbasic._clientid,
                        command.cmd_id,
                        platform,
                    ))
                    result = cursor.fetchall()

                    if result[0][0] > 0:
                        res = True
                        cmd = f'''UPDATE {self._tbname} set
                            Cmd=?,
                            TaskId=?,
                            BatchId=?,
                            Status=?,
                            Source=?,
                            CreateTime=?,
                            UpdateTime=?,
                            IsRelative=? 
                            WHERE ClientId=? and CmdId=? and Platform=? and CreateTime<=?;'''

                        result = cursor.execute(cmd, (
                            command.cmd_str,
                            taskid,
                            batchid,
                            cmdstatus.value,
                            command.source,
                            helper_time.timespan_to_datestr_tz(cmdtime),
                            helper_time.get_time_sec_tz(),
                            isrelative,
                            client._statusbasic._clientid,
                            command.cmd_id,
                            platform,
                            helper_time.timespan_to_datestr_tz(cmdtime),
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
                    # CmdId,
                    # Platform,
                    # TaskId,
                    # BatchId,
                    # Cmd,
                    # Status,
                    # Source,
                    # CmdRcvMsg,
                    # CreateTime,
                    # UpdateTime,
                    # Sequence
                    # IsRelative

                    # insert
                    cmd = f'''INSERT INTO {self._tbname}(
                        ClientId,
                        CmdId,
                        Platform,
                        TaskId,
                        BatchId,
                        Cmd,
                        Source,
                        Status,
                        CreateTime,
                        UpdateTime,
                        Sequence,
                        IsRelative) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)'''
                    # 有几个属于TaskBack的字段在此不更新
                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        client._statusbasic._clientid,
                        command.cmd_id,
                        platform,
                        taskid,
                        batchid,
                        command.cmd_str,
                        command.source,
                        cmdstatus.value,
                        helper_time.timespan_to_datestr_tz(cmdtime),
                        helper_time.get_time_sec_tz(),
                        0,
                        isrelative,
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
            self._logger.error("save_new_idowncmd error: %s" %
                               traceback.format_exc())

        return res

    @table_locker(__tb_IDownCmd._tbname)
    def select_cmd(self, conds: SqlConditions) -> IdownCmd:
        """按条件搜索任务，返回数据行转换成的字段字典迭代器"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            cmd = f'''SELECT 
                    ClientId,
                    CmdId,
                    Platform,
                    TaskId,
                    BatchId,
                    Cmd,
                    Status,
                    Source,
                    CmdRcvMsg,
                    CreateTime,
                    UpdateTime,
                    Sequence,
                    IsRelative 
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
            self._logger.error("Get IDownCmd error: %s" %
                               traceback.format_exc())

    @table_locker(__tb_IDownCmd._tbname)
    def select_cmds(self, conds: SqlConditions) -> iter:
        """按条件搜索任务，返回数据行转换成的字段字典迭代器"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            cmd = f'''SELECT 
                    ClientId,
                    CmdId,
                    Platform,
                    TaskId,
                    BatchId,
                    Cmd,
                    Status,
                    Source,
                    CmdRcvMsg,
                    CreateTime,
                    UpdateTime,
                    Sequence,
                    IsRelative 
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
                        # if len(row) != 15:
                        #     continue
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
            self._logger.error("Get IDownCmd error: %s" %
                               traceback.format_exc())

    @table_locker(__tb_IDownCmd._tbname)
    def update_cmd_status(self, platform: str, cmdid: str, clientid: str,
                          cmdstatus: ECommandStatus) -> bool:
        """更新cmd的Status状态字段"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        try:
            cmd = f'''UPDATE {self._tbname} set
                    Status=? 
                    WHERE Platform=? and CmdId=? and ClientId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    result = cursor.execute(
                        cmd, (cmdstatus.value, platform, cmdid, clientid))
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

    @table_locker(__tb_IDownCmd._tbname)
    def update_cmd(
            self,
            cmd: IdownCmd,
            taskid: str = None,
            batchid: str = None,
            isrelative: int = 1,
    ) -> bool:
        """更新cmd，条件为platform+cmdid，更新其他可更新字段"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        cmd: IdownCmd = cmd
        try:
            # ClientId
            # CmdId,
            # Platform,
            # TaskId,
            # BatchId,
            # Cmd,
            # Status,
            # Source,
            # CmdRcvMsg,
            # CreateTime,
            # UpdateTime,
            # Sequence,
            # IsRelative

            cmd = f'''UPDATE {self._tbname} set
                    TaskId=?,
                    BatchId=?,
                    Cmd=?,
                    Status=?,
                    Source=?,
                    CmdRcvMsg=?,
                    CreateTime=?,
                    UpdateTime=?,
                    Sequence=?,
                    IsRelative=?  
                    WHERE Platform=? and CmdId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    # task:Task = task
                    result = cursor.execute(
                        cmd,
                        (
                            taskid,
                            batchid,
                            cmd.cmd_str,
                            cmd.cmdstatus.value,
                            cmd.source,
                            cmd.cmdrcvmsg,
                            # 假设数据是按时间先后顺序过来的，所以createtime直接取本地时间。
                            # 若后面有问题，需要加idowncmd命令文件字段createtime字段
                            helper_time.get_time_sec_tz(),
                            helper_time.get_time_sec_tz(),
                            cmd._sequence,
                            isrelative,
                            cmd._platform,
                            cmd.cmd_id,
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

    @table_locker(__tb_IDownCmd._tbname)
    def update_cmdback(self, cmdback: CmdFeedBack) -> bool:
        """更新cmdback到数据库，条件为clientid+cmdid(+platform?)，更新其他可更新字段"""
        conn: SqliteConn = None
        cursor = None
        res: bool = False
        cmdback: CmdFeedBack = cmdback
        try:
            if cmdback is None or cmdback._platform is None:
                raise Exception("Invalid cmdback obj")

            # ClientId
            # CmdId,
            # Platform,
            # TaskId,
            # BatchId,
            # Cmd,
            # Status,
            # Source,
            # CmdRcvMsg,
            # CreateTime,
            # UpdateTime,
            # Sequence,
            # IsRelative
            cmd = f'''UPDATE {self._tbname} set
                    Status=?,
                    CmdRcvMsg=?,
                    UpdateTime=?,
                    Sequence=? 
                    WHERE ClientId=? and CmdId=?;'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    # task:Task = task
                    result = cursor.execute(cmd, (
                        cmdback._cmdstatus.value,
                        cmdback._cmdrcvmsg,
                        helper_time.get_time_sec_tz(),
                        cmdback._sequence,
                        cmdback.clientid,
                        cmdback.cmd_id,
                    ))
                    if not result is None and result.rowcount > 0:
                        res = True
                        break
                    else:
                        self._logger.error(
                            "Cmd not found in db:\ncmdid={}\nclientid={}".
                            format(cmdback.cmd_id, cmdback.clientid))

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
