"""
新增idown的task和userinfo关联的表
用于保存和关联user信息，并且回馈给后台
create by judy 2020/11/18
"""

# from datacontract.outputdata import EStandardDataType
import traceback

# from commonbaby.helpers import helper_time
from commonbaby.sql import SqliteColumn, SqliteConn, SqliteTable, table_locker

# from idownclient.clientdatafeedback import FeedDataBase, UniqueData
from .sqliteconfig import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbTaskUserInfo(TbSqliteBase):
    __tb_userinfo: SqliteTable = SqliteTable(
        "userinfo",
        True,
        SqliteColumn(
            colname="Id",
            coltype="INTEGER",
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True,
        ).set_index_new(),
        SqliteColumn(
            colname="taskid", coltype="CHAR", length=50, nullable=False
        ).set_index_new(),
        SqliteColumn(
            colname="batchid", coltype="CHAR", length=50, nullable=False
        ).set_index_new(),
        SqliteColumn(colname="userid", coltype="CHAR", length=50, nullable=False),
        SqliteColumn(colname="clientid", coltype="CHAR", length=50, nullable=False),
        # SqliteColumn(colname='Account', nullable=False),
        # SqliteColumn(colname='DownloadTime', coltype='DATETIME', nullable=False),
    )
    databasename = "idownuser"

    def __init__(self, dbcfg: SqliteConfig):
        TbSqliteBase.__init__(
            self,
            TbTaskUserInfo.__tb_userinfo._tbname,
            dbcfg,
            TbTaskUserInfo.databasename,
        )

    def _append_tables(self):
        self._conn_mngr.append_table(TbTaskUserInfo.__tb_userinfo)

    @table_locker(__tb_userinfo._tbname)
    def __count_userinfo(self, taskid, batchid):
        """
        每个taskid和batchid代表唯一的一个任务
        一个唯一的任务对应唯一的userid
        :param taskid:
        :return:
        """
        conn: SqliteConn = None
        res = []
        sql = """
        SELECT count(1) FROM userinfo
        WHERE taskid=? AND batchid=?
        """
        par = (taskid, batchid)
        try:
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    # conn._conn.row_factory = self._dict_factory
                    c = conn.cursor
                    c.execute(sql, par)
                    res_data = c.fetchall()
                    # print(res_data)
                    if len(res_data) > 0 and res_data[0][0] > 0:
                        res.extend(res_data)
                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                finally:
                    if conn is not None:
                        conn.close()
        except Exception:
            self._logger.error(
                f"Query user from userinfo error\nerr:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.close()
        return res

    def _get_update_sql(self, taskid, batchid, userid, clientid):
        """
        一个唯一的任务只有唯一的userid和唯一的clientid
        所以直接更新就好
        """
        params: list = []
        sql = "UPDATE userinfo SET userid=?, clientid=?"
        params.append(userid)
        params.append(clientid)
        sql += " WHERE taskid=? and batchid=?"
        params.append(taskid)
        params.append(batchid)
        return sql, params

    @table_locker(__tb_userinfo._tbname)
    def _updatesameuserinfo(self, taskid, batchid, userid, clientid):
        """
        在插入任务数据前，先检查iscantask表
        是否有相同的taskid, 如果taskid相同那么就更新整条数据的状态
        """
        res = False
        conn: SqliteConn = None
        resdata = self.__count_userinfo(taskid, batchid)
        if len(resdata) == 0:
            # 没有重复的id直接返回
            return False
        elif len(resdata) > 1:
            raise Exception(
                "The database has duplicated multiple skipids, please check the problem"
            )
        elif len(resdata) == 1:
            sql, par = self._get_update_sql(taskid, batchid, userid, clientid)
            try:
                for conn in self.connect_all(5):
                    try:
                        c = conn.cursor
                        result = c.execute(sql, par)
                        if result is not None and result.rowcount > 0:
                            res = True
                    except Exception as ex:
                        conn._conn.rollback()
                        raise ex
                    else:
                        conn.commit()
                    finally:
                        if conn is not None:
                            conn.close()
                        if res:
                            break
            except Exception:
                self._logger.error(
                    f"There was a problem updating the userinfo table\nerr:{traceback.format_exc()}"
                )
            finally:
                if conn is not None:
                    conn.close()
            return True

    @table_locker(__tb_userinfo._tbname)
    def save_idown_userinfo(self, taskid, batchid, userid, clientid):
        """
        保存idown的user信息
        主要用于关联idown task给后台反馈目前的cookie状态
        """
        conn: SqliteConn = None
        # 在插入数据前查询是否有相同的数据，一个taskid和一个batchid只能带有一个userid
        repeat = self._updatesameuserinfo(taskid, batchid, userid, clientid)
        if repeat:
            # 如果已经处理了重复的数据直接就结束了
            return
        sql = """insert into userinfo(
            taskid,
            batchid,
            userid,
            clientid
        ) values(?,?,?,?)"""
        pars = (taskid, batchid, userid, clientid)
        try:
            conn = self.connect_write(5)
            c = conn.cursor
            c.execute(sql, pars)
        except Exception:
            self._logger.error(
                f"There was a problem inserting data\nerr:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return

    @table_locker(__tb_userinfo._tbname)
    def query_idown_userinfo(self, taskid, batchid) -> dict:
        """
        查询每个任务的user信息
        每个任务对应唯一的user
        :return:
        """
        conn: SqliteConn = None
        res = None
        sql = """SELECT 
        *
        FROM userinfo
        WHERE taskid=? and batchid=?;"""
        pars = (taskid, batchid)
        try:
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    conn._conn.row_factory = self._dict_factory
                    c = conn._conn.cursor()
                    c.execute(sql, pars)
                    res_data = c.fetchall()
                    if len(res_data) > 0:
                        res = res_data[0]
                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                finally:
                    if conn is not None:
                        conn.close()
        except Exception:
            self._logger.error(
                f"Query idown userinfo error\nerr:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.close()
        return res
