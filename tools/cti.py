"""
修改taskid
"""
from pathlib import Path
import threading
from queue import Queue
import json
import time
from outputjtf import Outputjtf


class CTI(object):
    def __init__(self):
        self.inputpath = Path("./_serverinput")
        self.tmppath = Path("./_servertmp")
        self.outputpath = Path("./niboerdata")
        self.outputpath.mkdir(exist_ok=True)
        self.dataqueue = Queue()
        self.file_locker = threading.Locker()
        self.taskid = "9616bb92-d4a9-11ea-acbc-309c236f07ad"
        self.suffix = "iscan_search"

    def listfile(self):

        while True:
            for file in self.inputpath.iterdir():
                if file.suffix != self.suffix:
                    continue
                try:
                    res = file.read_text()
                    res_dict = json.loads(res)
                    self.dataqueue.put(res_dict)
                except:
                    print(f'Cant load res, sdata:{res}')

    def outpufile(self):

        while True:
            if self.dataqueue.empty():
                time.sleep(1)

            try:
                resdict = self.dataqueue.get()
                resdict['taskid'] = self.taskid
                Outputjtf.
                self.dataqueue.task_done
            except Exception as err:
                print(f'Change taskid error, err:{err}')
