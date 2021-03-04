"""
1、文件到这里
一份给ES 一份给自己
新增ES旧索引入库
在继承原有功能的基础上
重构备份程序，按照数据内的
国家-当前时间（年-月-日）
如果按照数据内的时间的话也会面临和按国家端口备份的问题
不用再分端口了
create by judy 20201217
"""
from pathlib import Path
import threading
import json
from queue import Queue
import traceback
import datetime
import time
from shutil import copyfile
import zipfile
import shutil


class ScanBackUP(object):

    def __init__(self) -> None:
        # super().__init__()
        # 所有数据先到这
        self._input = None
        # 所有数据先复制一份到这, 这个是程序不用管的文件夹
        self._esinput = None
        # 将要备份的数据放到这， 要处理的数据全部放在这里
        self._dbu_input = None
        self._databack = None
        self._zipdata: Path = None
        self._zip_size = None
        # 备份线程默认为一个，可以在配置里面更改重启
        self.backup_thread = 1
        self.zip_thread = 1
        # 增加一个是否拷贝到ES的功能
        self.copy_esinput_enable = True
        self._tmp = Path('./tmp')
        self._tmp.mkdir(exist_ok=True)
        # 文件是否需要拷贝一份到旧索引
        self._old_esinput = None
        self.config_path = Path(r'./config_path.json')
        try:
            self._init_cpinfo()
        except:
            raise Exception(
                f"初始化配置参数失败，请检查配置文件\nerror:{traceback.format_exc()}")
        # 需要用到的参数
        # 文件锁，同一时间只允许一个线程操作文件
        self.__file_locker = threading.Lock()
        self.__scan_file_locker = threading.Lock()
        self._zipfile_locker = threading.Lock()
        # 因为压缩可能处理的时间比较长，所以需要增加一个正在压缩的字典
        self._zip_dealing = {}
        # 根据后缀分配的需要处理的队列，目前只有iscan
        self.iscan_task_queue = Queue()
        self._zip_queue = Queue()
        self.iscan_suffix = '.iscan_search'
        # try:
        #     self._restore_existdata()
        # except:
        #     raise Exception(
        #         "There's something wrong with restoring the environment")

    def _init_cpinfo(self):
        """
        初始化配置文件中的路径和参数
        :return:
        """
        conf_str = self.config_path.read_text(encoding='utf-8')
        conf_dict = json.loads(conf_str)
        _input = conf_dict.get('data_input')
        if not isinstance(_input, str):
            raise Exception("Unknown data_input path")
        self._input = Path(_input)
        self._input.mkdir(exist_ok=True)
        print(
            f"Start scan data file, input_file_path:{self._input.as_posix()}")
        _esinput = conf_dict.get('es_input')
        if not isinstance(_esinput, str):
            raise Exception("Unknown es_input path")
        self._esinput = Path(_esinput)
        self._esinput.mkdir(exist_ok=True)
        print(f"Save data to ES, es_path:{self._esinput.as_posix()}")
        _dbuinput = conf_dict.get('backup_input')
        if not isinstance(_dbuinput, str):
            raise Exception("Unkown backup_input path")
        self._dbu_input = Path(_dbuinput)
        self._dbu_input.mkdir(exist_ok=True)
        print(f"Data backup process path:{self._dbu_input.as_posix()}")
        _databack = conf_dict.get('databackup')
        if not isinstance(_databack, str):
            raise Exception("Unknown databackup path")
        self._databack = Path(_databack)
        self._databack.mkdir(exist_ok=True)
        print(f"Data save backup path:{self._databack.as_posix()}")
        _zipdata = conf_dict.get('zipdata')
        if not isinstance(_zipdata, str):
            raise Exception("Unkown zipdata path")
        self._zipdata = Path(_zipdata)
        self._zipdata.mkdir(exist_ok=True)
        print(f"Zipdata save path:{self._zipdata.as_posix()}")
        _zip_size = conf_dict.get('zip_size')
        if not isinstance(_zip_size, int):
            raise Exception("Unknown zip_size type")
        # 将单位换算成B
        self._zip_size = _zip_size * 1024 * 1024
        print(f"Zip data size:{_zip_size}MB")
        backupthread = conf_dict.get('backup_thread')
        if not isinstance(backupthread, int):
            raise Exception("Unknown backupthread type")
        self.backup_thread = backupthread
        zipthread = conf_dict.get('zipdata_thread')
        if not isinstance(zipthread, int):
            raise Exception("Unknown zipthread type")
        self.zip_thread = zipthread
        time_limit = conf_dict.get('time_limit')
        if not isinstance(time_limit, int):
            raise Exception("Unknown time_limit type")
        self._backup_interval_time = time_limit * 24 * 60 * 60
        print(f"Zip data time expired after {time_limit} days")
        # 默认拷贝到ES的功能为开放
        copy_esinput_enable = conf_dict.get('copy_to_esinput', True)
        self.copy_esinput_enable = copy_esinput_enable
        # 拷贝旧索引数据
        _old_esinput = conf_dict.get('old_esinput')
        if not isinstance(_old_esinput, str):
            raise Exception("Unknown old_esinput path")
        self._old_esinput = Path(_old_esinput)
        self._old_esinput.mkdir(exist_ok=True)
        print(
            f"Save data to old ES, old_espath:{self._old_esinput.as_posix()}")

    def scan_file(self):
        """
        扫描输入的文件
        根据文件后缀进行分类，将文件放入待处理队列
        :return:
        """
        while True:
            try:
                for file in self._input.iterdir():
                    name = file.name
                    # 全部移动到tmp目录下去
                    tmpname = self._tmp / name
                    # file.replace(tmpname)
                    with self.__scan_file_locker:
                        # 这个文件得尽快移动到tmp文件夹，不然下次扫描又会扫描到它就会出问题
                        shutil.move(file.as_posix(), tmpname.as_posix())
                    try:
                        if tmpname.suffix == self.iscan_suffix:
                            # 只进行复制操作
                            # source: Path = self._input / name
                            target: Path = self._dbu_input / name
                            copyfile(tmpname.as_posix(), target.as_posix())
                            self.iscan_task_queue.put(target)
                            print(
                                f"Backup iscan_search data, filename:{file.as_posix()}")
                    except:
                        print(
                            f'Scan list file error, err:{traceback.format_exc()}')
                    finally:
                        # 最后无论如何都需要将文件输出到esinput
                        if self.copy_esinput_enable:
                            # 拷贝到新索引
                            outname = self._esinput / name
                            copyfile(tmpname.as_posix(), outname.as_posix())
                            # 拷贝带旧索引
                            old_outname = self._old_esinput / name
                            copyfile(tmpname.as_posix(),
                                     old_outname.as_posix())
                        # 一般来说是不会有文件存在的，但是意外不可避免嘛， 所以这里做一个判定，如果还存在文件就删了
                        if tmpname.exists():
                            tmpname.unlink()
            except:
                print(f'Scan task file error, err:{traceback.format_exc()}')
                continue
            finally:
                print("There is no scan data to back up")
                time.sleep(0.5)

    def _process_file(self, tmpfile: Path):
        """
        读取文件里面的数据打开一下，获取到信息后再关上
        """
        with tmpfile.open('r', encoding='utf-8') as fp:
            j_text = fp.read()
            d_text = json.loads(j_text)
            # scan_time = d_text.get('time')
            # if scan_time is None:
            # scan_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                country = d_text.get('geoinfo').get('country').get('code')
            except:
                country = 'UNKNOWN'
        return country

    def back_file(self):
        """
        开始备份数据，先保存到文件夹
        当这个文件夹到达一定大小然后压缩保存
        :return:
        """
        got = False
        while True:
            got = False
            if self.iscan_task_queue.empty():
                time.sleep(0.5)
                continue
            try:
                bfile: Path = self.iscan_task_queue.get()
                got = True
                name = bfile.name
                # 现在直接读文件里面的国家和日期
                country = self._process_file(bfile)
                # 每次保存之前去判断下是否需要修改文件名字并进行压缩备份
                date_now_str = datetime.datetime.now().strftime("%Y-%m-%d")
                # 新建文件夹的时候需要锁一下，其他时候直接移动即可
                with self.__file_locker:
                    # 先把文件移动过去
                    dirname: Path = self._databack / country / date_now_str
                    dirname.mkdir(exist_ok=True, parents=True)
                # 移过去的文件名
                filename = dirname / name
                # 移动到目标文件夹
                bfile.replace(filename)
                print(
                    f"Backup file, country:{country}, filename:{name}, date:{date_now_str}")
            except:
                print(f'Backup file error:\n{traceback.format_exc()}')
            finally:
                if got:
                    self.iscan_task_queue.task_done()

    def scan_zip_file(self):
        """
        压缩文件的线程，每天去扫描一次
        将昨天的文件夹压缩到压缩文件夹下
        """
        while True:
            try:
                date_now = datetime.datetime.now().date()
                for country in self._databack.iterdir():
                    if not country.exists():
                        continue
                    country_name = country.name
                    for d_file in country.iterdir():
                        if self._zip_dealing.__contains__(d_file):
                            continue
                        d_name = d_file.name
                        d_date = datetime.datetime.strptime(
                            d_name, "%Y-%m-%d").date()
                        # 如果是今天以前的数据那么就进行压缩
                        if date_now > d_date:
                            self._zip_queue.put((d_file, country_name))
                            with self._zipfile_locker:
                                # 加入正在处理队列
                                self._zip_dealing[d_file] = 1
                            print(
                                f"A file wait to zip, filename:{d_file.as_posix()}")
            except:
                print(f"Zip file error:\n{traceback.format_exc()}")
            finally:
                print("There is no scan data to zip")
                time.sleep(3600)

    def process_zip_file(self):
        """
        压缩今天以前的文件夹
        """
        got = False
        zipfile_path = None
        while True:
            got = False
            if self._zip_queue.empty():
                time.sleep(1)
                continue
            try:
                zipfile_path, country = self._zip_queue.get()
                got = True
                zip_store_file = self._zipdata / country
                zip_store_file.mkdir(exist_ok=True)
                zipname = zip_store_file/f"{zipfile_path.name}.zip"
                print(
                    f"Start zipfile, filename:{zipname.as_posix()}")
                # 增加一个写入限制
                with zipfile.ZipFile(zipname.as_posix(), 'a', zipfile.ZIP_DEFLATED) as write:
                    for file in zipfile_path.iterdir():
                        write.write(file.as_posix())
                        # 写入后删除
                        file.unlink()
                    write.close()
                # 最后删除已经压缩好的文件夹
                zipfile_path.rmdir()
                print(
                    f"Store zipfile success, filename:{zipname.as_posix()}")
            except:
                print(f"Zip file error:\n{traceback.format_exc()}")
            finally:
                if got:
                    self._zip_queue.task_done()
                    with self._zipfile_locker:
                        self._zip_dealing.pop(zipfile_path, None)

    def start(self):
        """
        项目启动
        :return:
        """
        thread1 = threading.Thread(target=self.scan_file, name="scanfile")
        thread1.start()
        for i in range(self.backup_thread):
            t = threading.Thread(target=self.back_file, name=f"backfile{i}")
            t.start()
        thread2 = threading.Thread(
            target=self.scan_zip_file, name=f"scan_zipfile")
        thread2.start()
        for j in range(self.zip_thread):
            tz = threading.Thread(
                target=self.process_zip_file, name=f"zipfile{j}")
            tz.start()


if __name__ == "__main__":

    scup = ScanBackUP()
    scup.start()
