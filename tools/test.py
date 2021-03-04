"""test"""

# -*- coding:utf-8 -*-

import logging
import os
import threading
import time
import traceback
from inspect import getattr_static, trace

from pympler import asizeof, tracker

# https://pympler.readthedocs.io/en/latest/
# https://pympler.readthedocs.io/en/latest/asizeof.html#refs

# 第一步，创建一个logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Log等级总开关
# 第二步，创建一个handler，用于写入日志文件
rq = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
log_dir = os.path.dirname(__file__) + '/_Log'
if not os.path.isdir(log_dir):
    os.makedirs(log_dir)
log_name = log_dir + rq + '.log'
logfile = log_name
fh = logging.FileHandler(logfile, mode='w')
fh.setLevel(logging.DEBUG)  # 输出到file的log等级的开关
# 第三步，定义handler的输出格式
formatter = logging.Formatter(
    "[%(asctime)s] [line:%(lineno)d] [%(levelname)s]: %(message)s")
fh.setFormatter(formatter)
# 第四步，将logger添加到handler里面
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
logger.addHandler(fh)
logger.addHandler(console_handler)

lst = []
dct = {}


class Printed:
    def __init__(self) -> None:
        self.printed = False


prtd = Printed()


def test():
    print("Start")
    for i in range(100000000):
        s = f"this is {i}"
        lst.append(s)
        dct[i] = s
        while not prtd.printed:
            time.sleep(0.01)
        # time.sleep(0.000001)
    print("OK")
    while True:
        time.sleep(1)


def pymp():
    tr = tracker.SummaryTracker()
    while True:
        try:
            # print(asizeof.asizesof(lst, dct))
            # print(asizeof.asized(lst, dct, detail=1))
            # tr.print_diff()
            prtd.printed = False
            sz_lst: asizeof.Asized = asizeof.asized(lst, detail=0)
            sz_dct: asizeof.Asized = asizeof.asized(dct, detail=0)
            print(f'''
lst-> size: {round(sz_lst.size/1048576,2)} MB   flat: {round(sz_lst.flat/1048576,2)} MB
dct-> size: {round(sz_dct.size/1048576,2)} MB   flat: {round(sz_dct.flat/1048576,2)} MB
            ''')
            prtd.printed = True
        except Exception as ex:
            logger.error(traceback.format_exc())
        finally:
            time.sleep(2)


if __name__ == "__main__":
    try:
        t1 = threading.Thread(target=pymp)
        t1.start()

        t2 = threading.Thread(target=test)
        t2.start()

        while True:
            time.sleep(1)
    except Exception as ex:
        traceback.print_exc()
