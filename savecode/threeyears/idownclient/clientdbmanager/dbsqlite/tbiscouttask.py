"""
存储iscout task
create by swm 20190709
新增查询iscout task的cmd，里面有验证码
modify by judy 20201113
"""

import traceback

from commonbaby.helpers import helper_str
from commonbaby.sql import SqliteColumn, SqliteConn, SqliteTable, table_locker

from datacontract.iscoutdataset import IscoutTask
from .sqliteconfig import SqliteConfig
from .tbsqlitebase import TbSqliteBase
from ..sqlcondition import SqlCondition, SqlConditions


class TbIscoutTask(TbSqliteBase):
    __tb_iscouttask: SqliteTable = SqliteTable(
        "iscouttask",
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
        SqliteColumn(
            colname="batchid", coltype="CHAR", length=50, nullable=False
        ).set_index_new(),
        SqliteColumn(colname="platform", coltype="CHAR", length=50, nullable=False),
        SqliteColumn(colname="clientid", coltype="CHAR", length=50, nullable=False),
        SqliteColumn(colname="source", coltype="CHAR", nullable=False),
        SqliteColumn(colname="objecttype", coltype="INT", nullable=False),
        SqliteColumn(colname="object", coltype="CHAR", nullable=False),
        SqliteColumn(colname="createtime", coltype="CHAR"),
        SqliteColumn(colname="cmdid", coltype="CHAR", length=50),
        SqliteColumn(colname="lastexecutetime", coltype="INT"),
        SqliteColumn(colname="failtimes", coltype="INT"),
        SqliteColumn(colname="successtimes", coltype="INT"),
        SqliteColumn(colname="taskstatus", coltype="INT"),
        SqliteColumn(colname="sequence", coltype="INT"),
        SqliteColumn(colname="periodnum", coltype="INT"),
    )
    databasename = "task"

    def __init__(self, dbcfg: SqliteConfig):
        TbSqliteBase.__init__(
            self, TbIscoutTask.__tb_iscouttask._tbname, dbcfg, TbIscoutTask.databasename
        )

    def _append_tables(self):
        self._conn_mngr.append_table(TbIscoutTask.__tb_iscouttask)

    @table_locker(__tb_iscouttask._tbname)
    def query_iscout_task(self, conds: SqlConditions) -> list:
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
        taskid,
        batchid,
        iscouttask.platform,
        clientid,
        source,
        objecttype,
        object,
        createtime,
        cmdid,
        cmd,
        taskstatus,
        sequence,
        periodnum
        FROM iscouttask  LEFT OUTER JOIN idowncmd USING (cmdid)
        WHERE  {};""".format(
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
                f"Query task according to the task status data problem,err:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.close()
        return res

    def _get_task_update_sql(self, src: dict, new: IscoutTask):
        """拼接更新task的sql，并返回sqlparameters列表"""
        params: list = []
        sql = "UPDATE iscouttask SET taskstatus=?, "
        params.append(new.taskstatus.value)
        sql += "objecttype=?, "
        params.append(new._objecttype.value)
        sql += "object=?, "
        params.append(new._object)

        # 增加一个存入时间
        # sql += 'taskstarttime=?, '
        # params.append(new.taskstarttime)
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
        sql += " WHERE batchid=? AND taskid=?"
        params.append(new.batchid)
        params.append(new.taskid)

        return sql, params

    @table_locker(__tb_iscouttask._tbname)
    def __count_iscouttask(self, taskid, batchid):
        """
        对数据库中的任务进行计数
        :param taskid:
        :param batchid:
        :return:
        """
        conn: SqliteConn = None
        res = []
        sql = """
        SELECT count(1) FROM iscouttask
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
                f"Query task according to the task status data problem\nerr:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.close()
        return res

    @table_locker(__tb_iscouttask._tbname)
    def _updatesamebatchiddata(self, dt: IscoutTask):
        """
        在插入任务数据前，先检查iscouttask表
        是否有相同的batchid, 如果batchid相同那么就更新整条数据的状态
        :param dt:
        :return:
        """
        res = False
        conn: SqliteConn = None
        resdata = self.__count_iscouttask(dt.taskid, dt.batchid)
        if len(resdata) == 0:
            # 没有重复的id直接返回
            return False
        elif len(resdata) > 1:
            raise Exception(
                "The database has duplicated multiple skipids, please check the problem"
            )
        elif len(resdata) == 1:
            self._logger.info(f"Get same task, update scout task info")
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
                            self._logger.info(f"Update task status success")
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
                    f"There was a problem updating the iscouttask table\nerr:{traceback.format_exc()}"
                )
            finally:
                if conn is not None:
                    conn.close()
            return res

    @table_locker(__tb_iscouttask._tbname)
    def insert_iscouttask(self, dt: IscoutTask):
        """
        扫描任务目前是直接存入数据库的表
        如果是重复的任务那么就更新
        :param dt:
        :return:
        """
        conn: SqliteConn = None
        # 在插入数据前查询是否有相同的数据(目前只根据taskid查询)，如果有相同的数据则不插入。
        repeat = self._updatesamebatchiddata(dt)
        if repeat:
            # 如果已经处理了重复的数据直接就结束了
            return
        sql = """
            INSERT INTO iscouttask(
            taskid,
            batchid,
            platform,
            clientid,
            source,
            objecttype,
            object,
            createtime,
            cmdid,
            taskstatus,
            sequence, 
            periodnum
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            dt.taskid,
            dt.batchid,
            dt.platform,
            dt._clientid,
            dt.source,
            dt._objecttype.value,
            dt._object,
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

    @table_locker(__tb_iscouttask._tbname)
    def update_iscout_status(self, key: str, value: int, batchid, taskid):
        """
        更新iscouttask表的任务状态，根据batchid定位数据
        :param key:
        :param value:
        :param taskid:
        :return:
        """
        res = False
        conn: SqliteConn = None
        sql = """UPDATE iscouttask set {}=? where taskid=? and batchid=?
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
                f"There was a problem inserting data, and duplicate data might have been inserted\nerr:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.close()
        return

    @table_locker(__tb_iscouttask._tbname)
    def update_iscout_info(self, tsk: IscoutTask):
        """
        更新下载完成后task的信息，作用于iscout的循环下载
        :param tsk:
        :return:
        """
        res = False
        conn: SqliteConn = None
        sql = """UPDATE iscouttask set 
        lastexecutetime=?,
        failtimes=?,
        successtimes=?,
        sequence=?, 
        periodnum=?
        where taskid=? and batchid=?
        """
        pars = (
            tsk.lastexecutetime,
            tsk.failtimes,
            tsk.successtimes,
            tsk._sequence,
            tsk.periodnum,
            tsk.taskid,
            tsk.batchid,
        )
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