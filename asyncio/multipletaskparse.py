"""
多线程文件解析的模板
create by swm 20200313
"""

"""
DNS嗅探
create by judy 2020/03/10
"""
import queue
import threading
import time
import uuid
from pathlib import Path
import base64

import requests


class DnsDetect(object):

    def __init__(self):
        # 创建需要使用的文件夹
        self.input_file_path = Path('./_inputpath')
        self.input_file_path.mkdir(exist_ok=True, parents=True)
        self.tmp_path = Path('./_tmppath')
        self.tmp_path.mkdir(exist_ok=True, parents=True)
        self.output_path = Path('./_outputpath')
        self.output_path.mkdir(exist_ok=True, parents=True)
        # 线程锁
        self.process_locker = threading.Lock()

        # 读取文件的队列
        self.task_queue = queue.Queue()
        # 处理的极限
        self.limit = 100
        # 文件后缀名
        self.file_suffix = 'an_dns'

    def read_file(self, file_path: Path):
        """
        读取文件里面的内容
        :param file_path:
        :return:
        """
        res = {}
        with file_path.open('r', encoding='utf-8') as fp:
            for line in fp.readlines():
                if line is None or line == "":
                    break
                idx: int = line.find(':')
                key = line[:idx]
                value = line[idx + 1:]
                if key is not None and key != '':
                    res[key] = value.strip()
        return res

    def start_scan_file(self):
        """
        扫描数据的线程
        :return:
        """
        while True:
            try:
                with self.process_locker:
                    # if self.task_queue.qsize() >= self.limit:
                    if self.task_queue.full():
                        print("The task queue is full, wait for 10 seconds")
                        time.sleep(10)
                        continue
                for file in self.input_file_path.iterdir():
                    if file.suffix == '.' + self.file_suffix:
                        # 这里拿到的是一个file的名字
                        name = file.name
                        print(f"Get file :{name}")
                        # 移动到tmp文件夹
                        tmpname = self.tmp_path / name
                        file.replace(tmpname)
                        res_dict = self.read_file(tmpname)
                        self.task_queue.put(res_dict)
                        # 删除存在的文件
                        tmpname.unlink()
            except Exception as error:
                print(f"Read file error, err:{error}")
            finally:
                # 1秒去扫描一次
                time.sleep(1)

    # def start_loop(self, loop):
    #     asyncio.set_event_loop(loop)
    #     loop.run_forever()
    #
    # async def fetch(self, url):
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(url) as resp:
    #             print(resp.status)
    #             return await resp.text()

    def base64str(self, s: str,
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

    def base64format(self, s: str, enc='utf-8', encerrors='strict',
                     decerrors='strict') -> str:
        """return standard base64 format: =?utf-8?B?xxxx"""
        try:
            # return "=?{}?b?{}".format(enc, base64.b64encode(s.encode(enc, encerrors)).decode(enc, decerrors))
            return "=?{}?b?{}".format(enc,
                                      self.base64str(s, enc, enc, encerrors, decerrors))
        except Exception as ex:
            s = repr(s)
            # return "=?{}?b?{}".format(enc, base64.b64encode(s.encode(enc, encerrors)).decode(enc, decerrors))
            return "=?{}?b?{}".format(enc,
                                      self.base64str(s, enc, enc, encerrors, decerrors))

    def process_dns(self, task: dict):
        """
        开始处理dns
        :param task:
        :return:
        """
        url = task.get('dnsreq')
        print(f'Start dns detect {url}')
        # if url is None or url == '':
        #     self.dnsdata['http'] = 0
        if not url.startswith('http://') or not url.startswith('https://'):
            url = 'http://' + url
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                task['http'] = 1
            else:
                task['http'] = 0
        except Exception as err:
            task['http'] = 0
            task['httpdes'] = self.base64format(err)
            print(f"Request {url} error, err:{err}")

        with self.process_locker:
            tmpname = None
            lines = ''
            try:
                # --------------------------------------------tmppath
                tmpname = self.tmp_path / f'{uuid.uuid1()}.{self.file_suffix}'
                while tmpname.exists():
                    tmpname = self.tmp_path / f'{uuid.uuid1()}.{self.file_suffix}'
                for k, v in task.items():
                    lines += f'{k}:{v}\n'
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

    def start_process_file(self):
        """
        处理队列里面堆积的文件
        可开多线程
        :return:
        """
        while True:
            if self.task_queue.empty():
                time.sleep(3)
                continue
            try:
                task = self.task_queue.get()
                self.process_dns(task)
            except Exception as error:
                print(f"Process file error, err:{error}")
            finally:
                self.task_queue.task_done()


if __name__ == '__main__':
    dd = DnsDetect()
    try:
        thread1 = threading.Thread(target=dd.start_scan_file, name="scantask")
        thread1.start()
        for i in range(1):
            thread2 = threading.Thread(target=dd.start_process_file, name="processtask")
            thread2.start()
        print('Start............')
    except(KeyboardInterrupt):
        print('Force to stop by keyboard')
