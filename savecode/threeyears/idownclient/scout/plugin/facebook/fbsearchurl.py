"""facebook search url"""

# -*- coding:utf-8 -*-

import html as ht
import re
import traceback

from commonbaby.helpers import helper_str

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import (Email, NetworkProfile,
                                                      Phone)
from .fbposts import FBPosts


class FBSearchUrl(FBPosts):
    """facebook search by user url"""

    # https://www.facebook.com/profile.php?id=100034757887484&
    _re_userid = re.compile(r'id=(\d+)(&|$)', re.S)
    # https://www.facebook.com/yingying.chung.35/friends?lst=100027859862248%3A100006478317397%3A1562314909&source_ref=pb_friends_tl
    _re_userid2 = re.compile(r'lst=\d+?%3A(\d+)%3A', re.S)

    def __init__(self, task: IscoutTask):
        super(FBSearchUrl, self).__init__(task)

    def _search_url(self,
                    userurl: str,
                    level: int,
                    reason,
                    get_profile_pic: bool = False) -> iter:
        """返回 NetworkProfile/Email/Phone"""
        succ = True # 
        try:
            if not isinstance(userurl, str):
                self._logger.error("Invalid userurl")
                succ = False
                return

            if not self._is_logined:
                self._logger.error("Pre-account not login")
                return

            profile: NetworkProfile = self._get_user_by_url(
                userurl, reason, get_profile_pic=get_profile_pic)
            # profile: NetworkProfile = self._get_profile_detail_userurl(userurl)
            if not isinstance(profile, NetworkProfile):
                return

            # # 提取邮箱
            # if len(profile._emails) > 0:
            #     for e in profile._emails:
            #         eml = Email(self.task, level, e)
            #         eml.source = self._SOURCE
            #         eml.reason = reason
            #         yield eml
            # # 提取电话
            # if len(profile._phones) > 0:
            #     for p in profile._phones:
            #         pho = Phone(self.task, level, p)
            #         pho.source = self._SOURCE
            #         pho.reason = reason
            #         yield pho

            yield profile

        except Exception:
            self._logger.error("Get user by url failed: {}".format(
                traceback.format_exc()))
