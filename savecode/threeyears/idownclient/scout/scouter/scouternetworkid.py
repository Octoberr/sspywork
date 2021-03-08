"""
networkid scouter
2019/07/10
"""
import json
import traceback

from datacontract import EObjectType, IscoutTask
from datacontract.idowncmd.iscoutcmd import SS, NetidInfo
from outputmanagement import OutputManagement

from ...clientdatafeedback.scoutdatafeedback import (
    Email,
    NetworkId,
    NetworkMsgs,
    NetworkPost,
    NetworkPosts,
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
from ..plugin import Facebook, LandingTwitter, PublicTwitter, SearchApi, SonarApi
from ..plugin.instagram import Instagram
from .scouterbase import ScouterBase


class ScouterNetworkId(ScouterBase):
    TARGET_OBJ_TYPE = EObjectType.NetworkId

    def __init__(self, task: IscoutTask):
        ScouterBase.__init__(self, task)

    def __segment_output(self, root: NetworkId, level, objvalue) -> NetworkId:
        """
        分段输出数据，达到分段输出的标准后给新的root
        没有达到那么就给旧的root
        :param root:
        :return:
        """
        if not isinstance(root, NetworkId):
            raise Exception("Invalid NetworkId for segment output")
        # 加载到max output就输出
        # 如果输出了那么就返回新的根节点
        if root._subitem_count() >= self.max_output:
            self.outputdata(root.get_outputdict(), root._suffix)
            root: NetworkId = NetworkId(self.task, level, objvalue)
        # 如果是老的那么就将根节点原封不动返回即可
        return root

    def __output_getdata(self, root: NetworkId, level, networkid: str) -> NetworkId:
        """
        单个插件拿到的数据太大了，每个插件执行完成后都输出下
        :param root:
        :param level:
        :param domain:
        :return:
        """
        if root._subitem_count() > 0:
            self.outputdata(root.get_outputdict(), root._suffix)
            root: NetworkId = NetworkId(self.task, level, networkid)
        return root

    def __segment_output_profiles(self, profiles: NetworkProfiles) -> NetworkProfiles:
        """输出 iscout_networkid_profile 数据"""
        if not isinstance(profiles, NetworkProfiles):
            raise Exception("Invalid NetworkProfiles for segment output")

        if len(profiles) >= self.max_output:
            self.outputdata(profiles.get_outputdict(), profiles._suffix)
            profiles = NetworkProfiles(self.task)

        return profiles

    def __segment_output_msgs(self, msgs: NetworkMsgs) -> NetworkMsgs:
        """输出 iscout_networkid_msgs 数据"""
        if not isinstance(msgs, NetworkMsgs):
            raise Exception("Invalid NetworkMsgs for segment output")

        if len(msgs) >= self.max_output:
            self.outputdata(msgs.get_outputdict(), msgs._suffix)
            msgs = NetworkMsgs(self.task)

        return msgs

    def __segment_output_posts(self, posts: NetworkPosts) -> NetworkPosts:
        """输出 iscout_networkid_posts 数据"""
        if not isinstance(posts, NetworkPosts):
            raise Exception("Invalid NetworkPosts for segment output")

        if len(posts) >= self.max_output:
            self.outputdata(posts.get_outputdict(), posts._suffix)
            posts = NetworkPosts(self.task)

        return posts

    def __set_value(self, root: NetworkId, data):
        """
        统一setvalue
        :param root:
        :param data:
        :return:
        """
        if isinstance(data, NetworkProfile):
            root.set_networkid_profile(data)
        # if isinstance(data, Email):
        #     root.set_email(data)
        # if isinstance(data, Phone):
        #     root.set_phone(data)
        elif isinstance(data, Whoisr):
            root.set_whoisr(data)
        elif isinstance(data, SearchEngine):
            root.set_searchengine(data)

    def _scoutsub(self, level, obj: ScoutFeedBackBase) -> iter:
        root: NetworkId = NetworkId(self.task, level, obj.value)
        # 身份落地
        try:
            # networkid whois 反查
            for data in self._get_whois(
                root, self.task, level, obj, reason=self.dtools.whois
            ):
                yield data
            root = self.__output_getdata(root, level, networkid=obj.value)

            # searchengine
            for data in self._get_searchengine(
                root, self.task, level, obj, reason=self.dtools.urlInfo
            ):
                yield data
            root = self.__output_getdata(root, level, networkid=obj.value)

            # landing
            for profile in self._landing(root, self.task, level, obj):
                yield profile
            # 这里的root出来会有东西，所以重置一下，里面已经输出过了后面需要把每个社交相关武器写独立业务
            root = NetworkId(self.task, level, networkid=obj.value)

            # email 这个要单独写业务
            for data in self._get_email(
                root, self.task, level, obj, reason=self.dtools.email
            ):
                yield data
            root = self.__output_getdata(root, level, networkid=obj.value)

            # phone 要单独写业务
            for data in self._get_phone(
                root, self.task, level, obj, reason=self.dtools.phone
            ):
                yield data
            root = self.__output_getdata(root, level, networkid=obj.value)

            # public
            # 这里不用传root进去，传进去没用，
            # 舆情监控不属于根实体
            self._public(level, obj)
        except:
            self._logger.error(f"Scouter networkid error, err:{traceback.format_exc()}")
        finally:
            # 这样写即保证即时出错了也要把拿到的数据输出出来，谁知道会出什么幺蛾子呢
            # 所有插件执行完成后再判断下还有没有新的数据，然后输出下
            if root._subitem_count() > 0:
                self.outputdata(root.get_outputdict(), root._suffix)

    #################################################
    # landing
    def _landing(
        self, root: NetworkId, task: IscoutTask, level, obj: ScoutFeedBackBase
    ):
        """landing"""
        try:
            # landing facebook
            if task.cmd.stratagyscout.cmdnetworkid.enabled_landing_facebook:
                self._logger.debug("NETWORKID:Start landing facebook.")
                log = f"开始收集目标{obj.value} {self.dtools.landing_facebook}信息"
                self._outprglog(log)
                count = 0
                for profile in self._landing_facebook(
                    root, level, obj, self.dtools.landing_facebook
                ):
                    self.__set_value(root, profile)
                    count += 1
                    root = self.__segment_output(root, level, obj.value)
                    yield profile
                # 结束完成输出获取的数据
                root = self.__output_getdata(root, level, networkid=obj.value)
                log = f"获取到目标{obj.value}未经处理的{count}条{self.dtools.landing_facebook}数据"
                self._outprglog(log)
            # landing twitter

            if task.cmd.stratagyscout.cmdnetworkid.enabled_landing_twitter:
                self._logger.debug("NETWORKID:Start landing twitter.")
                log = f"开始收集目标{obj.value} {self.dtools.landing_twitter}信息"
                self._outprglog(log)
                count = 0
                for profile in self._landing_twitter(
                    root, task, level, obj.value, self.dtools.landing_twitter
                ):
                    self.__set_value(root, profile)
                    count += 1
                    root = self.__segment_output(root, level, obj.value)
                    yield profile
                # 结束了输出
                root = self.__output_getdata(root, level, networkid=obj.value)
                log = f"获取到目标{obj.value}未经处理的{count}条{self.dtools.landing_twitter}数据"
                self._outprglog(log)
            # landing instagram
            # 注(仅我自己): 只当前业务文件下,涉及cmdnetworkid位置(即:iscoutcmd文件中的全是instgram)
            # 其余位置是正确的instagram拼写                                   ---------20200109 tms
            if task.cmd.stratagyscout.cmdnetworkid.enabled_landing_instgram:
                self._logger.debug("NETWORKID:Start landing instagram.")
                for profile in self._landing_instagram(
                    root, task, level, obj, self.dtools.landing_instagram
                ):
                    self.__set_value(root, profile)
                    root = self.__segment_output(root, level, obj.value)
                    yield profile
                # 输出获取的数据
                root = self.__output_getdata(root, level, networkid=obj.value)
        except Exception:
            self._logger.error(f"Landing networkid error, err:{traceback.format_exc()}")

    def _landing_facebook(
        self, root: NetworkId, level, obj: ScoutFeedBackBase, reason
    ) -> iter:
        """get facebook profiles by search username"""

        networkprofiles: NetworkProfiles = None
        try:
            fb: Facebook = Facebook(self.task)
            networkprofiles: NetworkProfiles = NetworkProfiles(self.task)

            got: bool = False
            if (
                not fb is None
                and fb._is_logined
                and self.task.cmd.stratagyscout.cmdnetworkid is not None
                and len(self.task.cmd.stratagyscout.cmdnetworkid.netidinfo) > 0
            ):
                # 这里是为了 当用于直接输入某个userid/url时，能够精准定位到某个用户
                for (
                    netidinfo_fb
                ) in self.task.cmd.stratagyscout.cmdnetworkid.netidinfo.values():
                    netidinfo_fb: NetidInfo = netidinfo_fb
                    if (
                        not isinstance(netidinfo_fb._source, str)
                        or netidinfo_fb._source != "facebook"
                    ):
                        continue

                    if netidinfo_fb._url is not None:
                        profile: NetworkProfile = fb.search_url(
                            netidinfo_fb._url, level, reason
                        )
                        if isinstance(profile, NetworkProfile):
                            # Get profile detail
                            profile = fb.get_profile_detail(
                                profile, self.dtools.landing_facebook
                            )
                            if not isinstance(profile, NetworkProfile):
                                continue
                            profile.reason = reason
                            networkprofiles.set_profile(profile)
                        got = True
                        yield profile

                    elif netidinfo_fb._userid is not None:
                        profile: NetworkProfile = fb.search_userid(
                            netidinfo_fb._userid, level, reason
                        )
                        if isinstance(profile, NetworkProfile):
                            # Get profile detail
                            profile = fb.get_profile_detail(
                                profile, self.dtools.landing_facebook
                            )
                            if not isinstance(profile, NetworkProfile):
                                continue
                            profile.reason = reason
                            networkprofiles.set_profile(profile)
                        got = True
                        yield profile

            if not got and not fb is None and fb._is_logined:
                # 如果上面没有 精准定位到任何用户
                # 则进行搜索
                idxstart: int = 0
                idxstop: int = 10
                if (
                    self.task.cmd.stratagyscout.cmdnetworkid.searchindex is not None
                    and self.task.cmd.stratagyscout.cmdnetworkid.searchindex.landing_facebook
                    is not None
                ):
                    si: SS = (
                        self.task.cmd.stratagyscout.cmdnetworkid.searchindex.landing_facebook
                    )
                    idxstart = si.start
                    idxstop = si.stop
                for profile in fb.search_users(
                    obj.value, level, reason, idxstart, idxstop
                ):
                    # 大哥你的profile是不是忘了输出了，单独的输出profiles
                    # 哦对的，谢谢大哥提醒
                    if isinstance(profile, NetworkProfile):
                        profile = fb.get_profile_detail(
                            profile, self.dtools.landing_facebook
                        )
                        if not isinstance(profile, NetworkProfile):
                            continue
                        profile.reason = reason
                        networkprofiles.set_profile(profile)
                        networkprofiles = self.__segment_output_profiles(
                            networkprofiles
                        )
                    yield profile

            self.task.success_count()

        except Exception:

            self.task.fail_count()
            self._logger.error(
                "Get facebook profiles by search name error:\ntaskid:{}\nbatchid:{}\nobj:{}\nerror:{}".format(
                    self.task.taskid,
                    self.task.batchid,
                    obj._objtype,
                    traceback.format_exc(),
                )
            )
        finally:
            if networkprofiles is not None and len(networkprofiles) > 0:
                self.outputdata(
                    networkprofiles.get_outputdict(), networkprofiles._suffix
                )

    def _landing_twitter(
        self, root: NetworkId, task: IscoutTask, level, email, reason
    ) -> iter:
        """
        去调用下载器下载profile,
        可能会回来其他的数据
        :param task:
        :param level:
        :param email:
        :return:
        """
        tw = LandingTwitter(task)
        # twitter get profile，这个profile是单独输出的
        networkprofiles: NetworkProfiles = NetworkProfiles(self.task)
        try:
            # 这里要先看看有没有指定需要获取的land信息
            got: bool = False
            if len(task.cmd.stratagyscout.cmdnetworkid.netidinfo) > 0:
                for (
                    netidinfo_tw
                ) in task.cmd.stratagyscout.cmdnetworkid.netidinfo.values():
                    netidinfo_tw: NetidInfo = netidinfo_tw
                    if (
                        not isinstance(netidinfo_tw._source, str)
                        or netidinfo_tw._source != "twitter"
                    ):
                        continue
                    if netidinfo_tw._userid is not None:
                        self._logger.debug(
                            f"Get task cmd twitter userid, userid:{netidinfo_tw._userid}"
                        )
                        profile: NetworkProfile = tw.landing_userid(
                            level, netidinfo_tw._userid, reason
                        )
                        # 大哥你这里面是不是也应该吧profile加到networkprofiles里面？
                        if isinstance(profile, NetworkProfile):
                            profile.reason = reason
                            networkprofiles.set_profile(profile)
                        got = True
                        yield profile
            # -----------------------------------上面是去拿特定的，可能会拿到没有指定的，下面才是去search
            if not got:
                self._logger.debug(f"Get twitter object value:{email}")
                idxstart: int = 0
                idxstop: int = 10
                if (
                    task.cmd.stratagyscout.cmdnetworkid.searchindex.landing_twitter
                    is not None
                ):
                    si = task.cmd.stratagyscout.cmdnetworkid.searchindex.landing_twitter
                    idxstart = si.start
                    idxstop = si.stop

                for tp in tw.landing(
                    level, email, reason, idxstart=idxstart, idxstop=idxstop
                ):
                    if isinstance(tp, NetworkProfile):
                        tp.reason = reason
                        networkprofiles.set_profile(tp)
                        networkprofiles = self.__segment_output_profiles(
                            networkprofiles
                        )
                    yield tp
            task.success_count()
        except:
            task.fail_count()
            self._logger.error(
                f"Get profile from twitter error\nerr:{traceback.format_exc()}"
            )
        finally:
            # 最后输出,最后剩下没有输出的，一定要输出，不管拿到多少个
            if len(networkprofiles) > 0:
                self.outputdata(
                    networkprofiles.get_outputdict(), networkprofiles._suffix
                )

    def _landing_instagram(
        self, root: NetworkId, task: IscoutTask, level, obj: ScoutFeedBackBase, reason
    ) -> iter:
        """get instagram profiles by search username"""

        ins: Instagram = Instagram(task)
        networkprofiles: NetworkProfiles = NetworkProfiles(self.task)
        try:
            if len(self.task.cmd.stratagyscout.cmdnetworkid.netidinfo) <= 0:
                if ins.judgment_url:
                    profile = ins.judgment_url(obj.value, level, reason)
                    if profile is not None:
                        yield profile
                        task.success_count()
                        return
                    else:
                        pass

                if ins.judgment_keyword:
                    for profile in ins.judgment_keyword(obj.value, level, reason):
                        yield profile
                    task.success_count()

        except Exception:
            task.fail_count()
            self._logger.error(
                "Get instagram profiles by search name error:\ntaskid:{}\nbatchid:{}\nobj:{}\nerror:{}".format(
                    self.task.taskid,
                    self.task.batchid,
                    obj._objtype,
                    traceback.format_exc(),
                )
            )
        finally:
            # 最后输出
            if networkprofiles is not None and len(networkprofiles) > 0:
                self.outputdata(
                    networkprofiles.get_outputdict(), networkprofiles._suffix
                )

    #################################################
    # public
    def _public(self, level, obj: ScoutFeedBackBase):
        """舆情监控"""
        try:
            # public facebook

            if self.task.cmd.stratagyscout.cmdnetworkid.enabled_public_facebook:
                self._logger.debug("NETWORKID:Start public facebook.")
                log = f"开始收集目标{obj.value} {self.dtools.public_facebook}信息"
                self._outprglog(log)
                self._public_facebook(obj, self.dtools.public_facebook)

            # public twitter

            if self.task.cmd.stratagyscout.cmdnetworkid.enabled_public_twitter:
                self._logger.debug("NETWORKID:Start public twitter.")
                log = f"开始收集目标{obj.value} {self.dtools.public_twitter}信息"
                self._outprglog(log)
                self._public_twitter(obj, self.dtools.public_twitter)

            # # public instgram
            # if self.task.cmd.stratagyscout.cmdnetworkid.enabled_landing_instgram:
            #     self._logger.debug("NETWORKID: Start public instgram.")
            #     self._public_instgram(obj)

        except Exception:
            self._logger.error(f"Public networkid error, err:{traceback.format_exc()}")

    def _public_facebook(self, obj: ScoutFeedBackBase, reason=None) -> iter:
        """facebook 舆情监控，不返回任何数据，所有数据在内部自行输出了已经"""
        # 用于输出所有人员信息/消息信息
        networkprofiles = None
        networkposts: NetworkPosts = None
        try:
            fb: Facebook = Facebook(self.task)

            if (
                self.task.cmd.stratagyscout.cmdnetworkid is not None
                and len(self.task.cmd.stratagyscout.cmdnetworkid.netidinfo) > 0
            ):
                for (
                    netidinfo_fb
                ) in self.task.cmd.stratagyscout.cmdnetworkid.netidinfo.values():
                    netidinfo_fb: NetidInfo = netidinfo_fb
                    if (
                        not isinstance(netidinfo_fb._source, str)
                        or netidinfo_fb._source != "facebook"
                    ):
                        continue

                    # ensure the hostuser
                    hostuser: NetworkProfile = None
                    if netidinfo_fb._url is not None:
                        hostuser = fb.get_user_by_userurl(
                            netidinfo_fb._url, self.dtools.public_facebook, True
                        )
                        if not isinstance(hostuser, NetworkProfile):
                            self._logger.error(
                                "Ensure user by userurl failed, userid={}".format(
                                    netidinfo_fb._url
                                )
                            )
                            continue
                    elif netidinfo_fb._userid is not None:
                        hostuser = fb.get_user_by_userid(
                            netidinfo_fb._userid, self.dtools.public_facebook, True
                        )
                        if not isinstance(hostuser, NetworkProfile):
                            self._logger.error(
                                "Ensure user by userurl failed, userid={}".format(
                                    netidinfo_fb._url
                                )
                            )
                            continue
                    else:
                        self._logger.error(
                            "Lack of userid or userurl, cannot do public:\ntaskid={}\nbatchid={}\nobj={}".format(
                                self.task.taskid, self.task.batchid, obj.value
                            )
                        )
                        continue

                    # 已确认账号，开始获取舆情
                    self._logger.info(
                        "Ensured user: {}({}) {}".format(
                            hostuser.nickname, hostuser._userid, hostuser.url
                        )
                    )
                    # 拿参数 posttime.timerange
                    log = "Ensured user: {}({}) {}".format(
                        hostuser.nickname, hostuser._userid, hostuser.url
                    )
                    self._outprglog(log)
                    # get contacts
                    self._logger.info(
                        "Start getting contacts of user: {}({})".format(
                            hostuser.nickname, hostuser._userid
                        )
                    )
                    log = "Start getting contacts of user: {}({})".format(
                        hostuser.nickname, hostuser._userid
                    )
                    self._outprglog(log)
                    networkprofiles: NetworkProfiles = NetworkProfiles(self.task)
                    for data in fb.get_contacts(
                        self.task, hostuser, self.dtools.public_facebook
                    ):
                        if isinstance(data, NetworkProfile):
                            networkprofiles.set_profile(data)
                            networkprofiles = self.__segment_output_profiles(
                                networkprofiles
                            )
                        if isinstance(data, NetworkResource):
                            OutputManagement.output(data)

                    # get posts
                    self._logger.info(
                        "Start getting posts of user: {}({})".format(
                            hostuser.nickname, hostuser._userid
                        )
                    )
                    log = "Start getting posts of user: {}({})".format(
                        hostuser.nickname, hostuser._userid
                    )
                    self._outprglog(log)
                    networkposts: NetworkPosts = NetworkPosts(self.task)
                    for data in fb.get_posts(
                        self.task, hostuser, self.dtools.public_facebook
                    ):
                        if isinstance(data, NetworkPost):
                            networkposts.set_posts(data)
                            networkposts = self.__segment_output_posts(networkposts)
                        if isinstance(data, NetworkResource):
                            OutputManagement.output(data)

            self.task.success_count()
        except:
            self.task.fail_count()
            self._logger.error(
                f"Get public_facebook error, err:{traceback.format_exc()}"
            )
        finally:
            # 最后输出,最后一定要输出不管拿到多少个
            if networkprofiles is not None and len(networkprofiles) > 0:
                self.outputdata(
                    networkprofiles.get_outputdict(), networkprofiles._suffix
                )
            if networkposts is not None and len(networkposts) > 0:
                self.outputdata(networkposts.get_outputdict(), networkposts._suffix)

    def _public_twitter(self, obj: ScoutFeedBackBase, reason=None):
        """
        使用拿到的twitter个人信息去拿这个人发的推文,
        舆情里面的信息都不会加入root,
        现在逻辑修改为拿到了个人信息后再根据userid去拿tweet
        :param obj:
        :param reason:
        :return:
        """
        # userid
        tw = PublicTwitter(self.task)
        obj_value = obj.value
        networkposts: NetworkPosts = NetworkPosts(self.task)
        try:
            count = 0
            got: bool = False
            if len(self.task.cmd.stratagyscout.cmdnetworkid.netidinfo) > 0:
                for (
                    netidinfo_tw
                ) in self.task.cmd.stratagyscout.cmdnetworkid.netidinfo.values():
                    netidinfo_tw: NetidInfo = netidinfo_tw
                    if (
                        not isinstance(netidinfo_tw._source, str)
                        or netidinfo_tw._source != "twitter"
                    ):
                        continue

                    if netidinfo_tw._userid is not None:
                        self._logger.debug(
                            f"Get twitter cmd userid:{netidinfo_tw._userid}"
                        )
                        for pdata in tw.public(netidinfo_tw._userid, reason):
                            if isinstance(pdata, NetworkPost):
                                networkposts.set_posts(pdata)
                                count += 1
                                networkposts = self.__segment_output_posts(networkposts)
                            if isinstance(pdata, NetworkResource):
                                OutputManagement.output(pdata)
                        got = True
            # -----------------------------------上面是去拿特定的，可能会拿到没有指定的，下面才是去search
            if not got:
                self._logger.debug(f"Get twitter objvalue:{obj_value}")
                for pdata in tw.public(obj_value, reason):
                    if isinstance(pdata, NetworkPost):
                        networkposts.set_posts(pdata)
                        count += 1
                        networkposts = self.__segment_output_posts(networkposts)
                    if isinstance(pdata, NetworkResource):
                        OutputManagement.output(pdata)
            self.task.success_count()
            log = f"获取到到目标{obj.value}未经处理的{count}条{self.dtools.public_twitter}数据"
            self._outprglog(log)
        except:
            self.task.fail_count()
            self._logger.error(
                f"Twitter public error, err:{traceback.format_exc()},userid:{obj_value}"
            )
        finally:
            if len(networkposts) > 0:
                posts_dict = networkposts.get_outputdict()
                self.outputdata(posts_dict, networkposts._suffix)

    # ---------------------------------------------------- whois
    def _get_whois(
        self,
        root: NetworkId,
        task: IscoutTask,
        level,
        obj: ScoutFeedBackBase,
        reason=None,
    ):
        """
        获取whois的方法
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmdnetworkid.enabled_whois_reverse:
            return

        self._logger.debug("NETWORKID:Start getting whois.")
        log = f"开始探测目标{obj.value} {self.dtools.whois_reverse}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            # sonar
            for data in self._sonar_get_whoisr(root, task, level, obj):
                count_dict[json.dumps(data.get_outputdict())] = 1
                yield data

        except:
            self._logger.error(f"Get whoisr error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{obj.value}未经处理的{count_dict.__len__()}条{self.dtools.whois_reverse}数据"
            self._outprglog(log)

    def _sonar_get_whoisr(
        self, root: NetworkId, task: IscoutTask, level, obj: ScoutFeedBackBase
    ):
        """
        使用sonar接口获取whois的信息
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        networkid = obj.value
        try:

            for data in SonarApi.networkidwhoisr(task, level, networkid):
                self.__set_value(root, data)
                root = self.__segment_output(root, level, networkid)
                yield data
        except:
            self._logger.error(f"Sonar get whoisr error, err:{traceback.format_exc()}")

    # ---------------------------------------------------- searchengine
    def _get_searchengine(
        self,
        root: NetworkId,
        task: IscoutTask,
        level,
        obj: ScoutFeedBackBase,
        reason=None,
    ):
        """
        搜索引擎全词匹配目标网络id相关信息
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        networkid = obj.value

        try:
            for data in self._get_google_searchengine(
                root, task, level, networkid, reason
            ):
                yield data
            for data1 in self._get_bing_searchengine(
                root, task, level, networkid, reason
            ):
                yield data1
            for data2 in self._get_baidu_searchengine(
                root, task, level, networkid, reason
            ):
                yield data2
        except:
            self._logger.error(f"Get search result error, err:{traceback.format_exc()}")

    def _get_google_searchengine(
        self, root: NetworkId, task: IscoutTask, level, networkid, reason=None
    ):
        """
        google 搜索
        :param root:
        :param task:
        :param level:
        :param networkid:
        :param reason:
        :return:
        """
        if not task.cmd.stratagyscout.cmdnetworkid.enabled_searchgoogle:
            return
        log = f"开始探测目标{networkid} {self.dtools.google}信息"
        self._outprglog(log)
        self._logger.debug("NETWORKID:Start getting google search.")
        count = 0
        try:

            keywords = (
                task.cmd.stratagyscout.cmdnetworkid.searchengine.search_google.keywords
            )
            filetypes = (
                task.cmd.stratagyscout.cmdnetworkid.searchengine.search_google.filetypes
            )
            sapi = SearchApi(task)
            for data in sapi.text_google_search_engine(
                keywords, filetypes, networkid, level, self.dtools.google
            ):
                # 输出截图数据/这里scouternetworkid里只可能是搜索引擎截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    count += 1
                    root = self.__segment_output(root, level, networkid)
                    yield data

        except:
            self._logger.error(f"Get google search error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{networkid}未经处理的{count}条{self.dtools.google}数据"
            self._outprglog(log)

    def _get_bing_searchengine(
        self, root: NetworkId, task: IscoutTask, level, networkid, reason=None
    ):
        """
        bing 搜索
        :param root:
        :param task:
        :param level:
        :param networkid:
        :param reason:
        :return:
        """
        if not task.cmd.stratagyscout.cmdnetworkid.enabled_searchbing:
            return
        log = f"开始探测目标{networkid} {self.dtools.bing}信息"
        self._outprglog(log)
        self._logger.debug("NETWORKID:Start getting bing search.")
        count = 0
        try:
            keywords = (
                task.cmd.stratagyscout.cmdnetworkid.searchengine.search_bing.keywords
            )
            filetypes = (
                task.cmd.stratagyscout.cmdnetworkid.searchengine.search_bing.filetypes
            )
            sapi = SearchApi(task)
            for data in sapi.text_bing_search_engine(
                keywords, filetypes, networkid, level, self.dtools.bing
            ):
                # 输出截图数据/这里scouternetworkid里只可能是搜索引擎截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    count += 1
                    root = self.__segment_output(root, level, networkid)
                    yield data

        except:
            self._logger.error(f"Get bing search error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{networkid}未经处理的{count}条{self.dtools.bing}数据"
            self._outprglog(log)

    def _get_baidu_searchengine(
        self, root: NetworkId, task: IscoutTask, level, networkid, reason=None
    ):
        """
        baidu 搜索
        :param root:
        :param task:
        :param level:
        :param networkid:
        :param reason:
        :return:
        """
        if not task.cmd.stratagyscout.cmdnetworkid.enabled_searchbaidu:
            return
        log = f"开始探测目标{networkid} {self.dtools.baidu}信息"
        self._outprglog(log)
        self._logger.debug("NETWORKID:Start getting baidu search.")
        count = 0
        try:
            keywords = (
                task.cmd.stratagyscout.cmdnetworkid.searchengine.search_baidu.keywords
            )
            filetypes = (
                task.cmd.stratagyscout.cmdnetworkid.searchengine.search_baidu.filetypes
            )
            sapi = SearchApi(task)
            for data in sapi.text_baidu_search_engine(
                keywords, filetypes, networkid, level, self.dtools.baidu
            ):
                # 输出截图数据/这里scouternetworkid里只可能是搜索引擎截图数据
                if isinstance(data, ScreenshotSE):
                    OutputManagement.output(data)

                elif isinstance(data, SearchFile):
                    OutputManagement.output(data)

                else:
                    self.__set_value(root, data)
                    count += 1
                    root = self.__segment_output(root, level, networkid)
                    yield data

        except:
            self._logger.error(f"Get baidu search error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{networkid}未经处理的{count}条{self.dtools.baidu}数据"
            self._outprglog(log)

    # ---------------------------------------------------- email
    def _get_email(
        self,
        root: NetworkId,
        task: IscoutTask,
        level,
        obj: ScoutFeedBackBase,
        reason=None,
    ):
        """
        去插件里面提取email
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmdnetworkid.enabled_email:
            return
        self._logger.debug("NETWORKID:Start getting email.")
        networkid = obj.value
        log = f"开始收集目标{networkid} {self.dtools.email}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            for data in self._google_search_email(root, task, level, networkid, reason):
                count_dict[data.value] = 1
                yield data

            for data1 in self._sonarapi_get_email(root, task, level, networkid, reason):
                count_dict[data1.value] = 1
                yield data1
        except:
            self._logger.error(f"Get email error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{networkid}未经处理的{count_dict.__len__()}条{self.dtools.email}数据"
            self._outprglog(log)

    def _google_search_email(
        self, root: NetworkId, task: IscoutTask, level, networkid, reason=None
    ):
        """
        去搜索引擎里面提取email
        :param root:
        :param task:
        :param level:
        :param networkid:
        :param reason:
        :return:
        """
        try:
            keywords = (
                task.cmd.stratagyscout.cmdnetworkid.searchengine.search_google.keywords
            )
            filetypes = []
            sapi = SearchApi(task)
            for data in sapi.text_google_search_engine(
                keywords, filetypes, networkid, level, reason
            ):
                # 输出截图数据/这里scouternetworkid里只可能是搜索引擎截图数据
                if isinstance(data, Email):
                    root.set_email(data)
                    root = self.__segment_output(root, level, networkid)
                    yield data
        except:
            self._logger.error(
                f"Get email from google search result error, err:{traceback.format_exc()}"
            )

    def _sonarapi_get_email(
        self, root: NetworkId, task: IscoutTask, level, networkid, reason
    ):
        """
        sonar api 先去查whoisr，然后使用查到的domain，再去domain whois那边拿phone
        :param root:
        :param task:
        :param level:
        :param networkid:
        :param reason:
        :return:
        """
        try:
            for ew in SonarApi.networkidwhoisr(task, level, networkid):
                domain = ew._domain
                self._logger.debug(f"Sonar search a domain:{domain}.")
                for data in SonarApi.domain_whois(task, level, domain, reason):
                    if isinstance(data, Email):
                        root.set_email(data)
                        root = self.__segment_output(root, level, domain)
                        yield data
        except:
            self._logger.error(
                f"Get email from sonar api error, err:{traceback.format_exc()}"
            )

    # ------------------------------------------------------ phone
    def _get_phone(
        self,
        root: NetworkId,
        task: IscoutTask,
        level,
        obj: ScoutFeedBackBase,
        reason=None,
    ):
        """
        去插件里面提取phone
        :param root:
        :param task:
        :param level:
        :param obj:
        :return:
        """
        if not task.cmd.stratagyscout.cmdnetworkid.enabled_phone:
            return
        self._logger.debug("NETWORKID:Start getting phone.")
        networkid = obj.value
        log = f"开始收集目标{networkid} {self.dtools.phone}信息"
        self._outprglog(log)
        count_dict = {}
        try:
            for data in self._google_search_phone(root, task, level, networkid, reason):
                count_dict[data.value] = 1
                yield data

            for data1 in self._sonarapi_get_phone(root, task, level, networkid, reason):
                count_dict[data1.value] = 1
                yield data1
        except:
            self._logger.error(f"Get phone info error, err:{traceback.format_exc()}")
        finally:
            log = f"获取到目标{networkid}未经处理的{count_dict.__len__()}条{self.dtools.phone}数据"
            self._outprglog(log)

    def _google_search_phone(
        self, root: NetworkId, task: IscoutTask, level, networkid, reason=None
    ):
        """
        去搜索引擎里面提取phone
        :param root:
        :param task:
        :param level:
        :param networkid:
        :param reason:
        :return:
        """
        try:
            keywords = (
                task.cmd.stratagyscout.cmdnetworkid.searchengine.search_google.keywords
            )
            filetypes = []
            sapi = SearchApi(task)
            for data in sapi.text_google_search_engine(
                keywords, filetypes, networkid, level, reason
            ):
                # 输出截图数据/这里scouternetworkid里只可能是搜索引擎截图数据
                if isinstance(data, Phone):
                    root.set_phone(data)
                    root = self.__segment_output(root, level, networkid)
                    yield data
        except:
            self._logger.error(
                f"Get phone from google search result error, err:{traceback.format_exc()}"
            )

    def _sonarapi_get_phone(
        self, root: NetworkId, task: IscoutTask, level, networkid, reason
    ):
        """
        sonar api 先去查whoisr，然后使用查到的domain，再去domain whois那边拿phone
        :param root:
        :param task:
        :param level:
        :param networkid:
        :param reason:
        :return:
        """
        try:
            for ew in SonarApi.networkidwhoisr(task, level, networkid):
                domain = ew._domain
                self._logger.debug(f"Sonar search a domain:{domain}.")
                for data in SonarApi.domain_whois(task, level, domain, reason):
                    if isinstance(data, Phone):
                        root.set_phone(data)
                        root = self.__segment_output(root, level, domain)
                        yield data
        except:
            self._logger.error(
                f"Get phone from sonar api error, err:{traceback.format_exc()}"
            )
