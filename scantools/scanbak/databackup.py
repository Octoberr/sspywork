"""
数据备份
需求：
1、文件到这里
一份给ES 一份给自己

按国家端口保存，按大小打包， zip保存到另外一个文件夹
稳定性，扩展性和效率

by judy 2020/08/31
"""
from pathlib import Path
import threading
import json
from queue import Queue
import traceback
import time
from shutil import copyfile
import zipfile
import shutil


class FileInfo(object):

    def __init__(self, ssize, ctime, filepath: Path, country, port):
        self.ssize = ssize
        self.ctime = ctime
        self.filepath = filepath
        self.country = country
        self.port = port


class DataBackup(object):

    def __init__(self):
        # 所有数据先到这
        self._input = None
        # 所有数据先复制一份到这, 这个是程序不用管的文件夹
        self._esinput = None
        # 将要备份的数据放到这， 要处理的数据全部放在这里
        self._dbu_input = None
        self._databack = None
        self._zipdata: Path = None
        self._zip_size = None
        # 备份需要一个时间限制,测试使用10秒，项目正式使用一天
        self._backup_interval_time = 86400
        self.backup_thread = 1
        self.zip_thread = 1
        # 增加一个是否拷贝到ES的功能
        self.copy_esinput_enable = True
        self._tmp = Path('./tmp')
        self._tmp.mkdir(exist_ok=True)
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
        # 根据后缀分配的需要处理的队列，目前只有iscan
        self.iscan_task_queue = Queue()
        self._zip_queue = Queue()
        self.iscan_suffix = '.iscan_search'
        # 使用一个全局变量来记录已经存储的文件大小
        self.zip_file_dict = {}
        try:
            self._restore_existdata()
        except:
            raise Exception(
                "There's something wrong with restoring the environment")

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

    def _restore_existdata(self):
        """
        程序意外退出后，再重启后
        1、tmp文件夹下的所有数据应该放进，esinput和备份目录
        2、backup文件夹下的数据，已经改名的放进zip队列，没有改名的要统计大小放入字典
        :return:
        """
        # 先清空tmp文件夹下剩余的文件
        if self._tmp.exists() > 0:
            for remain_file in self._tmp.iterdir():
                name = remain_file.name
                try:
                    if remain_file.suffix == self.iscan_suffix:
                        # 只进行复制操作
                        # source: Path = self._input / name
                        target: Path = self._dbu_input / name
                        copyfile(remain_file.as_posix(), target.as_posix())
                        self.iscan_task_queue.put(target)
                        print(
                            f"Backup iscan_search data, filename:{remain_file.as_posix()}")
                except:
                    print(
                        f'Scan list file error, err:{traceback.format_exc()}')
                finally:
                    # 最后无论如何都需要将文件输出到esinput
                    outname = self._esinput / name
                    remain_file.replace(outname)
                    # 一般来说是不会有文件存在的，但是意外不可避免嘛， 所以这里做一个判定，如果还存在文件就删了
                    if remain_file.exists():
                        remain_file.unlink()
        # 然后开始处理backup文件夹下的数据
        if self._databack.exists():
            for country_file in self._databack.iterdir():
                for port_file in country_file.iterdir():
                    name = port_file.name
                    size = sum(f.stat().st_size for f in port_file.iterdir())
                    if len(name.split('_')) > 1:
                        print(f"A zipfile restore {name}")
                        self._zip_queue.put((port_file, size))
                    else:
                        self.zip_file_dict[f'{country_file.name}_{name}'] = FileInfo(size,
                                                                                     int(port_file.stat(
                                                                                     ).st_ctime),
                                                                                     port_file, country_file.name, name)
                        print(f"A backfile restore {name}")

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
                            outname = self._esinput / name
                            tmpname.replace(outname)
                        # 一般来说是不会有文件存在的，但是意外不可避免嘛， 所以这里做一个判定，如果还存在文件就删了
                        if tmpname.exists():
                            tmpname.unlink()
            except:
                print(f'Scan task file error, err:{traceback.format_exc()}')
                continue
            finally:
                time.sleep(0.5)

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
                time.sleep(0.1)
                continue
            try:
                bfile: Path = self.iscan_task_queue.get()
                # 每次都去获取现在的时间，目前定义的备份时间为一天
                time_now = int(time.time())
                got = True
                name = bfile.name
                size = bfile.stat().st_size
                namelist = name.split('_')
                if not len(namelist) >= 3:
                    # 不是cn_80_file.iscan_search格式的文件处理
                    dirname = self._databack / 'unknown'
                    dirname.mkdir(exist_ok=True)
                    filename = dirname / name
                    # 移动
                    bfile.replace(filename)
                    continue
                country = namelist[0]
                port = namelist[1]
                # 先把文件移动过去
                # dirname: Path = self._databack / country / port
                # dirname.mkdir(exist_ok=True, parents=True)
                # filename = dirname / name
                # bfile.replace(filename)
                # 每次保存之前去判断下是否需要修改文件名字并进行压缩备份
                with self.__file_locker:
                    # 先把文件移动过去
                    dirname: Path = self._databack / country / port
                    dirname.mkdir(exist_ok=True, parents=True)
                    mktime = int(dirname.stat().st_ctime)
                    # 移过去的文件名
                    filename = dirname / name
                    bfile.replace(filename)
                    # 然后判断文件夹是否需要改名，并进行压缩
                    file_info = self.zip_file_dict.get(f'{country}_{port}')
                    # 如果是新的那么就赋值
                    if file_info is None:
                        self.zip_file_dict[f'{country}_{port}'] = FileInfo(
                            0, mktime, dirname, country, port)
                    # 前面为空的时候赋了值就一定会存在这个数据了
                    self.zip_file_dict[f'{country}_{port}'].ssize += size
                    # 当缓存的大小或者缓存的时间到的时候就压缩
                    if self.zip_file_dict[f'{country}_{port}'].ssize >= self._zip_size or \
                            (time_now - self.zip_file_dict[f'{country}_{port}'].ctime >= self._backup_interval_time):
                        ddirname = self._databack / country / \
                            f'{port}_{int(time.time() * 1000)}'
                        # 先改名字
                        dirname.rename(ddirname)
                        # 然后再压缩
                        self._zip_queue.put(
                            (ddirname, self.zip_file_dict[f'{country}_{port}'].ssize))
                        # 然后删除这个键，下次再有会重新创建
                        self.zip_file_dict.pop(f'{country}_{port}')
                        print(
                            f"Start zip backupfile, filename:{ddirname.as_posix()}")
            except:
                print(f'Backup file error:\n{traceback.format_exc()}')
            finally:
                if got:
                    self.iscan_task_queue.task_done()

    def time_expire_back(self):
        """
        日期过期备份，因为读取到的数据在字典里
        如果没有新数据来是不会被更新的
        这个备份时间跨度会非常长，所以需要定时去清理下
        :return:
        """
        while True:
            try:
                if self.zip_file_dict.__len__() == 0:
                    # 如果为空的话5S去检测一次
                    time.sleep(5)
                    continue
                with self.__file_locker:
                    time_back = []
                    time_now = int(time.time())
                    for k, v in self.zip_file_dict.items():
                        vtime = v.ctime
                        if time_now - vtime >= self._backup_interval_time:
                            time_back.append(k)
                    if len(time_back) > 0:
                        for zipk in time_back:
                            zipv = self.zip_file_dict.get(zipk)
                            if zipv is None:
                                self.zip_file_dict.pop(zipk)
                                continue
                            ddirname = self._databack / zipv.country / \
                                f'{zipv.port}_{int(time.time() * 1000)}'
                            # 先改名字
                            print(
                                f"A time expired file {zipv.filepath.as_posix()} will zipback")
                            zipv.filepath.rename(ddirname)
                            self._zip_queue.put((ddirname, zipv.ssize))
                            self.zip_file_dict.pop(zipk)
            except:
                print(
                    f"Zip time expired data error, err:{traceback.format_exc()}")

    def zip_file(self):
        """
        压缩文件并保存
        :return:
        """
        got = False
        while True:
            got = False
            if self._zip_queue.empty():
                time.sleep(1)
                continue
            try:
                zfile, fsize = self._zip_queue.get()
                got = True
                z_parts = zfile.parts
                country = z_parts[-2]
                port = z_parts[-1].split('_')[0]
                zip_store_file = self._zipdata / country
                zip_store_file.mkdir(exist_ok=True)
                # 先找一下已经压缩的文件，如果是同一个国家同一个端口，那么就将后续的文件放入这个比较小的文件
                zipname = None
                for zip_name in zip_store_file.iterdir():
                    name_str = zip_name.name
                    name_str_st = name_str.split('_')
                    # 先判断是不是一个国家端口
                    if country == name_str_st[0] and port == name_str_st[1]:
                        # 再判断保存的数据是不是没有超过限制
                        if zip_name.stat().st_size + fsize <= self._zip_size:
                            zipname = zip_name
                            break
                # 如果没有满足的那么就重新创建一个
                if zipname is None:
                    zipname = zip_store_file / \
                        f'{z_parts[-2]}_{z_parts[-1]}.zip'
                with zipfile.ZipFile(zipname.as_posix(), 'a', zipfile.ZIP_DEFLATED) as write:
                    for file in zfile.iterdir():
                        write.write(file.as_posix())
                        # 写入后删除
                        file.unlink()
                    write.close()
                # 最后删除已经压缩好的文件夹
                zfile.rmdir()
                print(f"Store zipfile success, filename:{zipname.as_posix()}")
            except:
                print(f"Zip file error:\n{traceback.format_exc()}")
            finally:
                if got:
                    self._zip_queue.task_done()

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
            target=self.time_expire_back, name=f"timeexpiredback")
        thread2.start()
        for j in range(self.zip_thread):
            tz = threading.Thread(target=self.zip_file, name=f"zipfile{j}")
            tz.start()


if __name__ == '__main__':
    dbu = DataBackup()
    dbu.start()
