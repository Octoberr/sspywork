"""facebook search url"""

# -*- coding:utf-8 -*-

import html as ht
import re
import traceback

from commonbaby.helpers import helper_str

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import (Email, NetworkProfile,
                                                      Phone)
from .fbposts_new import FBPosts_new


class FBSearchUrl_new(FBPosts_new):
    """facebook search by user url"""

    def __init__(self, task: IscoutTask):
        super(FBSearchUrl_new, self).__init__(task)

    def _search_url_v1(self,
                       userurl: str,
                       level: int,
                       reason,
                       get_profile_pic: bool = False) -> iter:
        """返回 NetworkProfile/Email/Phone"""
        try:
            if not isinstance(userurl, str):
                self._logger.error("Invalid userurl")
                return

            if not self._is_logined:
                self._logger.error("Pre-account not login")
                return

            profile: NetworkProfile = self._get_user_by_url_v1(
                userurl, reason, get_profile_pic=get_profile_pic)
            if not isinstance(profile, NetworkProfile):
                return

            return profile

        except Exception:
            self._logger.error("Get user by url failed: {}".format(
                traceback.format_exc()))
