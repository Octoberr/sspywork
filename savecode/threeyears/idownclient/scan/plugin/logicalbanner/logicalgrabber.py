"""logical grabber"""

# -*- coding:utf-8 -*-

import IPy
import traceback
from commonbaby.helpers import helper_domain
from commonbaby.mslog import MsLogger, MsLogManager

from idownclient.clientdatafeedback.scoutdatafeedback.portinfo import PortInfo
from .joomlacareers import JoomlaCareers
from .logicalgrabberbase import LogicalGrabberBase
from .lotussmtp import LotusSmtp
from .wordpress import WordPress
from .CVE20209054 import CVE20209054
from .huaweihg532 import HuaweiHg532
from .weblogic_rce import WeblogicRCE
from .vmware_vcenter_server import VmwareVcenterServer

from .temporary import TempScan


class LogicalGrabber:
    """controller of all logical banner grabber"""

    def __init__(self) -> None:

        self._logger: MsLogger = MsLogManager.get_logger("LogicalGrabber")

        self._grabbers: dict = {}
        self.__init_logical_banner_grabbers()

    def __init_logical_banner_grabbers(self):

        self._grabbers[JoomlaCareers.vuln] = JoomlaCareers()
        self._grabbers[LotusSmtp.vuln] = LotusSmtp()
        self._grabbers[WordPress.vuln] = WordPress()
        self._grabbers[CVE20209054.vuln] = CVE20209054()
        self._grabbers[HuaweiHg532.vuln] = HuaweiHg532()
        self._grabbers[WeblogicRCE.vuln] = WeblogicRCE()
        self._grabbers[VmwareVcenterServer.vuln] = VmwareVcenterServer()


        self._grabbers[TempScan.vuln] = TempScan()
        # module = sys.modules[__package__]
        # pyclbr.readmodule(module)
        # md = module.__dict__
        # modules = [
        #     md[c] for c in md
        #     if (isinstance(md[c], type) and md[c].__module__ == module.__name__
        #         )
        # ]

        # clsmembers = inspect.getmembers(sys.modules[__package__], inspect.isclass)
        # clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        # clsmembers = inspect.getmembers(
        #     sys.modules[__package__],
        #     lambda o: inspect.isclass(
        #         o),  # and issubclass(o, LogicalBannerBase)
        # )
        # for clsname in clsmembers:
        #     grabber: LogicalBannerBase = clsname[1]()
        #     self._grabbers[grabber.__class__.__name__] = grabber

    def grabbanner(self, portinfo: PortInfo, vulns: list, flag, **kwargs):
        """
        漏洞匹配
        """

        callback = kwargs.get('callback')

        grabbers = []

        for vl in vulns:
            vuln = self._grabbers.get(vl)
            if vuln is not None:
                grabbers.append(vuln)

        if flag == 'iscout':
            if len(vulns) > 0:
                self._logger.info("Scout start scan vulns")
        else:
            if len(vulns) > 0:
                self._logger.info("Scan start scan vulns")
        # else:
        #     self._logger.info("How did that happen, unknown vuln flag")
        host = portinfo._host
        try:
            for grabber in grabbers:
                grabber: LogicalGrabberBase = grabber
                portinfo: PortInfo = portinfo
                if not grabber.match_service(portinfo.service):
                    continue

                domains = [d for d in portinfo.domains]
                if (
                        not helper_domain.is_valid_domain(host)
                        and isinstance(domains, list)
                        and len(domains) > 0
                ):
                    host = domains[0]
                else:
                    try:
                        ip = IPy.IP(host)
                    except Exception as ex:
                        pass
                    else:
                        port = portinfo._port
                        host = f"{host}:{port}"

                grabber.run_logic_grabber(host, portinfo, **kwargs)

        except Exception as ex:
            self._logger.error("Grab banner error: {}".format(traceback.format_exc()))
        finally:
            if callable(callback):
                callback(portinfo)