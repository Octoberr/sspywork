"""
调用有道翻译来翻译一些词汇
create by swm 2019/07/02
"""
import hashlib
import json
import sqlite3
import time

import requests
import queue
import threading


class Translation(object):

    def __init__(self):
        self.queue = queue.Queue()
        self._tblocker = threading.Lock()

    @staticmethod
    def _get_sql_con():
        """
        会给一个sql的连接
        :return:
        """
        dbpath = './db-ip.db'
        con = sqlite3.connect(dbpath)
        return con

    def add_a_col(self, table, name):
        """
        增加一列
        :param table:
        :param name:
        :return:
        """
        sql = f'''
        ALTER  TABLE  {table}   ADD COLUMN  {name} TEXT
        '''
        con = self._get_sql_con()
        cur = con.cursor()
        cur.execute(sql)
        con.commit()
        con.close()
        return

    # 有道翻译
    # def trans(self, strword):
    #     """
    #     有道api翻译关键字
    #     :param strword:
    #     :return:
    #     """
    #     transurl = 'http://openapi.youdao.com/api'
    #     q = strword
    #     froml = 'EN'
    #     tol = 'zh-CHS'
    #     # tol = 'EN'
    #     appKey = '4f894c1343f1f594'
    #     salt = '7'
    #     key = 'VF3AJLNUY28LGdMyEclG2HDqBo991htK'
    #     str = (appKey + q + salt + key).encode(encoding='UTF-8')
    #     md5 = hashlib.md5(str)
    #     sign = md5.hexdigest()
    #     allurlinfo = transurl + '?' + 'q=' + q + '&from=' + froml + '&to=' + tol + '&appKey=' + appKey + '&salt=' + salt + '&sign=' + sign
    #     data = requests.get(allurlinfo)
    #     jsondata = json.loads(data.text)
    #
    #     trans_res = jsondata.get('translation')
    #     if trans_res is None:
    #         trans_res = [strword]
    #     return trans_res[0]

    def trans(self, strword):
        """
        有道api翻译关键字
        :param strword:
        :return:
        """
        transurl = 'http://openapi.youdao.com/api'
        q = strword
        froml = 'auto'
        tol = 'zh-CHS'
        # tol = 'EN'
        appKey = '6556fd81b17b01ed'
        salt = '7'
        key = 'Kx1muY1CSWjKrmiXAWpa4DVzHdAchrbS'
        str = (appKey + q + salt + key).encode(encoding='UTF-8')
        md5 = hashlib.md5(str)
        sign = md5.hexdigest()
        allurlinfo = transurl + '?' + 'q=' + q + '&from=' + froml + '&to=' + tol + '&appKey=' + appKey + '&salt=' + salt + '&sign=' + sign
        data = requests.get(allurlinfo)
        jsondata = json.loads(data.text)

        trans_res = jsondata.get('translation')
        if trans_res is None:
            trans_res = [strword]
        return trans_res[0]

    # def trans(self, strword):
    #     """
    #     有道api翻译关键字
    #     :param strword:
    #     :return:
    #     """
    #     transurl = 'http://openapi.youdao.com/api'
    #     q = strword
    #     froml = 'auto'
    #     tol = 'zh-CHS'
    #     # tol = 'EN'
    #     appKey = '1eb564dcb2c232bb'
    #     salt = '7'
    #     key = 'SEzzlzKeA42oPDbeprM2ppSL2nniGKbK'
    #     str = (appKey + q + salt + key).encode(encoding='UTF-8')
    #     md5 = hashlib.md5(str)
    #     sign = md5.hexdigest()
    #     allurlinfo = transurl + '?' + 'q=' + q + '&from=' + froml + '&to=' + tol + '&appKey=' + appKey + '&salt=' + salt + '&sign=' + sign
    #     data = requests.get(allurlinfo)
    #     jsondata = json.loads(data.text)
    #
    #     trans_res = jsondata.get('translation')
    #     if trans_res is None:
    #         trans_res = [strword]
    #     return trans_res[0]

    @staticmethod
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_table_info(self, tablename):
        """
        查询某个table里面的信息
        :param tablename:
        :return:
        """
        sql = f'''
        SELECT * FROM {tablename} WHERE CN IS NULL 
        '''
        con = self._get_sql_con()
        con.row_factory = self.dict_factory
        cur = con.cursor()
        cur.execute(sql)
        res = cur.fetchall()
        con.close()
        return res

    def update_info(self, tablename, value, convalue):
        """
        更新表的信息
        :param tablename:
        :param upinfo:
        :return:
        """
        sql = f'''
        UPDATE {tablename} SET CN=? WHERE ID=?
        '''
        value = (value, convalue)
        con = self._get_sql_con()
        con.execute(sql, value)
        con.commit()
        con.close()
        return

    def put_queue(self):
        # table = ['CITY', 'PROVINCE']
        # for el in table:
        #     self.add_a_col(el, 'CN')
        tableinfo = self.get_table_info('PROVINCE')
        for tl in tableinfo:
            self.queue.put(tl)

    def execute(self):
        emptytimes = 0
        while True:
            if emptytimes > 10:
                break

            if self.queue.empty():
                print("the queue is empty")
                time.sleep(3)
                emptytimes += 1
                continue
            try:
                tl = self.queue.get()
                key = 'EN'
                value = self.trans(tl.get(key))
                conkey = 'ID'
                convale = tl.get(conkey)
                with self._tblocker:
                    self.update_info('PROVINCE', value, convale)
                    print(f'ADD {tl.get(key)}--------{value}')
            except Exception as exc:
                print(exc)

            finally:
                self.queue.task_done()

    def start(self):
        self.add_a_col('PROVINCE', 'CN')
        thread1 = threading.Thread(target=self.put_queue, name='searchtable')
        thread1.start()
        for i in range(1):
            thread = threading.Thread(target=self.execute, name='execute')
            thread.start()


if __name__ == '__main__':
    ts = Translation()
    ts.start()
