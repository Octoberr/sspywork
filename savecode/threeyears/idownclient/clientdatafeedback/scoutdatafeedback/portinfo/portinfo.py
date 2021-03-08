"""represents a portinfo"""

# -*- coding:utf-8 -*-

from idownclient.clientdatafeedback.scoutdatafeedback.portinfo.weblogic_t3 import WeblogicT3
from idownclient.clientdatafeedback.scoutdatafeedback.portinfo import weblogic_t3
import threading

from datacontract.iscoutdataset.iscouttask import IscoutTask
from .ftp import FTP
from .imap import Imap
from .mongodb import MongoDB
from .mssql import Mssql
from .mysql import MySql
from .ntp import Ntp
from .pop3 import POP3
from .redis import Redis
from .siteinfo import SiteInfo
from .smtp import SMTP
from .sshinfo import SshInfo
from .sslcert import SslCert, Certificate
from .telnet import Telnet
from .ubiquiti import Ubiquiti


class PortInfo(object):
    """represents a portinfo.\n
    此数据包含banner信息、service运行服务信息和SSL证书信息。\n
    task: IScoutTask\n
    level: the recursion level\n
    host: 当前端口所属主机，可以为单个IP或单个域名\n
    port: int 当前端口\n
    transport: str 传输层协议"""

    @property
    def ips(self) -> iter:
        """extra field, used to save the ips that belongs to the current device"""
        with self.__ips_locker:
            for ip in self.__ips:
                yield ip

    def set_ips(self, *ips):
        """extra field, used to save the ips that belongs to the current device"""
        with self.__ips_locker:
            for ip in ips:
                if not ip in self.__ips:
                    self.__ips.append(ip)

    def __init__(self,
                 task: IscoutTask,
                 level: int,
                 host: str,
                 port: int,
                 transport: str = "tcp"):
        # 这个task需要
        # if not isinstance(task, IscoutTask):
        #     raise Exception("Invalid iscouttask")
        if not isinstance(level, int):
            raise Exception("Invalid level")
        if not isinstance(host, str) or host == "":
            raise Exception("Invalid host")
        if not isinstance(port, int) or port < 0 or port > 65535:
            raise Exception("Invalid port for PortInfo")
        if not transport in ["tcp", "udp"]:
            raise Exception("Invalid transport protocol for PortInfo")

        self._task: IscoutTask = task
        self._level: int = level

        # current fields
        self._host: str = host
        self._port: int = port
        self._transport: str = transport

        # extra field, used to save the ips that belongs to the current device
        self.__ips: list = []
        self.__ips_locker = threading.RLock()

        self._timestamp: str = None
        self._service: str = None
        self._app: str = None
        self._banner: str = ""

        self.__cpe: dict = {}
        self.__cpe_locker = threading.RLock()

        self.__tags: dict = {}
        self.__tags_locker = threading.RLock()

        self.__hostnames: dict = {}
        self.__hostnames_locker = threading.RLock()

        self.__domains: dict = {}
        self.__domains_locker = threading.RLock()

        self._link: str = None
        self._uptime: float = None
        self._device: str = None
        self._extrainfo: str = ""  # this should initialize to ''
        self._version: str = None
        self._os: str = None

        self.__sslinfo: dict = {}
        self.__sslinfo_locker = threading.RLock()

        self.__siteinfo: dict = {}
        self.__siteinfo_locker = threading.RLock()

        self.__sshinfo: dict = {}
        self.__sshinfo_locker = threading.RLock()

        self.__opts_telnet: dict = {}
        self.__opts_telnet_locker = threading.RLock()

        self.__ftpinfo: dict = {}
        self.__ftpinfo_locker = threading.RLock()

        self.__imapinfo: dict = {}
        self.__imapinfo_locker = threading.RLock()

        self.__pop3info: dict = {}
        self.__pop3info_locker = threading.RLock()

        self.__smtpinfo: dict = {}
        self.__smtpinfo_locker = threading.RLock()

        self.__ntp: dict = {}
        self.__ntp_locker = threading.RLock()

        self.__redis: dict = {}
        self.__redis_locker = threading.RLock()

        self.__mongodb: dict = {}
        self.__mongodb_locker = threading.RLock()

        self.__mssql: dict = {}
        self.__mssql_locker = threading.RLock()

        self.__mysql: dict = {}
        self.__mysql_locker = threading.RLock()

        self.__oracle: dict = {}
        self.__oracle_locker = threading.RLock()

        self.__ubiquiti: dict = {}
        self.__ubiquiti_locker = threading.RLock()

        self.__weblogic_t3: dict = {}
        self.__weblogic_t3_locker = threading.RLock()

    #######################################
    # 单独计算此数据长度

    def __len__(self):
        # 这样写要不得吧。。。性能消耗太大了？
        # 但有没有其他比如 无锁资源竞争 的方式来搞？。。
        res = 1  # 当前数据自带1长度
        with self.__sslinfo_locker:
            res += len(self.__sslinfo)
        with self.__siteinfo_locker:
            res += len(self.__siteinfo)
        with self.__sshinfo_locker:
            res += len(self.__sshinfo)
        with self.__opts_telnet_locker:
            res += len(self.__opts_telnet)
        with self.__ftpinfo_locker:
            res += len(self.__ftpinfo)
        with self.__imapinfo_locker:
            res += len(self.__imapinfo)
        with self.__pop3info_locker:
            res += len(self.__pop3info)
        with self.__smtpinfo_locker:
            res += len(self.__smtpinfo)
        with self.__ntp_locker:
            res += len(self.__ntp)
        with self.__redis_locker:
            res += len(self.__redis)
        with self.__mongodb_locker:
            res += len(self.__mongodb)
        with self.__mssql_locker:
            res += len(self.__mssql)
        with self.__mysql_locker:
            res += len(self.__mysql)
        with self.__oracle_locker:
            res += len(self.__oracle)
        with self.__ubiquiti_locker:
            res += len(self.__ubiquiti)
        with self.__weblogic_t3_locker:
            res += len(self.__weblogic_t3)
        return res

    #######################################
    # properties/set sub datas
    # 新增一个如果ssl 并且端口是http的那么就修改为https
    @property
    def ssl_flag(self) -> bool:
        """
        当前服务有没有ssl
        """
        flag = False
        if len(self.__sslinfo) > 0:
            flag = True
        return flag

    @property
    def timestamp(self) -> str:
        """当前数据被扫描到的时间"""
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        """当前数据被扫描到的时间"""
        if not isinstance(value, str) or value == "":
            raise Exception("Invalid timestamp")
        self._timestamp = value

    @property
    def service(self) -> str:
        """当前端口开放的服务"""
        return self._service

    @service.setter
    def service(self, value):
        """当前端口开放的服务"""
        if not isinstance(value, str) or value == "":
            # raise Exception("Invalid service")
            return
        self._service = value

    @property
    def app(self) -> str:
        """当前端口运行的app"""
        return self._app

    @app.setter
    def app(self, value):
        """当前端口运行的app"""
        if not isinstance(value, str) or value == "":
            # raise Exception("Invalid app")
            return
        self._app = value

    @property
    def banner(self) -> str:
        """当前端口采集到的banner"""
        return self._banner

    @banner.setter
    def banner(self, value):
        """当前端口采集到的banner"""
        if not isinstance(value, str) or value == "":
            # raise Exception("Invalid banner")
            return
        self._banner = self._banner.strip() + "\n\n" + value

    @property
    def cpes(self) -> iter:
        """yield cpe"""
        with self.__cpe_locker:
            for c in self.__cpe:
                yield c

    def set_cpe(self, *cpes):
        """设置当前端口的cpe 公开平台枚举"""
        with self.__cpe_locker:
            for cpe in cpes:
                if not isinstance(cpe, str) or cpe == "":
                    continue
                self.__cpe[cpe] = cpe

    @property
    def tags(self) -> iter:
        """yield tags"""
        with self.__tags_locker:
            for t in self.__tags:
                yield t

    def set_tag(self, *tags):
        """设置当前端口的 设备用途描述标签"""

        with self.__tags_locker:
            for tag in tags:
                if not isinstance(tag, str) or tag == "":
                    continue
                self.__tags[tag] = tag

    @property
    def hostnames(self) -> iter:
        """yield hostnames"""
        with self.__hostnames_locker:
            for h in self.__hostnames:
                yield h

    def set_hostname(self, *hostnames):
        """设置当前端口的 主机名"""
        with self.__hostnames_locker:
            for hostname in hostnames:
                if not isinstance(hostname, str) or hostname == "":
                    continue
                self.__hostnames[hostname] = hostname

    @property
    def domains(self) -> iter:
        with self.__domains_locker:
            for d in self.__domains:
                yield d

    def set_domain(self, *domains):
        """设置当前端口的 域名"""
        with self.__domains_locker:
            for domain in domains:
                if not isinstance(domain, str) or domain == "":
                    return
                self.__domains[domain] = domain

    @property
    def link(self) -> str:
        """当前端口的网络连接类型，Ethernet or moderm"""
        return self._link

    @link.setter
    def link(self, value):
        """当前端口的网络连接类型，Ethernet or moderm"""
        if not isinstance(value, str) or value == "":
            # raise Exception("Invalid link")
            return
        self._link = value

    @property
    def uptime(self) -> float:
        """主机运行时长，单位秒"""
        return self._uptime

    @uptime.setter
    def uptime(self, value):
        """主机运行时长，单位秒"""
        if not type(value) in [int, float]:
            # raise Exception("Invalid uptime")
            return
        self._uptime = value

    @property
    def device(self) -> str:
        """当前端口所在设备的 主机设备类型，shodan叫devicetype"""
        return self._device

    @device.setter
    def device(self, value):
        """当前端口所在设备的 主机设备类型，shodan叫devicetype"""
        if not isinstance(value, str) or value == "":
            # raise Exception("Invalid device")
            return
        self._device = value

    @property
    def extrainfo(self) -> str:
        """当前端口所主机的额外信息，shodan的devicetype"""
        return self._extrainfo

    @extrainfo.setter
    def extrainfo(self, value):
        """当前端口所主机的额外信息，shodan的devicetype"""
        if not isinstance(value, str) or value == "":
            # raise Exception("Invalid extrainfo")
            return
        self._extrainfo = value

    @property
    def version(self) -> str:
        """该端口下 app的版本"""
        return self._version

    @version.setter
    def version(self, value):
        """该端口下 app的版本"""
        if not isinstance(value, str) or value == "":
            # raise Exception("Invalid version")
            return
        self._version = value

    @property
    def os(self) -> str:
        """该端口下的 os 操作系统"""
        return self._os

    @os.setter
    def os(self, value):
        """该端口下的 os 操作系统"""
        if not isinstance(value, str) or value == "":
            # raise Exception("Invalid os")
            return
        self._os = value

    @property
    def siteinfos(self) -> iter:
        """yield siteinfos"""
        with self.__siteinfo_locker:
            for s in self.__siteinfo.values():
                yield s

    def set_siteinfo(self, *siteinfos: SiteInfo):
        """添加当前端口的网站信息"""
        with self.__siteinfo_locker:
            for siteinfo in siteinfos:
                if not isinstance(siteinfo, SiteInfo):
                    # raise Exception("Invalid SiteInfo")
                    return
                self.__siteinfo[siteinfo._site] = siteinfo

    def set_sslinfo(self, sslcert: SslCert):
        """add ssl cert info"""
        if not isinstance(sslcert, SslCert):
            return
        if not isinstance(sslcert._cert, Certificate):
            return
        if self.__sslinfo.__contains__(sslcert._cert._serialnum):
            return
        with self.__sslinfo_locker:
            if self.__sslinfo.__contains__(sslcert._cert._serialnum):
                return
            self.__sslinfo[sslcert._cert._serialnum] = sslcert

    def sslcert_contains_serialnum(self, serialnum: str) -> bool:
        """return whether the certificate list contains given serialnumber"""
        if not isinstance(serialnum, str) or serialnum == "":
            raise Exception("Invalid serial number for sslcert contains check")
        return self.__sslinfo.__contains__(serialnum)

    def set_sshinfo(self, ssh: SshInfo):
        if not isinstance(ssh, SshInfo):
            return
        if self.__sshinfo.__contains__(ssh._server_id + ssh._type +
                                       ssh._server_key):
            return
        with self.__sshinfo_locker:
            if self.__sshinfo.__contains__(ssh._server_id + ssh._type +
                                           ssh._server_key):
                return
            self.__sshinfo[ssh._server_id + ssh._type + ssh._server_key] = ssh

    def set_smtp(self, smtp: SMTP):
        if not isinstance(smtp, SMTP):
            return
        # same host, same port, filter duplicated SMTP service
        if self.__smtpinfo.__contains__(smtp._banner):
            return
        with self.__smtpinfo_locker:
            if self.__smtpinfo.__contains__(smtp._banner):
                return
            self.__smtpinfo[smtp._banner] = smtp

    def set_mysql(self, mysql: MySql):
        if not isinstance(mysql, MySql):
            return
        # use host+port for filter here
        key = self._host + ":" + str(self._port)
        if self.__mysql.__contains__(key):
            return
        with self.__mysql_locker:
            if self.__mysql.__contains__(key):
                return
            self.__mysql[key] = mysql

    def set_oracle(self, oracle_banner: str):
        if not isinstance(oracle_banner, str) or oracle_banner == "":
            return
        if self.__oracle.__contains__(oracle_banner):
            return
        with self.__oracle_locker:
            if self.__oracle.__contains__(oracle_banner):
                return
            self.__oracle[oracle_banner] = None

    def set_mongodb(self, mongodb: MongoDB):
        if not isinstance(mongodb, MongoDB):
            return
        if self.__mongodb.__contains__(mongodb.banner):
            return
        with self.__mongodb_locker:
            self.__mongodb[mongodb.banner] = mongodb

    def set_redis(self, redis: Redis):
        if not isinstance(redis, Redis):
            return
        if self.__redis.__contains__(redis.banner):
            return
        with self.__redis_locker:
            self.__redis[redis.banner] = redis

    def set_ftp(self, ftp: FTP):
        if not isinstance(ftp, FTP):
            return
        if self.__ftpinfo.__contains__(ftp.banner):
            return
        with self.__ftpinfo_locker:
            self.__ftpinfo[ftp.banner] = ftp

    def set_imap(self, imap: Imap):
        if not isinstance(imap, Imap):
            return
        if self.__imapinfo.__contains__(imap.banner):
            return
        with self.__imapinfo_locker:
            self.__imapinfo[imap.banner] = imap

    def set_mssql(self, mssql: Mssql):
        if not isinstance(mssql, Mssql):
            return
        if self.__mssql.__contains__(mssql.banner):
            return
        with self.__mssql_locker:
            self.__mssql[mssql.banner] = mssql

    def set_ntp(self, ntp: Ntp):
        if not isinstance(ntp, Ntp):
            return
        if self.__ntp.__contains__(ntp.reference_id):
            return
        with self.__ntp_locker:
            self.__ntp[ntp.reference_id] = ntp

    def set_ubiquiti(self, ubiquiti: Ubiquiti):
        if not isinstance(ubiquiti, Ubiquiti):
            return
        if self.__ubiquiti.__contains__(ubiquiti.ip):
            return
        with self.__ubiquiti_locker:
            self.__ubiquiti[ubiquiti.ip] = ubiquiti

    def set_pop3(self, pop3: POP3):
        if not isinstance(pop3, POP3):
            return
        if self.__pop3info.__contains__(pop3.banner):
            return
        with self.__pop3info_locker:
            self.__pop3info[pop3.banner] = pop3

    def set_telnet(self, telnet: Telnet):
        if not isinstance(telnet, Telnet):
            return
        if self.__opts_telnet.__contains__(telnet.banner):
            return
        with self.__opts_telnet_locker:
            self.__opts_telnet[telnet.banner] = telnet
    
    def set_weblgict3(self, weblogict3: WeblogicT3):
        if not isinstance(weblogict3, WeblogicT3):
            return
        if self.__weblogic_t3.__contains__(weblogict3.banner):
            return
        with self.__weblogic_t3_locker:
            self.__weblogic_t3[weblogict3.banner] = weblogict3
        

    #######################################
    # joint output dict

    def get_outputdict(self) -> dict:
        """return dict or None"""

        pinfodict: dict = {}
        # basic info
        self.__outputdict_add_basic(pinfodict)

        # sslinfo
        self.__outputdict_add_ssl(pinfodict)

        # site/http
        self.__outputdict_add_site(pinfodict)

        # ssh
        self.__outputdict_add_ssh(pinfodict)

        # telnet
        self.__outputdict_add_telnet(pinfodict)
        # ftp
        self.__outputdict_add_ftp(pinfodict)
        # smtp
        self.__outputdict_add_smtp(pinfodict)

        # mysql
        self.__outputdict_add_mysql(pinfodict)

        # oracle
        self.__outputdict_add_oracle(pinfodict)
        # mongodb
        self.__outputdict_add_mongodb(pinfodict)
        # redis
        self.__outputdict_add_redis(pinfodict)
        # imap
        self.__outputdict_add_imap(pinfodict)
        # mssql
        self.__outputdict_add_mssql(pinfodict)
        # ntp
        self.__outputdict_add_ntp(pinfodict)
        # ubiquiti
        self.__outputdict_add_ubiquiti(pinfodict)
        # pop3
        self.__outputdict_add_pop3(pinfodict)
        # weblogic t3
        self.__outputdict_add_weblogict3(pinfodict)

        return pinfodict

    def __outputdict_add_basic(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        pinfo["port"] = self._port
        pinfo["transport"] = self._transport
        if not self.timestamp is None and self.timestamp != "":
            pinfo["timestamp"] = self.timestamp
        pinfo["service"] = self.service
        if not self.app is None and self.app != "":
            pinfo["app"] = self.app
        if not self.banner is None and self.banner != "":
            pinfo["banner"] = self.banner
        if len(self.__cpe) > 0:
            pinfo["cpe"] = []
            for c in self.__cpe.values():
                if not c in pinfo["cpe"]:
                    pinfo["cpe"].append(c)
        if len(self.__tags) > 0:
            pinfo["tags"] = []
            for t in self.__tags.values():
                if not t in pinfo["tags"]:
                    pinfo["tags"].append(t)
        if len(self.__hostnames) > 0:
            pinfo["hostnames"] = []
            for h in self.__hostnames.values():
                if not h in pinfo["hostnames"]:
                    pinfo["hostnames"].append(h)
        if len(self.__domains) > 0:
            pinfo["domains"] = []
            for d in self.__domains.values():
                if not d in pinfo["domains"]:
                    pinfo["domains"].append(d)
        if not self.link is None and self.link != "":
            pinfo["link"] = self.link
        if not self.uptime is None:
            pinfo["uptime"] = self.uptime
        if not self.device is None and self.device != "":
            pinfo["device"] = self.device
        if not self.extrainfo is None and self.extrainfo != "":
            pinfo["extrainfo"] = self.extrainfo
        if not self.version is None and self.version != "":
            pinfo["version"] = self.version
        if not self.os is None and self.os != "":
            pinfo["os"] = self.os

    def __outputdict_add_ssl(self, pinfo: dict):
        if len(self.__sslinfo) < 1:
            return

        pinfo["sslinfo"] = []
        for cert in self.__sslinfo.values():
            pinfo["sslinfo"].append(cert.get_outputdict())

    def __outputdict_add_site(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__siteinfo) < 1:
            return

        if not pinfo.__contains__("siteinfo"):
            pinfo["siteinfo"] = []

        for site in self.siteinfos:
            site: SiteInfo = site
            if site._site in [s["site"] for s in pinfo["siteinfo"]]:
                continue
            sitedict = site.get_outputdict()
            if sitedict is None or len(sitedict) < 1:
                continue
            pinfo["siteinfo"].append(sitedict)

    def __outputdict_add_ssh(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__sshinfo) < 1:
            return

        if not pinfo.__contains__("sshinfo"):
            pinfo["sshinfo"] = []

        for ssh in self.__sshinfo.values():
            ssh: SshInfo = ssh
            sshinfo = ssh.get_outputdict()
            if not isinstance(sshinfo, dict) or len(sshinfo) < 1:
                continue
            pinfo["sshinfo"].append(sshinfo)

    def __outputdict_add_smtp(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__smtpinfo) < 1:
            return

        if not pinfo.__contains__("smtp"):
            pinfo["smtp"] = []

        for s in self.__smtpinfo.values():
            s: SMTP = s
            smtp = s.get_outputdict()
            if not isinstance(smtp, dict) or len(smtp) < 1:
                continue
            pinfo["smtp"].append(smtp)

    def __outputdict_add_mysql(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")

        if len(self.__mysql) < 1:
            return

        if not pinfo.__contains__("mysql"):
            pinfo["mysql"] = []

        for m in self.__mysql.values():
            m: MySql = m
            mysql = m.get_outputdict()
            if not isinstance(mysql, dict) or len(mysql) < 1:
                continue
            pinfo["mysql"].append(mysql)

    def __outputdict_add_oracle(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__oracle) < 1:
            return
        if not pinfo.__contains__("oracle"):
            pinfo["oracle"] = []

        for o in self.__oracle.keys():
            pinfo["oracle"].append({"banner": o})

    def __outputdict_add_mongodb(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__mongodb) < 1:
            return
        if not pinfo.__contains__("mongodb"):
            pinfo["mongodb"] = []

        for mdata in self.__mongodb.values():
            pinfo["mongodb"].append(mdata.get_outputdict())

    def __outputdict_add_redis(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__redis) < 1:
            return
        if not pinfo.__contains__("redis"):
            pinfo["redis"] = []

        for rdata in self.__redis.values():
            pinfo["redis"].append(rdata.get_outputdict())

    def __outputdict_add_ftp(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__ftpinfo) < 1:
            return
        if not pinfo.__contains__("ftp"):
            pinfo["ftp"] = []

        for fdata in self.__ftpinfo.values():
            pinfo["ftp"].append(fdata.get_outputdict())

    def __outputdict_add_imap(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__imapinfo) < 1:
            return
        if not pinfo.__contains__("imap"):
            pinfo["imap"] = []

        for idata in self.__imapinfo.values():
            pinfo["imap"].append(idata.get_outputdict())

    def __outputdict_add_mssql(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__mssql) < 1:
            return
        if not pinfo.__contains__("mssql"):
            pinfo["mssql"] = []

        for msdata in self.__mssql.values():
            pinfo["mssql"].append(msdata.get_outputdict())

    def __outputdict_add_ntp(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__ntp) < 1:
            return
        if not pinfo.__contains__("ntp"):
            pinfo["ntp"] = []

        for ndata in self.__ntp.values():
            pinfo["ntp"].append(ndata.get_outputdict())

    def __outputdict_add_ubiquiti(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__ubiquiti) < 1:
            return
        if not pinfo.__contains__("ubiquiti"):
            pinfo["ubiquiti"] = []

        for udata in self.__ubiquiti.values():
            pinfo["ubiquiti"].append(udata.get_outputdict())

    def __outputdict_add_pop3(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__pop3info) < 1:
            return
        if not pinfo.__contains__("pop3"):
            pinfo["pop3"] = []

        for pop3data in self.__pop3info.values():
            pinfo["pop3"].append(pop3data.get_outputdict())

    def __outputdict_add_telnet(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__opts_telnet) < 1:
            return
        if not pinfo.__contains__("opts"):
            pinfo["opts"] = {}

        # 这个只有一个值
        for teldata in self.__opts_telnet.values():
            pinfo["opts"]["telnet"] = teldata.get_outputdict()

    def __outputdict_add_weblogict3(self, pinfo: dict):
        if not isinstance(pinfo, dict):
            raise Exception("Invalid portinfo dict")
        if len(self.__weblogic_t3) < 1:
            return
        if not pinfo.__contains__("weblogic-t3"):
            pinfo["weblogic-t3"] = []

        for wdata in self.__weblogic_t3.values():
            pinfo["weblogic-t3"].append(wdata.get_outputdict())
