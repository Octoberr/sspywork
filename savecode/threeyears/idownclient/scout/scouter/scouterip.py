"""scouter ip"""

# -*- coding:utf-8 -*-

import traceback

import IPy

from datacontract import EObjectType, IscoutTask
from idownclient.scout.plugin import SideSiteDetect

from ...clientdatafeedback.scoutdatafeedback import (
    IP,
    URL,
    Domain,
    GeoInfo,
    IPWhoisData,
    PortInfo,
    RangeCHost,
    ScoutFeedBackBase,
    SideSite,
)
from ..plugin import IpMxDomain, Nmap, SonarApi, Zgrab2
from ..plugin.bingsidedetect import BingSideDetect
from ..plugin.dbip import DbipMmdb
from ..plugin.rdap import IPWhois
from ..plugin.searchengine.google.googlesearch import GoogleSearch
from .scouterbase import ScouterBase
from ...scan.plugin.logicalbanner import LogicalGrabber


class ScouterIp(ScouterBase):
    """scouter ip"""

    TARGET_OBJ_TYPE = EObjectType.Ip

    def __init__(self, task: IscoutTask):
        ScouterBase.__init__(self, task)
        self._logicalgrabber = LogicalGrabber()

    # def __init_scanners(self):
    #     """初始化放在这里是因为避免每次调用都去初始化一下。\n
    #     在Linux/docker环境下不会初始化失败"""
    #     try:
    #         self._nmap: Nmap = Nmap()
    #     except Exception:
    #         self._logger.error("Init Nmap error: {}".format(
    #             traceback.format_exc()))
    #     try:
    #         self._zmap: Zmap = Zmap()
    #     except Exception:
    #         self._logger.error("Init Zmap error: {}".format(
    #             traceback.format_exc()))
    #     try:
    #         self._zgrab2: Zgrab2 = Zgrab2()
    #     except Exception:
    #         self._logger.error("Init Zgrab2 error: {}".format(
    #             traceback.format_exc()))

    def __segment_output(self, root: IP, level, ip) -> IP:
        """
        分段输出数据，达到分段输出的标准后给新的root
        没有达到那么就给旧的root
        :param root:
        :return:
        """
        # 加载到max output就输出
        # 如果输出了那么就返回新的根节点
        if root._subitem_count() >= self.max_output:
            self.outputdata(root.get_outputdict(), root._suffix)
            root: IP = IP(self.task, level, ip)
        return root

    def __output_getdata(self, root: IP, level, ip: str) -> IP:
        """
        单个插件拿到的数据太大了，每个插件执行完成后都输出下
        :param root:
        :param level:
        :param ip:
        :return:
        """
        if root._subitem_count() > 0:
            self.outputdata(root.get_outputdict(), root._suffix)
            root: IP = IP(self.task, level, ip)
        return root

    def __set_value(self, root: IP, data):
        """
        统一set value，这样是不是好看点
        """
        if isinstance(data, Domain):
            root.set_bind_domain_history(data)
        elif isinstance(data, GeoInfo):
            root.set_geolocation(data)
        elif isinstance(data, IPWhoisData):
            root.set_ipwhois(data)
        elif isinstance(data, PortInfo):
            root.set_portinfo(data)
        # else:
        #     raise Exception("Unknow data type: {}".format(data))

    def _scoutsub(self, level: int, obj: ScoutFeedBackBase) -> iter:
        """scout ip"""
        root: IP = IP(self.task, level, obj.value)
        try:
            # domain log
            for data in self._get_domain_log(
                root, self.task, level, obj, reason=self.dtools.domain_history
            ):
                yield data
            root = self.__output_getdata(root, level, ip=obj.value)

            # geoinfo
            for ginfo in self._get_geoinfo(
                root, self.task, level, obj, reason=self.dtools.location
            ):
                yield ginfo
            root = self.__output_getdata(root, level, ip=obj.value)

            # ipwhois
            for data in self._get_ipwhois(
                root, self.task, level, obj, reason=self.dtools.ipwhois
            ):
                yield data
            root = self.__output_getdata(root, level, ip=obj.value)

            # port service
            for data in self._get_port_service(
                root, self.task, level, obj, reason=self.dtools.service
            ):
                yield data
            root = self.__output_getdata(root, level, ip=obj.value)

            # ------------------------------------新增
            # domain detect ip反查域名
            for data in self._get_domain_detect(
                root, self.task, level, obj, reason=self.dtools.domain_detec
            ):
                yield data
            root = self.__output_getdata(root, level, ip=obj.value)

            # url
            for data in self._get_url_list(
                root, self.task, level, obj, reason=self.dtools.urlInfo
            ):
                yield data
            root = self.__output_getdata(root, level, ip=obj.value)

            # side_site_detect
            for data in self._get_side_site_detect(
                root, self.task, level, obj, reason=self.dtools.side_site_detect
            ):
                yield data
            root = self.__output_getdata(root, level, ip=obj.value)

            # rangec_detect
            for data in self._get_rangec_detect(
                root, self.task, level, obj, reason=self.dtools.rangec_detect
            ):
                yield data
            root = self.__output_getdata(root, level, ip=obj.value)

        except Exception:
            self._logger.error(
                "Scout IP error, err:\ntaskid:{}\nbatchid:{}\nobject:{}\nobjtype:{}\nerror:{}".format(
                    self.task.taskid,
                    self.task.batchid,
                    obj.value,
                    obj._objtype.name,
                    traceback.format_exc(),
                )
            )
        finally:
            # 最后结束完成也要输出
            if root._subitem_count() > 0:
                self.outputdata(root.get_outputdict(), root._suffix)

    ######################################
    # domain history
    def _get_domain_log(
        self, root: IP, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ) -> iter:
        """get domain history"""
        if not task.cmd.stratagyscout.cmdip.enabled_domain_history:
            return
        log = f"开始获取目标{obj.value} {self.dtools.domain_history}信息"
        self._outprglog(log)
        self._logger.debug("IP:Start getting domain log.")
        count_dict = {}
        try:
            for dl in self._get_sonar_domain_log(root, task, level, obj):
                count_dict[dl.value] = 1
                yield dl
        except Exception:
            self._logger.error(
                "Get domain log error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )
        finally:
            log = f"获取到目标{obj.value}未经处理的{count_dict.__len__()}条{self.dtools.domain_history}数据"
            self._outprglog(log)

    def _get_sonar_domain_log(
        self, root: IP, task: IscoutTask, level, obj: ScoutFeedBackBase
    ) -> iter:
        """
        根据ip获取domian log
        :return:
        """
        ip = obj.value
        try:

            for dl in SonarApi.domain_log(task, level, ip):
                self.__set_value(root, dl)
                root = self.__segment_output(root, level, ip)
                yield dl
        except:
            self._logger.error(
                "Get sonar domain log error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )

    ######################################
    # geolocation info
    def _get_geoinfo(
        self, root: IP, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        根据ip获取geoinfo
        :return:
        """
        if not task.cmd.stratagyscout.cmdip.enabled_location:
            return
        count = 0
        try:
            log = f"开始获取目标{obj.value}的{self.dtools.location}信息"
            self._outprglog(log)
            self._logger.debug("IP:Start getting geoinfo.")
            # dbip geoinfo
            for data in self._get_dbip_geoinfo(root, task, level, obj):
                count += 1
                yield data

            # 如果db-ip没查到才走本地声呐
            if root._geoinfo is None:
                # sonar geoinfo
                for data in self._get_sonar_geoinfo(root, task, level, obj):
                    count += 1
                    yield data
        except:
            self._logger.error(
                "Get geoinfo error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )
        finally:
            log = f"获取到目标{obj.value}未经处理的{count}条{self.dtools.location}数据"
            self._outprglog(log)

    def _get_sonar_geoinfo(
        self, root: IP, task: IscoutTask, level, obj: ScoutFeedBackBase
    ):
        """
        sonar获取geoinfo
        :return:
        """
        ip = obj.value
        try:

            for gobj in SonarApi.geoinfo(task, level, ip):
                self.__set_value(root, gobj)
                root = self.__segment_output(root, level, ip)
                yield gobj
            task.success_count()
        except:
            task.fail_count()
            self._logger.error(
                "Get sonar geoinfo error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )

    def _get_dbip_geoinfo(
        self, root: IP, task: IscoutTask, level, obj: ScoutFeedBackBase
    ):
        """
        dbip获取geoinfo
        :param task:
        :param level:
        :param obj:
        :return:
        """

        ip = obj.value
        try:

            db = DbipMmdb()
            gobj, org, isp = db.get_ip_mmdbinfo(level, ip)
            root.org = org
            root.isp = isp
            if gobj is not None:
                task.success_count()
                self.__set_value(root, gobj)
                root = self.__segment_output(root, level, ip)
                yield gobj
            else:
                task.fail_count()

            # for gobj in db.get_ip_geoinfo(level, ip):
            #     self.__set_value(root, gobj)
            #     root = self.__segment_output(root, level, ip)
            #     yield gobj
        except:
            self._logger.error(
                "Get dbip geoinfo error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )

    ######################################
    # ipwhois
    def _get_ipwhois(
        self, root: IP, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """get ipwhois"""
        if not task.cmd.stratagyscout.cmdip.enabled_ipwhois:
            return
        log = f"开始获取目标{obj.value}的{self.dtools.ipwhois}信息"
        self._outprglog(log)
        self._logger.debug("IP:Start getting ipwhois.")

        plgipwhois = IPWhois()
        count_dict = {}
        try:
            for iw in plgipwhois.get_ipwhois_history(task, obj.value, reason, level):
                if iw is not None:
                    self.__set_value(root, iw)
                    count_dict[iw._handle + iw._md5] = 1
                    root = self.__segment_output(root, level, obj.value)
                    yield iw
            task.success_count("ipwhois", level=level)
        except Exception:
            task.fail_count("ipwhois", level=level)
            self._logger.error(
                "Get IPWhois error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    obj.value,
                    obj._objtype.name,
                    traceback.format_exc(),
                )
            )
        finally:
            log = f"获取到目标{obj.value}未经处理的{count_dict.__len__()}条{self.dtools.ipwhois}数据"
            self._outprglog(log)

    ######################################
    # port service
    def _get_port_service(
        self, root: IP, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ) -> iter:
        """扫描端口服务详情"""
        if not task.cmd.stratagyscout.cmdip.enabled_service:
            return
        count = 0
        try:
            log = f"开始获取目标{obj.value} {self.dtools.service}信息"
            self._outprglog(log)
            self._logger.debug("IP:Start getting port service.")

            ports = task.cmd.stratagyscout.default_ports
            if (
                isinstance(task.cmd.stratagyscout.cmdip.ports, list)
                and len(task.cmd.stratagyscout.cmdip.ports) > 0
            ):
                ports = task.cmd.stratagyscout.cmdip.ports

            vuls = task.cmd.stratagyscout.cmdip.vuls

            log = f"开始探测目标{obj.value}的端口，一共将会探测{len(ports)}个端口"
            self._outprglog(log)
            # here should use nmap,
            # for service type/version and os version scan
            nmap = Nmap()
            # 这里来的肯定是只有  一个域名
            for port in nmap.scan_open_ports(
                task,
                level,
                [obj.value],
                ports,
                outlog=self._outprglog,
            ):
                # 这里出来就是端口基本信息
                # 必有字段：
                # host
                # port
                # transport protocol
                # service
                if not isinstance(port, PortInfo):
                    continue

                port: PortInfo = port

                self._scan_application_protocol(
                    task, level, obj, port, outlog=self._outprglog
                )
                self._logicalgrabber.grabbanner(
                    port, [], flag="iscout", outlog=self._outprglog
                )

                self.__set_value(root, port)
                count += 1
                root = self.__segment_output(root, level, obj.value)

                yield port
            task.success_count("service", level=level)
        except Exception:
            task.fail_count("service", level=level)
            self._logger.error(
                "Scan IP port service error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    obj.value,
                    obj._objtype.name,
                    traceback.format_exc(),
                )
            )
        finally:
            log = f"获取到目标{obj.value}未经处理的{count}条{self.dtools.service}数据"
            self._outprglog(log)

    def _scan_application_protocol(
        self,
        task: IscoutTask,
        level: int,
        obj: ScoutFeedBackBase,
        port: PortInfo,
        **kwargs,
    ):
        """根据 portinfo 的协议类型，扫描其应用层协议"""
        try:
            zgrab2 = Zgrab2()
            outlog = kwargs.get("outlog")

            # all application protocol need to support TLS banner grab
            # protocols supported TLS:
            # http
            # mongodb
            # redis

            # 绝对不用扫描ssl证书的端口：
            # if port._port != 23 or \
            #         port._port != 25 or \
            #         port._port != 80 or \
            #         port._port != 110 or \
            #         port._port != 143 or \
            #         port._port != 993:
            if port._port != 80:
                zgrab2.get_tlsinfo(task, level, port)

            # 先简单匹配 banner抓取器 了，，后面需要单独出匹配banner 抓取器了
            if port.service == "ftp" or port._port == 21:
                zgrab2.get_ftp_info(task, level, port)
            elif port.service == "ssh" or port._port == 22:
                zgrab2.get_ssh_info(task, level, port)
            elif port.service == "telnet" or port._port == 23:
                zgrab2.get_telnet_info(task, level, port)
            elif port.service == "smtp" or port._port == 25 or port._port == 465:
                zgrab2.get_smtp_info(task, level, port)
            elif port.service == "http" or port._port == 80 or port._port == 443:
                zgrab2.get_siteinfo(task, level, port)
            elif port.service == "pop3" or port._port == 110 or port._port == 995:
                zgrab2.get_pop3_info(task, level, port)
            elif port.service == "ntp" or port._port == 123:
                zgrab2.get_ntp_info(task, level, port)
            elif port.service == "imap" or port._port == 143 or port._port == 993:
                zgrab2.get_imap_info(task, level, port)
            elif port.service == "mssql" or port._port == 1433:
                zgrab2.get_mssql_info(task, level, port)
            elif port.service == "redis" or port._port == 6379:
                zgrab2.get_redis_info(task, level, port)
            elif port.service == "mongodb" or port._port == 27017:
                zgrab2.get_mongodb_info(task, level, port)
            elif port.service == "mysql" or port._port == 3306:
                zgrab2.get_mysql_info(task, level, port)
            elif port.service == "oracle" or port._port == 1521:
                zgrab2.get_oracle_info(task, level, port)
            log = f"目标:{port._host},端口:{port._port},协议:{port.service},协议详情探测完成"
            outlog(log)
        except Exception:
            task.fail_count("service", level=level)
            self._logger.error(
                "Scout ip port application protocol error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )

    ######################################
    # domain detect(ip反查域名)
    def _get_domain_detect(
        self, root: IP, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        ip反查域名，获取指向此目标ip地址上的域名
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmdip.enabled_domain_detect:
            return
        self._logger.debug("IP:Start getting domain detect.")
        ip = obj.value
        log = f"开始探测目标{ip}的{self.dtools.domain_detec}信息"
        self._outprglog(log)
        # mx ip reverse
        count = 0
        try:
            for data in self._mx_domain_detect(root, task, level, ip, reason):
                count += 1
                yield data
        except:
            self._logger.error(f"Domain detect error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{ip}未经处理的{count}条{self.dtools.domain_detec}数据"
            self._outprglog(log)

    def _mx_domain_detect(self, root: IP, task: IscoutTask, level, ip, reason=None):
        """
        nslookup查询ip的域名
        :param root:
        :param task:
        :param level:
        :param ip:
        :param reason:
        :return:
        """
        try:
            mdd = IpMxDomain(task)
            reverse_domain = mdd.get_ip_reverse_domain(level, ip, reason)
            if reverse_domain is not None:
                # self.__set_value(root, reverse_domain)
                root.set_ipreverse(reverse_domain)
                root = self.__segment_output(root, level, ip)
                yield reverse_domain
            task.success_count()
        except:
            task.fail_count()
            self._logger.error(f"Get mx ip reverse error, err:{traceback.format_exc()}")

    ######################################
    # url list
    def _get_url_list(
        self, root: IP, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        对目标ip侦查得到的url信息，url枚举，获取当前目标存在的url地址
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmdip.enabled_url:
            return
        self._logger.debug("IP:Start getting url list.")
        gs = None
        ip = obj.value
        log = f"开始探测目标{ip} {self.dtools.urlInfo}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            query = f"intext:{ip}"
            gs = GoogleSearch(task)
            for u_link in gs.get_search_link(query):
                url = URL(task, level, u_link)
                root.set_url(url)
                count_dict[u_link] = 1
                root = self.__segment_output(root, level, ip)
                yield url

        except:
            self._logger.error(f"Get url error, err:{traceback.format_exc()}")
        finally:
            # 实例化googlesearch不会出现问题
            log = f"获取到目标{ip}未经处理的{count_dict.__len__()}条{self.dtools.urlInfo}数据"
            self._outprglog(log)
            if gs is not None:
                del gs

    # -------------------------------------------------side_site detect 旁站探测
    def _get_side_site_detect(
        self, root: IP, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        探测当前IP所在的服务器上的其他网站
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmdip.enabled_side_site_detect:
            return
        ip = obj.value
        count_dict = {}
        try:
            self._logger.debug("IP: Start getting side_site detect info")
            log = f"开始探测目标{ip} {self.dtools.side_site_detect}信息"
            self._outprglog(log)
            # sidesite api

            sd = SideSiteDetect(task)
            for side_site in sd.side_site_detect(ip, level):
                if not isinstance(side_site, SideSite):
                    continue
                root.set_side_site(side_site)
                count_dict[side_site.host + side_site.ip + str(side_site.port)] = 1
                root = self.__segment_output(root, level, ip)
                yield side_site

            # bing api
            for data in self._bing_search_side_site(root, task, level, ip, reason):
                count_dict[data.host + data.ip + str(data.port)] = 1
                yield data
            task.success_count("side_site_detect", level)
        except Exception:
            task.fail_count("side_site_detect", level)
            self._logger.error(
                "Sidesite detect error:\ntaskid:{}\nbatchid:{}\nobj:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    obj.value,
                    traceback.format_exc(),
                )
            )
        finally:
            log = f"获取到到目标{ip}未经处理的{count_dict.__len__()}条{self.dtools.side_site_detect}信息"
            self._outprglog(log)

    def _bing_search_side_site(self, root: IP, task: IscoutTask, level, ip, reason):
        """
        bing 搜索一个domain的旁站
        :param root:
        :param task:
        :param level:
        :param ip:
        :param reason:
        :return:
        """
        try:
            ss = BingSideDetect()
            for ssdata in ss.bing_ip_side_site(ip, level, reason):
                if isinstance(ssdata, SideSite):
                    root.set_side_site(ssdata)
                    root = self.__segment_output(root, level, ip)
                    yield ssdata
            task.success_count()
        except:
            task.fail_count()
            self._logger.error(
                f"Bing Search side site error, err:{traceback.format_exc()}"
            )

    # -------------------------------------------------rangec_detect C段存活探测
    def _get_rangec_detect(
        self, root: IP, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        获取ip所在的C段主机的存活情况
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmdip.enabled_rangec_detect:
            return
        count = 0
        try:
            log = f"开始探测目标{obj.value} {self.dtools.rangec_detect}信息"
            self._outprglog(log)
            self._logger.debug("IP:Start getting rangec detect.")

            # ports = task.cmd.stratagyscout.default_ports
            # if isinstance(
            #         self.task.cmd.stratagyscout.cmdip.ports,
            #         list) and len(self.task.cmd.stratagyscout.cmdip.ports) > 0:
            #     ports = self.task.cmd.stratagyscout.cmdip.ports

            ip: IPy.IP = IPy.IP(obj.value)
            ipcrange = ip.make_net("255.255.255.0")

            nmap = Nmap()
            for host in nmap.scan_alive_hosts(
                self.task,
                level,
                [ipcrange.__str__()],
            ):
                if not isinstance(host, RangeCHost):
                    continue
                root.set_rangec(host)
                count += 1
                root = self.__segment_output(root, level, obj.value)
                yield host

            task.success_count("rangec_detect", level=level)
        except Exception:
            task.fail_count("rangec_detect", level=level)
            self._logger.error(
                "Range C detect error:\ntaskid:{}\nbatchid:{}\nobj{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    obj.value,
                    traceback.format_exc(),
                )
            )
        finally:
            log = f"获取到目标{obj.value}未经处理的{count}条{self.dtools.rangec_detect}数据"
            self._outprglog(log)
