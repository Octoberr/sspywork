"""facebook search userid"""

# -*- coding:utf-8 -*-

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import NetworkProfile
from .fbsearchurl_new import FBSearchUrl_new


class FBSearchUserid_new(FBSearchUrl_new):
    """facebook search userid"""
    def __init__(self, task: IscoutTask):
        super(FBSearchUserid_new, self).__init__(task)

    def _search_userid_v1(self,
                          userid: str,
                          level: int,
                          reason,
                          get_profile_pic: bool = False) -> iter:
        """search by userid, return NetorkProfile/Email/Phone"""
        # https://www.facebook.com/profile.php?id=100034757887484
        # url: str = "https://www.facebook.com/profile.php?id={}".format(userid)
        res: NetworkProfile = self._get_user_by_userid_v1(
            userid, reason, get_profile_pic=get_profile_pic)
        return res
