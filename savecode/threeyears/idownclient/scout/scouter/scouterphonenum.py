"""
phone num scouter
2019/07/10
"""
import traceback

from datacontract import EObjectType, IscoutTask
from outputmanagement import OutputManagement

from ...clientdatafeedback.scoutdatafeedback import (
    Email,
    NetworkGroup,
    NetworkMsg,
    NetworkMsgs,
    NetworkProfile,
    NetworkProfiles,
    NetworkResource,
    Phone,
    ScoutFeedBackBase,
    ScreenshotSE,
    SearchEngine,
    SearchFile,
    Whoisr,
)
from ..plugin import SearchApi, SonarApi, TelegramPublic, TelegramLanding
from .scouterbase import ScouterBase


class ScouterPhoneNum(ScouterBase):
    """"""

    TARGET_OBJ_TYPE = EObjectType.PhoneNum

    def __init__(self, task: IscoutTask):
        ScouterBase.__init__(self, task)

    def __segment_output(self, root: Phone, level, phone) -> Phone:
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
            root: Phone = Phone(self.task, level, phone)
        return root

    def __output_getdata(self, root: Phone, level, phone: str) -> Phone:
        """
        单个插件拿到的数据太大了，每个插件执行完成后都输出下
        :param root:
        :param level:
        :param domain:
        :return:
        """
        if root._subitem_count() > 0:
            self.outputdata(root.get_outputdict(), root._suffix)
            root: Phone = Phone(self.task, level, phone)
        return root

    def __segment_output_profiles(self, profiles: NetworkProfiles) -> NetworkProfiles:
        """
        输出 iscout_networkid_profile 数据
        """
        if not isinstance(profiles, NetworkProfiles):
            raise Exception("Invalid NetworkProfiles for segment output")

        if len(profiles) >= self.max_output:
            self.outputdata(profiles.get_outputdict(), profiles._suffix)
            profiles = NetworkProfiles(self.task)

        return profiles

    def __segment_output_msgs(self, msgs: NetworkMsgs) -> NetworkMsgs:
        """
        输出 iscout_networkid_profile 数据
        """
        if not isinstance(msgs, NetworkMsgs):
            raise Exception("Invalid NetworkProfiles for segment output")

        if len(msgs) >= self.max_output:
            self.outputdata(msgs.get_outputdict(), msgs._suffix)
            msgs = NetworkMsgs(self.task)

        return msgs

    def __output_resources(self, resource: NetworkResource):
        """
        资源文件是直接输出，
        因为resource继承的output，所以调用输出器输出，到时候问下配不配
        :param resource:
        :return:
        """
        OutputManagement.output(resource)
        return

    def __set_value(self, root: Phone, data):
        """
        统一setvalue
        :param root:
        :param data:
        :return:
        """
        if isinstance(data, Whoisr):
            root.set_whoisr(data)
        elif isinstance(data, NetworkGroup):
            root.set_networkid_group(data)
        elif isinstance(data, SearchEngine):
            root.set_searchengine(data)

    def _scoutsub(self, level: int, obj: ScoutFeedBackBase) -> iter:
        # whoisr
        root: Phone = Phone(self.task, level, obj.value)
        try:
            # whoisr
            for whoisr in self._get_whoisr(
                root, self.task, level, obj, reason=self.dtools.whois_reverse
            ):
                yield whoisr
            root = self.__output_getdata(root, level, phone=obj.value)

            # landing
            # 目前的phone只有telegram，所以现在先写在这吧，等以后要加了再拆
            for data in self._landing(
                root, self.task, level, obj, reason=self.dtools.landing_telegram
            ):
                yield data
            root = self.__output_getdata(root, level, phone=obj.value)

            # searchengine
            for data in self._get_searchengine(
                root, self.task, level, obj, reason=self.dtools.urlInfo
            ):
                yield data
            root = self.__output_getdata(root, level, phone=obj.value)

            for data in self._get_email(
                root, self.task, level, obj, reason=self.dtools.email
            ):
                yield data
            root = self.__output_getdata(root, level, phone=obj.value)

            # public
            self._public(
                root, self.task, level, obj, reason=self.dtools.public_telegram
            )

        except:
            self._logger.error(f"Scouter phonenum error, err:{traceback.format_exc()}")
        finally:
            # 最后结束完成也要输出
            if root._subitem_count() > 0:
                self.outputdata(root.get_outputdict(), root._suffix)

    # -------------------------------------------------whoisr
    def _get_whoisr(
        self, root: Phone, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ) -> iter:
        """
        去调子类下载的东西
        :return:
        """
        if not task.cmd.stratagyscout.cmdphone.enabled_whois_reverse:
            return

        self._logger.debug("PHONE:Start getting whois.")

        phone: str = obj.value
        log = f"开始收集目标{phone} {self.dtools.whois_reverse}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            for pw in self._get_sonar_whoisr(root, task, level, phone):
                count_dict[pw._domain] = 1
                yield pw

        except:
            self._logger.error(f"Get whois error, err:{traceback.format_exc()}")
        finally:
            log = (
                f"获取到目标{phone}未经处理的{count_dict.__len__()}条{self.dtools.whois_reverse}数据"
            )
            self._outprglog(log)

    def _get_sonar_whoisr(self, root: Phone, task: IscoutTask, level, phone) -> iter:
        """
        去调子类下载的东西
        :return:
        """
        try:
            for pw in SonarApi.phone_whoisr(task, level, phone):
                self.__set_value(root, pw)
                root = self.__segment_output(root, level, phone)
                yield pw
            self.task.success_count()
        except:
            self.task.fail_count()
            self._logger.error(
                f"Get whois from sonar api error, err:{traceback.format_exc()}"
            )

    # -----------------------------------------------------------------telegram network id

    def _landing(
        self, root: Phone, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        账号落地详情监控，应该把实现工具分开写的，后面加了再分吧

        telegram落地流程大改 by judy 20201109
        现在分为两种情况
        1.不是自己的手机号，那么落地出来的就是别人的手机号信息
        2.是自己的手机号，那么落地出来的就有自己的信息和这个群的信息
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """

        if not task.cmd.stratagyscout.cmdphone.enabled_landing_telegram:
            return

        self._logger.debug("PHONE:Start landing")
        phone = obj.value
        log = f"开始收集目标{phone} {self.dtools.landing_telegram}信息"
        self._outprglog(log)
        tel_plugin = TelegramLanding(task)
        count = 0
        try:
            for l_data in tel_plugin.landing(phone, level, reason):
                if isinstance(l_data, NetworkProfile):
                    # 回来个人信息
                    root.set_networkid_profile(l_data)
                else:
                    # 回来群组信息
                    self.__set_value(root, l_data)
                count += 1
                root = self.__segment_output(root, level, phone)
                yield l_data
        except:
            self._logger.error(
                f"Get telegram landing data error\nerr:{traceback.format_exc()}"
            )
        finally:
            log = f"获取到目标{phone}未经处理的{count}条{self.dtools.landing_telegram}数据"
            self._outprglog(log)
            del tel_plugin

    def _public(
        self, root: Phone, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        这是用落地的信息去取舆情，
        唉，奇葩需求，咋办呢，写呗
        2019/10/16 修改后好多了，不是去拿每一个群组的信息，而只是拿指定目标的信息
        目前只有telegram的public，以后加入了message再分也可
        2019/10/31 现在又说要把群组和信息一起拿回来了,唉，先把功能实现了后面再来优化吧
        2020/10/28 目前的需求是说落地拿的是账号自己的群组信息，然后public的时候再去根据群组id去拿信息
        :param obj:
        :param reason:
        :return:
        """
        if not self.task.cmd.stratagyscout.cmdphone.enabled_public_telegram:
            return
        self._logger.debug("PHONE:Start public.")
        phone = obj.value
        log = f"开始收集目标{phone} {self.dtools.public_telegram}信息"
        self._outprglog(log)
        networkprofiles: NetworkProfiles = NetworkProfiles(self.task)
        networkpromsgs: NetworkMsgs = NetworkMsgs(self.task)
        tel_plugin = TelegramPublic(task)
        try:
            count = 0
            for p_data in tel_plugin.public(phone, reason):
                if isinstance(p_data, NetworkProfile):
                    networkprofiles.set_profile(p_data)
                    count += 1
                    networkprofiles = self.__segment_output_profiles(networkprofiles)
                if isinstance(p_data, NetworkMsg):
                    networkpromsgs.set_msgs(p_data)
                    count += 1
                    networkpromsgs = self.__segment_output_msgs(networkpromsgs)
                if isinstance(p_data, NetworkResource):
                    self.__output_resources(p_data)
                    count += 1
            log = f"获取到目标{phone}未经处理的{count}条{self.dtools.public_telegram}数据"
            self._outprglog(log)
        except:
            self._logger.error(f"Public telegram error, err:{traceback.format_exc()}")
        finally:
            # 最后结束完成也要输出，这样可以保证把拿到的数据输出了，免得出啥幺蛾子
            if len(networkprofiles) > 0:
                self.outputdata(
                    networkprofiles.get_outputdict(), networkprofiles._suffix
                )

            if len(networkpromsgs) > 0:
                self.outputdata(networkpromsgs.get_outputdict(), networkpromsgs._suffix)
            del tel_plugin

    def _get_searchengine(
        self, root: Phone, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ):
        """
        搜索引擎全词匹配目标电话相关信息
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        phone = obj.value

        try:
            for data in self._get_google_searchengine(root, task, level, phone, reason):
                yield data
            for data1 in self._get_bing_searchengine(root, task, level, phone, reason):
                yield data1
            for data2 in self._get_baidu_searchengine(root, task, level, phone, reason):
                yield data2

        except:

            self._logger.error(f"Get search res error, err:{traceback.format_exc()}")

    def _get_google_searchengine(
        self, root: Phone, task: IscoutTask, level, phone, reason=None
    ):
        """
        google search
        :param root:
        :param task:
        :param level:
        :param phone:
        :param reason:
        :return:
        """
        if not task.cmd.stratagyscout.cmdphone.enabled_searchgoogle:
            return
        log = f"开始收集目标{phone} {self.dtools.google}信息"
        self._outprglog(log)
        self._logger.debug("PHONE:Start google search.")
        count = 0
        try:
            keywords = (
                task.cmd.stratagyscout.cmdphone.searchengine.search_google.keywords
            )
            filetypes = (
                task.cmd.stratagyscout.cmdphone.searchengine.search_google.filetypes
            )
            sapi = SearchApi(task)
            for data in sapi.text_google_search_engine(
                keywords, filetypes, phone, level, self.dtools.google
            ):
                # 输出截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    root = self.__segment_output(root, level, phone)
                    count += 1
                    yield data

        except:
            self._logger.error(f"Get google search error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{phone}未经处理的{count}条{self.dtools.google}数据"
            self._outprglog(log)

    def _get_bing_searchengine(
        self, root: Phone, task: IscoutTask, level, phone, reason=None
    ):
        """
        google search
        :param root:
        :param task:
        :param level:
        :param phone:
        :param reason:
        :return:
        """
        if not task.cmd.stratagyscout.cmdphone.enabled_searchbing:
            return
        log = f"开始收集目标{phone} {self.dtools.bing}信息"
        self._outprglog(log)
        self._logger.debug("PHONE:Start bing search.")
        count = 0
        try:
            keywords = task.cmd.stratagyscout.cmdphone.searchengine.search_bing.keywords
            filetypes = (
                task.cmd.stratagyscout.cmdphone.searchengine.search_bing.filetypes
            )
            sapi = SearchApi(task)
            for data in sapi.text_bing_search_engine(
                keywords, filetypes, phone, level, self.dtools.bing
            ):
                # 输出截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    root = self.__segment_output(root, level, phone)
                    count += 1
                    yield data

        except:
            self._logger.error(f"Get bing search error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{phone}未经处理的{count}条{self.dtools.bing}数据"
            self._outprglog(log)

    def _get_baidu_searchengine(
        self, root: Phone, task: IscoutTask, level, phone, reason=None
    ):
        """
        google search
        :param root:
        :param task:
        :param level:
        :param phone:
        :param reason:
        :return:
        """
        if not task.cmd.stratagyscout.cmdphone.enabled_searchbaidu:
            return
        log = f"开始收集目标{phone} {self.dtools.baidu}信息"
        self._outprglog(log)
        self._logger.debug("PHONE:Start baidu search.")
        count = 0
        try:
            keywords = (
                task.cmd.stratagyscout.cmdphone.searchengine.search_baidu.keywords
            )
            filetypes = (
                task.cmd.stratagyscout.cmdphone.searchengine.search_baidu.filetypes
            )
            sapi = SearchApi(task)
            for data in sapi.text_baidu_search_engine(
                keywords, filetypes, phone, level, self.dtools.baidu
            ):
                # 输出截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    root = self.__segment_output(root, level, phone)
                    count += 1
                    yield data

        except:
            self._logger.error(f"Get baidu search error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{phone}未经处理的{count}条{self.dtools.baidu}数据"
            self._outprglog(log)

    # -----------------------------------------------email
    def _get_email(
        self, root: Phone, task: IscoutTask, level, obj: ScoutFeedBackBase, reason=None
    ) -> iter:
        """
        去重新调用插件获取email信息
        :return:
        """
        if not task.cmd.stratagyscout.cmdphone.enabled_email:
            return
        self._logger.debug("PHONE:Start getting email.")
        phone = obj.value
        log = f"开始收集目标{phone} {self.dtools.email}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            for data in self._google_search_email(root, task, level, phone, reason):
                count_dict[data.value] = 1
                yield data
            for data1 in self._sonarapi_get_email(root, task, level, phone, reason):
                count_dict[data1.value] = 1
                yield data1
        except:
            self._logger.error(f"Get email info error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{phone}未经处理的{count_dict.__len__()}条{self.dtools.email}数据"
            self._outprglog(log)

    def _google_search_email(
        self, root: Phone, task: IscoutTask, level, phone, reason=None
    ):
        """
        匹配google搜索引擎的结果里的email
        :param root:
        :param task:
        :param level:
        :param phone:
        :param reason:
        :return:
        """
        try:
            keywords = (
                task.cmd.stratagyscout.cmdphone.searchengine.search_google.keywords
            )
            filetypes = []
            sapi = SearchApi(task)
            for data in sapi.text_google_search_engine(
                keywords, filetypes, phone, level, reason
            ):
                # 输出截图数据
                if isinstance(data, Email):
                    root.set_email(data)
                    root = self.__segment_output(root, level, phone)
                    yield data
        except:
            self._logger.error(
                f"Get email from google search res error, err:{traceback.format_exc()}"
            )

    def _sonarapi_get_email(self, root: Phone, task: IscoutTask, level, phone, reason):
        """
        sonar api 先去查whoisr，然后使用查到的domain，再去domain whois那边拿phone
        :param root:
        :param task:
        :param level:
        :param phone:
        :param reason:
        :return:
        """
        try:
            for ew in SonarApi.phone_whoisr(task, level, phone):
                domain = ew._domain
                self._logger.debug(f"Sonar search a domain:{domain}.")
                for data in SonarApi.domain_whois(task, level, domain, reason):
                    if isinstance(data, Email):
                        root.set_email(data)
                        root = self.__segment_output(root, level, domain)
                        yield data
            task.success_count()
        except:
            task.fail_count()
            self._logger.error(
                f"Get email from sonar api error, err:{traceback.format_exc()}"
            )
