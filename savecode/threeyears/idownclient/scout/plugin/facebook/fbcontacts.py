"""facebook contacts"""

# -*- coding:utf-8 -*-

import re
import time
import traceback
from urllib import parse

from commonbaby.helpers import helper_str, helper_time

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import (NetworkProfile,
                                                      NetworkProfiles)
from .fbprofile import FBProfile


class FBContacts(FBProfile):
    """FB contacts"""

    # https://www.facebook.com/profile.php?id=100034757887484&
    _re_userid = re.compile(r'id=(\d+)(&|$)', re.S)
    # \u003Ca href=\"https:\/\/www.facebook.com\/profile.php?id=100015857955946&amp;fref=pb&amp;hc_location=profile_browser\" data-gt=\"&#123;&quot;engagement&quot;:&#123;&quot;eng_type&quot;:&quot;1&quot;,&quot;eng_src&quot;:&quot;2&quot;,&quot;eng_tid&quot;:&quot;100015857955946&quot;,&quot;eng_data&quot;:[]&#125;&#125;\" data-hovercard=\"\/ajax\/hovercard\/user.php?id=100015857955946&amp;extragetparams=\u00257B\u002522hc_location\u002522\u00253A\u002522profile_browser\u002522\u00257D\" data-hovercard-prefer-more-content-show=\"1\">\u674e\u4e54\u003C\/a>

    __re2 = re.compile(
        r'a\s*?href=\\"(https:\\/[^"]*?hc_location=friends_tab)\\"\s*?data-gt=.*?eng_tid&quot;:&quot;(\d{3,})&quot;.*?>([^\\]+?)\\u003C\\/a>',
        re.S)

    __re3 = re.compile(
        r'<a\s*?href="(https:[^"]+?)"\s*?data-gt=.*?eng_tid":"(\d{3,})",.*?>([^<]+?)</a',
        re.S)

    __re4 = re.compile(
        r'a\s*?href="(https://[^"]+?)"\s*?data-gt=.*?eng_tid&quot;:&quot;(\d{3,})&quot;,.*?>([^<]+?)</a',
        re.S)

    __re5 = re.compile(
        r'a\s*?href=\\"(https:[^"]+?)"\s*?data-gt=.*?eng_tid&quot;:&quot;(\d{3,})&quot;,.*?>([^<]+?)\\u003C\\/a',
        re.S)

    __re_contacts: list = [__re2, __re3, __re4, __re5]

    def __init__(self, task: IscoutTask):
        super(FBContacts, self).__init__(task)

    def _get_contacts_by_userid(self,
                                task: IscoutTask,
                                userid: str,
                                reason: str = None,
                                get_profile_pic: bool = False) -> iter:
        '''根据userid确定用户，并获取此用户的好友'''
        try:
            hostuser: NetworkProfile = self._get_user_by_userid(userid)
            if not isinstance(hostuser, NetworkProfile):
                return

            for ct in self._get_contacts(task,
                                         hostuser,
                                         reason,
                                         get_profile_pic=get_profile_pic):
                yield ct

        except Exception as ex:
            self._logger.error("Get contacts by userid error: {}".format(
                ex.args))

    def _get_contacts_by_url(self,
                             task: IscoutTask,
                             userurl: str,
                             reason: str = None,
                             get_profile_pic: bool = False) -> iter:
        """get contacts by url"""
        try:
            hostuser: NetworkProfile = self._get_user_by_url(
                userurl, reason=reason, get_profile_pic=get_profile_pic)
            if not isinstance(hostuser, NetworkProfile):
                return

            for ct in self._get_contacts(task,
                                         hostuser,
                                         reason,
                                         get_profile_pic=get_profile_pic):
                yield ct

        except Exception as ex:
            self._logger.error("Get contacts by userurl error: {}".format(
                ex.args))

    def _get_contacts(self,
                      task: IscoutTask,
                      hostuser: NetworkProfile,
                      reason: str = None,
                      get_profile_pic: bool = False) -> iter:
        """get contacts"""
        try:
            if not isinstance(hostuser, NetworkProfile):
                return

            for ct in self._get_contacts_sub(task,
                                             hostuser,
                                             reason,
                                             get_profile_pic=get_profile_pic):
                ct: NetworkProfile = ct
                yield ct

        except Exception as ex:
            self._logger.error("Get contacts by userurl error: {}".format(
                ex.args))

    def _build_contacts_url(self,
                            userid,
                            username,
                            userurl,
                            page,
                            collection_token: str = None,
                            cursor: str = None,
                            pagelet_token: str = None,
                            lst_ts: str = None,
                            isfirst: bool = False) -> str:
        url: str = None
        if isfirst:
            # https://www.facebook.com/profile.php?id=100012401268356&lst=100027859862248%3A100012401268356%3A1562307476&sk=friends&source_ref=pb_friends_tl&fb_dtsg_ag=AQyHiwDNG-z4a7hZcB1AdPcVqjasNA8i9QCtgVTVRAFSvw%3AAQx3vwLVynRS-2a6SZPiu3xugeBwpuAK85b4o4IltrdGdw&ajaxpipe=1&ajaxpipe_token=AXjWcQA1TZc-ouSd&quickling[version]=1000911922%3B0%3B&__user=100027859862248&__a=1&__dyn=7AgNe-4amaAxd2u6aJGeFxqeCwDKEyGzEy4arWo8oeES2N6wAxubwTy8884u5RUC3eF8vDKaxeUW2y4E4eczobrCCwVxCuifz8nxm1Dxa2m4o6e2fwmWwaWum0DVUhCxS68nxK2q15wRyUvwHzU5XximfKEgy9EbEcWy94u4EhwG-2ylxfwEx2cGczUjzUiUbU-5oy2qibxuE4ah2EgVFXAy8424UG1uz8oG5Ey6Ue8Wqexp2Utwwx-2y8wioowOwkEbGwCxe&__req=fetchstream_3&__be=1&__pc=PHASED%3Aufi_home_page_pkg&dpr=1&__rev=1000911922&__s=%3Apce3wy%3A00iqck&jazoest=28101&__spin_r=1000911922&__spin_b=trunk&__spin_t=1562234845&__adt=3&ajaxpipe_fetch_stream=1
            if userurl.__contains__('id='):
                url = userurl.replace('id={}'.format(userid), '').rstrip('?')
            url = '{}?id={}&lst={}%3A{}%3A{}&sk=friends&source_ref=pb_friends_tl&fb_dtsg_ag={}&ajaxpipe=1&ajaxpipe_token=AXjWcQA1TZc-ouSd&quickling[version]={}%3B0%3B&__user={}&__a=1&__req=fetchstream_{}&__be=1&__pc=PHASED%3Aufi_home_page_pkg&dpr=1&__rev={}&__s=%3Apce3wy%3A00iqck&jazoest={}&__spin_r={}&__spin_b=trunk&__spin_t={}&__adt=3&ajaxpipe_fetch_stream=1'.format(
                userurl,
                userid,
                self._userid,
                userid,
                lst_ts,
                parse.quote_plus(self.fb_dtsg_ag),
                self._rev,
                self._userid,
                self._req.get_next(),
                self._rev,
                self.jazoest,
                self._rev,
                self._spin_t,
            )
        else:
            # https://www.facebook.com/ajax/pagelet/generic.php/AllFriendsAppCollectionPagelet?fb_dtsg_ag=AQyHiwDNG-z4a7hZcB1AdPcVqjasNA8i9QCtgVTVRAFSvw%3AAQx3vwLVynRS-2a6SZPiu3xugeBwpuAK85b4o4IltrdGdw&data=%7B%22collection_token%22%3A%22100012401268356%3A2356318349%3A2%22%2C%22cursor%22%3A%22AQHRO663izQ7jF05sIY8Khdz3g2kkHfGc8BbRA0KrE8f62GgmxjoI92wwxvtTqcdVBxpkK9yYYI1mU3t8J9LZPZ57w%22%2C%22disablepager%22%3Afalse%2C%22overview%22%3Afalse%2C%22profile_id%22%3A%22100012401268356%22%2C%22pagelet_token%22%3A%22AWv9jIWdg5s52Nof1GKmH2bepQJzpLGdiuqTT299-mCLaJbofF9UT2MQtTo4Dk75kr8%22%2C%22tab_key%22%3A%22friends%22%2C%22lst%22%3A%22100027859862248%3A100012401268356%3A1562308053%22%2C%22order%22%3Anull%2C%22sk%22%3A%22friends%22%2C%22importer_state%22%3Anull%7D&__user=100027859862248&__a=1&__dyn=7AgNe-4amaAxd2u6aJGeFxqeCwDKEyGzEy4arWo8oeES2N6wAxubwTy8884u5RUC3eF8vDKaxeUW2y4E4eczobrCCwVxCuifz8nxm1Dxa2m4o6e2fwmWwaWum0DVUhCxS68nxK2q15wRyUvwHzU5XximfKEgy9EbEcWy94u4EhwG-2ylxfwEx2cGczUjzUiUbU-5oy2qibxuE4ah2EgVFXAy8424UG1uz8oG5Ey6Ue8Wqexp2Utwwx-2y8wioowOwkEbGwCxe&__req=s&__be=1&__pc=PHASED%3Aufi_home_page_pkg&dpr=1&__rev=1000911922&__s=%3Apce3wy%3A3zdsp6&jazoest=28101&__spin_r=1000911922&__spin_b=trunk&__spin_t=1562234845

            # collection_token=100012401268356:2356318349:2
            data = '{"collection_token":"' + collection_token + '","cursor":"' + cursor + '","disablepager":false,"overview":false,"profile_id":"' + userid + '","pagelet_token":"' + pagelet_token + '","tab_key":"friends","lst":"' + self._userid + ':' + userid + ':' + lst_ts + '","order":null,"sk":"friends","page_number":' + str(
                page) + ',"importer_state":null}'

            url = 'https://www.facebook.com/ajax/pagelet/generic.php/AllFriendsAppCollectionPagelet?fb_dtsg_ag={}&data={}&__user={}&__a=1&__req={}&__be=1&__pc=PHASED%3Aufi_home_page_pkg&dpr=1&__rev={}&__s=%3Apce3wy%3A3zdsp6&jazoest={}&__spin_r={}&__spin_b=trunk&__spin_t={}'.format(
                parse.quote_plus(self.fb_dtsg_ag),
                parse.quote_plus(data),
                self._userid,
                self._req.get_next(),
                self._rev,
                self.jazoest,
                self._rev,
                self._spin_t,
            )

        return url

    def _get_contacts_sub(self,
                          task: IscoutTask,
                          hostuser: NetworkProfile,
                          reason: str = None,
                          get_profile_pic: bool = False) -> iter:
        """get contacts"""
        try:
            hostuserid: str = hostuser._userid
            username: str = hostuser._networkid
            userurl: str = hostuser.url

            if userurl.__contains__('id='):
                m = FBContacts._re_userid.search(userurl)
                if not m is None:
                    userid = m.group(1).strip()
                    userurl = 'https://www.facebook.com/profile.php?id={}'.format(
                        userid)

            if not self._access_user_home(hostuserid, username, userurl):
                return

            totalcount = 0  #用于先写死只获取前100个好友
            page = 0
            got: bool = False
            curr_page_ct_cnt = 0
            collection_token: str = None
            cursor: str = None
            pagelet_token: str = None
            lst_ts: str = str(helper_time.ts_since_1970(10))
            isfirst: bool = True
            userids: dict = {}
            while True:
                try:

                    url = self._build_contacts_url(hostuserid, username,
                                                   userurl, page,
                                                   collection_token, cursor,
                                                   pagelet_token, lst_ts,
                                                   isfirst)

                    html = self._ha.getstring(url,
                                              headers='''
                    accept: */*
                    accept-encoding: gzip, deflate
                    accept-language: en,zh-CN;q=0.9,zh;q=0.8
                    cache-control: no-cache
                    pragma: no-cache
                    referer: {}
                    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'''
                                              .format(userurl))

                    if isfirst:
                        # aria-controls=\"pagelet_timeline_app_collection_100012401268356:2356318349:2\"
                        m = re.search(
                            r'pagelet_timeline_app_collection_([\d:]+?)\\"',
                            html, re.S)
                        if not m is None:
                            # 100012401268356:2356318349:2
                            collection_token = m.group(1).rstrip()
                        # "pagelet_token":"AWv9jIWdg5s52Nof1GKmH2bepQJzpLGdiuqTT299-mCLaJbofF9UT2MQtTo4Dk75kr8"
                        succ, pagelet_token = helper_str.substringif(
                            html, 'pagelet_token":"', '"')

                        # eachtime cursor changes
                        # enableContentLoader",.*?"(\w+?)"]]
                        m = re.search(r'enableContentLoader",.*?,"(.+?)"]]',
                                      html, re.S)
                        if not m is None:
                            cursor = m.group(1).strip()

                        isfirst = False

                    got = False
                    curr_page_ct_cnt = 0
                    for ct in self._parse_contacts(hostuser, html, reason,
                                                   get_profile_pic):

                        if userids.__contains__(ct._userid):
                            continue
                        else:
                            userids[ct._userid] = None
                            curr_page_ct_cnt += 1
                            totalcount += 1

                        if not got:
                            got = True

                        self._logger.info(
                            "Got a contact, hostuser:{}({}), contact:{}({})".
                            format(hostuser.nickname, hostuser._userid,
                                   ct.nickname, ct._userid))

                        yield ct

                        if totalcount >= 100:
                            break

                    if got:
                        self._logger.info(
                            "Get user {} contacts on page {}, {} contacts found"
                            .format(username, page, curr_page_ct_cnt))

                    if not got or curr_page_ct_cnt < 1:
                        self._logger.info(
                            "No contact found on page {} of user {}({})".
                            format(page, hostuser.nickname, hostuser._userid))
                        break
                    if not isfirst and cursor is None:
                        break
                    if totalcount >= 100:
                        break

                except Exception:
                    self._logger.error(
                        "Get contacts ont page {} failed: userid:{} nickname:{} ex:{}"
                        .format(page, hostuserid, username,
                                traceback.format_exc()))
                finally:
                    page += 1
                    time.sleep(0.5)

            self._logger.info("Got {} contacts of user {}({})".format(
                totalcount, hostuser.nickname, hostuser._userid))

        except Exception:
            self._logger.error(
                "Get fb contacts error:\nuserid={}\nusername={}\nerror:{}".
                format(hostuser._userid, hostuser.nickname,
                       traceback.format_exc()))

    def _parse_contacts(self,
                        hostuser: NetworkProfile,
                        html,
                        reason: str = None,
                        get_profile_pic: bool = False) -> iter:
        """return: (ct:Contact)"""
        try:
            if not isinstance(html, str):
                return

            got: bool = False
            for r in FBContacts.__re_contacts:
                for m in r.findall(html):
                    m: re.Match = m
                    got = True

                    ctid: str = m[1]
                    ctname: str = m[2]
                    cturl: str = m[0].replace(r'\/', '/')

                    ct: NetworkProfile = None
                    if get_profile_pic:
                        # 这是为了进去拿头像
                        ct = self._get_user_by_url(
                            cturl,
                            reason=reason,
                            get_profile_pic=get_profile_pic)
                    else:
                        ctname = ctname.encode('utf-8').decode(
                            'unicode-escape')
                        ct: NetworkProfile = NetworkProfile(
                            ctname, ctid, self._SOURCE)
                        ct.reason = reason if not reason is None else "facebook动态监测"
                        ct.url = cturl

                    if ct is None:
                        continue

                    ct.set_contacts(hostuser, isfriend=True)
                    hostuser.set_contacts(ct)

                    yield ct

                if got:
                    break

        except Exception:
            self._logger.error("Parse contacts list failed: {}".format(
                traceback.format_exc()))

    def _access_user_home(self, userid, username, userurl) -> bool:
        res: bool = False
        try:
            # https://www.facebook.com/search/people/?q=jaychou&epa=SERP_TAB
            # https://www.facebook.com/chou.jay.33046?ref=br_rs&fb_dtsg_ag=AQxoUUryaWE9SJ1CJqM8PVlidk2Dt5-xE77VaHgGxALI5w%3AAQwQFpGWrn-Jm3kN40X3WTKX0_KL7P5rDRA4ZpI7x3junQ&ajaxpipe=1&ajaxpipe_token=AXjUd4k4QHQCHGV6&quickling[version]=1000902971%3B0%3B&__user=100027859862248&__a=1&__dyn=7AgNe-4amaAxd2u6aJGeFxqeCwDKEKEW6qrWo8oeES2N6wAxu13wFU5SK9xK5WwIKaxeUW3KFUe8OdwJKdwVxCu58O5UlwpUiwBx61zwzU88eGwQwupVo7G2iu4pEtxy5Urwr8doK7UaU6XxGfKEgy9EbEcWy9pUix62PK2ilxfwEx2cGcByojzUiU98qxm2-ibxG12AgG4equV8y10xeaxq17z8oG5E98e8Wqexp2Utwwx-2y8woEcE5a2WE9Ejw&__req=fetchstream_4&__be=1&__pc=PHASED%3Aufi_home_page_pkg&dpr=1&__rev=1000902971&__s=%3A4flcl4%3A12l5x5&jazoest=27620&__spin_r=1000902971&__spin_b=trunk&__spin_t=1562034711&__adt=4&ajaxpipe_fetch_stream=1
            if not userurl.__contains__('?'):
                userurl = userurl + '?'
            if userurl.__contains__('?') and not userurl.endswith('?'):
                userurl = userurl + '&'
            url = '{}fb_dtsg_ag={}&ajaxpipe=1&ajaxpipe_token=AXjUd4k4QHQCHGV6&quickling[version]={}%3B0%3B&__user={}&__a=1&__req=fetchstream_{}&__be=1&__pc=PHASED%3Aufi_home_page_pkg&dpr=1&__rev={}&__s=%3A4flcl4%3A12l5x5&jazoest={}&__spin_r={}&__spin_b=trunk&__spin_t={}&__adt=4&ajaxpipe_fetch_stream=1'.format(
                userurl,
                self.fb_dtsg_ag,
                self._rev,
                self._userid,
                self._req.get_next(),
                self._rev,
                self.jazoest,
                self._rev,
                self._spin_t,
            )
            html = self._ha.getstring(url,
                                      headers='''
            accept: */*
            accept-encoding: gzip, deflate
            accept-language: en,zh-CN;q=0.9,zh;q=0.8
            cache-control: no-cache
            pragma: no-cache
            referer: https://www.facebook.com/
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'''
                                      )

            if not isinstance(html, str) or not userid in html:
                self._logger.error(
                    "Access user home failed:\nuserid:{}\nusername:{}\nuserurl:{}"
                    .format(userid, username, userurl))
                return res

            res = True
        except Exception:
            res = False
            self._logger.error(
                "Access user home failed:\nuserid:{}\nusername:{}\nuserurl:{}\nerror:{}"
                .format(userid, username, userurl, traceback.format_exc()))
        return res
