"""
加载14亿数据并存入数据库
by judy 2020/06/17
email和pwd设置为长字符串
"""
import queue
import threading
import time
import traceback
from pathlib import Path

import pymysql


class MailSecret(object):

    def __init__(self):
        self.datafile_queue = queue.Queue()
        self.res_queue = queue.Queue()
        self.data_path = Path(r"./data")
        self.get_data_file(self.data_path)
        self.allcount = 0
        # 长连接数据库
        self.db = pymysql.connect(host="192.168.90.66", user="root", password="123456", database="14yidata")
        # 插入标志位，要继续入
        self._insert_flag = True

    def get_data_file(self, datapath: Path):
        """
        获取所有的数据文件
        :return:
        """
        for el in datapath.iterdir():
            if el.is_dir():
                self.get_data_file(el)
            else:
                self.datafile_queue.put(el)

    def process_datafile(self):
        """
        处理文件
        email:pwd
        :return:
        """
        while True:

            if self.datafile_queue.empty():
                break

            try:
                datafile: Path = self.datafile_queue.get()
                print(f'Process file, file:{datafile.as_posix()}')
                with datafile.open('r', encoding='utf-8', errors="ignore") as fp:
                    for line in fp.readlines():
                        line = line.strip()
                        # errors = self.detect_decoding_errors_line(line)
                        # if errors:
                        #     print(f'Error encoding, line:{line}')
                        #     continue
                        try:
                            if ':' in line:
                                splite_res = line.split(':')
                            elif ';' in line:
                                splite_res = line.split(';')
                            elif len(line.split('\t')) == 3:
                                splite_res = line.split('\t')[1:]
                            else:
                                print(f'Unknown lines spilit: {line}')
                                continue
                            email, pwd = splite_res[0], splite_res[1]
                            # if not self._insert_flag:
                            #     if email == 'lollyman@gmail.com' and pwd == 'cocowow2':
                            #         self._insert_flag = True
                            #         print("Find the last record")
                            #         continue
                            while self.res_queue.qsize() > 100000:
                                print('Too many data, please wait 5 second')
                                time.sleep(5)
                            if self._insert_flag:
                                self.res_queue.put((email, pwd))
                        except:
                            print(f'error line:{line}')
                            continue
                self.datafile_queue.task_done()
            except Exception as err:
                print(f'read file error, err:{traceback.format_exc()}')

    def store_data(self, manydata: list):
        """
        保存数据到mysql
        :return:
        """
        db_curs = self.db.cursor()
        try:
            sql = '''
            INSERT INTO allb(Email, Password) VALUES (%s, %s);
            '''
            db_curs.executemany(sql, manydata)
            self.db.commit()
            print(f'Insert 10000 data ok')
        except Exception as error:
            self.db.rollback()
            print(f"insert error, err:{error}")
        finally:
            db_curs.close()

    def store_data_to_sqlite(self):
        """
        保存数据在mysql
        :return:
        """
        save_res = []
        count = 0
        stop = 10
        while True:

            if stop == 0:
                break

            if self.datafile_queue.empty() and self.res_queue.empty():
                stop -= 1
                print(f'No more data ,will exit in {stop} seconds')
                time.sleep(1)
                continue

            if count > 10000:
                self.allcount += count
                self.store_data(save_res)
                save_res = []
                count = 0
            data = self.res_queue.get()
            save_res.append(data)
            count += 1
            self.res_queue.task_done()
        # 结束后
        if count > 0:
            self.allcount += count
            self.store_data(save_res)
        print(f'All data stored, almost {self.allcount} lines')
        self.db.close()

    def start(self):
        for i in range(5):
            t1 = threading.Thread(target=self.process_datafile, name='getalldata')
            t1.start()
        t2 = threading.Thread(target=self.store_data_to_sqlite, name='store_data')
        t2.start()


if __name__ == '__main__':
    ms = MailSecret()
    ms.start()
