"""
对比算法
对比两个周期的增量数据
create by judy 2020/06/04
"""
import base64
import json
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from queue import Queue
import traceback

import pytz
import requests


class CTA(object):

    def __init__(self):
        # 文件锁
        self.__file_locker = threading.Lock()
        # ES地址
        self.es_http_url = 'http://192.168.111.222:9200/dg-al-scoutLog/_search'
        self._input_path = Path('./inputpath')
        self._input_path.mkdir(exist_ok=True)
        self._tmp_path = Path('./tmppath')
        self._tmp_path.mkdir(exist_ok=True)
        self._output_path = Path('./outputpath')
        self._output_path.mkdir(exist_ok=True)
        self.task_queue = Queue()
        self.suffix = '.iscan_period_vs_task'
        # 需要对比的数量，用于回馈进度
        self._compare_count: int = 0
        self.__progress: float = 0.0
        # 输出队列，输出线程
        self._output_queue = Queue()
        # 每次先处理一个任务，等到性能不够用了再扩展到多个任务
        self.ctaskid = None

    @staticmethod
    def base64str(s: str,
                  encoding: str = 'utf-8',
                  decoding='utf-8',
                  encerrors='strict',
                  decerrors='strict') -> str:
        """base64 encode a str and return the str form of result.
        s: src str
        encoding: default is 'utf-8'
        return: result str"""
        enc = encoding
        if enc is None or enc == '':
            enc = 'utf-8'
        dec = decoding
        if dec is None or dec == '':
            dec = 'utf-8'

        bsIn = bytes(s, enc, encerrors)
        bsOut = base64.b64encode(bsIn)
        res = str(bsOut, dec, decerrors)
        return res

    @staticmethod
    def base64format(s: str, enc='utf-8', encerrors='strict',
                     decerrors='strict') -> str:
        """return standard base64 format: =?utf-8?B?xxxx"""
        try:
            # return "=?{}?b?{}".format(enc, base64.b64encode(s.encode(enc, encerrors)).decode(enc, decerrors))
            return "=?{}?b?{}".format(enc,
                                      CTA.base64str(s, enc, enc, encerrors, decerrors))
        except Exception as ex:
            s = repr(s)
            # return "=?{}?b?{}".format(enc, base64.b64encode(s.encode(enc, encerrors)).decode(enc, decerrors))
            return "=?{}?b?{}".format(enc,
                                      CTA.base64str(s, enc, enc, encerrors, decerrors))

    def _parse_file_to_dict(self, taskfile: Path):
        """
        将文件内容解析成字典，方便后边调用
        :param taskfile:
        :return:
        """
        res: dict = {}
        try:
            with taskfile.open('r', encoding='utf-8') as fp:
                for line in fp.readlines():
                    tmp: str = line.strip()
                    if tmp is not None and tmp != '' and ':' in tmp:
                        sr = tmp.split(':')
                        res[sr[0]] = sr[1]
        except Exception as err:
            print(f'Parse file error\nfilename:{taskfile.as_posix()}\nerr:{traceback.format_exc()}')
        return res

    def scan_task(self):
        """
        扫描输入文件夹，发现需要待处理的任务
        :return:
        """
        while True:
            try:
                for file in self._input_path.iterdir():
                    try:
                        if file.suffix == self.suffix:
                            res_dict = self._parse_file_to_dict(file)
                            if len(res_dict) > 0:
                                self.task_queue.put(res_dict)
                            print(f"Get a task file, filename:{file.as_posix()}")
                    except Exception as err:
                        print(f'Scan list file error, err:{traceback.format_exc()}')
                    finally:
                        if file.exists():
                            file.unlink()
            except Exception as err:
                print(f'Scan task file error, err:{traceback.format_exc()}')
                continue
            finally:
                time.sleep(5)

    @property
    def time_now(self):
        """
        获取东八区当前的时间
        时间格式为标准的时间格式
        :return:
        """
        time_now = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        return time_now

    def connect_es_and_get_res(self, taskid: str, periodnum: str, gettotal=False):
        """
        查询ES的http端口，获取需要处理的数据
        :return:
        """
        headers = {
            'Content-Type': 'application/json'
        }
        page = 0  # 从0开始
        total = 0
        now_get = 0

        while True:
            # 停止执行条件
            if total != 0 and now_get != 0 and (total == now_get or now_get > total):
                break
            payload = f'''
                        {{
                "query": {{
                    "bool": {{
                        "filter": [
                            {{
                                "term": {{
                                    "TaskId": "{taskid}"
                                }}
                            }},
                            {{
                                "term": {{
                                    "PeriodNum": "{periodnum}"
                                }}
                            }}
                        ]
                    }}
                }},
                "from": {page},
                "size": 500
            }}
                        '''
            try:
                res = requests.post(self.es_http_url, headers=headers, data=payload)
                res.encoding = 'utf-8'
                rdict = json.loads(res.text)
                # 判断下是否访问成功
                time_out = rdict.get('timed_out')
                if time_out:
                    self.write_taskback(0, 0, "访问ES超时，请检查ES数据库和内网网络")
                    break
                hits = rdict.get('hits')
                # 如果是第一次去拿，那么需要统计下一共有多少数据
                if total == 0:
                    total = hits.get('total')
                    if gettotal:  # 用于统计对比进度
                        self._compare_count = total
                hits_res = hits.get('hits', [])
                now_get += len(hits_res)
                for el in hits_res:
                    yield el
                page += 1
            except Exception as err:
                print(f"Connect ES and get result error, err:{traceback.format_exc()}")
            finally:
                time.sleep(1)

    def start_compare_algorithm(self, task: dict):
        """
        查询ES的表，查询出来的数据包括两个周期的数据
        只需要输出后面一个周期比前一个周期多的数据
        包括任务执行中的状态，执行完成的状态
        :param task:
        :return:
        """
        # 这个是需要查询的数据的taskid
        iscantaskid = task.get('iscantaskid')
        # 这个id是本次对比任务的id，任务的回馈使用这个id，包括输出的数据也要这个id
        compareid = task.get('taskid')
        self.ctaskid = compareid
        speriod = task.get('srcperiodnum')
        dperiod = task.get('destperiodnum')
        # 创建一个字典来保存源周期的数据
        sdict = {}
        for el in self.connect_es_and_get_res(iscantaskid, speriod):
            try:
                rdata = el.get('_source')
                ip = rdata.get('Ip')
                # 一定会有一个port
                port = rdata.get('PortInfo')[0].get('Port')
                sdict[f'{ip}:{port}'] = 1
            except Exception as err:
                print(f"Parse {speriod} period res error\nsource element data:{el}\nerr:{traceback.format_exc()}")

        self.compare_src_and_dist_res(sdict, iscantaskid, dperiod)

    def _make_progress(self, hascompare):
        """
        制作进度，每次进度大于1才回馈
        :param hascompare:
        :return:
        """
        progress = round(hascompare / self._compare_count, 2)
        if progress - self.__progress > 0.1:
            self.__progress = progress
            print(f"Scan progress:{float(progress * 100)}%")
            self.write_taskback(3, progress, f'正在对比:已对比{float(progress * 100)}%')

    def compare_src_and_dist_res(self, sdict, iscantaskid, dperiod):
        """
        对比两个周期的结果
        每次查询一个对比一个，新增的就直接输出
        :return:
        """
        has_compare = 0
        for el in self.connect_es_and_get_res(iscantaskid, dperiod, True):
            try:
                rdata = el.get('_source')
                ip = rdata.get('Ip')
                # 一定会有一个port
                port = rdata.get('PortInfo')[0].get('Port')
                repeat = sdict.get(f'{ip}:{port}', None)
                # 只输出新增数据
                if repeat is None:
                    self._output_queue.put(rdata)
            except Exception as err:
                print(f"Parse {dperiod} period res error, err:{traceback.format_exc()}")
            finally:
                has_compare += 1
                # 每次都统计下进度
                self._make_progress(has_compare)
        # 对比完成后需要输出
        self.write_taskback(1, 1, '对比完成，已对比100%')
        print('Scan progress:100%')

    def output_file(self, res_str, suffix):
        """
        接收需要输出的字符串
        :return:
        """
        if not isinstance(self._tmp_path, Path):
            raise Exception("Tmpdir path should be Path object")
        if not isinstance(self._output_path, Path):
            raise Exception("Outdir should be Path object")

        with self.__file_locker:
            try:
                # --------------------------------------------tmppath
                tmpname = self._tmp_path / f'{uuid.uuid1()}.{suffix}'
                while tmpname.exists():
                    tmpname = self._tmp_path / f'{uuid.uuid1()}.{suffix}'
                # 这里的文件体大了后会出现无法写完的bug，不过应该不是这里的bug
                tmpname.write_text(res_str, encoding='utf-8')
                # ------------------------------------------outputpath
                outname = self._output_path / f'{uuid.uuid1()}.{suffix}'
                while outname.exists():
                    outname = self._output_path / f'{uuid.uuid1()}.{suffix}'
                # 将tmppath 移动到outputpath
                tmpname.replace(outname)
                tmpname = None
            except Exception as err:
                print(f'output data error\nerr:{traceback.format_exc()}\nerrorstr:{res_str}')
            finally:
                if tmpname is not None:
                    tmpname.unlink()

    def output_compare_res(self):
        """
        输出对比的结果，增加了一个对比任务的id
        compareid
        :return:
        """
        while True:
            if self._output_queue.empty():
                time.sleep(10)
                continue
            try:
                out_dict = self._output_queue.get()
                out_dict['compareid'] = self.ctaskid
                self.output_file(json.dumps(out_dict, ensure_ascii=False), 'iscan_compare')
                self._output_queue.task_done()
            except Exception as error:
                print(f'Output compare result error, err:{traceback.format_exc()}')
                continue
            finally:
                time.sleep(1)

    def write_taskback(self, state, progress, recvmsg):
        """
        输出任务命令的回馈
        taskid
        state:0失败1成功3执行中8任务被取消
        progress
        recvmsg
        time当前数据的生成时间（统一使用东八区的时间）
        :return:
        """
        res = ''
        res += f'taskid:{self.ctaskid}\n'
        res += f'state:{state}\n'
        res += f'progress:{progress}\n'
        res += f'recvmsg:{CTA.base64format(recvmsg)}\n'
        res += f'time:{self.time_now}\n'
        self.output_file(res, 'iscan_period_vs_task_back')

    def deal_a_compare_task(self):
        """
        1、拿一个任务
        2、查询ES，拿到两个周期的数据
        3、对比出结果，结果输出到output_path
        4、对比中给出对比进度回馈，任务完成给出任务完成回馈，任务失败给出任务失败回馈
        :return:
        """
        while True:

            if self.task_queue.empty():
                time.sleep(3)
                continue
            try:
                task = self.task_queue.get()
                self.start_compare_algorithm(task)
                self.task_queue.task_done()
            except Exception as err:
                print(f'Compare algorithm error, err:{traceback.format_exc()}')
                continue
            finally:
                print('This comparison task is over')
                time.sleep(3)


if __name__ == '__main__':
    cta = CTA()
    # 任务扫描线程
    t1 = threading.Thread(target=cta.scan_task, name="GetCompareTask")
    t1.start()
    # 任务对比线程，这个如果到时候对比任务过多，那么会修改为多线程
    t2 = threading.Thread(target=cta.deal_a_compare_task, name="StartCompareAlgorithm")
    t2.start()
    # 结果输出线程
    t3 = threading.Thread(target=cta.output_compare_res, name="OutputCompareResult")
    t3.start()
    print("Start compare algorithm")
