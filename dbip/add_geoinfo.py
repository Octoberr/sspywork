"""
需要离线添加一些ip的信息
by swm 2020/04/24
"""

import queue
import threading
import json
import time
import uuid
from pathlib import Path
import argparse

import maxminddb


class AddInfo(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("pthreads", help="55", type=int)
        self.args = self.parser.parse_args()

        # 需要读取的文件夹
        self.input_file_path = Path('./hkdata')
        if not self.input_file_path.exists():
            raise Exception("Error input path")
        # self.input_file_path.mkdir(exist_ok=True, parents=True)
        self.tmp_path = Path('./_tmppath')
        self.tmp_path.mkdir(exist_ok=True, parents=True)
        self.output_path = Path('./_outputpath')
        self.output_path.mkdir(exist_ok=True, parents=True)
        # 线程锁
        self.process_locker = threading.Lock()

        # 读取文件的队列
        self.task_queue = queue.Queue()
        # 输出文件队列
        self.output_queue = queue.Queue()
        # 处理的极限
        self.limit = 5
        # 文件后缀名
        self.file_suffix = 'iscan_search'

        # 线程数量的控制，根据实际需求来改变
        self.max_threads = int(self.args.pthreads)

    def read_file(self, file_path: Path):
        """
        读取文件里面的内容
        :param file_path:
        :return:
        """

        res = file_path.read_text(encoding='utf-8')
        return json.loads(res)

    def start_scan_file(self):
        """
        扫描数据的线程
        :return:
        """
        try:
            for file in self.input_file_path.iterdir():
                # 这里拿到的是一个file的名字
                if file.suffix == '.' + self.file_suffix:
                    name = file.name
                    print(f"Get file :{name}")
                    # 移动到tmp文件夹
                    tmpname = self.tmp_path / name
                    file.replace(tmpname)
                    try:
                        res_dict = self.read_file(tmpname)
                    except Exception as err:
                        print(f'some error happened, err:{err}')
                        continue
                    self.task_queue.put([res_dict, tmpname])
                else:
                    file.unlink()
                    continue

            print("Complete process data")
        except Exception as error:
            print(f"Read file error, err:{error}")
        finally:
            # 1秒去扫描一次
            time.sleep(1)

    def get_ip_geoinfo(self, ip: str) -> dict:
        """
        根据ip去查询所在的地址
        :param ip:
        :return:
        """
        res = {}
        try:
            # 1、先检测下东西在不在
            # 这样当前dbname就一定会有
            # with DbipMmdb.__scouter_ip_locker:
            # 一次只能有一个玩意在这检测版本，虽然慢但是多线程没办法
            # self.__check_db_version()
            reader = maxminddb.open_database('./_ip_location_dbs/dbfile/2020-05.mmdb')
            res = reader.get(ip)
            if res is None:
                return res
            reader.close()
        except Exception as error:
            print("Get geoinfo error:\nip={}\nerror:{}".format(ip, error))
        finally:
            return res

    def process_dns(self, file_info: list):
        """
        开始处理dns
        :param file_info:
        :return:
        """
        task = file_info[0]
        filename: Path = file_info[1]
        ip = task.get('ip')
        print(f'Start get ip info: {ip}')
        try:
            with self.process_locker:
                res_dict = self.get_ip_geoinfo(ip)
            tgeo = task.get('geoinfo')
            # 里面为空或者是里面没有东西
            if tgeo is None or len(tgeo) == 0:
                geodict = {}
                # 最近的数据没有拿到geoinfo，手动增加下
                data_city_en = res_dict.get('city', {}).get('names', {}).get('en', None)
                data_city_cn = res_dict.get('city', {}).get('names', {}).get('zh-CN', None)
                geodict['city'] = {'names': {'en': data_city_en, 'zh-CN': data_city_cn}}
                data_state_en = None
                data_state_cn = None
                subdivisions = res_dict.get('subdivisions', [])
                if len(subdivisions) > 0:
                    data_state_en = subdivisions[0].get('names', {}).get('en', None)
                    data_state_cn = subdivisions[0].get('names', {}).get('zh-CN', None)
                geodict['province'] = {'names': {'en': data_state_en, 'zh-CN': data_state_cn}}
                data_country_code = res_dict.get('country', {}).get('iso_code', None)
                data_country_en = res_dict.get('country', {}).get('names', {}).get('en')
                data_country_cn = res_dict.get('country', {}).get('names', {}).get('zh-CN')
                geodict['country'] = {'code': data_country_code, 'names': {'en': data_country_en, 'zh-CN': data_country_cn}}

                location = res_dict.get('location', {})
                lng = location.get('longitude', None)
                lat = location.get('latitude', None)
                geodict['location'] = {'lat': lat, 'lon': lng}
                ctinfo = res_dict.get('continent', {})
                ctcode = ctinfo.get('code')
                ctname_en = ctinfo.get('names', {}).get('en')
                ctname_cn = ctinfo.get('names', {}).get('zh-CN')
                geodict['continent'] = {'code': ctcode, 'names': {'en': ctname_en, 'zh-CN': ctname_cn}}
                globalcode = 852
                timezone = 0
                geodict['globaltelcode'] = globalcode
                geodict['timezone'] = timezone
                task['geoinfo'] = geodict

            traits_info = res_dict.get('traits', {})
            org = traits_info.get('organization', None)
            isp = traits_info.get('isp', None)
            if org is not None:
                task['org'] = org
            if isp is not None:
                task['isp'] = isp
        except Exception as err:
            print(err)
        finally:
            # 处理完成后删除文件
            self.output_queue.put(task)
            filename.unlink()

    def start_process_file(self):
        """
        处理队列里面堆积的文件
        可开多线程
        :return:
        """
        while True:
            if self.task_queue.empty():
                time.sleep(0.5)
                continue
            try:
                task = self.task_queue.get()
                self.process_dns(task)
            except Exception as error:
                print(f"Process file error, err:{error}")
            finally:
                self.task_queue.task_done()

    def outputdata(self):
        while True:
            if self.output_queue.empty():
                time.sleep(0.5)
                continue

            try:
                task = self.output_queue.get()
                tmpname = None
                lines = json.dumps(task, ensure_ascii=False)
                try:
                    # --------------------------------------------tmppath
                    tmpname = self.tmp_path / f'{uuid.uuid1()}.{self.file_suffix}'
                    while tmpname.exists():
                        tmpname = self.tmp_path / f'{uuid.uuid1()}.{self.file_suffix}'
                    tmpname.write_text(lines.strip(), encoding='utf-8')

                    # ------------------------------------------outputpath
                    outname = self.output_path / f'{uuid.uuid1()}.{self.file_suffix}'
                    while outname.exists():
                        outname = self.output_path / f'{uuid.uuid1()}.{self.file_suffix}'
                    # 将tmppath 移动到outputpath
                    tmpname.replace(outname)
                    tmpname = None  # 表示移动成功了，移动不会出问题
                    print(f'Output file {outname}')
                except Exception as error:
                    raise Exception(error)
                finally:
                    if tmpname is not None:
                        tmpname.unlink()
            except Exception as error:
                print(f"outputdata error, err:{error}")
                continue
            finally:
                self.output_queue.task_done()


if __name__ == '__main__':
    dd = AddInfo()
    print(f'Start {dd.max_threads} process threads')
    time.sleep(1)
    try:
        thread1 = threading.Thread(target=dd.start_scan_file, name="scantask")
        thread1.start()
        for i in range(dd.max_threads):
            thread2 = threading.Thread(target=dd.start_process_file, name="processtask")
            thread2.start()
        thread3 = threading.Thread(target=dd.outputdata, name='outputdata')
        thread3.start()
        print('Start............')
    except(KeyboardInterrupt):
        print('Force to stop by keyboard')
