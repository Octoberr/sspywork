"""
dns任务的分配和处理
create by judy 202/03/05
"""
import threading
import uuid
from pathlib import Path

from datacontract import DataMatcher, InputData
from dataparser import DataParser
from ..config_output import tmpdir, outputdir
# client的目录
from ..config_taskdeliver import taskdeliverconfig
from ..servicemanager.dealerbase import DealerBase
from ..statusmantainer import StatusMantainer


class DnsReqDealer(DealerBase):

    def __init__(self, datamatcher: DataMatcher):
        DealerBase.__init__(self, datamatcher)
        self._dispatch_queue_locker = threading.RLock()
        self.__dns_thread_locker = threading.RLock()
        # 缓存文件夹
        self._tmpdir = Path(tmpdir)
        # 输出文件夹
        self._outputdir = Path(outputdir)
        # 发送到client的后缀，也就是server和client内部自带的后缀
        self.c_suffix = 'an_dns_client'
        # 发送到结果的后缀,也就是原有的后缀
        self.o_suffix = 'an_dns'

    def _deal_data(self, data: InputData) -> bool:
        """
        处理数据的流程
        :param data:
        :return:
        """
        try:
            if data.stream is None or not data.stream.readable():
                self._logger.error(f"Data stream is None when trying to convert to standard Task: {data._source}")
                return False

            exten = data.extension
            for seg in DataParser.parse_standard_data(data.stream):
                # 获取到一个数据段
                data_fields = seg._fields
                if exten == self.o_suffix:
                    self.dispatch_to_client(data_fields)
                elif exten == self.c_suffix:
                    self.output_dns_data(data_fields, self.o_suffix, self._outputdir)
                    self._logger.info('Output dns_req result')
        except Exception as error:
            self._logger.error(f"Deal with dns data error, err:{error}")
        finally:
            data.on_complete()

    def dispatch_to_client(self, cdata: dict):
        """
        将数据分配到client
        1、选一个client
        2、从tmp文件夹到client的文件夹的路径
        :param cdata:
        :return:
        """
        choise = None
        clients: dict = StatusMantainer.get_clientstatus_ip_sorted()
        with self._dispatch_queue_locker:
            # 看有没有可用采集端
            if len(clients) < 1:
                self._logger.info(f"No available client")
            for c in clients.values():
                # dns是从vps扫下来的，client就必须会翻墙
                if c._statusbasic.crosswall == 1:
                    choise = c
                    break
        if choise is None:
            self._logger.error(f"No suitable machine was found to assign DNS_REQ")
        # 传输分配
        if not taskdeliverconfig._ipdir.__contains__(choise._statusbasic.ip):
            self._logger.error(f"Client transfer folder not configured: clientip={choise._statusbasic.ip}")
        else:
            tdir = taskdeliverconfig._ipdir[choise._statusbasic.ip]
            targetdir = Path(tdir)
            # 如果第一次启动可能没有创建文件夹，尝试创建文件夹, 当然如果文件夹创建了，那么也没有什么影响
            targetdir.mkdir(exist_ok=True, parents=True)
            self.output_dns_data(cdata, self.c_suffix, targetdir)
            self._logger.info(f"Allot dns_req to client {choise._statusbasic.ip}")
        return

    def output_dns_data(self, odata: dict, suffix, outdir: Path):
        """
        输出数据
        :param odata:
        :param suffix:
        :param outdir:
        :return:
        """
        with self.__dns_thread_locker:
            tmpname = None
            lines = ''
            try:
                # --------------------------------------------tmppath
                tmpname = self._tmpdir / f'{uuid.uuid1()}.{suffix}'
                while tmpname.exists():
                    tmpname = self._tmpdir / f'{uuid.uuid1()}.{suffix}'
                for k, v in odata.items():
                    lines += f'{k}:{v}\n'
                tmpname.write_text(lines.strip(), encoding='utf-8')

                # ------------------------------------------outputpath
                outname = outdir / f'{uuid.uuid1()}.{suffix}'
                while outname.exists():
                    outname = outdir / f'{uuid.uuid1()}.{suffix}'
                # 将tmppath 移动到outputpath
                tmpname.replace(outname)
                tmpname = None  # 表示移动成功了，移动不会出问题
            except Exception as error:
                raise Exception(error)
            finally:
                if tmpname is not None:
                    tmpname.unlink()
