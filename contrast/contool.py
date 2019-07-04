"""
两个csv文件的比较
功能很简单
难点：有可能数据量会很大，十万条百万条的那种
所以不能一下就加载到内存中
"""
import threading
import time
import traceback
from pathlib import Path
import queue
import csv


class Contool(object):

    def __init__(self):
        filepath = Path(__file__).parent
        # 输入文件夹
        self.inputfile: Path = filepath / '_input'
        self.inputfile.mkdir(exist_ok=True)
        # 存储文件夹
        self.outputfile: Path = filepath / '_output'
        self.outputfile.mkdir(exist_ok=True)
        # 保存源文件
        self.originfile: Path = filepath / '_origin'
        self.originfile.mkdir(exist_ok=True)
        # tmpdir
        self.tmpfile: Path = filepath / '_tmp'
        self.tmpfile.mkdir(exist_ok=True)

        # 下面初始化一些字段
        self._file_queue = queue.Queue()
        self.max_limit = 3

    def scan_dir(self):
        """
        扫描文件夹每次取两个
        :return:
        """
        while True:
            input_dir = []
            for x in self.inputfile.iterdir():
                if x.is_file():
                    tmpath = self.tmpfile / x.name
                    x.replace(tmpath)
                    print(f'Input file {x.name}')
                    input_dir.append(tmpath)
            if len(input_dir) < 2:
                time.sleep(3)
                continue

            self._file_queue.put((input_dir[0], input_dir[1]))

    def get_intersection(self, f1_data: list, f2):
        f2_data = []
        f2_count = 0
        fp2 = f2.open('r', newline='')
        while True:
            line = fp2.readline()
            if line == '':
                res = [x for x in f1_data if x in f2_data]
                yield res
                break
            f2_data.append(line.strip())
            f2_count += 1
            if f2_count == self.max_limit:
                res = [x for x in f1_data if x in f2_data]
                yield res
                f2_data.clear()
                f2_count = 0
        fp2.close()

    def outputdata(self, res: list, name1: str, name2: str):
        """
        输出一些数据
        :param name1:
        :param name2:
        :return:
        """
        if len(res) > 0:
            print("Find intersection, store in the output path.")
            outname = f'{name1.split(".")[0] + name2.split(".")[0]}.csv'
            outpath: Path = self.outputfile / outname
            fp = outpath.open('a+', newline='', encoding='utf-8')
            fp.writelines(res)
            # writer = csv.writer(fp)
            # writer.writerows(res)
            fp.close()
        return

    def contrast(self, f1: Path, f2: Path):
        """
        现在是拿到文件了
        进行比较
        :return:
        """
        name1 = f1.name
        name2 = f2.name
        f1_data = []
        f1_count = 0
        fp1 = f1.open('r', newline='')
        while True:
            line = fp1.readline()
            # 说明最后一行已经拿到了
            if line == '':
                # 可以进行最后一次的比较
                for res in self.get_intersection(f1_data, f2):
                    self.outputdata(res, name1, name2)
                break
            f1_data.append(line.strip())
            f1_count += 1
            if f1_count == self.max_limit:
                # 进行处理
                for res in self.get_intersection(f1_data, f2):
                    self.outputdata(res, name1, name2)
                f1_data.clear()
                f1_count = 0
        fp1.close()

    def process(self):
        """
        处理文件
        :return:
        """
        while True:

            if self._file_queue.empty():
                time.sleep(5)
            f1n, f2n = self._file_queue.get()
            try:
                print(f'Start to compare')
                self.contrast(f1n, f2n)
                print(f'Complete compare.')
            except:
                print(traceback.format_exc())
            finally:
                # 将文件移动到原始文件夹
                origin1: Path = self.originfile / f1n.name
                f1n.replace(origin1)
                origin2: Path = self.originfile / f2n.name
                f2n.replace(origin2)
                self._file_queue.task_done()

    def start(self):
        thread1 = threading.Thread(target=self.scan_dir, name='scan')
        thread1.start()
        thread2 = threading.Thread(target=self.process, name='process')
        thread2.start()


if __name__ == '__main__':
    # con = Contool()
    # con.scan_dir()
    # con.start()
    file = r"D:\gitcode\shensiwork\contrast\_origin\t1.csv"
    fp = open(file, 'r', encoding='utf-8')
    fp.seek(4)
    while True:
        a = fp.readline()
        print(a.strip())
        if a == '':
            break
