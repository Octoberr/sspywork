"""
task表
create by judy
2019/02/20
update by judy 2019/03/12
现在一个taskid 对应了多个batchid
所以以前所有的以taskid的查询条件现在全部使用batchid

增加了一个强制下载的字段forcedownload
by judy 2019/03/22
"""
import json
import traceback
import time
from datetime import datetime
import pytz

from commonbaby.helpers import helper_str
from commonbaby.sql import SqliteColumn, SqliteConn, SqliteTable, table_locker

from datacontract.idowndataset import Task
from .sqliteconfig import SqliteConfig
from .tbsqlitebase import TbSqliteBase
from ..sqlcondition import SqlCondition, SqlConditions


class TbTask(TbSqliteBase):
    __tb_task: SqliteTable = SqliteTable(
        "task",
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
        SqliteColumn(colname="parent_taskid", coltype="CHAR", length=50),
        SqliteColumn(colname="batchid", coltype="CHAR", length=50, nullable=False),
        SqliteColumn(colname="parentbatchid", coltype="CHAR", length=50),
        SqliteColumn(colname="apptype", coltype="INT"),
        SqliteColumn(colname="tasktype", coltype="INT"),
        SqliteColumn(colname="url", coltype="CHAR", length=50),
        SqliteColumn(colname="host", coltype="CHAR", length=50),
        SqliteColumn(colname="cookie", coltype="CHAR"),
        SqliteColumn(colname="preaccount", coltype="CHAR", length=50),
        SqliteColumn(colname="account", coltype="CHAR", length=50),
        SqliteColumn(colname="password", coltype="CHAR", length=50),
        SqliteColumn(colname="phone", coltype="CHAR", length=50),
        SqliteColumn(colname="input", coltype="CHAR", length=50),
        SqliteColumn(colname="taskstatus", coltype="INT"),
        SqliteColumn(colname="createtime", coltype="INT"),
        SqliteColumn(colname="lastexecutetime", coltype="INT"),
        SqliteColumn(colname="failtimes", coltype="INT"),
        SqliteColumn(colname="successtimes", coltype="INT"),
        SqliteColumn(colname="preglobaltelcode", coltype="CHAR", length=10),
        SqliteColumn(colname="globaltelcode", coltype="CHAR", length=10),
        SqliteColumn(colname="otherfileds", coltype="CHAR"),
        SqliteColumn(colname="tokentype", coltype="INT"),
        SqliteColumn(colname="sequence", coltype="INT"),
        SqliteColumn(colname="progress", coltype="REAL"),
        SqliteColumn(colname="forcedownload", coltype="CHAR", length=10),
        SqliteColumn(colname="source", coltype="CHAR", nullable=False),
        SqliteColumn(colname="cmdid", coltype="CHAR", length=50),
        SqliteColumn(colname="cookiealive", coltype="INT"),
        SqliteColumn(colname="cookielastkeeptime", coltype="INT"),
    )

    databasename = "task"

    def __init__(self, dbcfg: SqliteConfig):
        TbSqliteBase.__init__(
            self, TbTask.__tb_task._tbname, dbcfg, TbTask.databasename
        )

    def _append_tables(self):
        self._conn_mngr.append_table(TbTask.__tb_task)

    @table_locker(__tb_task._tbname)
    def query_task(self, conds: SqlConditions) -> list:
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
        task.platform,
        clientid,
        parent_taskid,
        batchid,
        parentbatchid,
        apptype,
        tasktype,
        url,
        host,
        cookie,
        preaccount,
        account,
        password,
        phone,
        input,
        taskstatus,
        createtime,
        lastexecutetime,
        failtimes,
        successtimes,
        preglobaltelcode,
        globaltelcode,
        otherfileds,
        tokentype,
        sequence,
        progress,
        forcedownload,
        source,
        cmdid,
        cmd,
        cookiealive,
        cookielastkeeptime
        FROM task  LEFT OUTER JOIN idowncmd USING (cmdid)
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

    def __modify_task_state(self, oldstate: int, task: Task):
        """
        这里的前置是已经为下载过的任务
        1、一次性任务，除了正在执行，新任务都会去更新状态
        2、循环任务，不会更新状态
        :param task:
        :return:
        """
        # 默认为不更新状态
        res = False
        circule_modle = task.cmd.stratagy.circulation_mode
        # 一次性任务
        if circule_modle == 1 and oldstate not in [0, 1, 2, 3, 5]:
            res = True
        # 循环任务或者其他情况都不去更新状态
        return res

    def _get_task_update_sql(self, src: dict, new: Task):
        """拼接更新task的sql，并返回sqlparameters列表"""
        params: list = []
        sql = "UPDATE task SET "
        # 特定条件更新任务下载状态
        if self.__modify_task_state(src["taskstatus"], new):
            sql += "taskstatus=?, "
            params.append(new.taskstatus.value)
        # 如果cmdid不一致则需要更新下cmd
        if src["cmdid"] != new.cmd_id:
            sql += "cmdid"
            params.append(new.cmd_id)
        # sql += 'otherfileds=?, '
        # params.append(json.dumps(new._other_fields))
        sql += "tasktype=?, "
        params.append(new.tasktype.value)
        if not helper_str.is_none_or_empty(new.cookie):
            sql += "cookie=?, "
            params.append(new.cookie)
        if helper_str.is_none_or_empty(src["url"]) and not helper_str.is_none_or_empty(
            new.url
        ):
            sql += "url=?, "
            params.append(new.url)
        if helper_str.is_none_or_empty(src["host"]) and not helper_str.is_none_or_empty(
            new.host
        ):
            sql += "host=?, "
            params.append(new.host)
        if helper_str.is_none_or_empty(
            src["account"]
        ) and not helper_str.is_none_or_empty(new.account):
            sql += "account=?, "
            params.append(new.account)
        if helper_str.is_none_or_empty(
            src["password"]
        ) and not helper_str.is_none_or_empty(new.password):
            sql += "password=?, "
            params.append(new.password)
        if helper_str.is_none_or_empty(
            src["phone"]
        ) and not helper_str.is_none_or_empty(new.password):
            sql += "phone=?, "
            params.append(new.password)
        if helper_str.is_none_or_empty(
            src["globaltelcode"]
        ) and not helper_str.is_none_or_empty(new.globaltelcode):
            sql += "globaltelcode=?, "
            params.append(new.globaltelcode)
        # if not helper_str.is_none_or_empty(new._sequence):
        #     sql += 'sequence=?, '
        #     params.append(int(new._sequence))
        if not helper_str.is_none_or_empty(new.forcedownload):
            sql += "forcedownload=?, "
            params.append(int(new.forcedownload))

        sql = sql.rstrip().rstrip(",")
        sql += " WHERE batchid=? AND taskid=?"
        params.append(new.batchid)
        params.append(new.taskid)

        return (sql, params)

    @table_locker(__tb_task._tbname)
    def __count_idowntask(self, taskid, batchid):
        """
        对数据库中的任务进行计数
        :param taskid:
        :param batchid:
        :return:
        """
        conn: SqliteConn = None
        res = []
        # sql = '''
        # SELECT count(1) FROM task
        # WHERE taskid=? AND batchid=?
        # '''
        sql = """
        SELECT * FROM task WHERE taskid=? AND batchid=?
        """
        par = (taskid, batchid)
        try:
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    # 只计数
                    # c = conn.cursor
                    # c.execute(sql, par)
                    # res_data = c.fetchall()
                    # print(res_data)
                    # if len(res_data) > 0 and res_data[0][0] > 0:
                    #     res.extend(res_data)
                    # 将数据库中的源数据查询出来
                    conn._conn.row_factory = self._dict_factory
                    c = conn._conn.cursor()
                    c.execute(sql, par)
                    fres: list = c.fetchall()
                    if len(fres) > 0:
                        res.extend(fres)
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

    @table_locker(__tb_task._tbname)
    def _updatesametaskiddata(self, dt: Task):
        """
        在插入任务数据前，先检查task表
        是否有相同的batchid, 如果batchid相同那么就更新整条数据的状态
        :param dt:
        :return:
        """
        res = False
        conn: SqliteConn = None
        resdata = self.__count_idowntask(dt.taskid, dt.batchid)
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
                    f"There was a problem updating the task table task data，err:{traceback.format_exc()}!"
                )
            finally:
                if conn is not None:
                    conn.close()
            return True

    @table_locker(__tb_task._tbname)
    def insert_task_to_sqlit(self, dt: Task):
        """
        通过登录测试的任务
        将有效的任务放入数据库的task表
        只会在这个地方插入一次
        :param dt:
        :return:
        """
        conn: SqliteConn = None
        # 在插入数据前查询是否有相同的数据(目前只根据taskid查询)，如果有相同的数据则不插入。
        repeat = self._updatesametaskiddata(dt)
        if repeat:
            # 如果已经处理了重复的数据直接就结束了
            return
        sql = """INSERT INTO task (
               taskid,
               platform,
               clientid,
               parent_taskid,
               batchid,
               parentbatchid,
               apptype,
               tasktype,
               url,
               host,
               cookie,
               preaccount,
               account,
               password,
               phone,
               input,
               taskstatus,
               createtime,
               lastexecutetime,
               failtimes,
               successtimes,
               preglobaltelcode,
               globaltelcode,
               otherfileds,
               tokentype,
               sequence,
               progress,
               forcedownload,
               source,
               cmdid,
               cookiealive,
               cookielastkeeptime
               )
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?,?,?,?,?,?);
               """
        params = (
            dt.taskid,
            dt.platform,
            dt._clientid,
            dt.parenttaskid,
            dt.batchid,
            dt.parentbatchid,
            int(dt.apptype),
            dt.tasktype.value,
            dt.url,
            dt.host,
            dt.cookie,
            dt.preaccount,
            dt.account,
            dt.password,
            dt.phone,
            dt.input,
            dt.taskstatus.value,
            dt.createtime,
            dt.lastexecutetime,
            dt.failtimes,
            dt.successtimes,
            dt.preglobaltelcode,
            dt.globaltelcode,
            json.dumps(dt._other_fields),
            dt.tokentype.value,
            int(dt._sequence),
            dt.progress,
            dt.forcedownload,
            dt.source,
            dt.cmd_id,
            dt.cookie_alive,
            dt.cookie_last_keep_alive_time,
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

    @table_locker(__tb_task._tbname)
    def update_status_by_taskid(self, key: str, value: int, batchid, taskid):
        """
        更新task表的任务状态，根据batchid和taskid共同定位数据
        :param key:
        :param value:
        :param taskid:
        :return:
        """
        res = False
        conn: SqliteConn = None
        sql = """UPDATE task set {}=? where taskid=? and batchid=?
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
                f"There was a problem inserting data, and duplicate "
                f"data might have been inserted, err:{traceback.format_exc()}."
            )
        finally:
            if conn is not None:
                conn.close()
        return

    @table_locker(__tb_task._tbname)
    def query_task_by_sql(self, sql, pars):
        """
        根据sql来查询数据库，提供一个对外查询的接口
        :param sql:
        :param pars:
        :return:
        """
        conn: SqliteConn = None
        allget = []
        try:
            for conn in self.connect_all(5):
                try:
                    conn._conn.row_factory = self._dict_factory
                    c = conn._conn.cursor()
                    c.execute(sql, pars)
                    res: list = c.fetchall()
                    if len(res) > 0:
                        allget.extend(res)
                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if conn is not None:
                        conn.close()
        except:
            self._logger.error(
                f"There was a problem querying data, err:{traceback.format_exc()}."
            )
        finally:
            if conn is not None:
                conn.close()
        return allget

    @table_locker(__tb_task._tbname)
    def update_task_resource(self, tsk: Task):
        """更新Task任务信息"""
        conn: SqliteConn = None
        res = False
        sql = """update task set
        url=?,
        host=?,
        cookie=?,
        account=?,
        password=?,
        phone=?, 
        lastexecutetime=?,
        successtimes=?,
        failtimes=?, 
        sequence=?
        where batchid=? and taskid=?"""
        pars = (
            tsk.url,
            tsk.host,
            tsk.cookie,
            tsk.account,
            tsk.password,
            tsk.phone,
            int(datetime.now(pytz.timezone("Asia/Shanghai")).timestamp()),
            tsk.successtimes,
            tsk.failtimes,
            tsk._sequence,
            tsk.batchid,
            tsk.taskid,
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
                f"Update task error:\nbatchid:{tsk.batchid}\nerror:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.close()
        return

    @table_locker(__tb_task._tbname)
    def update_task_by_sql(self, sql, pars):
        """
        提供一个对外根据sql更新task的接口，就不管拿来干啥了
        :param sql:
        :param pars:
        :return:
        """
        conn: SqliteConn = None
        res = False
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
                f"Update task by sql error, err:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.close()
        return
