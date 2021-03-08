"""facebook"""

# -*- coding:utf-8 -*-

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import NetworkProfile
from .fbsearchemail import FBSearchEmail
from .fbsearchemail_new import FBSearchEmail_new


class Facebook(FBSearchEmail, FBSearchEmail_new):
    """Facebook"""
    def __init__(self, task: IscoutTask):
        super(Facebook, self).__init__(task)

###################################
# login

    def login_cookie(self, cookie: str) -> bool:
        return self._cookie_login_(cookie)

    def login_pass(self, acc: str, pwd: str) -> bool:
        return self._login_pass(acc, pwd)

    def login_sms(self, phone: str) -> bool:
        raise NotImplementedError()

###################################
# search

    def search_url(self,
                   url: str,
                   level: int,
                   reason,
                   get_profile_pic: bool = False) -> NetworkProfile:
        """按 用户主页链接URL 搜索用户"""
        self._logger.info("Search by url: {}".format(url))
        if self.is_new_facebook:
            return self._search_url_v1(url,
                                       level,
                                       reason,
                                       get_profile_pic=get_profile_pic)
        else:
            return self._search_url(url,
                                    level,
                                    reason,
                                    get_profile_pic=get_profile_pic)

    def search_userid(self, userid: str, level: int, reason) -> NetworkProfile:
        """按 用户userid 搜索用户"""
        self._logger.info("Search by userid: {}".format(userid))
        if self.is_new_facebook:
            return self._search_userid_v1(userid, level, reason)
        else:
            return self._search_userid(userid, level, reason)

    def search_users(self,
                     name: str,
                     level: int,
                     reason,
                     search_index: int = 0,
                     search_count: int = 10,
                     get_profile_pic: bool = False) -> iter:
        """按 昵称 搜索用户"""
        self._logger.info("Search by name: {}".format(name))
        if self.is_new_facebook:
            return self._search_users_v1(name, level, reason)
        else:
            return self._search_users(name, level, reason)

    def search_email(self, email: str, level: int) -> NetworkProfile:
        """按 绑定的邮箱账号 搜索用户"""
        self._logger.info("Search by email: {}".format(email))
        return self._search_email(email, level)

###################################
# get/ensure user

    def get_user_by_userid(
            self,
            userid: str,
            reason: str = None,
            get_profile_pic: bool = True,
    ) -> NetworkProfile:
        """根据userid精确定位用户，失败返回None"""
        if self.is_new_facebook:
            return self._get_user_by_userid_v1(userid, reason, get_profile_pic)
        else:
            return self._get_user_by_userid(userid, reason, get_profile_pic)

    def get_user_by_userurl(
            self,
            userurl: str,
            reason: str = None,
            get_profile_pic: bool = True,
    ) -> NetworkProfile:
        """根据userurl用户主页链接精确定位用户，失败返回None"""
        if self.is_new_facebook:
            return self._get_user_by_url_v1(userurl, reason, get_profile_pic)
        else:
            return self._get_user_by_url(userurl, reason, get_profile_pic)

###################################
# get profile detail

    def get_profile_detail_userid(self,
                                  userid: str,
                                  reason: str = None,
                                  recursive: int = 0,
                                  get_profile_pic: bool = False
                                  ) -> NetworkProfile:
        """get user profile detail"""
        if self.is_new_facebook:
            return self._get_profile_detail_userid_v1(userid, reason, recursive,
                                                      get_profile_pic)
        else:
            return self._get_profile_detail_userid(userid, reason, recursive,
                                                   get_profile_pic)

    def get_profile_detail_userurl(self,
                                   userurl: str,
                                   reason: str = None,
                                   recursive: int = 0,
                                   get_profile_pic: bool = False
                                   ) -> NetworkProfile:
        """get user profile detail"""
        if self.is_new_facebook:
            return self._get_profile_detail_userurl_v1(userurl,
                                                       reason,
                                                       recursive=recursive,
                                                       get_profile_pic=get_profile_pic)
        else:
            return self._get_profile_detail_userurl(userurl,
                                                    reason,
                                                    recursive=recursive,
                                                    get_profile_pic=get_profile_pic)

    def get_profile_detail(self, profile: NetworkProfile,
                           reason: str = None) -> NetworkProfile:
        """get profile detail"""
        if self.is_new_facebook:
            return self._get_profile_detail_v1(profile, reason)
        else:
            return self._get_profile_detail(profile, reason)

###################################
# get contacts

    def get_contacts_userid(self,
                            task: IscoutTask,
                            userid: str,
                            reason: str = None,
                            get_profile_pic: bool = False) -> iter:
        """获取指定用户的 好友列表"""
        if not isinstance(userid, str) or userid == "":
            raise Exception("Invalid userid")
        if self.is_new_facebook:
            return self._get_contacts_by_userid_v1(task,
                                                   userid,
                                                   reason,
                                                   get_profile_pic=get_profile_pic)
        else:
            return self._get_contacts_by_userid(task,
                                                userid,
                                                reason,
                                                get_profile_pic=get_profile_pic)

    def get_contacts_userurl(self,
                             task: IscoutTask,
                             userurl: str,
                             reason: str = None,
                             get_profile_pic: bool = False) -> iter:
        """获取指定用户的 好友列表"""
        if not isinstance(userurl, str) or userurl == "":
            raise Exception("Invalid userurl")
        if self.is_new_facebook:
            return self._get_contacts_by_url_v1(task,
                                                userurl,
                                                reason,
                                                get_profile_pic=get_profile_pic)
        else:
            return self._get_contacts_by_url(task,
                                             userurl,
                                             reason,
                                             get_profile_pic=get_profile_pic)

    def get_contacts(self,
                     task: IscoutTask,
                     profile: NetworkProfile,
                     reason: str = None,
                     get_profile_pic: bool = False) -> iter:
        """获取指定用户的 好友列表"""
        if not isinstance(profile, NetworkProfile):
            raise Exception("Invalid NetworkPorfile")
        if self.is_new_facebook:
            return self._get_contacts_v1(task,
                                         profile,
                                         reason=reason,
                                         get_profile_pic=get_profile_pic)
        else:
            return self._get_contacts(task,
                                      profile,
                                      reason=reason,
                                      get_profile_pic=get_profile_pic)


###################################
# get posts

    def get_posts_userid(self,
                         task: IscoutTask,
                         userid: str,
                         reason: str = None) -> iter:
        """获取指定用户的 posts"""
        if not isinstance(userid, str) or userid == "":
            raise Exception("Invalid userid")
        if self.is_new_facebook:
            return self._get_posts_by_userid_v1(task, userid, reason)
        else:
            return self._get_posts_by_userid(task, userid, reason)

    def get_posts_url(self, task: IscoutTask, userurl: str,
                      reason: str = None) -> iter:
        """获取指定用户的 posts"""
        if not isinstance(userurl, str) or userurl == "":
            raise Exception("Invalid userurl")
        if self.is_new_facebook:
            return self._get_posts_by_url_v1(task, userurl, reason)
        else:
            return self._get_posts_by_url(task, userurl, reason)

    def get_posts(self,
                  task: IscoutTask,
                  hostuser: NetworkProfile,
                  reason: str = None,
                  timerange: int = 30) -> iter:
        """获取指定用户的 posts"""
        if not isinstance(hostuser, NetworkProfile):
            raise Exception("Invalid hostuser NetworkProfile")
        if self.is_new_facebook:
            return self._get_posts_v1(task, hostuser, reason, timerange=timerange)
        else:
            return self._get_posts(task, hostuser, reason, timerange=timerange)
