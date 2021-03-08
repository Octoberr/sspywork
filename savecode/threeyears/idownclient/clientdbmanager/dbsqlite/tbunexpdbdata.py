"""
保存autodata的唯一标识
create by judy 2019/08/15
"""

import traceback
from datetime import datetime

import pytz
from commonbaby.sql import (SqliteColumn, SqliteConn,
                            SqliteTable, table_locker)

from .sqliteconfig import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbUnEXPDBData(TbSqliteBase):
    __tb_autodata: SqliteTable = SqliteTable(
        'undata',
        True,
        SqliteColumn(
            colname='Id',
            coltype='INTEGER',
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True).set_index_new(),
        SqliteColumn(colname='UniqueId', nullable=False).set_index_new(),
        SqliteColumn(colname='DownloadTime', coltype='DATETIME', nullable=False),
    )
    databasename = 'expdbdata'

    def __init__(self, dbcfg: SqliteConfig):
        TbSqliteBase.__init__(self, TbUnEXPDBData.__tb_autodata._tbname, dbcfg, TbUnEXPDBData.databasename)

    def _append_tables(self):
        self._conn_mngr.append_table(TbUnEXPDBData.__tb_autodata)

    @table_locker(__tb_autodata._tbname)
    def insert_identify(self, unique_info):
        """
        存储数据的唯一标识
        :param unique_info:
        :return:
        """
        sql = '''
        INSERT INTO undata(
        UniqueId,
        DownloadTime
        )VALUES (?, ?)
        '''
        time_str = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        pars = (unique_info, time_str)
        res = False
        conn: SqliteConn = None
        try:
            conn: SqliteConn = self.connect_write(5)
            c = conn.cursor
            result = c.execute(sql, pars)
            if result is None or result.rowcount < 1:  # or len(result) < 1:
                res = False
            else:
                res = True
        except:
            self._logger.error(f"Insert auto unique data error,err:{traceback.format_exc()}")
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return res

    @table_locker(__tb_autodata._tbname)
    def identify_count(self, unique_info) -> bool:
        """
        查询数据库中是否已经下载了该数据
        :param unique_info:
        :return:
        """
        conn: SqliteConn = False
        res: bool = False
        sql = """select count(1) from undata where UniqueId=?"""
        pars = (unique_info,)
        try:
            for conn in self.connect_all(5):
                try:
                    conn: SqliteConn = conn
                    c = conn.cursor
                    result = c.execute(sql, pars)
                    for c in result:
                        # print(c)
                        if len(c) > 0 and c[0] > 0:
                            res = True
                            break
                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                finally:
                    if conn is not None:
                        conn.close()
                    if res:
                        break
        except:
            self._logger.error(f"Count auto unique data error,err:{traceback.format_exc()}")
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return res
