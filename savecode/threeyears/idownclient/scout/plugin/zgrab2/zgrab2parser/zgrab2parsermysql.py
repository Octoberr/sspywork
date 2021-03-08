"""
parser mysql
create by judy 2019/11/21
"""

import json
import os
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscoutdataset.iscouttask import IscoutTask

from .....clientdatafeedback.scoutdatafeedback import MySql, PortInfo
from .zgrab2parserbase import Zgrab2ParserBase
from .zgrab2parsertls import Zgrab2ParserTls


class Zgrab2ParserMySql(Zgrab2ParserBase):
    """zgrab2 parser"""

    # _logger: MsLogger = MsLogManager.get_logger("Zgrab2ParserMySql")

    def __init__(self):
        # self._name = type(self).__name__
        Zgrab2ParserBase.__init__(self)
        self._parser_tls = Zgrab2ParserTls()

    def parse_banner(self, task: IscoutTask, level: int, portinfo: PortInfo,
                     resultfi: str):
        """
        Parse mysql banner information
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

                        self._parse_mysql(sj, task, level, portinfo)

                        self._parse_tls(sj, task, level, portinfo)

                    except Exception:
                        self._logger.error(
                            "Parse one mysql banner json line error:\ntaskid:{}\nbatchid:{}\nresultfi:{}\nlinenum:{}"
                            .format(task.taskid, task.batchid, resultfi,
                                    linenum))
                    finally:
                        linenum += 1

        except Exception:
            self._logger.error(
                "Parse mysql banner error:\ntaskid:{}\nbatchid:{}\nresultfi:{}"
                .format(task.taskid, task.batchid, resultfi))

    def _parse_mysql(self, sj: dict, task: IscoutTask, level: int,
                     portinfo: PortInfo):
        """
        解析 mysql 的banner和一些其他的信息
        总之就是port里的信息
        :param sj:
        :param task:
        :param level:
        :param portinfo:
        :return:
        """
        try:
            # zgrab2 mysql result field is 'mssql'
            if not sj.__contains__("data") or not sj["data"].__contains__(
                    "mssql"):
                return

            if not isinstance(portinfo, PortInfo):
                self._logger.error("Invalid portinfo for mysql parse")
                return

            if (not sj.__contains__("data")
                    or not sj["data"].__contains__("mssql")
                    or not sj["data"]["mssql"].__contains__("status")
                    or not sj["data"]["mssql"].__contains__("result")):
                return

            # do not check mysql status
            # result = sj["data"]["mysql"]["status"]
            # if result != "success":
            #     return

            sjmysql: dict = sj["data"]["mssql"]["result"]
            if sjmysql is None:
                return

            self._get_port_timestamp(sj["data"]["mssql"], portinfo)

            mysql = MySql()

            mysql.protocol_version = sjmysql.get("protocol_version")
            mysql.server_version = sjmysql.get("server_version")
            mysql._errormsg = sjmysql.get("error_message")

            if (sjmysql.__contains__("status_flags")
                    and not sjmysql["status_flags"] is None):
                for k, v in sjmysql["status_flags"].items():
                    mysql.set_status_flag(k, v)

            if (sjmysql.__contains__("capability_flags")
                    and not sjmysql["capability_flags"] is None):
                for k, v in sjmysql["capability_flags"].items():
                    mysql.set_capability_flag(k, v)

            portinfo.banner = mysql.build_banner()
            portinfo.set_mysql(mysql)

        except:
            self._logger.error(
                f"Parse banner protocal error, err:{traceback.format_exc()}")

    def _parse_tls(self, sj: dict, task: IscoutTask, level: int,
                   portinfo: PortInfo):
        """parse mssql tls certificate"""
        try:

            if (not sj.__contains__("data")
                    or not sj["data"].__contains__("mssql")
                    or not sj["data"]["mssql"].__contains__("result")
                    or not sj["data"]["mssql"]["result"].__contains__("tls")
                    or not sj["data"]["mssql"]["result"]["tls"].__contains__(
                        "handshake_log")):
                return

            sjhandshake = sj["data"]["mssql"]["result"]["tls"]["handshake_log"]
            if sjhandshake is None or len(sjhandshake) < 1:
                return

            self._parser_tls._parse_cert(sjhandshake, portinfo)
        except Exception:
            self._logger.error(
                f"Parse banner protocal error, err:{traceback.format_exc()}")
