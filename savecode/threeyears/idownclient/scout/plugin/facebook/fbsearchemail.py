"""facebook search email"""

# -*- coding:utf-8 -*-

import traceback
import json

from datacontract.iscoutdataset import IscoutTask
from commonbaby.helpers.helper_str import substring

from .fbsearchname import FBSearchName
from urllib.parse import quote_plus


class FBSearchEmail(FBSearchName):
    """"""
    def __init__(self, task: IscoutTask):
        super(FBSearchEmail, self).__init__(task)

    def _search_email(self, email: str, level: int) -> iter:
        """按邮箱搜索人，返回搜索到的人的基本信息。\n
        后续需要用基本信息去get_profile获取详细信息？"""
        try:
            url = 'https://www.facebook.com/presma/user_search_typeahead/?search_mode=ANYONE_EXCEPT_VERIFIED_ACCOUNT'
            headers = """
accept: */*
accept-encoding: gzip, deflate
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
content-length: 611
Content-Type:application/x-www-form-urlencoded
origin: https://www.facebook.com
pragma: no-cache
referer: https://www.facebook.com
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-origin
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36
viewport-width: 1022"""
            postdata = f'q={quote_plus(email)}&__user={self._userid}&__a=1&__dyn=7AgNe-4amcxp2um4GJGi9FxqeCxWfyaF3oyfiheC264U9ES2N6xCagmyUc9EaobEgDxtoK6UnGi4FoWUuKewXyEe8OdxK4oGq4fwAxCczUO49E6am58iyEScx61zwzxu3a4GxKq4o7Cuq3K6U62WyUhxyufxKqfzWwTgC3mbx-9w93ximfK6bwqopxaicwG-2x4UjU8UlzUOmUpwAwLUdo4q1aBxyeKh7wGxm4UGqfyUeAUy5bxC2i17CzEmgK7o88vxKcy8ix28xO1fxW2-2WA2m4U4a5Ey58ym5EWfxW4V82ax61bwUw&__csr=&__req=n&__beoa=0&__pc=PHASED%3ADEFAULT&dpr=1&__rev={self._rev}&__s={self._s}&__hsi={self.hsi}&__comet_req=0&fb_dtsg={quote_plus(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}'
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            html = html.replace('for (;;);', '')
            try:
                sj = json.loads(html)
                payload = sj['payload']
                if not payload:
                    self._logger.info('Do not search any one result!')
                    return
                pay = payload[0]
                userid = pay['id']
                res = self._get_profile_detail_userid(userid)
                yield res
            except Exception:
                self._logger.error(
                    "Search by email error:\ntaskid:{}\nbatchid:{}\nsearch_keyword:{}\nerror{}"
                        .format(self.task.taskid, self.task.batchid, email,
                                traceback.format_exc()))
                return

        except Exception:
            self._logger.error(
                "Search by email error:\ntaskid:{}\nbatchid:{}\nsearch_keyword:{}\nerror{}"
                .format(self.task.taskid, self.task.batchid, email,
                        traceback.format_exc()))
            return
