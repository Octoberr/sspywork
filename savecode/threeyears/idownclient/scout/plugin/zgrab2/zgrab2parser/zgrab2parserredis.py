"""
parser redis
create by judy 2019/11/20
"""

import json
import os
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback.portinfo import (
    PortInfo, Redis)

from .zgrab2parserbase import Zgrab2ParserBase


class Zgrab2ParserRedis(Zgrab2ParserBase):
    """zgrab2 parser"""

    # _logger: MsLogger = MsLogManager.get_logger("Zgrab2Parserredis")

    def __init__(self):
        # self._name = type(self).__name__
        Zgrab2ParserBase.__init__(self)

    def parse_banner_redis(self, task: IscoutTask, level: int,
                           portinfo: PortInfo, resultfi: str):
        """
        Parse redis banner information
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

                        res = self._parse_redis(sj, task, level, portinfo)
                        # 如果成功了则证明已经将redis的信息解析出来了就不用再继续解析了
                        if res:
                            break
                    except Exception:
                        self._logger.error(
                            "Parse one redis banner json line error:\ntaskid:{}\nbatchid:{}\nresultfi:{}\nlinenum:{}"
                            .format(task.taskid, task.batchid, resultfi,
                                    linenum))
                    finally:
                        linenum += 1

        except Exception:
            self._logger.error(
                "Parse redis banner error:\ntaskid:{}\nbatchid:{}\nresultfi:{}"
                .format(task.taskid, task.batchid, resultfi))

    def _parse_redis(self, sj: dict, task: IscoutTask, level: int,
                     portinfo: PortInfo):
        """
        解析redis的banner和一些其他的信息
        总之就是port里的信息
        :param sj:
        :param task:
        :param level:
        :param portinfo:
        :return:
        """
        res = False
        if not sj.__contains__("data") or not sj["data"].__contains__("redis"):
            return
        try:
            sjredis = sj['data']['redis']
            succ = sjredis["status"]
            if succ != "success":
                return

            protocol = sjredis["protocol"]
            if protocol != "redis":
                return

            if portinfo.service != protocol:
                portinfo.service = protocol

            self._get_port_timestamp(sjredis, portinfo)

            # 开始构建redis的banner
            result = sjredis.get('result', {})
            rdata = Redis()
            rdata.info_response = result.pop('info_response', None)

            rdata.ping_response = result.pop('ping_response', None)
            portinfo.banner = rdata.build_banner()
            rdata.banner = portinfo.banner

            portinfo.version = result.pop('version')
            portinfo.os = result.pop('os')
            portinfo.extrainfo = json.dumps(result)
            res = True
            portinfo.set_redis(rdata)

        except:
            self._logger.error(
                f"Parse redis protocal error, err:{traceback.format_exc()}")
        return res
