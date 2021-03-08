"""sqlite table base"""

# -*- coding:utf-8 -*-

import sqlite3
import threading
import traceback
from abc import ABCMeta, abstractmethod

from commonbaby.mslog import MsLogger, MsLogManager
from commonbaby.sql import (SqlConn, SqliteColumn, SqliteConn,
                            SqliteConnManager, SqliteIndex, SqliteTable,
                            table_locker, table_locker_manual)

from .sqlite_config import SqliteConfig


class TbSqliteBase:
    """表示一个sqlite表操作基类"""

    __metaclass = ABCMeta

    _logger: MsLogger = MsLogManager.get_logger("DbSqlite")

    __all_tablenames: dict = {}
    __all_tablenames_locker = threading.RLock()

    def __init__(self, tbname: str, dbcfg: SqliteConfig):
        if not isinstance(tbname, str):
            raise Exception(
                "Invalid table name for TbSqliteBase: {}".format(tbname))

        with TbSqliteBase.__all_tablenames_locker:
            if TbSqliteBase.__all_tablenames.__contains__(tbname):
                raise Exception(
                    "Reduplicated table name for TbSqliteBase: {}".format(
                        tbname))

        if not isinstance(dbcfg, SqliteConfig):
            raise Exception("Invalid db config")

        self._tbname: str = tbname
        self._dbconfig: SqliteConfig = dbcfg

        self._conn_mngr: SqliteConnManager = SqliteConnManager(
            dbdir=self._dbconfig._dbdir,
            dbname='{}.db'.format(self._tbname),
            maxdbfisize=self._dbconfig._maxdbfisize,
            maxconnperdb=self._dbconfig._maxconnperdb,
            connecttimeoutsec=self._dbconfig._connecttimeoutsec,
            delete_on_error=self._dbconfig._delete_on_error,
        )

        self._append_tables()

    def _dict_factory(self, cursor, row):
        """dict factory for sqlite data rows"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def _text_factory(self, x):
        """text factory"""
        if x is None:
            return ''

        res = self._try_decode(x, 'utf-8')
        if res is None:
            res = self._try_decode(x, 'gb2312')
        if res is None:
            res = self._try_decode(x, 'gbk')
        if res is None:
            res = self._try_decode(x, 'unicode')
        if res is None:
            raise Exception("decode failed:" + x)

    def _try_decode(self, s: bytes, charset: str):
        try:
            if charset is None or charset == "":
                raise ValueError("charset is empty")

            if s is None:
                return ''

            return s.decode(charset)

        except Exception:
            return None

    @abstractmethod
    def _append_tables(self):
        """子类实现时，需要向当前tablesqlitebase对象中添加表，以执行自动建表\n
        例： self._conn_mngr._append_tables(SqliteTable(xxxx))"""
        raise NotImplementedError()

    def connect_write(self, timeout=None) -> SqlConn:
        """获取sqlite可用于增删改的链接"""
        conn = None
        try:
            conn = self._conn_mngr.connect_write(timeout)
        except Exception as ex:
            if not conn is None and not conn._conn_closed:
                conn.close()
            raise ex
        return conn

    def connect_all(self, timeout=None) -> iter:
        """获取sqlite所有数据库链接"""
        return self._conn_mngr.connect_all(timeout)

    def execute_search_one(self,
                           tablename: str,
                           sql: str,
                           params: tuple = None) -> sqlite3.Row:
        """执行增删改这种修改操作"""
        if not isinstance(tablename, str) or tablename == "":
            raise Exception("Must pass 'tablename' param")
        if not isinstance(tablename, str) or tablename == "":
            raise Exception("Must pass 'tablename' param")
        if not isinstance(sql, str) or sql == "":
            return False
        conn: SqliteConn = None
        cursor = None
        res = None
        try:
            with table_locker_manual(tablename):
                for conn in self._conn_mngr.connect_all():
                    # conn = DbSqlite._conn_mngr.connect_write()
                    cursor = conn.cursor

                    # cursor.execute(sql)

                    if not isinstance(params, tuple) or len(params) < 1:
                        cursor.execute(sql)
                    else:
                        cursor.execute(sql, params)

                    result = cursor.fetchall()
                    if len(result) < 1:
                        return res

                    fields: dict = {}
                    for i in range(len(result[0])):
                        fields[cursor.description[i][0].lower()] = result[0][i]

                    return fields

        except Exception:
            self._logger.error(
                "Get client status error: %s" % traceback.format_exc())
        finally:
            if not conn is None:
                conn.close()
        return res

    def execute_search_all(self,
                           tablename: str,
                           sql: str,
                           return_with_conn: bool = False,
                           params: tuple = None) -> iter:
        """执行增删改这种修改操作\n
        return_with_conn: 是否将结果与对应的数据库链接一并返回，默认为False"""
        if not isinstance(tablename, str) or tablename == "":
            raise Exception("Must pass 'tablename' param")
        if not isinstance(sql, str) or sql == "":
            return False
        conn: SqliteConn = None
        cursor = None
        try:
            with table_locker_manual(tablename):
                for conn in self._conn_mngr.connect_all():

                    try:
                        # conn = DbSqlite._conn_mngr.connect_write()
                        cursor = conn.cursor
                        # conn._conn.row_factory = self._dict_factory
                        # cursor = conn._conn.cursor()
                        if not isinstance(params, tuple) or len(params) < 1:
                            cursor.execute(sql)
                        else:
                            cursor.execute(sql, params)

                        result = cursor.fetchall()
                        if result is None or len(result) < 1:
                            continue

                        for line in result:
                            fields: dict = {}
                            for i in range(len(line)):
                                fields[cursor.description[i]
                                [0].lower()] = line[i]

                            yield fields

                    except Exception as ex:
                        raise ex
                    finally:
                        if not conn is None:
                            conn.close()

        except Exception:
            self._logger.error(
                "Get client status error: %s" % traceback.format_exc())

    def execute_modify(self, tablename: str, sql: str,
                       params: tuple = None) -> bool:
        """执行增删改这种修改操作"""
        if not isinstance(tablename, str) or tablename == "":
            raise Exception("Must pass 'tablename' param")
        if not isinstance(sql, str) or sql == "":
            return False
        res: int = 0
        conn: SqliteConn = None
        cursor = None
        try:
            conn = self._conn_mngr.connect_write()
            cursor = conn.cursor

            if not isinstance(params, tuple) or len(params) < 1:
                res = cursor.execute(sql)
            else:
                res = cursor.execute(sql, params)

            res = res.rowcount
            conn.commit()

        except Exception:
            self._logger.error(
                "Execute modify sql error: %s" % traceback.format_exc())
        finally:
            if not conn is None:
                conn.close()
        return res
