"""
scouter email
2019/07/10
"""
import traceback
import tld

from datacontract import EObjectType, IscoutTask
from .scouterbase import ScouterBase
from ..plugin import SonarApi, MXQuery, SearchApi, FBSearchEmail
from ...clientdatafeedback.scoutdatafeedback import (
    Email,
    ScoutFeedBackBase,
    Whoisr,
    MailServer,
    SearchEngine,
    ScreenshotSE,
    SearchFile,
    Phone,
    NetworkProfile,
    NetworkId,
    NetworkProfiles,
)
from outputmanagement import OutputManagement


class ScouterEMail(ScouterBase):
    """
    scouter email
    """

    TARGET_OBJ_TYPE = EObjectType.EMail

    def __init__(self, task: IscoutTask):
        ScouterBase.__init__(self, task)

    def __segment_output(self, root: Email, level, email) -> Email:
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
            root: Email = Email(self.task, level, email)
        return root

    def __segment_output_profiles(self, profiles: NetworkProfiles) -> NetworkProfiles:
        """输出 iscout_networkid_profile 数据"""
        if not isinstance(profiles, NetworkProfiles):
            raise Exception("Invalid NetworkProfiles for segment output")

        if len(profiles) >= self.max_output:
            self.outputdata(profiles.get_outputdict(), profiles._suffix)
            profiles = NetworkProfiles(self.task)

        return profiles

    def __output_getdata(self, root: Email, level, email: str) -> Email:
        """
        单个插件拿到的数据太大了，每个插件执行完成后都输出下
        :param root:
        :param level:
        :param email:
        :return:
        """
        if root._subitem_count() > 0:
            self.outputdata(root.get_outputdict(), root._suffix)
            root: Email = Email(self.task, level, email)
        return root

    def __set_value(self, root: Email, data):
        """
        插入数据
        :param root:
        :param data:
        :return:
        """
        if isinstance(data, Whoisr):
            root.set_whoisr(data)
        elif isinstance(data, MailServer):
            root.set_mailserver(data)
        elif isinstance(data, SearchEngine):
            root.set_searchengine(data)

    def _scoutsub(self, level: int, obj: ScoutFeedBackBase) -> iter:
        root: Email = Email(self.task, level, obj.value)
        # whoisr
        try:
            # whoisr
            for whoisr in self._get_whoisr(
                root, self.task, level, obj, reason=self.dtools.whois_reverse
            ):
                yield whoisr
            # 每完成一个插件输出一次，避免数据过大导致入库的问题
            root = self.__output_getdata(root, level, email=obj.value)

            # mailserver
            for mailserver in self._get_mailserver(
                root, self.task, level, obj, reason=self.dtools.mail_server
            ):
                yield mailserver
            root = self.__output_getdata(root, level, email=obj.value)

            # ---------------------------------新增
            # landing，public，这里的处理有点复杂，可能到时候需要自定义怎么实现
            # 这里的reason是随便给的，插件具体使用的时候自己指定
            for data in self._landing(
                root, self.task, level, obj, reason=self.dtools.landing_messenger
            ):
                yield data
            root = self.__output_getdata(root, level, email=obj.value)

            # searchengine
            for data in self._get_searchengine(
                root, self.task, level, obj, reason=self.dtools.urlInfo
            ):
                yield data
            root = self.__output_getdata(root, level, email=obj.value)

            for data in self._get_phone(
                root, self.task, level, obj, reason=self.dtools.phone
            ):
                yield data
            root = self.__output_getdata(root, level, email=obj.value)

            # public
            self._public(obj, reason=self.dtools.public_twitter)

        except:
            self._logger.error(f"Scouter mail error, err:{traceback.format_exc()}")

        finally:
            # 最后结束完成也要输出
            if root._subitem_count() > 0:
                self.outputdata(root.get_outputdict(), root._suffix)

    # --------------------------------------whoisr
    def _get_whoisr(
        self, root: Email, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ) -> iter:
        """
        根据邮箱账号来反查
        :return:
        """
        if not task.cmd.stratagyscout.cmdemail.enabled_whois_reverse:
            return

        self._logger.debug("EMIAL:Start getting whoisr")

        email: str = obj.value
        log = f"开始收集目标{email} {self.dtools.whois_reverse}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            for ew in self.__get_sonar_whoisr(root, task, level, email):
                count_dict[ew._domain] = 1
                yield ew

        except:
            self._logger.error(f"Get whoisr data error, err:{traceback.format_exc()}")
        finally:
            log = (
                f"获取到目标{email}未经处理的{count_dict.__len__()}条{self.dtools.whois_reverse}数据"
            )
            self._outprglog(log)

    def __get_sonar_whoisr(self, root: Email, task: IscoutTask, level, email):
        """
        sonar的api
        :param root:
        :param task:
        :param level:
        :param email:
        :return:
        """
        try:
            for ew in SonarApi.email_whoisr(task, level, email):
                self.__set_value(root, ew)
                root = self.__segment_output(root, level, email)
                yield ew
            task.success_count()
        except:
            task.fail_count()
            self._logger.error(
                f"Get Sonar email whoisr error, err:{traceback.format_exc()}"
            )

    # -------------------------email server
    def _get_mailserver(
        self, root: Email, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        根据邮箱后缀查询邮件服务地址
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmdemail.enabled_mailserver:
            return

        self._logger.debug("EMIAL:Start getting mail server")

        email: str = tld.get_tld(
            obj.value, fail_silently=True, as_object=True, fix_protocol=True
        ).fld
        log = f"开始收集目标{email} {self.dtools.mail_server}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            for ms in self.__get_mx_email_server(root, task, level, email):
                count_dict[ms._host] = 1
                yield ms
        except:
            self._logger.error(f"Get mx mailserver error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{email}未经处理的{count_dict.__len__()}条{self.dtools.mail_server}数据"
            self._outprglog(log)

    def __get_mx_email_server(self, root: Email, task: IscoutTask, level, email):
        """
        根据mx记录查询邮服地址
        :param root:
        :param task:
        :param level:
        :param email:
        :return:
        """
        try:
            mxq = MXQuery(task)
            for ms in mxq.get_mail_server(level, email):
                self.__set_value(root, ms)
                root = self.__segment_output(root, level, email)
                yield ms
            task.success_count()
        except:
            task.fail_count()
            self._logger.error(f"Get mx maiserver error, err:{traceback.format_exc()}")

    def _landing(
        self, root: Email, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        目标账号落地到各大主流网站的网络id 信息
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """

        if not task.cmd.stratagyscout.cmdemail.enabled_landing_facebook:
            return
        self._logger.debug("EMIAL:Start landing")
        log = f"开始收集目标{obj.value} {self.dtools.landing_facebook}信息"
        self._outprglog(log)
        networkprofiles: NetworkProfiles = NetworkProfiles(self.task)
        count = 0
        try:

            fb = FBSearchEmail(self.task)
            for res in fb._search_email(root._email, level):
                count += 1
                if isinstance(res, NetworkProfile):
                    networkprofiles.set_profile(res)
                    networkprofiles = self.__segment_output_profiles(networkprofiles)
                yield res

        except:
            pass
        finally:
            log = f"获取到目标{obj.value}未经处理的{count}条{self.dtools.landing_facebook}数据"
            self._outprglog(log)
            # 最后输出,最后剩下没有输出的，一定要输出，不管拿到多少个
            if len(networkprofiles) > 0:
                self.outputdata(
                    networkprofiles.get_outputdict(), networkprofiles._suffix
                )

    def _public(self, obj: ScoutFeedBackBase, reason=None):
        """
        这里是用网络id去拿舆情信息
        修改逻辑后是根据拿到的具体信息后再去拿相关的信息
        而且public的数据是不会加入root的，所以这样就好
        :param obj:
        :return:
        """
        if not self.task.cmd.stratagyscout.cmdemail:
            return
        self._logger.debug("EMIAL:Start public")
        return

    def _get_searchengine(
        self, root: Email, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        搜索引擎全词匹配目标邮箱账号相关信息
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        email = obj.value

        try:
            for data in self._get_google_searchengine(root, task, level, email, reason):
                yield data
            for data1 in self._get_bing_searchengine(root, task, level, email, reason):
                yield data1
            for data2 in self._get_baidu_searchengine(root, task, level, email, reason):
                yield data2
        except:
            self._logger.error(f"Get search engine error, err:{traceback.format_exc()}")

    def _get_google_searchengine(
        self, root: Email, task: IscoutTask, level, email, reason=None
    ):
        """
        google search engine
        :param root:
        :param task:
        :param level:
        :param email:
        :param reason:
        :return:
        """
        if not task.cmd.stratagyscout.cmdemail.enabled_searchgoogle:
            return
        log = f"开始收集目标{email} {self.dtools.google}信息"
        self._outprglog(log)
        self._logger.debug("EMIAL:Start getting google search result")
        keywords: list = (
            task.cmd.stratagyscout.cmdemail.searchengine.search_google.keywords
        )
        filetypes: list = (
            task.cmd.stratagyscout.cmdemail.searchengine.search_google.filetypes
        )
        count = 0
        try:

            sapi = SearchApi(task)
            for data in sapi.text_google_search_engine(
                keywords, filetypes, email, level, self.dtools.google
            ):
                # 输出截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    count += 1
                    root = self.__segment_output(root, level, email)
                    yield data

        except:
            self._logger.error(f"Get google search error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{email}未经处理的{count}条{self.dtools.google}数据"
            self._outprglog(log)

    def _get_bing_searchengine(
        self, root: Email, task: IscoutTask, level, email, reason=None
    ):
        """
        bing search engine
        :param root:
        :param task:
        :param level:
        :param email:
        :param reason:
        :return:
        """
        if not task.cmd.stratagyscout.cmdemail.enabled_searchbing:
            return
        log = f"开始收集目标{email} {self.dtools.bing}信息"
        self._outprglog(log)
        self._logger.debug("EMIAL:Start getting bing search result")
        keywords: list = (
            task.cmd.stratagyscout.cmdemail.searchengine.search_bing.keywords
        )
        filetypes: list = (
            task.cmd.stratagyscout.cmdemail.searchengine.search_bing.filetypes
        )
        count = 0
        try:

            sapi = SearchApi(task)
            for data in sapi.text_bing_search_engine(
                keywords, filetypes, email, level, self.dtools.bing
            ):
                # 输出截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    count += 1
                    root = self.__segment_output(root, level, email)
                    yield data

        except:
            self._logger.error(f"Get bing search error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{email}未经处理的{count}条{self.dtools.bing}数据"
            self._outprglog(log)

    def _get_baidu_searchengine(
        self, root: Email, task: IscoutTask, level, email, reason=None
    ):
        """
        baidu search engine
        :param root:
        :param task:
        :param level:
        :param email:
        :param reason:
        :return:
        """
        if not task.cmd.stratagyscout.cmdemail.enabled_searchbaidu:
            return
        log = f"开始收集目标{email} {self.dtools.baidu}信息"
        self._outprglog(log)
        self._logger.debug("EMIAL:Start getting baidu search result")
        keywords: list = (
            task.cmd.stratagyscout.cmdemail.searchengine.search_baidu.keywords
        )
        filetypes: list = (
            task.cmd.stratagyscout.cmdemail.searchengine.search_baidu.filetypes
        )
        count = 0
        try:
            sapi = SearchApi(task)
            for data in sapi.text_baidu_search_engine(
                keywords, filetypes, email, level, self.dtools.baidu
            ):
                # 输出截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    count += 1
                    root = self.__segment_output(root, level, email)
                    yield data

        except:
            self._logger.error(f"Get baidu search error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{email}未经处理的{count}条{self.dtools.baidu}数据"
            self._outprglog(log)

    # phone
    def _get_phone(
        self, root: Email, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        根据插件信息去查phone
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmdemail.enabled_phone:
            return
        self._logger.debug("EMIAL:Start getting phone")
        email = obj.value
        log = f"开始收集目标{email} {self.dtools.phone}信息"
        self._outprglog(log)
        # 搜索引擎
        count_dict = {}
        try:
            for data in self._google_search_phone(root, task, level, email, reason):
                count_dict[data.value] = 1
                yield data
            # whois里面的信息
            for data1 in self._sonarapi_get_phone(root, task, level, email, reason):
                count_dict[data1.value] = 1
                yield data1
        except:
            self._logger.error(f"Get phone info error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{email}未经处理的{count_dict.__len__()}条{self.dtools.phone}数据"
            self._outprglog(log)

    def _google_search_phone(self, root: Email, task: IscoutTask, level, email, reason):
        """
        google浏览器去提取phone信息
        :param root:
        :param task:
        :param level:
        :param email:
        :param reason:
        :return:
        """
        try:
            keywords: list = (
                task.cmd.stratagyscout.cmdemail.searchengine.search_google.keywords
            )
            # filetypes: list = task.cmd.stratagyscout.cmdemail.searchengine.search_google.filetypes
            filetypes: list = []

            sapi = SearchApi(task)
            for data in sapi.text_google_search_engine(
                keywords, filetypes, email, level, reason
            ):
                if isinstance(data, Phone):
                    root.set_phone(data)
                    root = self.__segment_output(root, level, email)
                    yield data
        except:
            self._logger.error(
                f"Get phone from google search engine error, err:{traceback.format_exc()}"
            )

    def _sonarapi_get_phone(self, root: Email, task: IscoutTask, level, email, reason):
        """
        sonar api 先去查whoisr，然后使用查到的domain，再去domain whois那边拿phone
        :param root:
        :param task:
        :param level:
        :param email:
        :param reason:
        :return:
        """
        try:
            for ew in SonarApi.email_whoisr(task, level, email):
                domain = ew._domain
                self._logger.debug(f"Sonar search a domain:{domain}")
                for data in SonarApi.domain_whois(task, level, domain, reason):
                    if isinstance(data, Phone):
                        root.set_phone(data)
                        root = self.__segment_output(root, level, domain)
                        yield data
            task.success_count()
        except:
            task.fail_count()
            self._logger.error(
                f"Get phone from sonar api error, err:{traceback.format_exc()}"
            )
