"""the managed sqlite connection"""

# -*- coding:utf-8 -*-

import sqlite3
import threading

from ..sqlconn import SqlConn


class SqliteCursor(sqlite3.Cursor):
    """表示一个封装的sqlite游标"""

    @property
    def description(self):
        return self._cursor.description

    @property
    def arraysize(self):
        return self._cursor.arraysize

    @property
    def connection(self):
        return self._cursor.connection

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def row_factory(self):
        return self._cursor.row_factory

    @row_factory.setter
    def row_factory(self, value):
        self._cursor.row_factory = value

    def __init__(self, conn):
        if conn is None:
            raise Exception("Invalid connection object")
        self._conn = conn
        self._cursor: sqlite3.Cursor = conn.cursor()
        self._cursor_refresh_locker = threading.RLock()

    def _re_init_(self):
        with self._cursor_refresh_locker:
            self._cursor.close()
            self._cursor = self._conn.cursor()

    def execute(self, *args, **kwargs):
        """sqlite3.connection.cursor.execute"""
        try:
            return self._cursor.execute(*args, **kwargs)
        except Exception as ex:
            raise ex

    def executemany(self, *args, **kwargs):
        try:
            return self._cursor.executemany(*args, **kwargs)
        except Exception as ex:
            raise ex

    def fetchall(self):
        """sqlite3.connection.cursor.fetchall"""
        return self._cursor.fetchall()

    def fetchmany(self, size: sqlite3.Cursor.arraysize):
        """"""
        return self._cursor.fetchmany(size)

    def fetchone(self):
        return self._cursor.fetchone()


class SqliteConn(SqlConn):
    """表示一个线程安全的，被管理的Sqlite数据库连接"""

    # 针对同一个数据库文件的全局静态提交锁
    __commit_lockers_locker = threading.RLock()
    __commit_lockers: dict = {}

    @property
    def cursor(self):
        return self.__cursor

    @property
    def cursor_new(self):
        return self._conn.cursor()

    def __init__(self,
                 dispose_func,
                 fipath: str,
                 timeoutsec: float = None,
                 check_same_thread=False):
        if not callable(dispose_func):
            raise Exception(
                """Sqlite disponse function must be callable like:\n
            def disponse_func(self, conn:SqlConn): pass""")
        SqlConn.__init__(self, dispose_func)

        if fipath is None:
            raise Exception("Sqlite db file path cannot be None")
        self._fipath = fipath

        self._timeoutsec: float = 60
        if type(timeoutsec) in [int, float]:
            if timeoutsec <= 0:
                self._timeoutsec = None
            else:
                self._timeoutsec = timeoutsec

        self._check_same_thread: bool = False
        if isinstance(check_same_thread, bool):
            self._check_same_thread = check_same_thread

        self._conn = None
        self._conn_closed: bool = True
        self._conn_closed_locker = threading.RLock()

        self._conn_disposed: bool = True
        self._conn_disposed_locker = threading.RLock()
        self._re_init()

        self.__cursor = SqliteCursor(self._conn)
        self._execute_locker = threading.RLock()

    @classmethod
    def __check_commit_locker(cls, dbfipath: str):
        """如果不存在，则添加针对指定dbfipath的数据库提交锁"""
        if dbfipath is None or dbfipath == "":
            raise Exception("Given param 'dbfipath' cannot be None or empty.")
        if not cls.__commit_lockers.__contains__(dbfipath):
            with cls.__commit_lockers_locker:
                if not cls.__commit_lockers.__contains__(dbfipath):
                    cls.__commit_lockers[dbfipath] = threading.RLock()

    @classmethod
    def __get_comit_locker(cls, dbfipath: str):
        """获取针对指定dbfipath的数据库提交锁对象"""
        if dbfipath is None or dbfipath == "":
            raise Exception("Given param 'dbfipath' cannot be None or empty.")
        SqliteConn.__check_commit_locker(dbfipath)
        with SqliteConn.__commit_lockers_locker:
            return SqliteConn.__commit_lockers[dbfipath]

    def execute(self, *args, **kwargs) -> object:
        """执行指定sql"""
        try:
            # 这里不能用 db所在文件路径为键的锁对象？？？？
            # 这句会导致sqlite锁住 ↓↓↓↓↓ ？？？？？？？
            # with SqliteConn.__get_comit_locker(self._fipath):

            # 这样写就可以了
            # with self._execute_locker:
            #     # return self._conn.execute(sql)
            #     return self.__cursor.execute(sql)
            return self.cursor.execute(*args, **kwargs)

        except Exception as ex:
            raise ex

    def commit(self):
        """提交对当前连接执行的操作"""
        with SqliteConn.__get_comit_locker(self._fipath):
            return self._conn.commit()

    def _re_init(self):
        """重新初始化当前链接对象的各种状态和数据库链接"""
        if self._conn_closed:
            with self._conn_closed_locker:
                if self._conn_closed:
                    self._conn_closed = False

        if self._conn_disposed:
            with self._conn_disposed_locker:
                if self._conn_disposed:
                    if not self._conn is None:
                        self._conn.close()
                    self._conn = sqlite3.connect(
                        self._fipath,
                        timeout=self._timeoutsec,
                        check_same_thread=self._check_same_thread)
                    self._conn_disposed = False

    def _close_sub(self):
        """每次关闭要执行一下commit"""
        if self._conn_closed:
            return
        with self._conn_closed_locker:
            if self._conn_closed:
                return
            self.commit()
            # self.__cursor.close()
            self._conn_closed = True

    def dispose(self):
        """释放当前数据库链接的资源，不可逆"""
        if self._conn_disposed:
            return
        with self._conn_disposed_locker:
            if self._conn_disposed:
                return
            self._conn.close()
            self._conn = None
            self._conn_disposed = True

    def __repr__(self):
        if not self._fipath is None and not self._fipath == "":
            return self._fipath
        else:
            return self._conn.__repr__()

    @classmethod
    def _row_dict_factory(cls, cursor, row):
        """dict factory for sqlite data rows"""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d