"""
parser imap
create by judy 2019/11/19
"""

import json
import os
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscandataset.iscantask import IscanTask
from idownclient.clientdatafeedback.scoutdatafeedback.portinfo import (Imap,
                                                                       PortInfo
                                                                       )

from .zgrab2parserbase import Zgrab2ParserBase
from .zgrab2parsertls import Zgrab2ParserTls


class Zgrab2ParserImap(Zgrab2ParserBase):
    """zgrab2 parser"""

    # _logger: MsLogger = MsLogManager.get_logger("Zgrab2Parserimap")

    def __init__(self):
        # self._name = type(self).__name__
        Zgrab2ParserBase.__init__(self)
        self._parser_tls: Zgrab2ParserTls = Zgrab2ParserTls()

    def parse_banner_imap(self, task: IscanTask, level: int, pinfo_dict, resultfi: str):
        """
        Parse imap banner information
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

                        res = self._parse_imap(sj, task, level, portinfo)
                        # 如果成功了则证明已经将imap的信息解析出来了就不用再继续解析了
                        if res:
                            # 解析ssl
                            break
                    except Exception:
                        self._logger.error(
                            "Parse one imap banner json line error:\ntaskid:{}\nresultfi:{}\nlinenum:{}"
                            .format(task.taskid, task.batchid, resultfi, linenum))
                    finally:
                        linenum += 1

        except Exception:
            self._logger.error(
                "Parse imap banner error:\ntaskid:{}\nresultfi:{}".
                format(task.taskid, task.batchid, resultfi))

    def _parse_imap(self, sj: dict, task: IscanTask, level: int,
                    portinfo: PortInfo):
        """
        解析imap的banner和一些其他的信息
        总之就是port里的信息
        :param sj:
        :param task:
        :param level:
        :param portinfo:
        :return:
        """
        res = False
        if not sj.__contains__("data") or not sj["data"].__contains__("imap"):
            return
        try:
            sjimap = sj['data']['imap']
            succ = sjimap["status"]
            if succ != "success":
                return

            protocol = sjimap["protocol"]
            if protocol != "imap":
                return

            if portinfo.service != protocol:
                portinfo.service = protocol

            self._get_port_timestamp(sjimap, portinfo)

            # 开始构建imap的banner

            mres = sjimap.get('result')
            if mres is None:
                return
            idata = Imap()
            idata.banner = mres.get('banner')
            idata.starttls = mres.get('starttls')

            idata.close = mres.get('close')

            portinfo.banner = idata.build_banner()
            res = True
            # 开始解析tls
            sjtls = mres.get('tls')
            if sjtls is not None:
                sjhandshake = sjtls.get("handshake_log")
                if sjhandshake is None or len(sjhandshake) < 1:
                    return
                self._parser_tls._parse_cert(sjhandshake, portinfo)

            portinfo.set_imap(idata)
        except:
            self._logger.error(
                f"Parse imap protocal error, err:{traceback.format_exc()}")
        return res
