"""
parser ntp
create by judy 2019/11/19
"""

import json
import os
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback.portinfo import (Ntp,
                                                                       PortInfo
                                                                       )

from .zgrab2parserbase import Zgrab2ParserBase


class Zgrab2ParserNtp(Zgrab2ParserBase):
    """zgrab2 parser"""

    # _logger: MsLogger = MsLogManager.get_logger("Zgrab2Parserntp")

    def __init__(self):
        # self._name = type(self).__name__
        Zgrab2ParserBase.__init__(self)

    def parse_banner_ntp(self, task: IscoutTask, level: int,
                         portinfo: PortInfo, resultfi: str):
        """
        Parse ntp banner information
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

                        res = self._parse_ntp(sj, task, level, portinfo)
                        # 如果成功了则证明已经将ntp的信息解析出来了就不用再继续解析了
                        if res:
                            break
                    except Exception:
                        self._logger.error(
                            "Parse one ntp banner json line error:\ntaskid:{}\nbatchid:{}\nresultfi:{}\nlinenum:{}"
                            .format(task.taskid, task.batchid, resultfi,
                                    linenum))
                    finally:
                        linenum += 1

        except Exception:
            self._logger.error(
                "Parse ntp banner error:\ntaskid:{}\nbatchid:{}\nresultfi:{}".
                format(task.taskid, task.batchid, resultfi))

    def _parse_ntp(self, sj: dict, task: IscoutTask, level: int,
                   portinfo: PortInfo):
        """
        解析ntp的banner和一些其他的信息
        总之就是port里的信息
        :param sj:
        :param task:
        :param level:
        :param portinfo:
        :return:
        """
        res = False
        if not sj.__contains__("data") or not sj["data"].__contains__("ntp"):
            return
        try:
            sjntp = sj['data']['ntp']
            succ = sjntp["status"]
            if succ != "success":
                return

            protocol = sjntp["protocol"]
            if protocol != "ntp":
                return

            if portinfo.service != protocol:
                portinfo.service = protocol

            self._get_port_timestamp(sjntp, portinfo)

            # 开始构建ntp的banner

            mres = sjntp.get('result')
            if mres is None:
                return
            ndata = Ntp()
            ndata.version = mres.get('version')

            ndata.stratum = mres.get('stratum')

            ndata.leap_indicator = mres.get('leap_indicator')

            ndata.precision = mres.get('precision')

            ndata.root_delay = mres.get('root_delay', {})

            ndata.root_dispersion = mres.get('root_dispersion', {})

            ndata.reference_id = mres.get('reference_id')

            ndata.reference_timestamp = mres.get('reference_timestamp')

            ndata.poll = mres.get('poll')

            portinfo.banner = ndata.build_banner()
            res = True
            portinfo.set_ntp(ndata)

        except:
            self._logger.error(
                f"Parse ntp protocal error, err:{traceback.format_exc()}")
        return res
