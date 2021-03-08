"""represents a sqlite table"""

# -*- coding:utf-8 -*-

import sqlite3
import threading

from .sqliteconn import SqliteConn


class SqliteIndex:
    """represents a sqlite column index\n
    ownercol: the owner SqliteColumn object of current SqliteIndex object\n
    idxname: the name of current index, if this is None, 
        will automatically generate an unique index name"""

    def __init__(self, idxname: str = None, is_asc: bool = True):
        """index name can be None"""

        self._ownercol = None
        self._idxname = idxname
        self._is_asc: bool = True
        if isinstance(is_asc, bool):
            self._is_asc = is_asc

        # 表初始化状态缓存
        self._initialed_conns: dict = {}
        self._initialed_conns_locker = threading.RLock()

    def set_owner_column(self, col):
        """为当前SqliteIndex索引设置所属SqliteColumn列"""
        if col is None:
            raise Exception("Invalid SqliteColumn object")
        self._ownercol = col

    def check_index(self, conn: SqliteConn) -> bool:
        """检查给予的sqlite数据库连接的当前索引是否缺失，并根据配置动态创建，返回bool指示是否成功"""
        res: bool = False
        try:
            if not isinstance(conn, SqliteConn):
                raise Exception("Invalid sqlite connection")

            # 检查缓存是否标记为已初始化
            if self._initialed_conns.__contains__(conn):
                return True
            with self._initialed_conns_locker:
                if self._initialed_conns.__contains__(conn):
                    return True

                if self._idxname is None:
                    self._idxname = "Idx_{}_{}".format(
                        self._ownercol._ownertable._tbname,
                        self._ownercol._colname)
                sql = f"CREATE INDEX IF NOT EXISTS {self._idxname} ON {self._ownercol._ownertable._tbname}({self._ownercol._colname} {'ASC' if self._is_asc else 'DESC'});"

                cursor = conn.cursor
                result = cursor.execute(sql)
                conn.commit()
                # 结果为None视为创建失败
                if result is None:
                    return res

                res = True

        except Exception as ex:
            raise ex
        finally:
            # 只要成功，且只要跑过一次此函数，则算作已初始化，并记录
            if res and not self._initialed_conns.__contains__(conn):
                with self._initialed_conns_locker:
                    if res and not self._initialed_conns.__contains__(conn):
                        self._initialed_conns[conn] = True
        return res


