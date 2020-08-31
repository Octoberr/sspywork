"""
修改taskid
"""
import json
import os
import threading
import time
from pathlib import Path
from queue import Queue
from uuid import uuid1
import uuid
from outputjtf import Outputjtf
import traceback


class CTI(object):
    def __init__(self):
        self.inputpath = Path("./hkscandata")
        self.tmppath = Path("./_servertmp")
        self.tmppath.mkdir(exist_ok=True)
        self.outputpath = Path("./niboerdata")
        self.outputpath.mkdir(exist_ok=True)
        self.dataqueue = Queue()
        self.taskid = "9616bb92-d4a9-11ea-acbc-309c236f07ad"
        self.suffix = "iscan_search"

        self._succdir = Path("./succ")
        self._succdir.mkdir(exist_ok=True)
        self._errdir = Path("./err")
        self._errdir.mkdir(exist_ok=True)

    def listfile(self):

        succ: bool = False
        while True:
            res = None
            succ = False
            for file in self.inputpath.iterdir():
                if file.suffix != "." + self.suffix:
                    continue
                try:
                    res = file.read_text(encoding="utf-8")
                    res_dict = json.loads(res)
                    self.dataqueue.put(res_dict)

                    successname = self._succdir / f"{file.name}"
                    while successname.exists():
                        successname = self._succdir / f"{uuid.uuid1()}.{self.suffix}"

                    file.replace(successname)
                    succ = True
                except Exception as e:
                    errorname = self._errdir / f"{file.name}"
                    while errorname.exists():
                        errorname = self._errdir / f"{uuid.uuid1()}.{self.suffix}"

                    file.replace(errorname)
                    print(
                        f"Cant load res, sdata:{file.as_posix()} {traceback.format_exc()}"
                    )
                finally:
                    print("{}: {}".format(succ, file.as_posix()))

    def outpufile(self):
        got = False
        while True:
            if self.dataqueue.empty():
                time.sleep(1)

            try:
                got = False
                resdict = self.dataqueue.get()
                got = True
                resdict["taskid"] = self.taskid
                Outputjtf.output_json_to_file(
                    resdict, self.tmppath, self.outputpath, self.suffix
                )
            except Exception as err:
                print(f"Change taskid error, err:{err}")
            finally:
                if got:
                    self.dataqueue.task_done()

    def start(self):

        thread1 = threading.Thread(target=self.listfile, name="readfile")
        thread1.start()

        for i in range(1):
            t = threading.Thread(target=self.outpufile, name="outputfile")
            t.start()


if __name__ == "__main__":
    cti = CTI()
    cti.start()
