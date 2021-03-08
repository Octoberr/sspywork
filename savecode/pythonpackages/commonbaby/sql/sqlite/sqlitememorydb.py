"""sqlite operator"""

# -*- coding:utf-8 -*-

import os
import queue
import shutil
import sqlite3
import threading
import time
import traceback

from ..sqlconn import SqlConn
from .sqliteconn import SqliteConn, SqliteCursor
from .sqlitetable import SqliteColumn, SqliteTable
from commonbaby.helpers import helper_decorate

# 对每个表的操作上锁
__table_lockers: dict = {}
__table_lockers_locker = threading.RLock()


def table_locker(tablename: str):
    """表操作上锁装饰器，参数名填写表名，避免多线程抢占同一sqlite
    文件资源同时提交出错。用法：\n
    
    @table_locker("TableA")\n
    def save_to_TableA(xxx):
        xxx
    """

    if not isinstance(tablename, str) or tablename == "":
        raise Exception("Table name must be specified")
    if not __table_lockers.__contains__(tablename):
        with __table_lockers_locker:
            if not __table_lockers.__contains__(tablename):
                __table_lockers[tablename] = threading.RLock()

    def lock_table(func: callable):
        """上锁"""

        def do_func(*args, **kwargs):

            with __table_lockers[tablename]:
                return func(*args, **kwargs)

        do_func.__doc__ = func.__doc__
        return do_func

    return lock_table


# 对于同一个监控目录下的一个数据库文件，只能有一个SqliteConnManager实例，
# 所以此处使用单例模式，若dbdir一样，则返回已有SqliteConnManager实例，
# 例：\n
# xxx/aaa.db 和 xxx/aaa.db 返回同一个 SqliteConnManager实例，
# xxx/aaa.db 和 xxx/bbb.db 返回不同的SqliteConnManager实例
__db_mutex = threading.RLock()
__dbmngrs: dict = {}


def __check_dbfi_mutex(dbpath: str) -> bool:
    """检查数据库文件互斥锁，若互斥，则返回已有的SqliteConnManager实例，否则返回False"""
    if dbpath is None:
        raise Exception("Param 'dbpath' for dbfi mutex is None or empty")
    with __db_mutex:
        if __dbmngrs.__contains__(dbpath):
            return __dbmngrs[dbpath]
        else:
            return False


def __add_current_dbmngr_instance(mngr, db_mutex_path):
    """将当前实例添加到互斥锁集合"""
    if mngr is None:
        raise Exception("Given param 'mngr' is invalid")
    with __db_mutex:
        if not __dbmngrs.__contains__(db_mutex_path):
            __dbmngrs[db_mutex_path] = mngr


def __remove_current_dbmngr_instance(mngr):
    """从互斥锁集合中移除当前实例"""
    if mngr is None:
        raise Exception("Given param 'mngr' is invalid")
    with __db_mutex:
        if __dbmngrs.__contains__(mngr.__db_mutex_path):
            __dbmngrs.pop(mngr.__db_mutex_path, None)


def __singleton_connmngr(cls):
    """单例"""

    # __singleton_connmngr.__doc__ = cls.__doc__

    def _singleton(dbname: str = 'data.db',
                   pagesize: int = 512,
                   max_page_count: int = 204800,
                   connecttimeoutsec: float = 60,
                   delete_on_error: bool = True,
                   loghook: callable = None,
                   *tables):
        """"""

        with __db_mutex:
            db_mutex_path: str = os.path.join(':memory:', dbname)
            # 检查互斥锁
            mtx_result = __check_dbfi_mutex(db_mutex_path)
            if isinstance(mtx_result, cls):
                return mtx_result
            inst = cls(
                dbname=dbname,
                pagesize=pagesize,
                max_page_count=max_page_count,
                connecttimeoutsec=connecttimeoutsec,
                delete_on_error=delete_on_error,
                loghook=loghook,
                *tables)
            __add_current_dbmngr_instance(inst, db_mutex_path)
            return inst

    _singleton.__doc__ = cls.__doc__
    return _singleton


