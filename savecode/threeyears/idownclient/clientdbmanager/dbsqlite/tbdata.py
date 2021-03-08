"""
data表
create by judy
2019/02/20
插入data表前判断数据是否存在于数据库中
update by judy 2019/03/22

作为当前数据的唯一标识，保留当前数据的uniqueid
不再需要account来分辨不同的账号，因为uniqueid确实回事独一无二的
update by judy 2019/03/27
"""

from datacontract.outputdata import EStandardDataType
import traceback

from commonbaby.helpers import helper_time
from commonbaby.sql import (SqliteColumn, SqliteConn, SqliteTable,
                            table_locker)

from idownclient.clientdatafeedback import FeedDataBase, UniqueData
from .sqliteconfig import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbData(TbSqliteBase):
    __tb_data: SqliteTable = SqliteTable(
        'data',
        True,
        SqliteColumn(
            colname='Id',
            coltype='INTEGER',
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True).set_index_new(),
        SqliteColumn(colname='UniqueId', nullable=False).set_index_new(),
        SqliteColumn(colname='DataType', nullable=False),
        SqliteColumn(colname='AppType', coltype='INTEGER', nullable=False),
        # SqliteColumn(colname='Account', nullable=False),
        SqliteColumn(colname='DownloadTime', coltype='DATETIME', nullable=False),
    )
    databasename = 'idowndata'

    def __init__(self, dbcfg: SqliteConfig):
        TbSqliteBase.__init__(self, TbData.__tb_data._tbname, dbcfg, TbData.databasename)

    def _append_tables(self):
        self._conn_mngr.append_table(TbData.__tb_data)

    def _get_execute_sql_pars(self, data: FeedDataBase):
        if not isinstance(data, UniqueData):
            raise Exception("Param data is invalid.")
        sqls = []
        if not data._is_muti_seg:
            sql = self.__get_sql_pars(data, data._datatype.value)
            sqls.append(sql)
        else:
            for inner in data:
                sql = self.__get_sql_pars(inner, data._datatype.value)
                sqls.append(sql)
        return sqls

    def __get_sql_pars(self, data: UniqueData, datatype):
        pars = (
            data.get_uniqueid(),
            datatype,
            data._task.apptype,
            # data._task.account,
            helper_time.get_time_sec_tz(),
        )
        return pars

    def _dump_pars(self, pars):
        conn = None
        sql = '''
        SELECT count(1) FROM data 
        WHERE UniqueId=?
        '''
        newdata = []
        for par in pars:
            try:
                # 默认数据不是重复的
                dump_res = False
                for conn in self.connect_all(5):
                    try:
                        conn: SqliteConn = conn
                        c = conn.cursor
                        c.execute(sql, (par[0], ))
                        result = c.fetchall()
                        # 防止没有查出来
                        if len(result) > 0 and result[0][0] > 0:
                            # 数据是重复的
                            dump_res = True
                            break
                    except Exception as ex:
                        conn._conn.rollback()
                        raise ex
                    finally:
                        if conn is not None:
                            conn.close()
                if not dump_res:
                    newdata.append(par)
            except:
                self._logger.error(
                    f'Dump data error, err:{traceback.format_exc()}')
            finally:
                if conn is not None:
                    conn.commit()
                    conn.close()
        return newdata

    @table_locker(__tb_data._tbname)
    def insert_uniquely_identifies(self, data: FeedDataBase) -> bool:
        """
        向数据库存入数据唯一标识，用于去重。返回是否插入成功True/False
        由于存在强制下载，所以可能需要更新已有的资源数据
        """
        conn: SqliteConn = None
        res: bool = False
        sql = """insert into data(
            UniqueId,
            DataType,
            AppType,
            DownloadTime
        ) values(?,?,?,?)"""

        try:
            pars = self._get_execute_sql_pars(data)
            if len(pars) == 0:
                return res
            # 插入前查询数据是否在数据库里
            new_pars = self._dump_pars(pars)
            if len(new_pars) == 0:
                return res
            pars = new_pars
            conn = self.connect_write()
            c = conn._conn.cursor()
            if len(pars) == 1:
                result = c.execute(sql, pars[0])
            else:
                result = c.executemany(sql, pars)
            if result is None or result.rowcount < 1:  # or len(result) < 1:
                res = False
            else:
                res = True
        except Exception:
            self._logger.error(
                f"Insert data to db error:\ndatatype:{data._datatype}\n"
                f"datauniqueid:{data.get_uniqueid()}\nerror:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return res

    @table_locker(__tb_data._tbname)
    def is_data_exists(self, data: UniqueData,
                       datatype: EStandardDataType) -> bool:
        """检查数据是否已存在。返回True/False"""
        conn: SqliteConn = False
        res: bool = False
        try:
            if not isinstance(data, UniqueData):
                raise Exception("Param data is invalid.")
            sql = """select count(1) from data where
            UniqueId=? and
            DataType=? and
            AppType=?"""
            for conn in self.connect_all(5):
                try:
                    conn: SqliteConn = conn
                    c = conn.cursor
                    result = c.execute(sql, (
                        data.get_uniqueid(),
                        datatype.value,
                        data._task.apptype,
                    ))
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
        except Exception:
            self._logger.error(
                "Check data duplication error:\ndatatype:{}\ndataid:{}\nerror:{}"
                .format(data._datatype.name, data.get_uniqueid(),
                        traceback.format_exc()))
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return res
