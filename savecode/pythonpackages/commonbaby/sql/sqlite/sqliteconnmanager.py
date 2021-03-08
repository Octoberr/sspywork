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


def table_locker_manual(tablename: str) -> threading._RLock:
    """用于手动调用sqlite表上锁"""
    if not isinstance(tablename, str) or tablename == "":
        raise Exception("Table name must be specified")
    if not __table_lockers.__contains__(tablename):
        with __table_lockers_locker:
            if not __table_lockers.__contains__(tablename):
                __table_lockers[tablename] = threading.RLock()
    return __table_lockers[tablename]


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

    def _singleton(dbdir: str = './_database',
                   dbname: str = 'data.db',
                   maxdbfisize: float = 100 * 1024 * 1024,
                   maxconnperdb: int = 20,
                   connecttimeoutsec: float = 60,
                   delete_on_error: bool = True,
                   loghook: callable = None,
                   *tables):
        """"""

        with __db_mutex:
            db_mutex_path: str = os.path.join(dbdir, dbname)
            # 检查互斥锁
            mtx_result = __check_dbfi_mutex(db_mutex_path)
            if isinstance(mtx_result, cls):
                return mtx_result
            inst = cls(
                dbdir=dbdir,
                dbname=dbname,
                maxdbfisize=maxdbfisize,
                maxconnperdb=maxconnperdb,
                connecttimeoutsec=connecttimeoutsec,
                delete_on_error=delete_on_error,
                loghook=loghook,
                *tables)
            __add_current_dbmngr_instance(inst, db_mutex_path)
            return inst

    _singleton.__doc__ = cls.__doc__
    return _singleton


