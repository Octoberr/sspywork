"""
验证码表
create by judy
2019/02/20
"""
import traceback

from commonbaby.sql import (SqliteColumn, SqliteConn, SqliteTable, table_locker)

from datacontract.idowndataset import Task
from .sqliteconfig import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbInputData(TbSqliteBase):
    __tb_inputdata: SqliteTable = SqliteTable(
        'inputdata',
        True,
        SqliteColumn(
            colname='ID',
            coltype='INTEGER',
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True).set_index_new(),
        SqliteColumn(colname='taskid', coltype='CHAR', length=50, nullable=False).set_index_new(),
        SqliteColumn(colname='platform', coltype='CHAR', length=50, nullable=False),
        SqliteColumn(colname='parenttaskid', coltype='CHAR', length=50, nullable=False),
        SqliteColumn(colname='batchid', coltype='CHAR', length=50, nullable=False),
        SqliteColumn(colname='parentbatchid', coltype='CHAR', length=50, nullable=False),
        SqliteColumn(colname='input', coltype='CHAR', length=50, nullable=False),
    )
    databasename = 'idownverify'

    def __init__(self, dbcfg: SqliteConfig):
        TbSqliteBase.__init__(self, TbInputData.__tb_inputdata._tbname, dbcfg, TbInputData.databasename)

    def _append_tables(self):
        self._conn_mngr.append_table(TbInputData.__tb_inputdata)

    @table_locker(__tb_inputdata._tbname)
    def input_insert(self, tsk: Task):
        """
        将交互输入的验证码存入数据库的inputdata表，
        验证码在取得后就删除在数据库中的记录
        :param tsk:
        :return:
        """
        conn: SqliteConn = None
        sql = '''INSERT INTO inputdata(
        taskid,
        platform,
        parenttaskid,
        batchid,
        parentbatchid,
        input
        )VALUES (?,?,?,?,?,?);
        '''
        params = (tsk.taskid, tsk.platform, tsk.parenttaskid, tsk.batchid, tsk.parentbatchid, tsk.input)
        try:
            conn = self.connect_write()
            c = conn.cursor
            c.execute(sql, params)
        except Exception as err:
            self._logger.error("There was a problem inserting data, err:{}.".format(err))
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
            return

    @table_locker(__tb_inputdata._tbname)
    def query_input(self, task: Task):
        """
        查询数据库的inputdata表，寻找验证码
        根据传入的taskid = parentid,
        查询完成后即时删除这条数据
        :param taskid:
        :return:
        """
        conn: SqliteConn = None
        input = None
        sql = '''SELECT * FROM inputdata
        WHERE platform=? AND parenttaskid=? AND parentbatchid=?;
        '''
        delsql = '''DELETE FROM inputdata
        WHERE platform=? AND parenttaskid=? AND parentbatchid=?;
        '''
        par = (task.platform, task.taskid, task.batchid)
        try:
            for conn in self.connect_all(5):
                conn._conn.row_factory = self._dict_factory
                c = conn._conn.cursor()
                c.execute(sql, par)
                allget: dict = c.fetchall()
                # 以防万一一个任务多个验证码
                if len(allget) > 1:
                    c.execute(delsql, par)
                    conn.commit()
                    conn.close()
                    self._logger.error("There are multiple verification codes for the same sms task. "
                                       "All verification codes have been deleted. Please re-enter and send a valid verification code.")
                    break
                if len(allget) == 0:
                    conn.close()
                    continue
                else:
                    res = allget[0]
                    # 获取验证码
                    input = res.get('input')
                    if input is not None:
                        c.execute(delsql, par)
                    break
        except:
            self._logger.error(f"Query verification code error,err:{traceback.format_exc()}")
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return input
