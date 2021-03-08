"""
parser zgrab2 ftp
by judy 19/11/26
"""
import json
import os
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscandataset.iscantask import IscanTask
from idownclient.clientdatafeedback.scoutdatafeedback.portinfo import (FTP,
                                                                       PortInfo
                                                                       )

from .zgrab2parserbase import Zgrab2ParserBase
from .zgrab2parsertls import Zgrab2ParserTls


class Zgrab2ParserFtp(Zgrab2ParserBase):
    """zgrab2 parser"""

    _logger: MsLogger = MsLogManager.get_logger("Zgrab2Parserftp")

    def __init__(self):
        Zgrab2ParserBase.__init__(self)
        self._parser_tls: Zgrab2ParserTls = Zgrab2ParserTls()

    def parse_banner_ftp(self, task: IscanTask, level: int, pinfo_dict, resultfi: str):
        """
        Parse ftp banner information
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

                        res = self._parse_ftp(sj, task, level, portinfo)
                        # 如果成功了则证明已经将ftp的信息解析出来了就不用再继续解析了
                        if res:
                            break
                    except Exception:
                        self._logger.error(
                            "Parse one ftp banner json line error:\ntaskid:{}\nresultfi:{}\nlinenum:{}"
                            .format(task.taskid, resultfi, linenum))
                    finally:
                        linenum += 1

        except Exception:
            self._logger.error(
                "Parse ftp banner error:\ntaskid:{}\nresultfi:{}".
                format(task.taskid, resultfi))

    def _parse_ftp(self, sj: dict, task: IscanTask, level: int,
                   portinfo: PortInfo):
        """
        解析ftp的banner和一些其他的信息
        总之就是port里的信息
        :param sj:
        :param task:
        :param level:
        :param portinfo:
        :return:
        """
        res = False
        if not sj.__contains__("data") or not sj["data"].__contains__("ftp"):
            return
        try:
            sjftp = sj['data']['ftp']
            succ = sjftp["status"]
            if succ != "success":
                return

            protocol = sjftp["protocol"]
            if protocol != "ftp":
                return

            if portinfo.service != protocol:
                portinfo.service = protocol

            self._get_port_timestamp(sjftp, portinfo)

            # 开始构建ftp的banner

            mres = sjftp.get('result')
            if mres is None:
                return
            fdata = FTP()

            banr = mres.get('banner')
            fdata.banner = banr
            auth_tls = mres.get('auth_tls')
            fdata.auth_tls = auth_tls
            portinfo.banner = fdata.build_banner()
            res = True
            # 开始解析tls
            sjtls = mres.get('tls')
            if sjtls is not None:
                sjhandshake = sjtls.get("handshake_log")
                if sjhandshake is None or len(sjhandshake) < 1:
                    return
                self._parser_tls._parse_cert(sjhandshake, portinfo)
            portinfo.set_ftp(fdata)

        except:
            self._logger.error(
                f"Parse ftp protocal error, err:{traceback.format_exc()}")
        return res