class SqliteColumn:
    """represents a sqlite column\n
    defaultval: 默认值，可以传callable对象，会自动调用callable_obj.__call__()"""

    __sqlite_col_types: dict = {
        "BIGINT": "BIGINT",
        "BLOB": "BLOB",
        "BOOLEAN": "BOOLEAN",
        "CHAR": "CHAR",
        "DATE": "DATE",
        "DATETIME": "DATETIME",
        "DECIMAL": "DECIMAL",
        "DOUBLE": "DOUBLE",
        "INT": "INT",
        "INTEGER": "INTEGER",
        "NONE": "NONE",
        "NUMERIC": "NUMERIC",
        "REAL": "REAL",
        "STRING": "STRING",
        "TEXT": "TEXT",
        "TIME": "TIME",
        "VARCHAR": "VARCHAR",
    }

    def __init__(self,
                 colname: str,
                 coltype: str = 'TEXT',
                 length: int = None,
                 nullable: bool = True,
                 is_primary_key: bool = False,
                 is_auto_increament: bool = False,
                 is_unique: bool = False,
                 defaultval: str = None,
                 create_on_miss: bool = True,
                 idx: SqliteIndex = None,
                 description: str = None):
        if colname is None:
            raise Exception("Colname cannot be None")
        if coltype is None or not SqliteColumn.__sqlite_col_types.__contains__(
                coltype):
            raise Exception(
                "Coltype cannot be None or is invalid: {}".format(coltype))

        self._ownertable = None
        self._colname: str = colname

        self._index: SqliteIndex = None
        self._index_locker = threading.RLock()
        if isinstance(idx, SqliteIndex):
            self.set_index_exists(idx)

        self._coltype: str = coltype
        self._length: int = None
        if isinstance(length, int):
            self._length = length
        self._nullable: bool = True
        if isinstance(nullable, bool):
            self._nullable = nullable
        self._is_primary_key: bool = False
        if isinstance(is_primary_key, bool):
            self._is_primary_key = is_primary_key
        self._is_auto_increament: bool = False
        if isinstance(is_auto_increament, bool):
            self._is_auto_increament = is_auto_increament
        self._is_unique: bool = False
        if isinstance(is_unique, bool):
            self._is_unique = is_unique
        self._defaultval: str = None
        if not defaultval is None:
            if isinstance(defaultval, str):
                self._defaultval = repr(defaultval)
            else:
                self._defaultval = defaultval
        self._create_on_miss: bool = True
        if isinstance(create_on_miss, bool):
            self._create_on_miss = create_on_miss
        self._description: str = description

        # 表初始化状态缓存
        self._initialed_conns: dict = {}
        self._initialed_conns_locker = threading.RLock()

    def set_owner_table(self, table):
        """为当前SqliteColumn设置所属SqliteTable表"""
        if table is None:
            raise Exception("Invalid owner SqliteTable")
        self._ownertable = table

    def set_index_exists(self, idx: SqliteIndex):
        """为当前SqliteColumn设置SqliteIndex索引，返回当前SqliteColumn本神"""
        if not isinstance(idx, SqliteIndex):
            raise Exception("Invalid SqliteIndex object")
        idx.set_owner_column(self)
        self._index = idx
        return self

    def set_index_new(self, idxname: str = None, is_asc: bool = True):
        """为当前SqliteColumn设置SqliteIndex索引，返回当前SqliteColumn本身\n
        idxname: the name of current index, if this is None, 
        will automatically generate an unique index name"""
        idx = SqliteIndex(idxname=idxname, is_asc=is_asc)
        idx.set_owner_column(self)
        self._index = idx
        return self

    def check_column(self, conn: SqliteConn) -> bool:
        """检查给予的sqlite数据库连接的当前列是否缺失，并根据配置动态创建，返回bool指示是否成功"""
        res: bool = False
        try:
            if not isinstance(conn, SqliteConn):
                raise Exception("Invalid sqlite connection")

            # 检查缓存是否标记为已初始化
            if self._initialed_conns.__contains__(conn):
                return True
            with self._initialed_conns_locker:
                if self._initialed_conns.__contains__(conn):
                    return True

                sql = f'PRAGMA table_info([{self._ownertable._tbname}])'
                cursor: sqlite3.Cursor = conn.cursor
                result = cursor.execute(sql)
                conn.commit()
                exist: bool = False
                for c in result:
                    # c 为一个列的信息
                    # print(c)
                    # id_ = c[0]
                    # name = c[1]
                    # type_ = c[2]
                    # notnull = c[3]
                    # dftval = c[4]
                    # primarykey = c[5]
                    # 暂时只支持根据列名判断是否应增加列，
                    # 暂不支持判断类型，默认值并修改列等。
                    if c[1] == self._colname:
                        # and \
                        # type_ == self._coltype and \
                        # bool(notnull) != self._nullable and \
                        # dftval is not None and dftval ==self._defaultval and \
                        # primarykey ==self._is_primary_key:
                        exist = True
                        break

                # 列缺失则创建
                if not exist:
                    sql = f'ALTER TABLE {self._ownertable._tbname} ADD COLUMN {self._colname} {self._coltype}'
                    if not self._defaultval is None:
                        if isinstance(self._defaultval, str):
                            sql += f' DEFAULT({repr(self._defaultval)})'
                        elif callable(self._defaultval):
                            sql += f' DEFAULT({self._defaultval()})'
                        else:
                            sql += f' DEFAULT({self._defaultval})'
                    if not self._nullable:
                        sql += ' NOT NULL'

                    result = cursor.execute(sql)
                    conn.commit()
                    # 结果为None视为创建失败
                    if result is None:
                        return res

                # 否则检查当前列是否有索引，并创建
                # 创建索引
                if not self._index is None:
                    if not self._index.check_index(conn):
                        return res  # 创建失败

                res = True

        except Exception as ex:
            raise ex
        finally:
            # 只要成功，且只要跑过一次此函数，则算作已初始化，并记录
            if res and not self._initialed_conns.__contains__(conn):
                with self._initialed_conns_locker:
                    if res and not self._initialed_conns.__contains__(conn):
                        self._initialed_conns[conn] = True

        return res

    def get_col_creation_sql(self) -> str:
        """返回当前列的创建sql语句"""
        res = None
        # Id                  INTEGER PRIMARY KEY AUTOINCREMENT
        #                             UNIQUE
        #                             NOT NULL,
        # ClientId            TEXT    NOT NULL,
        res = '{} {}'.format(self._colname, self._coltype)

        if isinstance(self._length, int) and self._length > 0:
            res += f'({self._length})'
        if self._is_primary_key:
            res += ' PRIMARY KEY'
        if self._is_auto_increament:
            res += ' AUTOINCREMENT'
        if self._is_unique:
            res += ' UNIQUE'
        if not self._nullable:
            res += ' NOT NULL'
        if not self._defaultval is None:
            if isinstance(self._defaultval, str):
                res += f' DEFAULT({self._defaultval})'
            elif callable(self._defaultval):
                res += f' DEFAULT({self._defaultval()})'
            else:
                res += f' DEFAULT({self._defaultval})'

        return res

    def create_index(self, conn: SqliteConn) -> bool:
        """当前列若做了索引，则创建，返回是否创建成功。"""
        res: bool = True
        if not self._index is None:
            res = self._index.check_index(conn)
        return res


