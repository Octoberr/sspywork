"""table idownbatchtoken"""

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


class TbIDownBatchToken(TbSqliteBase):
    """Task表及相关操作"""

    __tb_IDownBatchToken: SqliteTable = SqliteTable(
        'IDownBatchToken',
        True,
        SqliteColumn(
            colname='Id',
            coltype='INTEGER',
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True).set_index_new(),
        SqliteColumn(colname='TokenId', nullable=False).set_index_new(),
        SqliteColumn(colname='TokenType', coltype='INTEGER',
                     nullable=False).set_index_new(),
        SqliteColumn(colname='Input'),
        SqliteColumn(colname='PreGlobalTelCode'),
        SqliteColumn(colname='PreAccount'),
        SqliteColumn(colname='GlobalTelCode'),
        SqliteColumn(colname='Phone'),
        SqliteColumn(colname='Account'),
        SqliteColumn(colname='Password'),
        SqliteColumn(colname='Url'),
        SqliteColumn(colname='Host'),
        SqliteColumn(colname='Cookie'),
        SqliteColumn(
            colname='CreateTime',
            coltype='DATETIME',
            defaultval=helper_time.ts_since_1970_tz()),
        SqliteColumn(colname='UpdateTime', coltype='REAL',
                     nullable=False).set_index_new(),
    )

    # 所有列，复制粘贴用...：
    # TokenId,
    # TokenType,
    # Input,
    # PreGlobalTelCode,
    # PreAccount,
    # GlobalTelCode,
    # Phone,
    # Account,
    # Password,
    # Url,
    # Host,
    # Cookie,
    # UpdateTime,
    # CreateTime

    def __init__(self, dbcfg: SqliteConfig):
        """"""
        TbSqliteBase.__init__(
            self, TbIDownBatchToken.__tb_IDownBatchToken._tbname, dbcfg)

    def _append_tables(self):
        self._conn_mngr.append_table(TbIDownBatchToken.__tb_IDownBatchToken)

    @table_locker(__tb_IDownBatchToken._tbname)
    def save_new_idownbatchtoken(
            self,
            task: Task,
    ) -> bool:
        """保存新的批处理任务的令牌资源\n
        task:任务对象"""
        res = False
        conn: SqliteConn = None
        cursor = None
        task: Task = task
        try:
            # 搜索每个库，看有没有 TokenId一样的，且时间更新
            # 的，一样就更新其他所有字段
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE 
            TokenId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (task.tokenid, ))
                    result = cursor.fetchall()

                    if result[0][0] > 0:
                        res = True
                        # 只根据TaskId、ParentTaskId和ClientId关联，
                        # 不考虑 任务文件产生时间与现有数据库中已存在任务的时间，每次直接覆盖，以符合用户操作。
                        # 若来了TaskId一样的数据，则必然分配给同一个ClientId
                        cmd = f'''UPDATE {self._tbname} set
                            TokenType=?,
                            Input=?,
                            PreGlobalTelCode=?,
                            PreAccount=?,
                            GlobalTelCode=?,
                            Phone=?,
                            Account=?,
                            Password=?,
                            Url=?,
                            Host=?,
                            Cookie=?
                            WHERE TokenId=? and UpdateTime<=?;'''

                        result = cursor.execute(cmd, (
                            task.tokentype.value,
                            task.input,
                            task.preglobaltelcode,
                            task.preaccount,
                            task.globaltelcode,
                            task.phone,
                            task.account,
                            task.password,
                            task.url,
                            task.host,
                            task.cookie,
                            task.tokenid,
                            task.time,
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
                    # insert
                    cmd = f'''INSERT INTO {self._tbname}(
                        TokenId,
                        TokenType,
                        Input,
                        PreGlobalTelCode,
                        PreAccount,
                        GlobalTelCode,
                        Phone,
                        Account,
                        Password,
                        Url,
                        Host,
                        Cookie,
                        UpdateTime,
                        CreateTime) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                    # 有几个属于TaskBack的字段在此不更新
                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        task.tokenid,
                        task.tokentype.value,
                        task.input,
                        task.preglobaltelcode,
                        task.preaccount,
                        task.globaltelcode,
                        task.phone,
                        task.account,
                        task.password,
                        task.url,
                        task.host,
                        task.cookie,
                        task.time,
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
                "save_new_idownbatchtask error: %s" % traceback.format_exc())

        return res

    @table_locker(__tb_IDownBatchToken._tbname)
    def select_token(self, conds: SqlConditions) -> iter:
        """按条件搜索任务，返回数据行转换成的字段字典迭代器"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            cmd = f'''SELECT 
                    TokenId,
                    TokenType,
                    Input,
                    PreGlobalTelCode,
                    PreAccount,
                    GlobalTelCode,
                    Phone,
                    Account,
                    Password,
                    Url,
                    Host,
                    Cookie,
                    UpdateTime,
                    CreateTime FROM {self._tbname} WHERE {conds.text_normal}'''
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
            self._logger.error(
                "Save new idown_task error: %s" % traceback.format_exc())

    @table_locker(__tb_IDownBatchToken._tbname)
    def select_token_one(self, conds: SqlConditions) -> dict:
        """按条件搜索任务，返回数据行转换成的字段字典"""
        for fields in self.select_token(conds):
            return fields
