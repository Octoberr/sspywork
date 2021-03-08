"""
处理vps抓包数据定义，添加http服务标记字段
create by judy 2020/03/04
"""

import requests
import threading
from idownclient.config_task import clienttaskconfig
import uuid


class DnsData(object):
    def __init__(self, dnsdata: dict):
        self.dnsdata = dnsdata


class DnsReq(object):
    # 添加一个全局锁
    __dns_thread_locker = threading.RLock()

    def __init__(self):
        self.tmppath = clienttaskconfig.tmppath
        self.outpath = clienttaskconfig.outputpath
        self.suffix = 'an_dns_client'

    def dns_response(self, dnsdata: dict):
        url = dnsdata.get('dnsreq')
        # if url is None or url == '':
        #     self.dnsdata['http'] = 0
        if not url.startswith('http://') or not url.startswith('https://'):
            url = 'http://'+url
        try:
            response = requests.get(url)
            if response.status_code == 200:
                dnsdata['http'] = 1
            else:
                dnsdata['http'] = 0
        except Exception as err:
            dnsdata['http'] = 0

        with self.__dns_thread_locker:
            tmpname = None
            lines = ''
            try:
                # --------------------------------------------tmppath
                tmpname = self.tmppath / f'{uuid.uuid1()}.{self.suffix}'
                while tmpname.exists():
                    tmpname = self.tmppath / f'{uuid.uuid1()}.{self.suffix}'
                for k, v in dnsdata.items():
                    lines += f'{k}:{v}\n'
                tmpname.write_text(lines.strip(), encoding='utf-8')

                # ------------------------------------------outputpath
                outname = self.outpath / f'{uuid.uuid1()}.{self.suffix}'
                while outname.exists():
                    outname = self.outpath / f'{uuid.uuid1()}.{self.suffix}'
                # 将tmppath 移动到outputpath
                tmpname.replace(outname)
                tmpname = None   # 表示移动成功了，移动不会出问题
            except Exception as error:
                raise Exception(error)
            finally:
                if tmpname is not None:
                    tmpname.unlink()
