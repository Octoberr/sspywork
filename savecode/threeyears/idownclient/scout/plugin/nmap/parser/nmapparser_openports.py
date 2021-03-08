"""nmap parser"""

# -*- coding:utf-8 -*-

import traceback

from idownclient.clientdatafeedback.scoutdatafeedback.portinfo.ubiquiti import Ubiquiti 
from commonbaby.mslog import MsLogger, MsLogManager
from lxml import etree

from datacontract.iscoutdataset.iscouttask import IscoutTask
from .....clientdatafeedback.scoutdatafeedback import PortInfo


class NmapParserOpenPorts:
    """NmapParserOpenPorts"""

    _logger: MsLogger = MsLogManager.get_logger("NmapParser")

    def __init__(self):
        self._name = type(self).__name__

    @classmethod
    def parse_open_ports(cls, task: IscoutTask, level: int,
                         nmap_result_fi: str) -> iter:
        """yield Port"""
        try:
            doc: etree._ElementTree = etree.parse(nmap_result_fi)
            # xroot: minidom.Document = doc.documentElement
            xroot: etree._Element = doc.getroot()
            xhosts = xroot.findall("host")
            for xhost in xhosts:
                xhost: etree._Element = xhost
                if xhost is None:
                    continue
                # get opening ports
                for port in cls._get_ports(xhost, task, level):
                    if not isinstance(port, PortInfo):
                        continue

                    yield port

        except Exception:
            cls._logger.error("Parse Nmap result error: {}".format(
                traceback.format_exc()))

    @classmethod
    def _get_ports(cls, xhost: etree._Element, task: IscoutTask,
                   level: int) -> iter:
        """parse xml, yield return PortInfo"""

        # get ip address
        ip, iptype = cls._get_ip(xhost)
        if not isinstance(ip, str) or ip == '' or not isinstance(
                iptype, str) or iptype == '':
            return

        # hostnames
        hostnames: list = cls._get_hostnames(xhost)

        # os
        os, oscpe = cls._get_os(xhost)

        # uptime
        xuptime = xhost.get('uptime')
        uptime: int = None
        if not xuptime is None:
            seconds = xuptime.get('seconds')
            if not seconds is None:
                try:
                    uptime = int(seconds)
                except Exception:
                    pass

        # open ports
        xports = xhost.findall("ports/port")
        if xports is None or len(xports) < 1:
            return
        for xp in xports:
            try:
                if not cls._check_port_open(xp):
                    continue

                transprotocol = xp.get("protocol")
                port: int = int(xp.get("portid").strip())

                portinfo: PortInfo = PortInfo(task, level, ip, port,
                                              transprotocol)
                portinfo.set_ips(ip)
                if not os is None and not os == "":
                    portinfo.os = os
                if not oscpe is None and len(oscpe) > 0:
                    portinfo.set_cpe(*oscpe)
                if not uptime is None:
                    portinfo.uptime = uptime
                portinfo.set_domain(*hostnames)

                xservice = xp.find('service')
                if not xservice is None:
                    cls._get_port_service(xp, portinfo)

                yield portinfo

            except Exception:
                cls._logger.debug("Get ports warn: {}".format(
                    traceback.format_exc()))

    @classmethod
    def _get_ip(cls, xhost: etree._Element) -> (str, str):
        """Get and return ip address from a nmap result xml 'host' section.
        return: (ip, iptype)
        iptype: ipv4/ipv6"""
        ipaddr = None
        iptype = None
        if xhost is None:
            return
        xaddrs = xhost.findall("address")
        if xaddrs is None or len(xaddrs) < 1:
            return
        for xaddr in xaddrs:
            # get ip address type from the ipaddr type attribute
            xiptp = xaddr.get("addrtype")
            if not isinstance(
                    xiptp, str) or xiptp == '' or not xiptp.startswith('ip'):
                continue
            iptype = xiptp
            # get ip address from the ipaddr attribute
            xip = xaddr.get("addr")
            if not isinstance(xip, str) or xip is None or xip == '':
                return
            ipaddr = xip

        return (ipaddr, iptype)

    @classmethod
    def _get_hostnames(cls, xhost: etree._Element) -> list:
        """返回当前主机的hostnames列表"""
        res: list = []
        try:
            if xhost is None:
                return res

            xhostnames = xhost.findall('hostnames/hostname')
            if xhostnames is None or len(xhostnames) < 1:
                return res

            for xhostname in xhostnames:
                hostname = xhostname.get('name')
                if not isinstance(hostname, str) or hostname == "":
                    continue
                if not hostname in res:
                    res.append(hostname)

        except Exception:
            cls._logger.debug("Get hostnames error:{}".format(
                traceback.format_exc()))
        return res

    @classmethod
    def _get_os(cls, xhost: etree._Element) -> (str, list):
        """get os type/name/version/cpe\n
        return (osname, list(cpes))"""
        xosmatches = xhost.findall('os/osmatch')
        if xosmatches is None or len(xosmatches) < 1:
            return (None, None)

        cpes: list = []
        xosmatch = None
        curracuracy = 0
        for xm in xosmatches:
            # sort by accuracy
            try:

                # get the most accurate osname
                accuracy = int(xm.get('accuracy'))
                if accuracy > curracuracy:
                    curracuracy = accuracy
                    xosmatch = xm

                # get all cpes
                xcpes = xm.findall('osclass/cpe')
                if xcpes is None or len(xcpes) < 1:
                    continue
                for xcpe in xcpes:
                    if not xcpe.text in cpes:
                        cpes.append(xcpe.text)

            except Exception:
                pass

        if xosmatch is None:
            return (None, None)

        name: str = xosmatch.get('name')
        if not isinstance(name, str) or name == "":
            return (None, None)

        return (name, cpes)

    @classmethod
    def _check_port_open(cls, xport: etree._Element) -> bool:
        """<port... <state state="open" ...
        To check the xml document if the port's state is open."""
        res = False
        if xport is None:
            return res
        xstate: etree._Element = xport.find("state")
        if xstate is None:
            return res
        astate = xstate.get("state")
        if astate is None or astate == '' or astate != 'open':
            return res
        res = True
        return res

    @classmethod
    def _get_port_service(cls, xp: etree._Element, portinfo: PortInfo):
        """xp: xmlelement_port\n
        get:
        service name/product/product version/extrainfo/devicetype"""
        xservice = xp.find('service')
        if xservice is None:
            return
        service: str = xservice.get('name')
        if isinstance(service, str) and service != "":
            portinfo.service = service
        product: str = xservice.get('product')
        if isinstance(product, str) and product != "":
            portinfo.app = product
        version: str = xservice.get('version')
        if isinstance(version, str) and version != "":
            portinfo.version = version
        extrainfo: str = xservice.get('extrainfo')
        if isinstance(extrainfo, str) and extrainfo != "":
            portinfo.extrainfo += extrainfo
        devicetype = xservice.get('devicetype')
        if isinstance(devicetype, str) and devicetype != "":
            portinfo.device = devicetype
        # get cpe for service
        xcpe: str = xservice.find('cpe')
        if not xcpe is None:
            portinfo.set_cpe(xcpe.text)

    @classmethod
    def parse_udp_10001(cls, task: IscoutTask, level: int, nmap_result_fi: str):
        """yield Port"""
        try:
            doc: etree._ElementTree = etree.parse(nmap_result_fi)
            infos: list = doc.xpath('//ports/port/script')
            for info in infos:
                res = info.xpath('elem[@key="hostname"]')
                if info is None or len(res) == 0:
                    continue
                port = cls._get_udp_10001_portinfo(info, task, level)
                if not isinstance(port, PortInfo):
                    continue
                yield port
        except Exception:
            cls._logger.error("Parse Nmap result error: {}".format(traceback.format_exc()))

    @classmethod
    def _get_udp_10001_portinfo(cls, info: etree._Element, task: IscoutTask, level: int) -> iter:
        try:
            # 1: hostname
            hostname = cls._get_udp_10001_hostname(info=info)

            # 2: product
            product = cls._get_udp_10001_product(info=info)

            # 3: version
            version = cls._get_udp_10001_version(info=info)

            # 4: ip
            # 5: mac
            # 6: alternate_ip
            # 7: alternate_mac
            ip, mac, alternate_ip, alternate_mac = cls._get_udp_10001_ip_mac(info=info)

            port: int = 10001
            transprotocol = 'udp'
            portinfo: PortInfo = PortInfo(task, level, ip, port, transprotocol)

            ubiquiti = Ubiquiti()
            ubiquiti.hostname = hostname
            ubiquiti.product = product
            ubiquiti.version = version
            ubiquiti.ip = ip
            ubiquiti.mac = mac
            ubiquiti.alternate_ip = alternate_ip
            ubiquiti.alternate_mac = alternate_mac

            portinfo.service = 'ubiquiti-discovery'
            portinfo.banner = ubiquiti.build_banner()
            portinfo.set_ubiquiti(ubiquiti)

            return portinfo
        except Exception:
            cls._logger.error("Parse udp 10001 result error: {}".format(traceback.format_exc()))

    @classmethod
    def _get_udp_10001_hostname(cls, info: etree._Element):
        hostname = info.xpath('elem[@key="hostname"]')[0].text
        return hostname

    @classmethod
    def _get_udp_10001_product(cls, info: etree._Element):
        product = info.xpath('elem[@key="product"]')[0].text
        return product

    @classmethod
    def _get_udp_10001_version(cls, info: etree._Element):
        version = info.xpath('elem[@key="firmware"]')[0].text
        return version

    @classmethod
    def _get_udp_10001_ip_mac(cls, info: etree._Element):
        addreses = info.xpath('./table')[0].getchildren()

        addreses_length = len(addreses)

        mac = ''
        ip = ''
        alternate_mac = ''
        alternate_ip = ''

        if (addreses_length <= 0):
            return ('', '', '', '')
        elif (addreses_length == 1):
            mac = addreses[0].get('key')
            ip = addreses[0].getchildren()[0].text
        else:
            mac = addreses[0].get('key')
            ip = addreses[0].getchildren()[0].text
            alternate_mac = addreses[1].get('key')
            alternate_ip = addreses[1].getchildren()[0].text

        return (ip, mac, alternate_ip, alternate_mac)
