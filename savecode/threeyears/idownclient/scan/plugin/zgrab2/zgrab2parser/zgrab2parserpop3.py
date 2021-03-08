"""
parser pop3
create by judy 2019/11/19
"""

import json
import os
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscandataset.iscantask import IscanTask
from idownclient.clientdatafeedback.scoutdatafeedback.portinfo import (POP3,
                                                                       PortInfo
                                                                       )

from .zgrab2parserbase import Zgrab2ParserBase
from .zgrab2parsertls import Zgrab2ParserTls


class Zgrab2ParserPop3(Zgrab2ParserBase):
    """zgrab2 parser"""

    # _logger: MsLogger = MsLogManager.get_logger("Zgrab2Parserpop3")

    def __init__(self):
        # self._name = type(self).__name__
        Zgrab2ParserBase.__init__(self)
        self._parser_tls: Zgrab2ParserTls = Zgrab2ParserTls()

    def parse_banner_pop3(self, task: IscanTask, level: int, pinfo_dict, resultfi: str):
        """
        Parse pop3 banner information
        """
        try:
            if not os.path.isfile(resultfi):
                self._logger.error(
                    f"Resultfi not exists:\ntaskid:{task.taskid}\nresultfi:{resultfi}"
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
                        ip = sj.get('ip')
                        if ip is None or pinfo_dict.get(ip) is None:
                            self._logger.error("Unexpect error, cant get ip info from zgrab2 result")
                            continue
                        portinfo = pinfo_dict.get(ip)

                        res = self._parse_pop3(sj, task, level, portinfo)
                        # 如果成功了则证明已经将pop3的信息解析出来了就不用再继续解析了
                        if res:
                            break
                    except Exception:
                        self._logger.error(
                            "Parse one pop3 banner json line error:\ntaskid:{}\nresultfi:{}\nlinenum:{}"
                            .format(task.taskid, resultfi, linenum))
                    finally:
                        linenum += 1

        except Exception:
            self._logger.error(
                "Parse pop3 banner error:\ntaskid:{}\nresultfi:{}".
                format(task.taskid, resultfi))

    def _parse_pop3(self, sj: dict, task: IscanTask, level: int,
                    portinfo: PortInfo):
        """
        解析pop3的banner和一些其他的信息
        总之就是port里的信息
        :param sj:
        :param task:
        :param level:
        :param portinfo:
        :return:
        """
        res = False
        if not sj.__contains__("data") or not sj["data"].__contains__("pop3"):
            return
        try:
            sjpop3 = sj['data']['pop3']
            succ = sjpop3["status"]
            if succ != "success":
                return

            protocol = sjpop3["protocol"]
            if protocol != "pop3":
                return

            if portinfo.service != protocol:
                portinfo.service = protocol

            self._get_port_timestamp(sjpop3, portinfo)

            # 开始构建pop3的banner

            mres = sjpop3.get('result')
            if mres is None:
                return
            popdata = POP3()
            popdata.banner = mres.get('banner')

            popdata.noop = mres.get('noop')

            popdata.help = mres.get('help')

            popdata.starttls = mres.get('starttls')

            popdata.quit = mres.get('quit')

            portinfo.banner = popdata.build_banner()
            res = True
            # 开始解析tls
            sjtls = mres.get('tls')

            if sjtls is not None:
                sjhandshake = sjtls.get("handshake_log")
                if sjhandshake is None or len(sjhandshake) < 1:
                    return
                self._parser_tls._parse_cert(sjhandshake, portinfo)

            portinfo.set_pop3(popdata)

        except:
            self._logger.error(
                f"Parse pop3 protocal error, err:{traceback.format_exc()}")
        return res