@__singleton_connmngr
class SqliteMemoryDB:
    """注意：外部自行控制并发操作，多线程等。
    check_create_table: 检查并创建针对当前数据库文件的表的函数: def foo(self, conn): xxx\n
    dbname: 数据库文件名\n
    maxdbfisize: 数据库最大大小\n
    maxconnperdb: 每个数据库允许的最大同时链接数量，默认为20个\n
    connecttimeoutsec: 数据库链接超时时间，float，单位秒，默认60秒\n
    delete_on_error: 是否删除出错的数据库，默认为True\n
    loghook: 接收日志输出的函数，callable, 默认为 lambda msg: print(msg)\n
    tables: SqliteTable objects"""

    def __init__(self,
                 dbname: str = 'data.db',
                 pagesize: int = 512,
                 max_page_count: int = 204800,
                 connecttimeoutsec: float = 60,
                 delete_on_error: bool = True,
                 loghook: callable = None,
                 *tables):
        """"""
        self._tables_locker = threading.RLock()
        self._tables: dict = {}
        for t in tables:
            self.append_table(t)

        self._dbdir = ":memory:"

        self._dbname = "data.db"
        if isinstance(dbname, str) and not dbname == "":
            self._dbname = dbname

        self.__db_mutex_path: str = os.path.join(self._dbdir, dbname)

        self._pagesize: int = pagesize
        self._maxpagecount = max_page_count

        self._connecttimeoutsec: float = 60
        if type(connecttimeoutsec) in [int, float]:
            if connecttimeoutsec <= 0:
                self._connecttimeoutsec = None
            else:
                self._connecttimeoutsec = connecttimeoutsec

        self._delete_on_error: bool = True
        if isinstance(delete_on_error, bool):
            self._delete_on_error = delete_on_error

        self._loghook: callable = lambda msg: print(msg)
        if callable(loghook):
            self._loghook = loghook

        self.__conn_locker = threading.RLock()
        self.__conn = SqliteConn(self.__dispose_conn, ":memory:",
                                 self._connecttimeoutsec)

        cur = self.conn.cursor
        cur.execute("PRAGMA max_page_count = 195313")
        cur.execute("PRAGMA page_size = 512")
        self.conn.commit()

    @property
    def conn(self) -> SqliteConn:
        # self.__conn._re_init()
        return self.__conn

    def append_table(self, table: SqliteTable):
        """向当前连接管理器添加一个表(若表不存在于当前连接管理器中)，
        并返回当前SqliteConnManager对象本身"""
        if not isinstance(table, SqliteTable):
            raise Exception("Table is invalid")
        if self._tables.__contains__(table._tbname):
            # 若已存在同名表，则视为已添加
            return self
        with self._tables_locker:
            if self._tables.__contains__(table._tbname):
                # 若已存在同名表，则视为已添加
                return self

            with self.__conn_locker:
                if table.check_table_creation(self.__conn):
                    self._tables[table._tbname] = table
                else:
                    self._loghook(
                        "Append table failed, check table creation failed.")
        return self

    def check_table_creation(self, conn: SqliteConn) -> bool:
        """检查给与的数据库文件的所有当前管理器中的表，
        并丢弃出错的数据库文件，或者动态增加新增的列"""
        res: bool = True
        try:
            for tb in self._tables.values():
                tb: SqliteTable = tb
                res = tb.check_table_creation(conn)
                if not res:
                    return res

        except Exception:
            res = False
            self._loghook(traceback.format_exc())
        return res

    def close(self):
        """释放当前SqliteConnManager"""
        # 释放所有数据库链接
        with self.__conn_locker:
            try:
                self.__conn.close()
            except Exception:
                self._loghook("Dispose SqliteMemoryDB error: {}".format(
                    traceback.format_exc()))
        __remove_current_dbmngr_instance(self)

    def __dispose_conn(self, conn: SqliteConn):
        """释放SqliteConn在外部的引用，并将其添加回连接池"""
        pass