@__singleton_connmngr
class SqliteConnManager:
    """带表动态表检测的Sqlite底层操作，注意使用 table_locker装饰器将表操作上锁。\n
    # 对于同一个监控目录下的一个数据库文件，只能有一个SqliteConnManager实例，\n
    # 所以此处使用单例模式，若dbdir/dbname一样，则返回已有SqliteConnManager实例，\n
    # 例：\n
    # xxx/aaa.db 和 xxx/aaa.db 返回同一个 SqliteConnManager实例，\n
    # xxx/aaa.db 和 xxx/bbb.db 返回不同的SqliteConnManager实例\n
    check_create_table: 检查并创建针对当前数据库文件的表的函数: def foo(self, conn): xxx\n
    dbdir: 数据库文件存放路径\n
    dbname: 数据库文件名\n
    maxdbfisize: 数据库文件最大大小\n
    maxconnperdb: 每个数据库允许的最大同时链接数量，默认为20个\n
    connecttimeoutsec: 数据库链接超时时间，float，单位秒，默认60秒\n
    delete_on_error: 是否删除出错的数据库文件，默认为True\n
    loghook: 接收日志输出的函数，callable, 默认为 lambda msg: print(msg)\n
    tables: SqliteTable objects"""

    def __init__(self,
                 dbdir: str = './_database',
                 dbname: str = 'data.db',
                 maxdbfisize: float = 100 * 1024 * 1024,
                 maxconnperdb: int = 20,
                 connecttimeoutsec: float = 60,
                 delete_on_error: bool = True,
                 loghook: callable = None,
                 *tables):
        """"""
        self._tables_locker = threading.RLock()
        self._tables: dict = {}
        for t in tables:
            self.append_table(t)

        self._dbdir = os.path.abspath("./_database")
        if isinstance(dbdir, str) and not dbdir == "":
            self._dbdir = os.path.abspath(dbdir)
        if not os.path.exists(self._dbdir):
            os.makedirs(self._dbdir)

        self._dbname = "data.db"
        if isinstance(dbname, str) and not dbname == "":
            self._dbname = dbname

        self.__db_mutex_path: str = os.path.join(dbdir, dbname)
        self._maxdbfisize: float = 100 * 1024 * 1024
        if type(maxdbfisize) in (int, float) and maxdbfisize >= 1024 * 1024:
            self._maxdbfisize = maxdbfisize

        self._maxconnperdb: int = 20
        if isinstance(maxconnperdb, int) and maxconnperdb > 0:
            self._maxconnperdb = maxconnperdb

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

        # 最新的可以用于写入的连接
        self._currwritedbfi: sqlite3.Connection = None
        self._last_flag: int = -1
        self._currwritedbfilocker = threading.RLock()

        # 所有连接 <filepath, quque.Queue(SqliteConn)>
        self._all_conns: dict = {}
        self._all_conns_locker = threading.RLock()  #在查询和往字典中添加新文件键时上锁
        self._check_exist_dbs()

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
            for conn in self.connect_all():
                if table.check_table_creation(conn):
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
        with self._all_conns_locker:
            for dbitem in self._all_conns.items():
                disposed_count: int = 0
                while disposed_count < self._maxconnperdb:
                    try:
                        conn = dbitem[1].get(self._connecttimeoutsec)
                        if not conn is None:
                            conn.dispose()

                    except queue.Empty:
                        continue
                    except Exception:
                        self._loghook(
                            "Dispose SqliteConnManager error: {}".format(
                                traceback.format_exc()))
        __remove_current_dbmngr_instance(self)

    def __dispose_conn(self, conn: SqliteConn):
        """释放SqliteConn在外部的引用，并将其添加回连接池"""
        if not isinstance(conn, SqliteConn):
            raise Exception("Must be a SqliteConn object")

        # 没有此fipath，说明当前数据库文件已出错，并被移除
        if not self._all_conns.__contains__(conn._fipath):
            return
        # 此处不锁，释放链接时，若原有的conn._fipath不存在，则当作此
        # 数据库文件已废弃。
        with self._all_conns_locker:
            if not self._all_conns.__contains__(conn._fipath):
                return
            self._all_conns[conn._fipath].put(conn)

    def _check_exist_dbs(self):
        """检查已有数据库文件，并添加到列表"""
        if not os.path.exists(self._dbdir):
            os.makedirs(self._dbdir)
            return

        # 先删除所有的journal文件
        with self._currwritedbfilocker:
            for p in os.listdir(self._dbdir):
                p: str = p
                path: str = os.path.join(self._dbdir, p)
                if not os.path.isfile(path):
                    continue
                if not p.startswith(self._dbname):
                    continue
                flag = p.replace(self._dbname, '').strip()
                if flag.endswith('journal'):  # 数据库锁文件，，直接删
                    os.remove(path)
                    continue

            for p in os.listdir(self._dbdir):
                p: str = p
                path: str = os.path.join(self._dbdir, p)
                if not os.path.isfile(path):
                    continue
                if not p.startswith(self._dbname):
                    continue

                with self._all_conns_locker:
                    if not self._all_conns.__contains__(path):
                        self._all_conns[path] = queue.Queue()
                        for i in range(self._maxconnperdb):
                            con = SqliteConn(self.__dispose_conn, path,
                                             self._connecttimeoutsec)
                            if self.check_table_creation(con):
                                self._all_conns[path].put(con)
                            elif not self._invalid_dbfi(con):
                                self._loghook(
                                    "Deal invalid sqlite database file failed."
                                )

                flag = p.replace(self._dbname, '').strip()
                flag: int = int(flag)
                if flag > self._last_flag:
                    self._last_flag = flag
                    self._currwritedbfi = path
                elif self._currwritedbfi is None or self._currwritedbfi == "":
                    self._currwritedbfi = path
            # 若一个都没有，需要创建一个
            if self._last_flag < 0 or self._currwritedbfi == None or self._currwritedbfi == "":
                self._last_flag = 0
                newdbfi = self._create_new_dbfi(self._last_flag)
                self._add_dbfi_to_queue(newdbfi)

    def _create_new_dbfi(self, flag: int) -> str:
        """返回一个新的的Sqlite数据库文件全路径"""
        path = os.path.abspath(
            os.path.join(self._dbdir,
                         "%s%d" % (self._dbname, self._last_flag)))
        while os.path.exists(path):
            self._last_flag += 1
            path = os.path.abspath(
                os.path.join(self._dbdir,
                             "%s%d" % (self._dbname, self._last_flag)))
        return path

    def _delete_invalid_dbfi(self, conn: SqliteConn):
        """Delete specified sqlite db file and remove it from db container"""
        # 没有就说明已经移除了，反正就是不会再被使用了。
        with self._all_conns_locker:
            self._remove_dbfi_from_queue(conn)
            # 删除数据库文件
            if os.path.exists(conn._fipath):
                os.remove(conn._fipath)

    def _rename_invalid_dbfi(self, conn: SqliteConn):
        """Rename specified sqlite db file and remove it from db container"""
        with self._all_conns_locker:
            self._remove_dbfi_from_queue(conn)
            if os.path.exists(conn._fipath):
                d, n = os.path.split(conn._fipath)
                newfi = os.path.join(d, "invalid_%s" % n)
                shutil.move(conn._fipath, newfi)

    def _invalid_dbfi(self, conn: SqliteConn) -> bool:
        """Deal invalid dbfile, return if dealt succeed"""
        res: bool = False
        try:
            if self._delete_on_error:
                self._delete_invalid_dbfi(conn)
            else:
                self._rename_invalid_dbfi(conn)

            res = True
        except Exception as ex:
            res = False
            self._loghook(ex)
        return res

    def _add_dbfi_to_queue(self, newdbfi):
        """将新的数据库文件加入队列中，切换当前最新用于增删改操作的数据库文件路径
        self._currwritedbfi，并为其创建连接池"""
        with self._all_conns_locker:
            with self._currwritedbfilocker:
                self._currwritedbfi = newdbfi
                if not self._all_conns.__contains__(newdbfi):
                    self._all_conns[newdbfi] = queue.Queue()
                for i in range(self._maxconnperdb):
                    newconn = SqliteConn(self.__dispose_conn, newdbfi,
                                         self._connecttimeoutsec)
                    if not self.check_table_creation(newconn):
                        if not self._invalid_dbfi(newconn):
                            self._loghook(
                                "Deal invalid sqlite database file failed.")
                    else:
                        self._all_conns[newdbfi].put(newconn)

    def _remove_dbfi_from_queue(self, conn: SqliteConn):
        """从队列移除指定的数据库链接和db文件键"""
        # 没有就说明已经移除了，反正就是不会再被使用了。
        if not self._all_conns.__contains__(conn._fipath):
            return
        with self._all_conns_locker:
            if not self._all_conns.__contains__(conn._fipath):
                return

        # 关闭并移除所有当前数据库文件关联的链接
        try:
            if conn._fipath == self._currwritedbfi:
                with self._currwritedbfilocker:
                    while True:
                        try:
                            con: SqliteConn = self._all_conns[
                                conn._fipath].get(3)
                            if not isinstance(con, SqliteConn):
                                continue
                            con.dispose()
                        except queue.Empty:
                            break
                        finally:
                            if not con is None:
                                self._all_conns[conn._fipath].task_done()
            else:
                with self._all_conns_locker:
                    while True:
                        try:
                            con: SqliteConn = self._all_conns[
                                conn._fipath].get(3)
                            if not isinstance(con, SqliteConn):
                                continue
                            con.dispose()
                        except queue.Empty:
                            break
                        finally:
                            if not con is None:
                                self._all_conns[conn._fipath].task_done()
        except Exception as ex:
            self._loghook(
                "Error while remove invalid database file: {}\n{}".format(
                    conn._fipath, traceback.format_exc()))

        # 移除键
        with self._all_conns_locker:
            self._all_conns.pop(conn._fipath, None)

    def connect_write(self, timeout=None) -> SqliteConn:
        """
        获取一个可以用于写入的数据库连接
        """
        # 若需要上两个锁，则统一先上_all_conns_locker，
        # 再上_currwritedbfilelocker，否则会造成死锁
        with self._all_conns_locker:
            with self._currwritedbfilocker:

                # 若数据库文件达到条件上限，则新建数据库文件
                if os.path.getsize(
                        self._currwritedbfi
                ) >= self._maxdbfisize or not self._all_conns.__contains__(
                        self._currwritedbfi):
                    newdbfi = self._switch_write_dbfi()
                    if not self._all_conns.__contains__(newdbfi):
                        self._add_dbfi_to_queue(newdbfi)

                if not self._all_conns.__contains__(
                        self._currwritedbfi) and os.path.isfile(
                            self._currwritedbfi):
                    self._add_dbfi_to_queue(self._currwritedbfi)

                # 上锁后取链接，避免别处将连接搞挂
                conn: SqliteConn = None
                try:
                    if not type(timeout) in [int, float]:
                        conn = self._all_conns[self._currwritedbfi].get(
                            timeout=timeout)
                    else:
                        conn = self._all_conns[self._currwritedbfi].get(
                            timeout=self._connecttimeoutsec)
                    if not conn is None:
                        conn._re_init()
                    # self._all_conns[self._currwritedbfi].task_done()
                except queue.Empty as em:
                    raise em
                except Exception as ex:
                    raise ex
                finally:
                    if not conn is None:
                        self._all_conns[self._currwritedbfi].task_done()

        return conn

    def connect_all(self, timeout=None) -> iter:
        """获取所有数据库文件连接 SqliteConn(SqlConn) 对象"""
        # 此处不锁，每个线程每次取走一个，用完释放后才取下一个。
        with self._all_conns_locker:
            for dbitem in self._all_conns.items():
                conn = None
                try:
                    # 若需要上两个锁，则统一先上_all_conns_locker，
                    # 再上_currwritedbfilelocker，否则会造成死锁
                    if dbitem[0] == self._currwritedbfi:
                        with self._currwritedbfilocker:
                            try:
                                if not type(timeout) in [int, float]:
                                    conn = dbitem[1].get(timeout=timeout)
                                else:
                                    conn = dbitem[1].get(
                                        timeout=self._connecttimeoutsec)

                                if not conn is None:
                                    conn._re_init()
                            finally:
                                if not conn is None:
                                    dbitem[1].task_done()
                    else:
                        try:
                            if not type(timeout) in [int, float]:
                                conn = dbitem[1].get(timeout=timeout)
                            else:
                                conn = dbitem[1].get(
                                    timeout=self._connecttimeoutsec)

                            if not conn is None:
                                conn._re_init()
                        finally:
                            if not conn is None:
                                dbitem[1].task_done()

                    yield conn

                except queue.Empty as em:
                    raise em
                except Exception as ex:
                    raise ex

    def _switch_write_dbfi(self) -> str:
        """切换到一个新的用于写入的数据库文件，并返回新数据库文件路径"""
        newdbfi: str = None
        try:
            with self._currwritedbfilocker:
                newdbfi = self._create_new_dbfi(self._last_flag)
                self._loghook("Create dbfile: %s" % newdbfi)

        except Exception:
            self._loghook("Switch db file error: %s" % traceback.format_exc())
            newdbfi = None
        return newdbfi
