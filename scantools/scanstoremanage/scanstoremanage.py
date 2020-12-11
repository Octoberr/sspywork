"""
-支持永久记录各国家资产的taskid，并能够友好的展示和便于复制粘贴
create by judy 20201209
"""
import sqlite3
import traceback
from .config import file_folder


class ScanStoreManage(object):

    def __init__(self) -> None:
        # super().__init__()
        # 检查下是否有这个表，没有的话需要创建一个
        self.db_path = self.init_db()

    def init_db(self):
        """
        每次实例化之前检查下数据库是否存在
        """
        dbpath = file_folder/'scandb.db'
        conn = sqlite3.connect(dbpath.as_posix())
        c = conn.cursor()
        sql = '''CREATE TABLE IF NOT EXISTS SCANSTORE
        (ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
        country           TEXT    NOT NULL,
        taskid            TEXT     NOT NULL);'''
        c.execute(sql)
        conn.commit()
        conn.close()
        return dbpath

    def _dict_factory(self, cursor, row):
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

    def get_cursor(self):
        """
        获取当前数据的cursor
        """
        conn = sqlite3.connect(self.db_path.as_posix())
        c = conn.cursor()
        c.row_factory = self._dict_factory
        return c

    def count_data(self, country):
        """
        每次插入前需要查询数据是否存在
        如果存在那么就更新
        """
        res = None
        sql = """
        SELECT count(1) FROM SCANSTORE
        WHERE country=?
        """
        pars = (country,)
        cursor = None
        try:
            cursor = self.get_cursor()
            cursor.execute(sql, pars)
            res = cursor.fetchall()
        except:
            print(f"Count data error\nerr:{traceback.format_exc()}")
        finally:
            if cursor is not None:
                cursor.close()
        return res

    def insert_data(self, country, taskid):
        """
        保存新的数据
        每条数据都是唯一的，如果重复了就需要更新
        一般是一个国家对应一个taskid
        """
        # 1、先判断这个国家是否存在
        count_res = self.count_data(country)
        if count_res is None:
            print(f"Count {country} error, check the error")
        count_country = count_res[0]['count(1)']
        if count_country > 0:
            # 2、如果数据库中保存了数据那么就直接更新
            self.update_data(country, taskid)
        else:
            # 3、如果数据库中没有保存数据那么就直接插入
            sql = """INSERT INTO SCANSTORE(country, taskid)
            VALUES (?, ?)
            """
            pars = (country, taskid)
            conn = self.get_cursor()
            try:
                conn.execute(sql, pars)
            except:
                print(
                    f"Insert data error, country:{country} taskid:{taskid}\nerror:{traceback.format_exc()}")
                conn.rollback()
            finally:
                conn.close()
                conn.close()

    def update_data(self, country=None, taskid=None, flag='country'):
        """
        修改国家的taskid或者修改taskid的国家
        当flag为country时，修改country的taskid
        当flag为taskid时，修改taskid的country
        """
        sql = """
        UPDATE SCANSTORE SET 
        """
        if flag == 'country':
            sql += 'taskid=? WHERE country=?'
            pars = (taskid, country)
        else:
            sql += 'country=? WHERE taskid=?'
            pars = (country, taskid)
        conn = self.get_cursor()
        try:
            result = conn.execute(sql, pars)
            if (
                result is not None and result.rowcount > 0
            ):  # or len(result) < 1:
                res = True
        except:
            print(f"Update error, err:{traceback.format_exc()}")
            conn.rollback()
        finally:
            conn.commit()
            conn.close()
        return

    def select_data(self):
        """
        展示所有的数据
        """
        sql = """
        SELECT country, taskid FROM SCANSTORE 
        """
        conn = self.get_cursor()
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
