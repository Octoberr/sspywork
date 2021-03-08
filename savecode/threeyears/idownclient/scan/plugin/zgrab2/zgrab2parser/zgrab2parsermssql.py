"""
parser mssql
create by judy 2019/11/19
"""
import json
import os
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.iscandataset.iscantask import IscanTask
from idownclient.clientdatafeedback.scoutdatafeedback.portinfo import (Mssql,
                                                                       PortInfo
                                                                       )

from .zgrab2parserbase import Zgrab2ParserBase
from .zgrab2parsertls import Zgrab2ParserTls


class Zgrab2ParserMssql(Zgrab2ParserBase):
    """zgrab2 parser"""

    # _logger: MsLogger = MsLogManager.get_logger("Zgrab2Parsermssql")

    def __init__(self):
        # self._name = type(self).__name__
        Zgrab2ParserBase.__init__(self)
        self._parser_tls: Zgrab2ParserTls = Zgrab2ParserTls()

    def parse_banner_mssql(self, task: IscanTask, level: int, pinfo_dict, resultfi: str):
        """
        Parse mssql banner information
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
                        # 这个暂时没有使用
                        res = self._parse_mssql(sj, task, level, portinfo)
                        # 如果成功了则证明已经将mssql的信息解析出来了就不用再继续解析了
                        if res:
                            break
                    except Exception:
                        self._logger.error(
                            "Parse one mssql banner json line error:\ntaskid:{}\nresultfi:{}\nlinenum:{}"
                            .format(task.taskid, resultfi, linenum))
                    finally:
                        linenum += 1

        except Exception:
            self._logger.error(
                "Parse mssql banner error:\ntaskid:{}\nresultfi:{}"
                .format(task.taskid, resultfi))

    def _parse_mssql(self, sj: dict, task: IscanTask, level: int,
                     portinfo: PortInfo):
        """
        解析mssql的banner和一些其他的信息

        暂时未使用

        :param sj:
        :param task:
        :param level:
        :param portinfo:
        :return:
        """
        res = False
        if not sj.__contains__("data") or not sj["data"].__contains__("mssql"):
            return
        try:
            sjmssql = sj['data']['mssql']
            succ = sjmssql["status"]
            if succ != "success":
                return

            protocol = sjmssql["protocol"]
            if protocol != "mssql":
                return

            if portinfo.service != protocol:
                portinfo.service = protocol

            self._get_port_timestamp(sjmssql, portinfo)

            # 开始构建mssql的banner
            msdata = Mssql()
            mres = sjmssql.get('result')
            if mres is None:
                return
            # 就只构建有的吧，模仿的shodan的https://www.shodan.io/host/119.18.55.104

            instancename = mres.get('instance_name', '')
            msdata.instance_name = instancename
            msdata.version = mres.get('version')
            portinfo.banner = msdata.build_banner()
            msdata.banner = portinfo.banner
            res = True
            # 开始解析tls
            sjtls = mres.pop('tls', None)
            portinfo.extrainfo = json.dumps(mres)

            if sjtls is not None:
                sjhandshake = sjtls.get("handshake_log")
                if sjhandshake is None or len(sjhandshake) < 1:
                    return
                self._parser_tls._parse_cert(sjhandshake, portinfo)
            portinfo.set_mssql(msdata)

        except:
            self._logger.error(
                f"Parse mssql protocal error, err:{traceback.format_exc()}")
        return res
