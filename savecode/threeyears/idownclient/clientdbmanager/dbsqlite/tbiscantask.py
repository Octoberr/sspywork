"""
存储iscan task
create by judy 2019/06/24
"""

import traceback

from commonbaby.helpers import helper_str
from commonbaby.sql import SqliteColumn, SqliteConn, SqliteTable, table_locker

from datacontract.iscandataset import IscanTask
from .sqliteconfig import SqliteConfig
from .tbsqlitebase import TbSqliteBase
from ..sqlcondition import SqlCondition, SqlConditions


class TbIscanTask(TbSqliteBase):
    __tb_iscantask: SqliteTable = SqliteTable(
        "iscantask",
        True,
        SqliteColumn(
            colname="ID",
            coltype="INTEGER",
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True,
        ).set_index_new(),
        SqliteColumn(
            colname="taskid", coltype="CHAR", length=50, nullable=False
        ).set_index_new(),
        SqliteColumn(colname="platform", coltype="CHAR", length=50, nullable=False),
        SqliteColumn(colname="clientid", coltype="CHAR", length=50, nullable=False),
        SqliteColumn(colname="source", coltype="CHAR", nullable=False),
        SqliteColumn(colname="scantype", coltype="INT", nullable=False),
        SqliteColumn(colname="createtime", coltype="CHAR"),
        SqliteColumn(colname="cmdid", coltype="CHAR", length=50),
        SqliteColumn(colname="lastexecutetime", coltype="INT"),
        SqliteColumn(colname="failtimes", coltype="INT"),
        SqliteColumn(colname="successtimes", coltype="INT"),
        SqliteColumn(colname="taskstatus", coltype="INT"),
        SqliteColumn(colname="sequence", coltype="INT"),
        SqliteColumn(colname="periodnum", coltype="INT"),
        SqliteColumn(colname="query_date", coltype="CHAR"),
        SqliteColumn(colname="query_page", coltype="INT"),
    )
    databasename = "task"

    def __init__(self, dbcfg: SqliteConfig):
        TbSqliteBase.__init__(
            self, TbIscanTask.__tb_iscantask._tbname, dbcfg, TbIscanTask.databasename
        )

    def _append_tables(self):
        self._conn_mngr.append_table(TbIscanTask.__tb_iscantask)

    @table_locker(__tb_iscantask._tbname)
    def query_iscan_task(self, conds: SqlConditions) -> list:
        """
        根据任务状态来取出task表的任务，
        根据不同的状态来查询不同的任务数据
        :param conds:
        :return:
        """
        conn: SqliteConn = None
        res = []
        sql = """SELECT 
        taskid,
        iscantask.platform,
        clientid,
        source,
        scantype,
        createtime,
        cmdid,
        cmd,
        taskstatus,
        sequence,
        periodnum,
        query_date,
        query_page
        FROM iscantask  LEFT OUTER JOIN idowncmd USING (cmdid)
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
                f"Query task according to the task status error\nerr:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.close()
        return res

    def _get_task_update_sql(self, src: dict, new: IscanTask):
        """
        相同的任务更新字段
        taskstatus
        cmdid
        source
        periodnum
        拼接更新task的sql，并返回sqlparameters列表
        iscantask接收的是server发放的周期任务和暂停任务
        所以每次都需要将状态给更新
        """
        params: list = []
        sql = "UPDATE iscantask SET taskstatus=?, "
        params.append(new.taskstatus.value)
        # sql += 'scantype=?, '
        # params.append(new.scantype.value)
        if not helper_str.is_none_or_empty(new.cmd_id):
            sql += "cmdid=?, "
            params.append(new.cmd_id)
        if not helper_str.is_none_or_empty(new.source):
            sql += "source=?, "
            params.append(new.source)
        if not helper_str.is_none_or_empty(new.periodnum):
            sql += "periodnum=?, "
            params.append(new.periodnum)

        sql = sql.rstrip().rstrip(",")
        sql += " WHERE taskid=?"
        params.append(new.taskid)

        return sql, params

    @table_locker(__tb_iscantask._tbname)
    def __count_iscanttask(self, taskid):
        """
        对数据库中的任务进行计数
        :param taskid:
        :return:
        """
        conn: SqliteConn = None
        res = []
        sql = """
        SELECT count(1) FROM iscantask
        WHERE taskid=?
        """
        par = (taskid,)
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
                f"Query task according to the task status error\nerr:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.close()
        return res

    @table_locker(__tb_iscantask._tbname)
    def _updatesametaskiddata(self, dt: IscanTask):
        """
        在插入任务数据前，先检查iscantask表
        是否有相同的taskid, 如果taskid相同那么就更新整条数据的状态
        :param dt:
        :return:
        """
        res = False
        conn: SqliteConn = None
        resdata = self.__count_iscanttask(dt.taskid)
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
                    f"There was a problem updating the iscan table task data\nerr:{traceback.format_exc()}"
                )
            finally:
                if conn is not None:
                    conn.close()
            return True

    @table_locker(__tb_iscantask._tbname)
    def insert_iscantask(self, dt: IscanTask):
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
            INSERT INTO iscantask(
            taskid,
            platform,
            clientid,
            source,
            scantype,
            createtime,
            cmdid,
            taskstatus,
            sequence,
            periodnum
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            dt.taskid,
            dt.platform,
            dt._clientid,
            dt.source,
            dt.scantype.value,
            dt.createtimestr,
            dt.cmd_id,
            dt.taskstatus.value,
            dt._sequence,
            dt.periodnum,
        )
        try:
            conn = self.connect_write(5)
            c = conn.cursor
            c.execute(sql, params)
        except Exception:
            self._logger.error(
                f"There was a problem inserting data\nerr:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return

    @table_locker(__tb_iscantask._tbname)
    def update_iscan_status(self, key: str, value: int, taskid):
        """
        更新task表的任务状态，根据batchid定位数据
        :param key:
        :param value:
        :param taskid:
        :return:
        """
        res = False
        conn: SqliteConn = None
        sql = """UPDATE iscantask set {}=? where taskid=?
        """.format(
            key
        )
        pars = (value, taskid)
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
                f"There was a problem inserting data\nerr:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.close()
        return

    @table_locker(__tb_iscantask._tbname)
    def update_iscan_query_data(self, query_date, query_page, taskid):
        """
        在下载国家数据时记录date和page，
        当程序意外停止时，再启动时能够继续下载
        :param query_date:
        :param query_page:
        :param taskid:
        :return:
        """
        res = False
        conn: SqliteConn = None
        sql = """UPDATE iscantask set query_date=?, query_page=? where taskid=?
        """
        pars = (query_date, query_page, taskid)
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
                f"There was a problem updating data\nerr:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.close()
        return