class SqliteTable:
    """represents a sqlite table\n
    对于一个表结构对象来说，它应该是不变的，而很多个数据库都可以来应用这个表结构，
    所以表初始化缓存记录在SqliteTable里\n
    tbname: 表名\n
    craete_on_miss: 是否在数据库文件缺少此表时创建表，默认为True"""

    def __init__(
            self,
            tbname: str,
            create_on_miss: bool = True,
            *cols,
    ):
        if tbname is None:
            raise Exception("Param 'tbname' cannot be None")
        self._tbname = tbname

        self._cols: dict = {}
        self._cols_locker = threading.RLock()
        for c in cols:
            self.append_column(c)

        self._create_on_miss: bool = True
        if isinstance(create_on_miss, bool):
            self._create_on_miss = create_on_miss

        # 表初始化状态缓存
        self._initialed_conns: dict = {}
        self._initialed_conns_locker = threading.RLock()

    def append_column(self, col: SqliteColumn):
        """向当前sqlitetable添加一个列，返回当前SqliteTable对象本身"""
        if not isinstance(col, SqliteColumn):
            raise Exception("Invalid sqlite column")
        if self._cols.__contains__(col._colname):
            raise Exception("Reduplicated column name: {}".format(
                col._colname))

        with self._cols_locker:
            if self._cols.__contains__(col._colname):
                raise Exception("Reduplicated column name: {}".format(
                    col._colname))
            self._cols[col._colname] = col
            col.set_owner_table(self)

        return self

    def new_column(self,
                   colname: str,
                   coltype: str = 'TEXT',
                   length: int = None,
                   nullable: bool = True,
                   is_primary_key: bool = False,
                   is_auto_increament: bool = False,
                   is_unique: bool = False,
                   defaultval: str = None,
                   create_on_miss: bool = True,
                   *indexs):
        """在当前SqliteTable中创建一个SqliteColumn列对象，并返回当前SqliteTable本身"""
        newcol = SqliteColumn(
            colname=colname,
            coltype=coltype,
            length=length,
            nullable=nullable,
            is_primary_key=is_primary_key,
            is_auto_increament=is_auto_increament,
            is_unique=is_unique,
            defaultval=defaultval,
            create_on_miss=create_on_miss,
            *indexs)
        return self.append_column(newcol)

    def check_table_creation(
            self,
            conn: SqliteConn,
    ) -> bool:
        """检查给与的数据库文件的给与的表，没有则创建，或动态增加新的列，并返回是否操作成功"""
        res: bool = False
        try:
            if not isinstance(conn, SqliteConn):
                raise Exception("Invalid sqlite connection")

            # 检查缓存是否标记为已初始化
            if self._initialed_conns.__contains__(conn):
                return True
            with self._initialed_conns_locker:
                if self._initialed_conns.__contains__(conn):
                    return True

                # 先检查表是否存在
                cursor = conn.cursor
                cmd = '''
SELECT COUNT()
FROM sqlite_master
WHERE type = 'table' AND
name = ?;'''
                result: sqlite3.Cursor = cursor.execute(cmd, (self._tbname, ))
                conn.commit()
                exists: bool = False
                for c in result:
                    # print(c)
                    if len(c) > 0 and c[0] == 1:
                        exists = True
                        break
                if not exists:
                    # 若不存在，需要建表建索引
                    if self._create_on_miss and self.create_table(conn):
                        res = True
                    # 若是新建的表，直接返回即可
                    return res

                # 表存在则检查列是否缺失
                # 检查列功能应放到SqliteColumn对象里，
                # 里面每个列都去查一次也无所谓，
                # 反正做了缓存，每次启动只会检查一次。
                for col in self._cols.values():
                    col: SqliteColumn = col
                    if not col.check_column(conn):
                        return res

                res = True

        except Exception as ex:
            raise ex
        finally:
            # 只要成功，且只要跑过一次此函数，则算作已初始化，并记录
            if res and not self._initialed_conns.__contains__(conn):
                with self._initialed_conns_locker:
                    if res and not self._initialed_conns.__contains__(conn):
                        self._initialed_conns[conn] = True

        return res

    def create_table(self, conn: SqliteConn) -> bool:
        """在给与的数据库文件上创建当前表，返回bool指示是否成功"""
        res: bool = False
        try:
            # 创建表
            cmd: str = f'CREATE TABLE IF NOT EXISTS {self._tbname}('
            for c in self._cols.values():
                c: SqliteColumn = c
                c_sql: str = c.get_col_creation_sql()

                cmd += c_sql
                cmd += ','

            cmd = cmd.rstrip(',')
            cmd += ');'

            cursor: sqlite3.Cursor = conn.cursor
            result = cursor.execute(cmd)
            conn.commit()
            if result is None:
                # raise Exception("Create table ClientStatus failed.")
                return res

            # 创建索引
            for col in self._cols.values():
                col: SqliteColumn = col
                if not col.create_index(conn):
                    return res

            res = True

        except Exception as ex:
            raise ex
        return res

    def _get_table_creation_sql(self) -> str:
        """反回当前表的创建语句"""
        res: str = None

        res = 'CREATE TABLE IF NOT EXISTS ClientStatus('
        for c in self._cols:
            c: SqliteColumn = c
            c_sql: str = c.get_col_creation_sql()
            if c_sql is None:
                return None
            res += c_sql
            res += ','

        res += ');'

        return res
