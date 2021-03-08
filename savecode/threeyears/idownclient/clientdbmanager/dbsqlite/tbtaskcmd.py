"""
cmd表，存储通用的配置，邮箱的配置默认配置
by judy 2019/05/06
"""
import json
import traceback

from commonbaby.sql import SqliteColumn, SqliteConn, SqliteTable, table_locker

from datacontract.idowncmd import cmd_dict, IdownCmd
from .sqliteconfig import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbTaskCmd(TbSqliteBase):
    __tb_task_cmd: SqliteTable = SqliteTable(
        "idowncmd",
        True,
        SqliteColumn(
            colname="ID",
            coltype="INTEGER",
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True,
        ).set_index_new(),
        SqliteColumn(colname="cmdid"),
        SqliteColumn(colname="platform", defaultval="zplus"),
        SqliteColumn(colname="default_value", coltype="INT", length=5),
        SqliteColumn(colname="cmd", nullable=False),
    )
    databasename = "task"

    def __init__(self, dbcfg: SqliteConfig):
        TbSqliteBase.__init__(
            self, TbTaskCmd.__tb_task_cmd._tbname, dbcfg, TbTaskCmd.databasename
        )
        # 初始化自定义下载策略的默认值
        self.cmd_str = json.dumps(cmd_dict)
        self._initial_default_confg()

    def _append_tables(self):
        self._conn_mngr.append_table(TbTaskCmd.__tb_task_cmd)

    @table_locker(__tb_task_cmd._tbname)
    def _initial_default_confg(self):
        """
        初始化cmd，目前来看三个地方都使用了cmd
        但是只有idown目前有修改全局的功能，所以为了不互相影响需要放3份
        """
        # 只需要查询一个是否有
        if self.get_default_idown_cmd() is not None:
            return
        conn: SqliteConn = None

        sql = """
        INSERT INTO idowncmd(cmdid, default_value, cmd)
        VALUES (?, ?, ?);       
        """
        params = [
            ("iscan", 1, self.cmd_str),
            ("iscout", 1, self.cmd_str),
            ("idown", 1, self.cmd_str),
        ]
        # params = ('iscan', 1, self.cmd_str)
        try:
            conn = self.connect_write(5)
            c = conn.cursor
            c.executemany(sql, params)
            # c.execute(sql, params)
        except Exception:
            self._logger.error(
                f"There was a problem inserting default cmd data, err:{traceback.format_exc()}"
            )
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return

    @table_locker(__tb_task_cmd._tbname)
    def get_default_cmd(self, cmdid, default_value=1):
        """
        获取已存储的默认配置
        :return:
        """
        res = None
        conn: SqliteConn = None
        sql = """
        SELECT * FROM idowncmd 
        WHERE cmdid=? and default_value=?;
        """
        params = (cmdid, default_value)
        try:
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    conn._conn.row_factory = self._dict_factory
                    c = conn._conn.cursor()
                    c.execute(sql, params)
                    res_data = c.fetchall()
                    if len(res_data) > 0:
                        res = res_data[0]
                        break
                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                finally:
                    if conn is not None:
                        conn.close()
        except Exception:
            self._logger.error(
                f"Query default idown cmd error,err:{traceback.format_exc()}."
            )
        finally:
            if conn is not None:
                conn.close()
            return res

    def get_default_idown_cmd(self):
        """
        只获取idown的默认cmd
        modify by judy 2020/08/12
        """
        res = self.get_default_cmd("idown")
        return res

    def get_default_iscan_cmd(self):
        """
        只获取iscan的默认cmd
        modify by judy 2020/08/12
        """
        res = self.get_default_cmd("iscan")
        return res

    def get_default_iscout_cmd(self):
        """
        只获取iscout的默认cmd
        modify by judy 2020/08/12
        """
        res = self.get_default_cmd("iscout")
        return res

    @table_locker(__tb_task_cmd._tbname)
    def update_cmd_by_cmdid(self, cmdid, cmdr: str):
        """
        根据cmdid更新cmd
        :param cmdid:
        :param cmdr:
        :return:
        """
        res = False
        sql = """
        UPDATE idowncmd SET cmd=? WHERE cmdid=?
        """
        pars = (cmdr, cmdid)
        conn: SqliteConn = None
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
                f"Update default cmd error,err:{traceback.format_exc()}."
            )
        finally:
            if conn is not None:
                conn.close()
        return

    def _update_the_same_cmdid(self, cmdid, cmd_str: str):
        """
        更新数据库中相同的cmd
        :param cmdid:
        :param cmd_str:
        :return:
        """
        res = False
        repeat_data = self.query_cmd_by_cmdid(cmdid)
        if repeat_data is not None:
            # 表示数据库中已经存储了这个设置，那么就更新数据即可
            # fill_dict = self._filling_default_cmd(json.loads(cmd_str), json.loads(repeat_data.get('cmd')))
            self.update_cmd_by_cmdid(cmdid, cmd_str)
            res = True
        return res

    @table_locker(__tb_task_cmd._tbname)
    def store_task_cmd(self, cmdid, cmd_str):
        """
        补齐默认配置，存储cmd数据
        :param cmdid:
        :param cmd_str:
        :return:
        """
        # 更新相同的cmdid的信息
        repeat = self._update_the_same_cmdid(cmdid, cmd_str)
        if repeat:
            # 如果更新了即可
            return

        sql = """
        INSERT INTO idowncmd(cmdid, cmd)
        VALUES (?, ?)
        """
        # cmd_dict = json.loads(cmd_str)

        # 补齐默认配置
        # fill_dict = self._filling_default_cmd(cmd_dict)
        pars = (cmdid, cmd_str)
        conn: SqliteConn = None
        try:
            conn = self.connect_write(5)
            c = conn.cursor
            c.execute(sql, pars)
        except Exception:
            self._logger.error(
                f"There was a problem inserting data, err:{traceback.format_exc()}."
            )
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return

    @table_locker(__tb_task_cmd._tbname)
    def query_cmd_by_cmdid(self, cmdid):
        """
        根据cmdid查询默认的配置
        有结果返回{}
        没有结果返回None
        :return:
        """
        conn: SqliteConn = None
        sql = """
        SELECT * FROM idowncmd
        WHERE cmdid=?;
        """
        pars = (cmdid,)
        try:
            for conn in self.connect_all(5):
                try:
                    conn._conn.row_factory = self._dict_factory
                    c = conn._conn.cursor()
                    c.execute(sql, pars)
                    res: list = c.fetchall()
                    if len(res) > 0:
                        return res[0]
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
                f"There was a problem query cmd by cmdid\nerr:{traceback.format_exc()}."
            )
        finally:
            if conn is not None:
                conn.close()
        return

    def _filling_default_idown_cmd(self, icmd: IdownCmd) -> str:
        """
        在存储默认配置的时候可能需要补齐一些默认配置
        补齐默认的配置后再存储
        :param icmd:
        :return:
        """
        default_cmd: str = self.get_default_idown_cmd().get("cmd")
        dcmd = IdownCmd(default_cmd)
        # 如果任务自己带有一些设置，那么补齐一些配置即可,只要调用了fill那么cmd就会是完整的
        icmd.fill_defcmd(dcmd)
        return icmd.filled_cmd_str

    @table_locker(__tb_task_cmd._tbname)
    def update_default_idown_cmd(self, icmd: IdownCmd):
        """
        修改默认的cmd,会自动找寻数据库中最新的cmd补齐
        :param icmd:
        :return:
        """
        res = False
        sql = """
        UPDATE idowncmd SET cmd=? WHERE cmdid=? and default_value=?
        """
        # cmd_dict = json.loads(new_cmdr)
        # 补齐默认配置
        new_cmdr = self._filling_default_idown_cmd(icmd)
        pars = (new_cmdr, "idown", 1)
        conn: SqliteConn = None
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
                f"Update default cmd error,err:{traceback.format_exc()}."
            )
        finally:
            if conn is not None:
                conn.close()
        return
