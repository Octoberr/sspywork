"""domain scouter"""
import json
import traceback

import tld

from datacontract import EObjectType, IscoutTask
from idownclient.scout.plugin import SideSiteDetect
from outputmanagement import OutputManagement

from ...clientdatafeedback.scoutdatafeedback import (
    IP,
    URL,
    Domain,
    Email,
    MailServer,
    Phone,
    PortInfo,
    ScoutFeedBackBase,
    ScreenshotSE,
    SearchEngine,
    SearchFile,
    SideSite,
    Whois,
)
from ..plugin import (
    DomainMXQuery,
    Nmap,
    SearchApi,
    SonarApi,
    WafDetect,
    WhoisSoft,
    Zgrab2,
)
from ..plugin.bingsidedetect import BingSideDetect
from ..plugin.dbip import DbipMmdb
from ..plugin.rdap import IPWhois
from ..plugin.realipdetect.realipdetect import RealipDetect

# googlesearch
from ..plugin.searchengine.google.googlesearch import GoogleSearch
from .scouterbase import ScouterBase
from ...scan.plugin.logicalbanner import LogicalGrabber


class ScouterDomain(ScouterBase):
    """
    scout domain
    """

    TARGET_OBJ_TYPE = EObjectType.Domain

    def __init__(self, task: IscoutTask):
        ScouterBase.__init__(self, task)

        self._logicalgrabber = LogicalGrabber()
        self._download_ipinfo = {}

    def __segment_output(self, root: Domain, level, domain: str) -> Domain:
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
            root: Domain = Domain(self.task, level, domain)
        # 如果是老的那么就将根节点原封不动返回即可
        return root

    def __output_getdata(self, root: Domain, level, domain: str) -> Domain:
        """
        单个插件拿到的数据太大了，每个插件执行完成后都输出下
        :param root:
        :param level:
        :param domain:
        :return:
        """
        if root._subitem_count() > 0:
            self.outputdata(root.get_outputdict(), root._suffix)
            root: Domain = Domain(self.task, level, domain)
        return root

    def __set_value(self, root: Domain, data):
        """set value\n
        如果这里要提升性能，那就搞个字典缓存放data类型对应的root的set方法"""
        if isinstance(data, Domain):
            root.set_subdomain(data)
        elif isinstance(data, IP):
            root.set_iplog(data)
        elif isinstance(data, Whois):
            root.set_whois(data)
        elif isinstance(data, SearchEngine):
            root.set_searchengine(data)
        elif isinstance(data, URL):
            root.set_url(data)
        elif isinstance(data, PortInfo):
            root.set_portinfo(data)
        elif isinstance(data, MailServer):
            # 数据还没有写
            # 没写两句话就写了啊。。
            root.set_mailserver(data)
        # else:
        #     raise Exception("Unknow data type: {}".format(data))

    def _scoutsub(self, level: int, obj: ScoutFeedBackBase) -> iter:
        """
        去调子类实现的下载器下载东西
        :return:
        """

        root: Domain = Domain(self.task, level, obj.value)

        try:
            # subdomain
            for data in self._get_subdomain(
                root, self.task, level, obj, reason=self.dtools.subdomain
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

            # iplog
            for data in self._get_iplog(
                root, self.task, level, obj, reason=self.dtools.ip_history
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

            # whois
            for data in self._get_whois(
                root, self.task, level, obj, reason=self.dtools.whois
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

            # email 这个要单独写业务
            for data in self._get_email(
                root, self.task, level, obj, reason=self.dtools.email
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

            # phone 要单独写业务
            for data in self._get_phone(
                root, self.task, level, obj, reason=self.dtools.phone
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

            # searchengine
            for data in self.get_searchengine(
                root, self.task, level, obj, reason=self.dtools.google
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

            # port service
            for data in self._get_port_service(
                root, self.task, level, obj, reason=self.dtools.service
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

            # ---------------------------------------------------------新增
            # mail_server
            for data in self._get_mailserver(
                root, self.task, level, obj, reason=self.dtools.mail_server
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

            # side_site_detect
            for data in self._get_side_site_detect(
                root, self.task, level, obj, reason=self.dtools.side_site_detect
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

            # waf_detect
            for data in self._get_waf_detect(
                root, self.task, level, obj, reason=self.dtools.waf_detect
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

            # real_ip
            for data in self._get_realip(
                root, self.task, level, obj, reason=self.dtools.real_ip
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

            # url list
            for data in self._get_url_list(
                root, self.task, level, obj, reason=self.dtools.urlInfo
            ):
                yield data
            root = self.__output_getdata(root, level, obj.value)

        except:
            self._logger.error(
                "Scout domain error, err:\ntaskid:{}\nbatchid:{}\nobject:{}\nobjtype:{}\nerror:{}".format(
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

    ##############################################
    # subdomain
    def _get_subdomain(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ) -> iter:
        """
        下载subdomain，reason接受外面传的，也接受根据插件的功能自定义的reason，
        总而言之插件只需要接受传的reason即可，这个字段按着需求添加即可
        :return:
        """
        if not task.cmd.stratagyscout.cmddomain.enabled_subdomain:
            return
        count_dict = {}
        try:
            self._logger.debug("DOMAIN:Start getting subdomain.")
            log = f"开始探测目标{obj.value} {self.dtools.subdomain}信息"
            self._outprglog(log)
            # sonar

            for subdomain in self._get_subdomain_sonar(root, task, level, obj):
                count_dict[subdomain.value] = 1
                yield subdomain

        except:
            self._logger.error(
                "Get subdomain error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )
        finally:
            log = (
                f"获取到目标{obj.value}未经处理的{count_dict.__len__()}条{self.dtools.subdomain}数据"
            )
            self._outprglog(log)

    def _get_subdomain_sonar(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase
    ) -> iter:
        domain: str = obj.value
        try:
            for subdomain in SonarApi.subdomains(task, level, domain):
                self.__set_value(root, subdomain)
                root = self.__segment_output(root, level, domain)
                yield subdomain

        except Exception:
            self._logger.error(
                "Get Sonar subdomain error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )

    ##############################################
    # ip log
    def _get_iplog(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ) -> iter:
        """
        下载iplog
        :return:
        """

        if not task.cmd.stratagyscout.cmddomain.enabled_ip_history:
            return
        self._logger.debug("DOMIAN:Start getting iplog.")
        domain: str = obj.value
        log = f"开始探测目标{domain} {self.dtools.ip_history}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            for iplog in SonarApi.iplogs(task, level, domain):
                self.__set_value(root, iplog)
                root = self.__segment_output(root, level, domain)
                # 去下载当前ip geoinfo 和ip whois, add by judy 191121
                ip = iplog.value
                if not self._download_ipinfo.__contains__(ip):
                    self.__get_ip_whois_and_geoinfo(task, level, ip, reason)
                    self._download_ipinfo[ip] = 1
                    count_dict[ip] = 1
                self._logger.debug(f"Got ip log for domain: domain={domain}, ip={ip}")
                yield iplog

        except:
            self._logger.error(
                "Get Sonar iplog error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )
        finally:
            log = f"获取到目标{domain}未经处理的{count_dict.__len__()}条{self.dtools.ip_history}数据"
            self._outprglog(log)

    ##############################################
    # whois
    def _get_whois(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ) -> iter:
        """
        下载domain_whois
        :return:
        """
        if not task.cmd.stratagyscout.cmddomain.enabled_whois:
            return
        self._logger.debug("DOMIAN: Start getting whois info.")
        # sonar
        log = f"开始探测目标{obj.value} {self.dtools.whois}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            for data in self._get_whois_sonar(root, task, level, obj, reason):
                count_dict[json.dumps(data.get_whois_outputdict())] = 1
                yield data
            # whoissoft 反正只使用一个，后面的会被顶掉，所以目前就用sonar吧
            # for data in self._get_whois_whoissoft(root, task, level, obj, reason):
            #     yield data
        except:
            self._logger.error(
                "Get whois error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )
        finally:
            log = f"获取到目标{obj.value}未经处理的{count_dict.__len__()}条{self.dtools.whois}数据"
            self._outprglog(log)

    def _get_whois_whoissoft(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason
    ) -> iter:
        try:
            domain: str = obj.value
            wi = WhoisSoft(task)
            for data in wi.get_whoisres(level, domain, reason):
                if isinstance(data, Whois):
                    self.__set_value(root, data)
                    root = self.__segment_output(root, level, domain)
                    yield data

        except Exception:
            self._logger.error(
                "Get whoissoft subdomain error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )

    def _get_whois_sonar(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason
    ) -> iter:
        domain: str = tld.get_tld(
            obj.value, fail_silently=True, as_object=True, fix_protocol=True
        ).fld
        try:
            for data in SonarApi.domain_whoishistory(task, level, domain, reason):
                if isinstance(data, Whois):
                    # self.__set_value(root, data)
                    self._logger.info(
                        "Got a whois data: {}".format(
                            data._registrar + data._registtime + data.infotime
                        )
                    )  # 取到一条whois信息
                    root.set_whois(data)
                    root = self.__segment_output(root, level, domain)
                    yield data
            task.success_count()
        except Exception:
            task.fail_count()
            self._logger.error(
                "Get sonar whoishistory data error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )

    ##############################################
    # searchengine
    def get_searchengine(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ) -> iter:
        """
        目前在使用的就只有google
        bing应该会弃用，目前这样写可以，后期非要bing的话再加
        :param root:
        :param task:
        :param level:
        :param obj:
        :param reason:
        :return:
        """
        domain = obj.value
        try:
            for data in self._get_google_searchengine(
                root, task, level, domain, reason
            ):
                yield data
            for data1 in self._get_bing_searchengine(root, task, level, domain, reason):
                yield data1
            for data2 in self._get_baidu_searchengine(
                root, task, level, domain, reason
            ):
                yield data2
        except:
            self._logger.info(f"Get search engine error, err:{traceback.format_exc()}")

    def _get_google_searchengine(
        self, root: Domain, task: IscoutTask, level, domain, reason=None
    ):
        """
        google 搜索引擎
        :param root:
        :param task:
        :param level:
        :param domain:
        :param reason:
        :return:
        """
        # 目前只有google搜索
        if not task.cmd.stratagyscout.cmddomain.enabled_searchgoogle:
            return
        log = f"开始探测目标{domain} {self.dtools.google}信息"
        self._outprglog(log)
        count = 0
        try:
            self._logger.debug("DOMIAN:Start getting googlesearch.")
            sapi = SearchApi(task)
            for data in sapi.domain_google_search_engine(
                domain, level, self.dtools.google
            ):
                # 输出截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    root = self.__segment_output(root, level, domain)
                    count += 1
                    yield data
        except:
            self._logger.error(
                f"Get google search engine result error, err:{traceback.format_exc()}"
            )
        finally:
            log = f"获取到目标{domain}未经处理的{count}条{self.dtools.google}数据"
            self._outprglog(log)

    def _get_bing_searchengine(
        self, root: Domain, task: IscoutTask, level, domain, reason=None
    ):
        """
        bing 搜索引擎
        :param root:
        :param task:
        :param level:
        :param domain:
        :param reason:
        :return:
        """
        # 目前只有google搜索
        if not task.cmd.stratagyscout.cmddomain.enabled_searchbing:
            return
        log = f"开始探测目标{domain} {self.dtools.bing}信息"
        self._outprglog(log)
        count = 0
        try:
            self._logger.debug("DOMIAN:Start getting bing search.")
            sapi = SearchApi(task)
            for data in sapi.domain_bing_search_engine(domain, level, self.dtools.bing):
                # 输出截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    root = self.__segment_output(root, level, domain)
                    count += 1
                    yield data
        except:
            self._logger.error(
                f"Get bing search engine result error, err:{traceback.format_exc()}"
            )
        finally:
            log = f"获取到目标{domain}未经处理的{count}条{self.dtools.bing}数据"
            self._outprglog(log)

    def _get_baidu_searchengine(
        self, root: Domain, task: IscoutTask, level, domain, reason=None
    ):
        """
        baidu 搜索引擎
        :param root:
        :param task:
        :param level:
        :param domain:
        :param reason:
        :return:
        """
        # 目前只有google搜索
        if not task.cmd.stratagyscout.cmddomain.enabled_searchbaidu:
            return
        log = f"开始探测目标{domain} {self.dtools.baidu}信息"
        self._outprglog(log)
        count = 0
        try:
            self._logger.debug("DOMIAN:Start getting baidu search.")
            sapi = SearchApi(task)
            for data in sapi.domain_baidu_search_engine(
                domain, level, self.dtools.baidu
            ):
                # 输出截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    root = self.__segment_output(root, level, domain)
                    count += 1
                    yield data

        except:
            self._logger.error(
                f"Get baidu search engine result error, err:{traceback.format_exc()}"
            )
        finally:
            log = f"获取到目标{domain}未经处理的{count}条{self.dtools.baidu}数据"
            self._outprglog(log)

    ##############################################
    # port service
    def _get_port_service(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ) -> iter:
        """扫描端口服务详情"""
        if not task.cmd.stratagyscout.cmddomain.enabled_service:
            return
        count = 0
        try:
            log = f"开始探测目标{obj.value} {self.dtools.service}信息"
            self._outprglog(log)
            self._logger.debug("DOMIAN:Start getting port service.")

            ports = task.cmd.stratagyscout.default_ports
            if (
                isinstance(task.cmd.stratagyscout.cmddomain.ports, list)
                and len(task.cmd.stratagyscout.cmddomain.ports) > 0
            ):
                ports = task.cmd.stratagyscout.cmddomain.ports

            vuls = task.cmd.stratagyscout.cmddomain.vuls

            scanner = None
            # here should use nmap,
            # for service type/version and os version scan
            scanner = Nmap()

            # 这里来的肯定是只有  一个域名

            for port in scanner.scan_open_ports(
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
                count += 1
                port: PortInfo = port
                self._scan_application_protocol(
                    task, level, obj, port, outlog=self._outprglog
                )
                self._logicalgrabber.grabbanner(
                    port, [], flag="iscout", outlog=self._outprglog
                )
                self.__set_value(root, port)
                root = self.__segment_output(root, level, obj.value)
                yield port
            task.success_count()
        except Exception:
            task.fail_count()
            self._logger.error(
                "Scan domain port service error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}\nerror:{}".format(
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
            outlog = kwargs.get("outlog")
            zgrab2 = Zgrab2()
            # all application protocol need to support TLS banner grab
            # 绝对不用扫描ssl证书的端口：
            # 谁说的绝对不用...人家有个StartTLS命令可以切换协议

            # if port._port != 23 \
            #         or port._port != 25 \
            #         or port._port != 80 \
            #         or port._port != 110 \
            #         or port._port != 143 \
            #         or port._port != 993:
            if port._port != 80:
                zgrab2.get_tlsinfo(task, level, port)

            # 先简单匹配 banner抓取器 了，，后面需要单独出匹配banner 抓取器了
            if port.service == "ftp" or port._port == 21:
                zgrab2.get_mssql_info(task, level, port)
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
            log = f"目标:{port._host},端口:{port._port},协议:{port.service},协议详情探测完成"
            outlog(log)
        except Exception:
            self._logger.error(
                "Scan domain port application protocol error:\ntaskid:{}\nbatchid:{}\nrootobject:{}\nobjtype:{}".format(
                    task.taskid, task.batchid, obj.value, obj._objtype.name
                )
            )

    # ----------------------------------------mail server
    def _get_mailserver(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ) -> iter:
        """
        使用域名去查询邮箱域名的mx记录
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmddomain.enabled_mail_server:
            return

        self._logger.debug("DOMIAN:Start getting mail server.")
        domain = obj.value
        log = f"开始解析目标{domain} {self.dtools.mail_server}信息"
        self._outprglog(log)
        count = 0
        try:
            mxq = DomainMXQuery(task)
            for ms in mxq.get_mail_server(level, domain, reason):
                self.__set_value(root, ms)
                root = self.__segment_output(root, level, domain)
                count += 1
                yield ms
            task.success_count()
        except:
            task.fail_count()
            self._logger.error(
                f"Get domain mx maiserver error, err:{traceback.format_exc()}"
            )
        finally:
            log = f"获取到目标{domain}未经处理的{count}条{self.dtools.mail_server}数据"
            self._outprglog(log)

        # 如果插件少就直接在这里写，但是插件多的话就分多个方法，在拿到数据时进行set和output操作

    # -------------------------------------side_site detect 旁站探测
    def _get_side_site_detect(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        探测当前域名所在服务器上的其他网站
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmddomain.enabled_side_site_detect:
            return
        domain = obj.value
        count_dict = {}
        try:
            log = f"开始收集目标{domain} {self.dtools.side_site_detect}信息"
            self._outprglog(log)
            self._logger.debug("DOMIAN: Start getting side_site detect info.")

            # sidesite api

            sd = SideSiteDetect(task)
            for side_site in sd.side_site_detect(domain, level):
                if not isinstance(side_site, SideSite):
                    continue
                root.set_side_site(side_site)
                root = self.__segment_output(root, level, domain)
                count_dict[side_site.host + side_site.ip + str(side_site.port)] = 1
                yield side_site

            # bing api
            for data in self._bing_search_side_site(root, task, level, domain, reason):
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
            log = f"获取到目标{domain}未经处理的{count_dict.__len__()}条{self.dtools.side_site_detect}数据"
            self._outprglog(log)

    def _bing_search_side_site(
        self, root: Domain, task: IscoutTask, level, domain, reason
    ):
        """
        bing 搜索一个domain的旁站
        :param root:
        :param task:
        :param level:
        :param domain:
        :param reason:
        :return:
        """
        try:
            ss = BingSideDetect()
            for ssdata in ss.bing_domain_side_site(domain, level, reason):
                if isinstance(ssdata, SideSite):
                    root.set_side_site(ssdata)
                    root = self.__segment_output(root, level, domain)
                    yield ssdata
            task.success_count()
        except:
            task.fail_count()
            self._logger.error(
                f"Bing Search side site error, err:{traceback.format_exc()}"
            )

    # ------------------------------------waf_detect目标防护探测
    def _get_waf_detect(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        目标防护探测数据，探测当前URL在服务器上的web防火墙
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmddomain.enabled_waf_detect:
            return
        log = f"开始收集目标{obj.value} {self.dtools.waf_detect}信息"
        self._outprglog(log)
        self._logger.debug("DOMIAN: Start getting waf_detect info.")
        count_dict = {}
        try:
            wd = WafDetect(task)
            if "http://" in obj.value or "https://" in obj.value:
                self._logger.error("http:// or https:// should not in obj.value!")
                return
            # 探测目标是HTTP协议
            for waf in wd.waf_detect("http://" + obj.value):
                if not isinstance(waf, str):
                    continue
                root.set_waf(waf)
                count_dict[waf] = 1
                root = self.__segment_output(root, level, obj.value)
                yield waf
            task.success_count()
            # 探测目标是HTTPS协议
            for waf in wd.waf_detect("https://" + obj.value):
                if not isinstance(waf, str):
                    continue
                count_dict[waf] = 1
                root.set_waf(waf)
                root = self.__segment_output(root, level, obj.value)
                yield waf
            task.success_count()

        except Exception:
            task.fail_count()
            self._logger.error(
                "Waf detect error:\ntaskid:{}\nbatchid:{}\nobj:{}\nerror:{}".format(
                    self.task.taskid,
                    self.task.batchid,
                    obj.value,
                    traceback.format_exc(),
                )
            )
        finally:
            log = f"获取到目标{obj.value}未经处理的{count_dict.__len__()}条{self.dtools.waf_detect}数据"
            self._outprglog(log)

    # -------------------------------------------realip真实ip探测
    def _get_realip(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        真实ip探测,透过CDN找到目标真实ip"
        :param root:
        :param task:
        :param level:
        :param obj:
        :param reason:
        :return:
        """
        if not task.cmd.stratagyscout.cmddomain.enabled_real_ip:
            return
        log = f"开始收集目标{obj.value} {self.dtools.real_ip}信息"
        self._outprglog(log)
        self._logger.debug("DOMAIN: Start getting Realip info")

        count_dict = {}
        try:

            rd = RealipDetect(task)
            for realip in rd.get_real_ip(obj.value, level):
                if not isinstance(realip, str):
                    continue
                root.set_realip(realip)
                count_dict[realip] = 1
                root = self.__segment_output(root, level, obj.value)

                # 新增查找ip相关信息, add by judy 191121
                # 如果这个是None说明没有下载过
                if not self._download_ipinfo.__contains__(realip):
                    self.__get_ip_whois_and_geoinfo(task, level, realip, reason)
                    self._download_ipinfo[realip] = 1
                self._logger.debug(
                    f"Got realip for domain: domain={obj.value}, ip={realip}"
                )
                yield realip

            self.task.success_count("real_ip", level)
        except Exception:
            self.task.fail_count("real_ip", level)
            self._logger.error(
                "Realip detect error:\ntaskid:{}\nbatchid:{}\nobj:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    obj.value,
                    traceback.format_exc(),
                )
            )
        finally:
            log = f"获取到目标{obj.value}未经处理的{count_dict.__len__()}条{self.dtools.real_ip}数据"
            self._outprglog(log)

    # ------------------------------------------------------------------------email
    def _get_email(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        去其它地方拿邮箱
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmddomain.enabled_email:
            return
        self._logger.debug("DOMIAN:Start getting email.")
        domain: str = obj.value
        log = f"开始探测目标{domain} {self.dtools.email}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            # sonar接口
            for data in self.__sonar_get_email(root, task, level, domain, reason):
                count_dict[data.value] = 1
                yield data
            # google 搜索接口
            for data1 in self.__google_get_email(root, task, level, domain, reason):
                count_dict[data1.value] = 1
                yield data1

        except Exception:
            self._logger.error(
                "Get email error:\ntaskid:{}\nbatchid:{}\nobj:{}\nerror:{}".format(
                    task.taskid,
                    task.batchid,
                    obj.value,
                    traceback.format_exc(),
                )
            )
        finally:
            log = f"获取到目标{domain}未经处理的{count_dict.__len__()}条{self.dtools.email}数据"
            self._outprglog(log)

    def __sonar_get_email(
        self, root: Domain, task: IscoutTask, level, domain, reason=None
    ):
        """
        email只返回email
        :param root:
        :param task:
        :param level:
        :param domain:
        :param reason:
        :return:
        """

        try:
            for data in SonarApi.domain_whois(task, level, domain, reason):
                # email插件只要email
                if isinstance(data, Email):
                    # self.__set_value(root, data)
                    root.set_email(data)
                    root = self.__segment_output(root, level, domain)
                    yield data
            task.success_count()
        except Exception:
            task.fail_count()
            self._logger.error(
                f"Get email from sonar whois error, err:{traceback.format_exc()}"
            )

    def __google_get_email(
        self, root: Domain, task: IscoutTask, level, domain, reason=None
    ):
        """
        google 搜索引擎解析email
        :param root:
        :param task:
        :param level:
        :param domain:
        :param reason:
        :return:
        """
        try:
            sapi = SearchApi(task)
            for data in sapi.domain_google_search_engine(domain, level, reason):
                # 输出截图数据
                if isinstance(data, Email):
                    root.set_email(data)
                    root = self.__segment_output(root, level, domain)
                    yield data
        except:
            self._logger.error(
                f"Get email from  google search engine error, err:{traceback.format_exc()}"
            )

    # --------------------------------------------------------------------------phone
    def _get_phone(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        去其它地方拿电话
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmddomain.enabled_phone:
            return
        self._logger.debug("DOMIAN:Start getting phone.")
        domain: str = obj.value
        log = f"开始探测目标{domain} {self.dtools.phone}信息"
        self._outprglog(log)
        # sonar接口
        count_dict = {}
        try:
            for data in self.__sonar_get_phone(root, task, level, domain, reason):
                count_dict[data.value] = 1
                yield data

            for data1 in self.__google_get_phone(root, task, level, domain, reason):
                count_dict[data1.value] = 1
                yield data1

        except:
            self._logger.error(f"Domain get phone error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{domain}未经处理的{count_dict.__len__()}条{self.dtools.phone}数据"
            self._outprglog(log)

    def __sonar_get_phone(
        self, root: Domain, task: IscoutTask, level, domain, reason=None
    ):
        """
        phone只返回phone
        :param root:
        :param task:
        :param level:
        :param domain:
        :param reason:
        :return:
        """
        try:
            for data in SonarApi.domain_whois(task, level, domain, reason):
                # email插件只要email
                if isinstance(data, Phone):
                    root.set_phone(data)
                    root = self.__segment_output(root, level, domain)
                    yield data
            task.success_count()
        except Exception:
            task.fail_count()
            self._logger.error(
                f"Get phone from sonar whois error, err:{traceback.format_exc()}"
            )

    def __google_get_phone(
        self, root: Domain, task: IscoutTask, level, domain, reason=None
    ):
        """
        google 搜索引擎解析phone
        :param root:
        :param task:
        :param level:
        :param domain:
        :param reason:
        :return:
        """
        try:
            sapi = SearchApi(task)
            for data in sapi.domain_google_search_engine(domain, level, reason):
                # 输出截图数据
                if isinstance(data, Phone):
                    root.set_phone(data)
                    root = self.__segment_output(root, level, domain)
                    yield data
        except:
            self._logger.error(
                f"Get google search engine result error, err:{traceback.format_exc()}"
            )

    # -------------------------------------------------------url list
    def _get_url_list(
        self, root: Domain, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        去google search拿 url list
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmddomain.enabled_url:
            return
        gs = None
        domain = obj.value
        log = f"开始收集目标{obj.value} {self.dtools.urlenum}信息"
        self._outprglog(log)
        self._logger.debug("DOMIAN:Start getting url list.")
        query = f"site:{domain}"
        count_dict = {}
        try:
            gs = GoogleSearch(task)
            for u_link in gs.get_search_link(query):
                url = URL(task, level, u_link)
                root.set_url(url)
                count_dict[url] = 1
                root = self.__segment_output(root, level, domain)
                yield url

        except:
            self._logger.error(f"Get url error, err:{traceback.format_exc()}")
        finally:
            # 实例化googlesearch不会出现问题
            log = f"获取到目标{obj.value}未经处理的{count_dict.__len__()}条{self.dtools.urlenum}数据"
            self._outprglog(log)
            if gs is not None:
                del gs

    # -----------------------------------------------------get ip geoinfo and ipwhois
    def __get_ip_whois_and_geoinfo(self, task: IscoutTask, level, ip: str, reason=None):
        """
        domain查询到的ip需要附带ip的whois信息和geoinfo
        relationfrom需要改为当前ip，相当于输出ip的信息
        :param task: 这个task里面附带的信息是输出需要带有的，需要修改的只是value 和 relatioform
        :param level:
        :param ip:
        :return:
        """
        ipinfo = IP(task, level, ip)
        ipinfo.relationfrom = ip  # 修改relationfrom的值
        try:
            db = DbipMmdb()
            gobj, org, isp = db.get_ip_mmdbinfo(level, ip)
            ipinfo.org = org
            ipinfo.isp = isp
            if gobj is None:
                for gobj in SonarApi.geoinfo(task, level, ip):
                    ipinfo.set_geolocation(gobj)
            else:
                ipinfo.set_geolocation(gobj)
        except:
            self._logger.error(
                f"Get ipinfo geoinfo error, err:{traceback.format_exc()}"
            )
        try:
            plgipwhois = IPWhois()
            iw = plgipwhois.get_ipwhois(ip, reason)
            ipinfo.set_ipwhois(iw)
        except:
            self._logger.error(f"Get ipinfo whoid error, err:{traceback.format_exc()}")

        if ipinfo._subitem_count() > 0:
            self.outputdata(ipinfo.get_outputdict(), ipinfo._suffix)
        return
