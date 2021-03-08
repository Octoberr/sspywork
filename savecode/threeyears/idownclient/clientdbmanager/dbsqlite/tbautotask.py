"""
存储，读取，更新
autotask
create by judy 2019/07/27
"""

import traceback

from commonbaby.helpers import helper_str
from commonbaby.sql import SqliteColumn, SqliteConn, SqliteTable, table_locker

from datacontract.automateddataset import AutomatedTask
from .sqliteconfig import SqliteConfig
from .tbsqlitebase import TbSqliteBase
from ..sqlcondition import SqlCondition, SqlConditions


class TbAutoTask(TbSqliteBase):
    __tb_autotask: SqliteTable = SqliteTable(
        "autotask",
        True,
        SqliteColumn(
            colname="ID",
            coltype="INTEGER",
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True,
        ).set_index_new(),
        SqliteColumn(colname="platform", coltype="CHAR", length=50),
        SqliteColumn(colname="source", coltype="CHAR", length=50),
        SqliteColumn(colname="periodnum", coltype="INT", length=50),
        SqliteColumn(colname="taskid", coltype="CHAR", length=50, nullable=False),
        SqliteColumn(
            colname="batchid", coltype="CHAR", length=50, nullable=False
        ).set_index_new(),
        SqliteColumn(colname="autotasktype", coltype="INT", nullable=False),
        SqliteColumn(colname="createtime", coltype="CHAR"),
        SqliteColumn(colname="cmdid", coltype="CHAR"),
        SqliteColumn(colname="lastendtime", coltype="INT"),
        SqliteColumn(colname="sequence", coltype="INT"),
        SqliteColumn(colname="taskstatus", coltype="INT"),
        SqliteColumn(colname="clientid", coltype="CHAR", length=50),
    )

    databasename = "task"

    def __init__(self, dbcfg: SqliteConfig):
        TbSqliteBase.__init__(
            self, TbAutoTask.__tb_autotask._tbname, dbcfg, TbAutoTask.databasename
        )

    def _append_tables(self):
        self._conn_mngr.append_table(TbAutoTask.__tb_autotask)

    @table_locker(__tb_autotask._tbname)
    def query_auto_task(self, conds: SqlConditions) -> list:
        """
        根据任务状态来取出task表的任务，
        根据不同的状态来查询不同的任务数据
        :param key:
        :param value:
        :return:
        """
        conn: SqliteConn = None
        res = []
        sql = """SELECT 
         autotask.platform,
         source,
         periodnum,
         taskid,
         batchid,
         autotasktype,
         createtime,
         cmdid,
         cmd,
         lastendtime,
         sequence,
         taskstatus,
         clientid
        FROM autotask LEFT OUTER JOIN idowncmd USING (cmdid) 
        WHERE {};""".format(
            conds.text_normal
        )
        try:
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    conn._conn.row_factory = self._dict_factory
                    c = conn._conn.cursor()
                    c.execute(sql, conds.params)
                    res_data = c.fetchall()
                    if len(res_data) > 0:
                        res.extend(res_data)
                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                finally:
                    if conn is not None:
                        conn.close()
        except Exception:
            self._logger.error(
                f"Query task according to the task status data problem,err:{traceback.format_exc()}."
            )
        finally:
            if conn is not None:
                conn.close()
        return res

    def _get_task_update_sql(self, src: dict, new: AutomatedTask):
        """拼接更新task的sql，并返回sqlparameters列表"""
        params: list = []
        sql = "UPDATE autotask SET taskstatus=?, "
        params.append(new.taskstatus.value)
        sql += "autotasktype=?, "
        params.append(new.autotasktype.value)
        if helper_str.is_none_or_empty(new.periodnum):
            sql += "periodnum=?, "
            params.append(new.periodnum)
        # if helper_str.is_none_or_empty(new.others):
        #     sql += 'others=?, '
        #     params.append(new.others)

        sql = sql.rstrip().rstrip(",")
        sql += " WHERE batchid=? AND taskid=?"
        params.append(new.batchid)
        params.append(new.taskid)
        return sql, params

    @table_locker(__tb_autotask._tbname)
    def __count_autotask(self, taskid, batchid):
        """
        对数据库中的任务进行计数
        :param taskid:
        :param batchid:
        :return:
        """
        conn: SqliteConn = None
        res = []
        sql = """
        SELECT count(1) FROM autotask
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
                    if len(res_data) > 0 and res_data[0][0] > 0:
                        res.extend(res_data)
                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                finally:
                    if conn is not None:
                        conn.close()
        except Exception:
            self._logger.error(f"Count autotask error,err:{traceback.format_exc()}.")
        finally:
            if conn is not None:
                conn.close()
        return res

    @table_locker(__tb_autotask._tbname)
    def _updatesametaskiddata(self, dt: AutomatedTask):
        """
        在插入任务数据前，先检查autotak表
        是否有相同的taskid, 如果taskid相同那么就更新整条数据的状态
        :param dt:
        :return:
        """
        res = False
        conn: SqliteConn = None
        resdata = self.__count_autotask(dt.taskid, dt.batchid)
        if len(resdata) == 0:
            # 没有重复的id直接返回
            return False
        elif len(resdata) > 1:
            raise Exception(
                "The database has duplicated multiple skipids, please check the problem"
            )
        elif len(resdata) == 1:
            sql, par = self._get_task_update_sql(resdata[0], dt)
            try:
                for conn in self.connect_all(5):
                    try:
                        c = conn.cursor
                        result = c.execute(sql, par)
                        if (
                            result is not None and result.rowcount > 0
                        ):  # or len(result) < 1:
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
                    f"There was a problem updating the iscan table task data，err:{traceback.format_exc()}!"
                )
            finally:
                if conn is not None:
                    conn.close()
            return True

    @table_locker(__tb_autotask._tbname)
    def insert_autotask(self, dt: AutomatedTask):
        """
        扫描任务目前是直接存入数据库的表
        如果是重复的任务那么就更新
        :param dt:
        :return:
        """
        conn: SqliteConn = None
        # 在插入数据前查询是否有相同的数据(目前只根据taskid查询)，如果有相同的数据则不插入。
        repeat = self._updatesametaskiddata(dt)
        if repeat:
            # 如果已经处理了重复的数据直接就结束了
            return
        sql = """
            INSERT INTO autotask(
            platform,
            source,
            periodnum,
            taskid,
            batchid,
            autotasktype,
            createtime,
            cmdid,
            lastendtime,
            sequence,
            taskstatus,
            clientid
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            dt.platform,
            dt.source,
            dt.periodnum,
            dt.taskid,
            dt.batchid,
            dt.autotasktype.value,
            dt.createtime,
            dt.cmd_id,
            dt.lastendtime,
            dt._sequence,
            dt.taskstatus.value,
            dt._clientid,
        )
        try:
            conn = self.connect_write(5)
            c = conn.cursor
            c.execute(sql, params)
        except Exception:
            self._logger.error(
                f"There was a problem inserting data, err:{traceback.format_exc()}."
            )
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return

    @table_locker(__tb_autotask._tbname)
    def update_auto_status(self, key: str, value: int, batchid, taskid):
        """
        更新task表的任务状态，根据batchid定位数据
        :param key:
        :param value:
        :param batchid:
        :return:
        """
        res = False
        conn: SqliteConn = None
        sql = """UPDATE autotask set {}=? where taskid=? and batchid=?
        """.format(
            key
        )
        pars = (value, taskid, batchid)
        try:
            for conn in self.connect_all(5):
                try:
                    c = conn.cursor
                    result = c.execute(sql, pars)
                    if (
                        result is not None and result.rowcount > 0
                    ):  # or len(result) < 1:
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
                f"There was a problem update task status data, err:{traceback.format_exc()}."
            )
        finally:
            if conn is not None:
                conn.close()
        return
