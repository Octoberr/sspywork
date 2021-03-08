"""proxy sqlite db"""

# -*- coding:utf-8 -*-

import sqlite3
import threading
import time
import traceback
from abc import ABCMeta, abstractmethod

from ..mslog.loghook import LogHook
from ..mslog.msloglevel import MsLogLevel, MsLogLevels
from ..sql import (SqlCondition, SqlConditions, SqlConn, SqliteColumn,
                   SqliteConn, SqliteIndex, SqliteMemoryDB, SqliteTable,
                   table_locker, table_locker_manual)
from .eproxyanonymity import EProxyAnonymity
from .eproxytype import EProxyType
from .proxydbconfig import ProxyDbConfig
from .proxyitem import ProxyItem


class DbSqliteBase:
    """表示一个sqlite表操作基类"""

    __metaclass = ABCMeta

    __all_tablenames: dict = {}
    __all_tablenames_locker = threading.RLock()

    def __init__(self,
                 dbname: str,
                 dbcfg: ProxyDbConfig,
                 logger_hook: callable = None):
        self._logger: LogHook = LogHook(logger_hook)

        if not isinstance(dbname, str):
            raise Exception(
                "Invalid table name for TbSqliteBase: {}".format(dbname))

        with DbSqliteBase.__all_tablenames_locker:
            if DbSqliteBase.__all_tablenames.__contains__(dbname):
                raise Exception(
                    "Reduplicated table name for TbSqliteBase: {}".format(
                        dbname))

        if not isinstance(dbcfg, ProxyDbConfig):
            dbcfg = ProxyDbConfig()
            self._logger.debug("Proxydb config is None, use default settings.")

        self._dbname: str = dbname
        self._dbconfig: ProxyDbConfig = dbcfg

        self._conn_mngr: SqliteMemoryDB = SqliteMemoryDB(
            dbname='{}.db'.format(self._dbname),
            pagesize=self._dbconfig._pagesize,
            max_page_count=self._dbconfig._maxpagecount,
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

    def connect(self, timeout=None) -> SqlConn:
        """获取sqlite可用于增删改的链接"""
        conn = None
        try:
            conn = self._conn_mngr.conn
            # conn.cursor.row_factory = sqlite3.Cursor.row_factory
        except Exception as ex:
            if not conn is None and not conn._conn_closed:
                conn.close()
            raise ex
        return conn

    def execute_search_one(self,
                           tablename: str,
                           sql: str,
                           params: tuple = None) -> sqlite3.Row:
        """执行增删改这种修改操作\n
        tablename: 必传，用于表加锁"""
        if not isinstance(tablename, str) or tablename == "":
            raise Exception("Must pass 'tablename' param")
        if not isinstance(sql, str) or sql == "":
            return False
        conn: SqliteConn = None
        cursor = None
        res = None
        try:
            with table_locker_manual(tablename):
                conn = self.connect()
                cursor = conn.cursor_new

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

            try:
                with table_locker_manual(tablename):
                    conn = self.connect()
                    cursor = conn.cursor_new

                    if not isinstance(params, tuple) or len(params) < 1:
                        cursor.execute(sql)
                    else:
                        cursor.execute(sql, params)
                    # result = cursor.fetchall()

                    # for row in result:
                    #     if return_with_conn:
                    #         yield (row, conn)
                    #     else:
                    #         yield row

                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        return

                    fields: dict = {}
                    for i in range(len(result[0])):
                        fields[cursor.description[i][0].lower()] = result[0][i]

                    yield fields

            except Exception as ex:
                raise ex
            finally:
                if not conn is None:
                    conn.close()

        except Exception:
            self._logger.error(
                "Get client status error: %s" % traceback.format_exc())

    def execute(self, tablename: str, sql: str, params: tuple = None) -> int:
        """执行操作，返回execute()的结果对象"""
        if not isinstance(tablename, str) or tablename == "":
            raise Exception("Must pass 'tablename' param")
        if not isinstance(sql, str) or sql == "":
            return False
        res: int = 0
        conn: SqliteConn = None
        cursor = None
        try:
            with table_locker_manual(tablename):
                conn = self.connect()
                cursor = conn.cursor_new

                if not isinstance(params, tuple) or len(params) < 1:
                    result = cursor.execute(sql)
                else:
                    result = cursor.execute(sql, params)

                res = cursor.fetchone()

        except Exception:
            self._logger.error(
                "Execute modify sql error: %s" % traceback.format_exc())
        finally:
            if not conn is None:
                conn.close()
        return res

    def execute_modify(self, tablename: str, sql: str,
                       params: tuple = None) -> int:
        """执行增删改这种修改操作，返回受影响的行数"""
        if not isinstance(tablename, str) or tablename == "":
            raise Exception("Must pass 'tablename' param")
        if not isinstance(sql, str) or sql == "":
            return False
        res: int = 0
        conn: SqliteConn = None
        cursor = None
        try:
            with table_locker_manual(tablename):
                conn = self.connect()
                cursor = conn.cursor_new

                if not isinstance(params, tuple) or len(params) < 1:
                    res = cursor.execute(sql)
                else:
                    res = cursor.execute(sql, params)

                if res is None:
                    return 0

                res = res.rowcount

                conn.commit()

        except Exception:
            self._logger.error(
                "Execute modify sql error: %s" % traceback.format_exc())
        finally:
            if not conn is None:
                conn.close()
        return res


#####################################################
#####################################################
#####################################################
#####################################################
# TableProxy


class ProxyDB(DbSqliteBase):
    """TbProxy"""

    __tb_Proxy: SqliteTable = SqliteTable(
        'TbProxy',
        True,
        SqliteColumn(
            colname='Id',
            coltype='INTEGER',
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True).set_index_new(),
        SqliteColumn(colname='IP', nullable=False).set_index_new(),
        SqliteColumn(colname='Port', coltype='INTEGER',
                     nullable=False).set_index_new(),
        SqliteColumn(
            colname='IPType', coltype='INTEGER', nullable=False,
            defaultval=1).set_index_new(),
        SqliteColumn(
            colname='ProxyType',
            coltype='INTEGER',
            nullable=False,
            defaultval=EProxyType.HTTP.value).set_index_new(),
        SqliteColumn(
            colname='IsSsl', coltype='INTEGER', nullable=False,
            defaultval=0).set_index_new(),
        SqliteColumn(
            colname='Anonymous',
            coltype='INTEGER',
            nullable=False,
            defaultval=EProxyAnonymity.Elite.value).set_index_new(),
        SqliteColumn(colname='CountryCode').set_index_new(),
        SqliteColumn(colname='AliveSec'),
        SqliteColumn(colname='ISP'),
        SqliteColumn(colname='Location'),
        SqliteColumn(colname='LastVerifyTime'),
        SqliteColumn(colname='ResponseSec'),
        SqliteColumn(colname='User'),
        SqliteColumn(colname='Pwd'),
        SqliteColumn(colname='UpdateTime', coltype='DATETIME',
                     nullable=False).set_index_new(),
        SqliteColumn(colname='CreateTime', coltype='DATETIME',
                     nullable=False).set_index_new(),
    )

    # 所有列
    # IP
    # Port
    # IPType
    # ProxyType
    # IsSsl
    # Anonymous
    # CountryCode
    # AliveSec
    # ISP
    # Location
    # LastVerifyTime
    # ResponseSec
    # User
    # Pwd
    # UpdateTime
    # CreateTime

    def __init__(self, dbcfg: ProxyDbConfig, logger_hook: callable = None):
        """"""
        DbSqliteBase.__init__(
            self,
            dbname=ProxyDB.__tb_Proxy._tbname,
            dbcfg=dbcfg,
            logger_hook=logger_hook)

    def _append_tables(self):
        self._conn_mngr.append_table(ProxyDB.__tb_Proxy)

    @table_locker(__tb_Proxy._tbname)
    def pop_proxyitem(self, conds: SqlConditions) -> dict:
        """按条件搜索，返回第一个匹配行，并删除此行"""
        res: dict = None
        try:
            res: dict = self.select_proxyitem(conds)
            if not isinstance(res, dict) or len(res) < 1:
                return res

            rowid = res["id"]
            cnt = self.delete_proxyitem(
                SqlConditions(SqlCondition(colname='Id', val=rowid)))
            if cnt < 1:
                self._logger.debug(
                    "Pop proxyitem from db, delete row by rowid failed.")

        except Exception:
            self._logger.error("Pop proxyitem error: {}".format(
                traceback.format_exc()))
        return res

    @table_locker(__tb_Proxy._tbname)
    def select_proxyitem(self, conds: SqlConditions) -> dict:
        """按条件搜索，返回数据行转换成的字段字典"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            # IP
            # Port
            # IPType
            # ProxyType
            # IsSsl
            # Anonymous
            # CountryCode
            # AliveSec
            # ISP
            # Location
            # LastVerifyTime
            # ResponseSec
            # User
            # Pwd
            # UpdateTime
            # CreateTime
            cmd = f'''select 
                    Id,
                    IP,
                    Port,
                    IPType,
                    ProxyType,
                    IsSsl,
                    Anonymous,
                    CountryCode,
                    AliveSec,
                    ISP,
                    Location,
                    LastVerifyTime,
                    ResponseSec,
                    User,
                    Pwd,
                    UpdateTime,
                    CreateTime 
                    FROM {ProxyDB.__tb_Proxy._tbname} WHERE {conds.text_normal}'''
            conn: SqliteConn = self.connect()
            # conn._conn.row_factory = self._dict_factory
            try:
                cursor = conn.cursor_new
                cursor.execute(cmd, conds.params)
                result = cursor.fetchall()
                if result is None or len(result) < 1:
                    return None

                fields: dict = {}
                for i in range(len(result[0])):
                    try:
                        fields[cursor.description[i][0].lower()] = result[0][i]
                    except Exception as e:
                        print(e)

                return fields

            except Exception:
                self._logger.error("Get ProxyItem error: {}".format(
                    traceback.format_exc()))
            finally:
                if not conn is None:
                    conn.close()

        except Exception:
            self._logger.error(
                "Get ProxyItem error: %s" % traceback.format_exc())
        return None

    @table_locker(__tb_Proxy._tbname)
    def select_proxyitems(self, conds: SqlConditions) -> iter:
        """按条件搜索，返回数据行转换成的字段字典迭代器"""
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            # IP
            # Port
            # IPType
            # ProxyType
            # IsSsl
            # Anonymous
            # CountryCode
            # AliveSec
            # ISP,
            # Location,
            # LastVerifyTime,
            # ResponseSec,
            # User
            # Pwd
            # UpdateTime
            # CreateTime
            cmd = f'''SELECT 
                    Id,
                    IP,
                    Port,
                    IPType,
                    ProxyType,
                    IsSsl,
                    Anonymous,
                    CountryCode,
                    AliveSec,
                    ISP,
                    Location,
                    LastVerifyTime,
                    ResponseSec,
                    User,
                    Pwd,
                    UpdateTime,
                    CreateTime 
                    FROM {ProxyDB.__tb_Proxy._tbname} WHERE {conds.text_normal}'''
            conn: SqliteConn = self.connect()
            # conn._conn.row_factory = self._dict_factory
            try:
                cursor = conn.cursor_new
                cursor.execute(cmd, conds.params)
                result = cursor.fetchall()
                if result is None or len(result) < 1:
                    return

                for row in result:
                    fields: dict = {}
                    for i in range(len(result[0])):
                        fields[cursor.description[i][0].lower()] = row[i]

                    yield fields

            except Exception:
                self._logger.error("Get ProxyItems error: {}".format(
                    traceback.format_exc()))
            finally:
                if not conn is None:
                    conn.close()

        except Exception:
            self._logger.error(
                "Get ProxyItems error: %s" % traceback.format_exc())

    @table_locker(__tb_Proxy._tbname)
    def save_new_proxyitem(self, proxyitem: ProxyItem) -> bool:
        """"""
        res = False
        isnew: bool = False
        conn: SqliteConn = None
        cursor = None
        proxyitem: ProxyItem = proxyitem

        try:
            cmd = f'''SELECT COUNT(1) FROM {ProxyDB.__tb_Proxy._tbname} WHERE 
            IP=? and Port=? and ProxyType=?'''
            conn: SqliteConn = self.connect()
            try:
                cursor = conn.cursor_new
                cursor.execute(cmd, (
                    proxyitem._ip,
                    proxyitem._port,
                    proxyitem._proxytype.value,
                ))
                result = cursor.fetchall()
                if result[0][0] > 0:
                    res = True
                    cmd = f'''UPDATE {ProxyDB.__tb_Proxy._tbname} set
                        ProxyType=?,
                        IsSsl=?,
                        Anonymous=?,
                        CountryCode=?,
                        AliveSec=?,
                        ISP=?,
                        Location=?,
                        LastVerifyTime=?,
                        ResponseSec=?,
                        User=?,
                        Pwd=?,
                        UpdateTime=? 
                        WHERE IP=? and Port=? and ProxyType=?;'''

                    result = cursor.execute(cmd, (
                        proxyitem._proxytype.value,
                        1 if proxyitem._is_ssl else 0,
                        proxyitem._anonymous.value,
                        proxyitem.countrycode,
                        proxyitem.alive_sec,
                        proxyitem.isp,
                        proxyitem.location,
                        proxyitem.lastverifytime,
                        proxyitem.response_sec,
                        proxyitem.user,
                        proxyitem.pwd,
                        time.time(),
                        proxyitem._ip,
                        proxyitem._port,
                        proxyitem._proxytype.value,
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

            # IP
            # Port
            # IPType
            # ProxyType
            # IsSsl
            # Anonymous
            # CountryCode
            # AliveSec
            # ISP,
            # Location,
            # LastVerifyTime,
            # ResponseSec,
            # User
            # Pwd
            # UpdateTime
            # CreateTime
            # 若没找到，则insert一条到最新的库
            # res==True表示至少有一个库里面有一条符合条件的任务，且已更新其字段
            if not res:
                isnew = True
                conn = self.connect(5)
                try:
                    # insert
                    cmd = f'''INSERT INTO {ProxyDB.__tb_Proxy._tbname}(
                        IP,
                        Port,
                        IPType,
                        ProxyType,
                        IsSsl,
                        Anonymous,
                        CountryCode,
                        AliveSec,
                        ISP,
                        Location,
                        LastVerifyTime,
                        ResponseSec,
                        User,
                        Pwd,
                        UpdateTime,
                        CreateTime) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                    # 有几个属于TaskBack的字段在此不更新
                    cursor = conn.cursor_new
                    result = cursor.execute(cmd, (
                        proxyitem._ip,
                        proxyitem._port,
                        proxyitem.iptype,
                        proxyitem._proxytype.value,
                        1 if proxyitem._is_ssl else 0,
                        proxyitem._anonymous.value,
                        proxyitem.countrycode,
                        proxyitem.alive_sec,
                        proxyitem.isp,
                        proxyitem.location,
                        proxyitem.lastverifytime,
                        proxyitem.response_sec,
                        proxyitem.user,
                        proxyitem.pwd,
                        time.time(),
                        time.time(),
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
                "save new ProxyItem error: %s" % traceback.format_exc())
        finally:
            if not conn is None:
                conn.close()
        return res

    @table_locker(__tb_Proxy._tbname)
    def update_proxyitem(self, ip: str, port: int, proxytype: EProxyType,
                         updatefields: dict) -> bool:
        """"""
        res = False
        conn: SqliteConn = None
        cursor = None
        try:
            # 搜索每个库，看有没有 TokenId一样的，且时间更新
            # 的，一样就更新其他所有字段
            cmd = f'''SELECT COUNT(1) FROM {ProxyDB.__tb_Proxy._tbname} WHERE
            IP=? and Port=? and ProxyType=?'''
            conn: SqliteConn = self.connect()
            conn: SqliteConn = conn
            try:
                cursor = conn.cursor_new
                cursor.execute(cmd, (ip, port, proxytype.value))
                result = cursor.fetchall()

                if result[0][0] > 0:
                    # 只根据TaskId、platform作为条件，
                    # 不考虑 任务文件产生时间与现有数据库中已存在任务的时间，每次直接覆盖，以符合用户操作。
                    # 若来了TaskId一样的数据，则必然分配给同一个ClientId
                    sqlset = ''
                    for k in updatefields.keys():
                        sqlset = sqlset + '{}=?,'.format(k)
                    sqlset = sqlset.rstrip(',')
                    cmd = f'''UPDATE {ProxyDB.__tb_Proxy._tbname} set {sqlset} WHERE IP=? and Port=? and ProxyType=?;'''
                    params = [v for v in updatefields.values()]
                    params.append(ip)
                    params.append(port)
                    params.append(proxytype.value)
                    result = cursor.execute(cmd, params)

                    if result is None or result.rowcount < 1:  # or len(result) < 1:
                        pass
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
                "Update ProxyItem error: %s" % traceback.format_exc())

        return res

    @table_locker(__tb_Proxy._tbname)
    def delete_proxyitem(self, conds: SqlConditions) -> int:
        """按条删除行，返回受影响的行数"""
        res: int = 0
        conn: SqliteConn = None
        cursor = None
        conds: SqlConditions = conds
        try:
            # IP
            # Port
            # IPType
            # ProxyType
            # IsSsl
            # Anonymous
            # CountryCode
            # AliveSec
            # ISP,
            # Location,
            # LastVerifyTime,
            # ResponseSec,
            # User
            # Pwd
            # UpdateTime
            # CreateTime
            cmd = f'''delete FROM {ProxyDB.__tb_Proxy._tbname} WHERE {conds.text_normal}'''
            conn: SqliteConn = self.connect()
            # conn._conn.row_factory = self._dict_factory
            try:
                cursor = conn.cursor_new
                result = cursor.execute(cmd, conds.params)
                res = result.rowcount

            except Exception:
                self._logger.error("Get ProxyItem error: {}".format(
                    traceback.format_exc()))
            finally:
                if not conn is None:
                    conn.close()

        except Exception:
            self._logger.error(
                "Get ProxyItem error: %s" % traceback.format_exc())
        return res
