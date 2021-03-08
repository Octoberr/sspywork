"""
数据库表的基类
create by judy
2019/02/20
"""
import threading
from abc import ABCMeta, abstractmethod

from commonbaby.mslog import MsLogger, MsLogManager
from commonbaby.sql import (SqlConn, SqliteConnManager)

from idownclient.config_db import sqlitecfg
from .sqliteconfig import SqliteConfig


class TbSqliteBase(object):
    """表示一个sqlite表操作基类"""
    __metaclass = ABCMeta

    _logger: MsLogger = MsLogManager.get_logger("DbSqlite")

    __all_tablenames: dict = {}
    __all_tablenames_locker = threading.RLock()

    def __init__(self, tbname: str, dbcfg: SqliteConfig, databasename: str):
        if not isinstance(tbname, str):
            raise Exception("Invalid table name for TbSqliteBase: {}".format(tbname))

        with TbSqliteBase.__all_tablenames_locker:
            if TbSqliteBase.__all_tablenames.__contains__(tbname):
                raise Exception("Reduplicated table name for TbSqliteBase: {}".format(tbname))

        if not isinstance(dbcfg, SqliteConfig):
            raise Exception("Invalid db config")

        if not isinstance(databasename, str):
            raise Exception('Database cannot be None')

        self.databasename = databasename
        self._tbname: str = tbname
        self._dbconfig: SqliteConfig = dbcfg

        self._conn_mngr: SqliteConnManager = SqliteConnManager(
            dbdir=sqlitecfg._dbdir,
            dbname=f'{self.databasename}.db',
            maxdbfisize=sqlitecfg._maxdbfisize,
            maxconnperdb=sqlitecfg._maxconnperdb,
            connecttimeoutsec=sqlitecfg._connecttimeoutsec,
            delete_on_error=sqlitecfg._delete_on_error,
        )

        self._append_tables()

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

    def _dict_factory(self, cursor, row):
        """
        格式化查询结果为字典
        :param cursor:
        :param row:
        :return:
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
