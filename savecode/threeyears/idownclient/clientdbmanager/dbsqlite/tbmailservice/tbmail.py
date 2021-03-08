"""
pop3和imap邮件服务的地址和端口
create by judy 2019/05/20
"""
import traceback
from pathlib import Path
from xml.etree import ElementTree as ET

from commonbaby.sql import (SqliteColumn, SqliteConn,
                            SqliteTable,
                            table_locker)

from ..sqliteconfig import SqliteConfig
from ..tbsqlitebase import TbSqliteBase


class TbMail(TbSqliteBase):
    __tb_mail_service: SqliteTable = SqliteTable(
        'mailservice',
        True,
        SqliteColumn(
            colname='ID',
            coltype='INTEGER',
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True).set_index_new(),
        SqliteColumn(colname='service_name', nullable=False),
        SqliteColumn(colname='imap_host'),
        SqliteColumn(colname='imap_port'),
        SqliteColumn(colname='pop3_host'),
        SqliteColumn(colname='pop3_port'),
    )
    databasename = 'task'

    def __init__(self, dbcfg: SqliteConfig):
        TbSqliteBase.__init__(self, TbMail.__tb_mail_service._tbname, dbcfg, TbMail.databasename)
        self._xml_path = Path(__file__).parent / 'host.xml'
        self._init_default_service()

    def _append_tables(self):
        self._conn_mngr.append_table(TbMail.__tb_mail_service)

    def _init_default_service(self):
        """
        初始化数据，读取本地的xml文件，然后存入数据库
        :return:
        """
        if len(self._get_default_mail_service()) != 0:
            return
        tree = ET.parse(str(self._xml_path))
        root = tree.getroot()
        childs = iter(root)
        for child in childs:
            tag = child.attrib.get('name')
            server = iter(child)
            imap = next(server)
            pop3 = next(server)
            imap_host = imap.attrib.get('host')
            imap_port = imap.attrib.get('port')
            pop3_host = pop3.attrib.get('host')
            pop3_port = pop3.attrib.get('port')
            self.insert_a_piece_of_data(tag, imap_host, imap_port, pop3_host, pop3_port)
        return

    @table_locker(__tb_mail_service._tbname)
    def _get_default_mail_service(self):
        conn: SqliteConn = None
        res = []
        sql = '''
        SELECT * FROM mailservice
        '''
        try:
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    conn._conn.row_factory = self._dict_factory
                    c = conn._conn.cursor()
                    c.execute(sql)
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
            self._logger.error(f"Query task according to the task status data problem,err:{traceback.format_exc()}.")
        finally:
            if conn is not None:
                conn.close()
        return res

    @table_locker(__tb_mail_service._tbname)
    def insert_a_piece_of_data(self, service_name, imap_host, imap_port, pop3_host, pop3_port):
        """
        向数据库插入一条完整的数据
        :param service_name:
        :param imap_host:
        :param imap_port:
        :param pop3_host:
        :param pop3_port:
        :return:
        """
        conn: SqliteConn = None
        sql = '''
        INSERT INTO mailservice(service_name, imap_host, imap_port, pop3_host, pop3_port)
        VALUES (?, ?, ?, ?, ?);       
        '''
        params = (service_name, imap_host, imap_port, pop3_host, pop3_port)
        try:
            conn = self.connect_write(5)
            c = conn.cursor
            c.execute(sql, params)
        except Exception:
            self._logger.error(f"There was a problem inserting data, err:{traceback.format_exc()}.")
        finally:
            if conn is not None:
                conn.commit()
                conn.close()
        return

    @table_locker(__tb_mail_service._tbname)
    def update_service_by_sql(self, sql, pars):
        """
        通过sql更新数据
        :param sql:
        :param pars:
        :return:
        """
        res = False
        conn: SqliteConn = None
        try:
            for conn in self.connect_all(5):
                try:
                    c = conn.cursor
                    result = c.execute(sql, pars)
                    if result is not None and result.rowcount > 0:  # or len(result) < 1:
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
            self._logger.error(f"Update default cmd error,err:{traceback.format_exc()}.")
        finally:
            if conn is not None:
                conn.close()
        return

    @table_locker(__tb_mail_service._tbname)
    def delete_one_mail_service(self, mail):
        """
        删除某个mail
        :param mail:
        :return:
        """
        sql = f'''DELETE FROM mailservice WHERE service_name=?'''
        pars = (mail,)
        res = False
        conn: SqliteConn = None
        try:
            for conn in self.connect_all(5):
                try:
                    c = conn.cursor
                    result = c.execute(sql, pars)
                    if result is not None and result.rowcount > 0:  # or len(result) < 1:
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
            self._logger.error(f"Update default cmd error,err:{traceback.format_exc()}.")
        finally:
            if conn is not None:
                conn.close()
        return
