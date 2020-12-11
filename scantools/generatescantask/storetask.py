"""
目前来看就只是保存每次生成任务的模板
然后查询展示模板
删除功能可以后面加上
create by judy 20201211
"""
from os import lseek
from pathlib import Path
import sqlite3
from datetime import datetime
from .config import file_folder
import traceback


class StoreTask(object):

    def __init__(self):
        # super().__init__()
        self.db_path = self._init_db()

    def _init_db(self) -> Path:
        """
        每次实例化之前检查下数据库是否存在
        """
        dbpath = file_folder/'generatetask.db'
        conn = sqlite3.connect(dbpath.as_posix())
        c = conn.cursor()
        sql = '''CREATE TABLE IF NOT EXISTS GTask
        (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        clientid         TEXT    NOT NULL,
        tinfo            TEXT    NOT NULL,
        createtime       CHAR    NOT NULL);'''
        c.execute(sql)
        conn.commit()
        conn.close()
        return dbpath

    def _dict_factory(self, cursor, row) -> dict:
        """
        格式化查询结果为字典
        :param cursor:
        :param row:
        :return:
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def _get_cursor(self) -> sqlite3.Cursor:
        """
        获取当前数据的cursor
        """
        conn = sqlite3.connect(self.db_path.as_posix())
        c = conn.cursor()
        c.row_factory = self._dict_factory
        return c

    def insert_tinfo(self, tinfo, clientid):
        """
        保存每次生成任务的模板，以及下发到了哪个client
        """
        time_now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        INSERT INTO GTask(clientid, tinfo, createtime)
        VALUES (?, ?, ?)
        """
        pars = (clientid, tinfo, time_now_str)
        conn = self._get_cursor()
        try:
            conn.execute(sql, pars)
            print(f"Save {clientid} info success")
        except:
            print(f"Insert data to GTask error\nerr:{traceback.format_exc()}")
            conn.rollback()
        finally:
            conn.commit()
            conn.close()

    def show_me_info(self) -> list:
        """
        每次查询的时候展示所有已经保存的模板
        """
        sql = """
        SELECT clientid, tinfo, createtime from GTask
        """
        conn = self._get_cursor()
        res = None
        try:
            conn.execute(sql)
            res = conn.fetchall()
        except:
            print(f"Select data error\nerror:{traceback.format_exc()}")
            conn.rollback()
        finally:
            # conn.commit()
            conn.close()
        return res
