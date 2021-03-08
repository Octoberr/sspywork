"""
1、单次下载shodan的国家数据会出现很多重复的文件
重复的数据会浪费传输带宽
2、这个表为单个任务使用当任务完成后需要删除清除该表的数据
create by judy 2019/08/27
"""

import traceback

from commonbaby.sql import (SqliteColumn, SqliteConn,
                            SqliteTable, table_locker)

from .sqliteconfig import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbUnShodanData(TbSqliteBase):
    __tb_shodandata: SqliteTable = SqliteTable(
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
    databasename = 'shodandb'

    def __init__(self, dbcfg: SqliteConfig):
        TbSqliteBase.__init__(self, TbUnShodanData.__tb_shodandata._tbname, dbcfg, TbUnShodanData.databasename)

    def _append_tables(self):
        self._conn_mngr.append_table(TbUnShodanData.__tb_shodandata)

    @table_locker(__tb_shodandata._tbname)
    def insert_identify(self, unique_info, time_str):
        """
        存储数据的唯一标识和时间
        shodan 可能会更新时间，所以需要更新时间后的数据
        :param unique_info:
        :return:
        """
        sql = '''
        INSERT INTO undata(
        UniqueId,
        DownloadTime
        )VALUES (?, ?)
        '''
        # time_str = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
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
            self._logger.error(f"Insert unshodan data error,err:{traceback.format_exc()}")
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return res

    @table_locker(__tb_shodandata._tbname)
    def identify_count(self, unique_info, time_str) -> bool:
        """
        查询数据库中是否已经下载了该数据
        :param unique_info:
        :return:
        """
        conn: SqliteConn = False
        res: bool = False
        sql = """select count(1) from undata where UniqueId=? and DownloadTime=?"""
        pars = (unique_info, time_str)
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

    @table_locker(__tb_shodandata._tbname)
    def delete_table(self):
        """
        当次的数据只使用与当次的任务，与下一次任务并无交集
        所以在使用完成后需要删除数据
        :return:
        """
        conn: SqliteConn = False
        sql = """DELETE FROM undata"""
        try:
            for conn in self.connect_all(5):
                try:
                    conn: SqliteConn = conn
                    c = conn.cursor
                    c.execute(sql)
                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                finally:
                    if conn is not None:
                        conn.close()
        except:
            self._logger.error(f"Delete unique data error,err:{traceback.format_exc()}")
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return
