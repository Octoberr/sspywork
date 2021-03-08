"""
parser smtp
create by judy 2019/11/21
"""

import json
import os
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask

from .....clientdatafeedback.scoutdatafeedback import SMTP, PortInfo
from .zgrab2parserbase import Zgrab2ParserBase
from .zgrab2parsertls import Zgrab2ParserTls


class Zgrab2ParserSMTP(Zgrab2ParserBase):
    """zgrab2 parser"""

    # _logger: MsLogger = MsLogManager.get_logger("Zgrab2ParserSMTP")

    def __init__(self):
        # self._name = type(self).__name__
        Zgrab2ParserBase.__init__(self)
        self._parser_tls = Zgrab2ParserTls()

    def parse_banner(self, task: IscoutTask, level: int, portinfo: PortInfo,
                     resultfi: str):
        """
        Parse smtp banner information
        """
        try:
            if not os.path.isfile(resultfi):
                self._logger.error(
                    f"Resultfi not exists:\ntaskid:{task.taskid}\nbatchid:{task.batchid}\nresultfi:{resultfi}"
                )
                return

            # its' one json object per line

            linenum = 1
            with open(resultfi, mode="r") as fs:
                while True:
                    try:
                        line = fs.readline()
                        if line is None or line == "":
                            break

                        sj = json.loads(line)
                        if sj is None:
                            continue

                        self._parse_smtp(sj, task, level, portinfo)

                        self._parse_tls(sj, task, level, portinfo)

                    except Exception:
                        self._logger.error(
                            "Parse one smtp banner json line error:\ntaskid:{}\nbatchid:{}\nresultfi:{}\nlinenum:{}"
                            .format(task.taskid, task.batchid, resultfi,
                                    linenum))
                    finally:
                        linenum += 1

        except Exception:
            self._logger.error(
                "Parse smtp banner error:\ntaskid:{}\nbatchid:{}\nresultfi:{}".
                format(task.taskid, task.batchid, resultfi))

    def _parse_smtp(self, sj: dict, task: IscoutTask, level: int,
                    portinfo: PortInfo):
        """
        解析smtp的banner和一些其他的信息
        总之就是port里的信息
        :param sj:
        :param task:
        :param level:
        :param portinfo:
        :return:
        """
        try:
            if not sj.__contains__("data") or not sj["data"].__contains__(
                    "smtp"):
                return

            if not isinstance(portinfo, PortInfo):
                self._logger.error("Invalid portinfo for smtp parse")
                return

            if (not sj.__contains__("data")
                    or not sj["data"].__contains__("smtp")
                    or not sj["data"]["smtp"].__contains__("status")
                    or not sj["data"]["smtp"].__contains__("result")):
                return

            result = sj["data"]["smtp"]["status"]
            if result != "success":
                return

            sjsmtp: dict = sj["data"]["smtp"]["result"]
            if sjsmtp is None:
                return

            self._get_port_timestamp(sj["data"]["smtp"], portinfo)

            banner = sjsmtp.get("banner")
            if banner is None or banner == "":
                return
            smtp = SMTP(banner)
            smtp.ehlo = sjsmtp.get("ehlo")
            smtp.starttls = sjsmtp.get("starttls")

            portinfo.banner = smtp.build_banner()
            portinfo.set_smtp(smtp)

        except:
            self._logger.error(
                f"Parse banner protocal error, err:{traceback.format_exc()}")

    def _parse_tls(self, sj: dict, task: IscoutTask, level: int,
                   portinfo: PortInfo):
        """parse smtp tls certificate"""
        try:

            if (not sj.__contains__("data")
                    or not sj["data"].__contains__("smtp")
                    or not sj["data"]["smtp"].__contains__("result")
                    or not sj["data"]["smtp"]["result"].__contains__("tls")
                    or not sj["data"]["smtp"]["result"]["tls"].__contains__(
                        "handshake_log")):
                return

            sjhandshake = sj["data"]["smtp"]["result"]["tls"]["handshake_log"]
            if sjhandshake is None or len(sjhandshake) < 1:
                return

            self._parser_tls._parse_cert(sjhandshake, portinfo)
        except Exception:
            self._logger.error(
                f"Parse banner protocal error, err:{traceback.format_exc()}")
