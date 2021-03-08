"""
parser telnet
create by judy 2019/11/21
"""

import json
import os
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback.portinfo import (
    PortInfo, Telnet)

from .zgrab2parserbase import Zgrab2ParserBase


class Zgrab2ParserTelnet(Zgrab2ParserBase):
    """zgrab2 parser"""

    # _logger: MsLogger = MsLogManager.get_logger("Zgrab2Parsertelnet")

    def __init__(self):
        # self._name = type(self).__name__
        Zgrab2ParserBase.__init__(self)

    def parse_banner_telnet(self, task: IscoutTask, level: int,
                            portinfo: PortInfo, resultfi: str):
        """
        Parse telnet banner information
        """
        try:
            if not os.path.isfile(resultfi):
                self._logger.error(
                    f"Resultfi not exists:\ntaskid:{task.taskid}\nbatchid:{task.batchid}\nresultfi:{resultfi}"
                )
                return

            # its' one json object per line

            linenum = 1
            with open(resultfi, mode='r') as fs:
                while True:
                    try:
                        line = fs.readline()
                        if line is None or line == '':
                            break

                        sj = json.loads(line)
                        if sj is None:
                            continue

                        res = self._parse_telnet(sj, task, level, portinfo)
                        # 如果成功了则证明已经将telnet的信息解析出来了就不用再继续解析了
                        if res:
                            break
                    except Exception:
                        self._logger.error(
                            "Parse one telnet banner json line error:\ntaskid:{}\nbatchid:{}\nresultfi:{}\nlinenum:{}"
                            .format(task.taskid, task.batchid, resultfi,
                                    linenum))
                    finally:
                        linenum += 1

        except Exception:
            self._logger.error(
                "Parse telnet banner error:\ntaskid:{}\nbatchid:{}\nresultfi:{}"
                .format(task.taskid, task.batchid, resultfi))

    def _parse_telnet(self, sj: dict, task: IscoutTask, level: int,
                      portinfo: PortInfo):
        """
        解析telnet的banner和一些其他的信息
        总之就是port里的信息
        :param sj:
        :param task:
        :param level:
        :param portinfo:
        :return:
        """
        res = False
        if not sj.__contains__("data") or not sj["data"].__contains__(
                "telnet"):
            return
        try:
            sjtelnet = sj['data']['telnet']
            succ = sjtelnet["status"]
            if succ != "success":
                return

            protocol = sjtelnet["protocol"]
            if protocol != "telnet":
                return

            if portinfo.service != protocol:
                portinfo.service = protocol

            self._get_port_timestamp(sjtelnet, portinfo)

            # 开始构建telnet的banner
            mres = sjtelnet.get('result')
            if mres is None:
                return
            tdata = Telnet()
            tdata.banner = mres.get('banner')
            portinfo.banner = tdata.build_banner()
            res = True
            portinfo.set_telnet(tdata)

        except:
            self._logger.error(
                f"Parse banner protocal error, err:{traceback.format_exc()}")
        return res
