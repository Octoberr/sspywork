"""
多线程执行
获取任务和电脑信息
create by judy 2018/10/22
"""
import threading

from .clientbasicstatus import ClientBasicInfo
from .clienttaskstatus import ClientTaskStatus


class CollectClientInfo(object):

    def __init__(self):
        self.bi = ClientBasicInfo()
        self.ts = ClientTaskStatus()

    def start_collect_client(self):
        thread1 = threading.Thread(target=self.bi.start, name="collectbasic")
        # thread2 = threading.Thread(target=self.ts.start, name="collecttask")
        thread1.start()
        # thread2.start()
