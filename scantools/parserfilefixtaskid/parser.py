"""
解析文件，并可以修改文件的taskid
就直接修改吧
create by judy 20201210
"""
import json
import time
import shutil
import threading
import traceback
from pathlib import Path
from shutil import copyfile
from queue import Queue

from .config import input_folder, output_folder, tmp_folder


class Parser(object):
    __scan_file_locker = threading.Lock()
    __file_process_locker = threading.Lock()

    def __init__(self) -> None:
        # super().__init__()
        self.input_folder = Path(input_folder)
        self.input_folder.mkdir(exist_ok=True)
        self.output_folder = Path(output_folder)
        self.output_folder.mkdir(exist_ok=True)
        self.tmp_folder = Path(tmp_folder)
        self.tmp_folder.mkdir(exist_ok=True)
        self.iscan_suffix = '.iscan_search'
        self.iscan_task_queue = Queue()
        # 恢复一下程序
        self.resume_program()

    def scanfile(self):
        """
        扫描输入文件夹的文件，将文件移动到tmp文件夹
        并加入到待处理队列
        """
        while True:
            try:
                for ifile in self.input_folder.iterdir():
                    name = ifile.name
                    # 全部移动到tmp目录下去
                    tmpname = self.tmp_folder / name
                    # file.replace(tmpname)
                    with self.__scan_file_locker:
                        # 这个文件得尽快移动到tmp文件夹，加锁是为了避免在移动的时候被扫到然后又在移动过程中又移动
                        shutil.move(ifile.as_posix(), tmpname.as_posix())
                        # 这里先把直接把文件放队列，等到全部处理完成了再删除
                        self.iscan_task_queue.put(tmpname)
                    print(f"Dealing iscan_search data, filename:{name}")

            except:
                print(f'Scan task file error, err:{traceback.format_exc()}')
                continue
            finally:
                time.sleep(0.5)

    def resume_program(self):
        """
        程序因为外部或者内部等各种原因停止了
        那么就需要在重新启动的时候将未完成的工作完成
        """
        # 直接判断tmp文件夹是否存在
        if not self.tmp_folder.exists():
            return
        try:
            for rfile in self.tmp_folder.iterdir():
                self.iscan_task_queue.put(rfile)
                print(f"Resuming iscan search data, filename:{rfile.name}")
        except:
            print(f"Resume file error\nerr:{traceback.format_exc()}")
        finally:
            pass

    def _process_file(self, tmpfile: Path, taskid):
        """
        具体实现处理文件的方法
        1、读取文件
        2、解析文件
        3、输出到目标文件夹
        """
        j_text = tmpfile.read_text(encoding='utf-8')
        d_text = json.loads(j_text)
        d_text['taskid'] = taskid
        res_text = json.dumps(d_text)
        outname = self.output_folder/tmpfile.name
        outname.write_text(res_text, encoding='utf-8')
        return

    def processfile(self, taskid):
        """
        开始处理文件，处理完成后再将文件输出
        """
        got = False
        while True:
            got = False
            if self.iscan_task_queue.empty():
                time.sleep(0.5)
                continue
            tfile: Path = self.iscan_task_queue.get()
            got = True
            try:
                if tfile.suffix == self.iscan_suffix:
                    # 只去处理iscan_search的文件，过滤一些奇奇怪怪的文件
                    self._process_file(tfile, taskid)
            except:
                print(f"Parse file error\nerr:{traceback.format_exc()}")
            finally:
                if got:
                    # 完成任务
                    self.iscan_task_queue.task_done()
                # 删除tmp文件夹的源文件
                if tfile.exists():
                    tfile.unlink()
