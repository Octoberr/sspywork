"""facebook get posts"""

# -*- coding:utf-8 -*-

import datetime
import json
import re
import time
import traceback
from urllib import parse
import threading

from commonbaby.helpers import helper_str, helper_time
from lxml import etree

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import (EResourceType,
                                                      NetworkPost,
                                                      NetworkProfile,
                                                      NetworkResource)
from .fbcontacts import FBContacts


class FBPosts(FBContacts):
    """get fb posts"""
    # https://www.facebook.com/profile.php?id={}
    # https://www.facebook.com/haley.kersey.16?ref=br_rs
    # https://www.facebook.com/haley.kersey.16
    _re_vanity = re.compile("https://www.facebook.com/([^/]+?)(/|\?|$)", re.S)

    # ["InitMMoreItemAutomatic","main",[],[{id:"u_0_1m",href:"/profile/timeline/stream/?cursor=AQHRDmoe23KH9qAtHPkka_DCWPDDq-pH0XYAtBhPZ0wIO4XwH4GJmTBGOIdaPaCf8UsqIXEalYyYw0HO-hh1oV_EsnrymM2ZCWwNOF4Ztt4I0G_F90UhOFK5oqVwNr_3OTzG&start_time=-9223372036854775808&profile_id=100015608551408&replace_id=u_0_1m",proximity_pages:5,persist_on_reload:false,logger_name:"unnamed",logger_id:"u_0_1n",load_first_immediately:false,retryOnError:false,addToCache:true,sendGeolocation:false,alwaysProcess:false,scrollPrefetchThrottleFreq:0,insertWhileScrolling:false,loading_text:"",cta_text:"",shouldCapRetries:false}]]
    # \"id\":\"u_0_0\",\"href\":\"\\\/profile\\\/timeline\\\/stream\\\/?cursor=AQHRd7ngvnlV8GMhxIBxLYYD_f4bE5eaJN1sap2JZZwnn0-04VhCx6qhhIEKRUhtoJ7WZuu7ycrsm9AAwIV9POYKvvVYHjU1KHjePoggIpohaIVfKfKYisQ66_WZ1K32FVRn&start_time=-9223372036854775808&profile_id=100015608551408&replace_id=u_0_0\",\"proximity_pages\":5,\"persist_on_reload\":false,\"logger_name\":\"unnamed\",\"logger_id\":\"u_0_1\",\"load_first_immediately\":false,\"retryOnError\":false,\"addToCache\":true,\"sendGeolocation\":false,\"alwaysProcess\":false,\"scrollPrefetchThrottleFreq\":0,\"insertWhileScrolling\":false,\"loading_text\":\"\",\"cta_text\":\"\",\"shouldCapRetries\":false}
    _re_m_cursor = re.compile(r'href.*?(cursor=([^&]+?)&.+?)"', re.S)

    # 第一次进来的html里的
    # ,end:"1575187199",cursor:"AQHRCsR
    # HqleZpitW_pLn1TW5kI5g5GXOjAtMUO1L
    # Teik1PlM4pP0CxCKEuJoc2_V281DTyW-E
    # -znuu7cGvTVfPD59oJb5rfXAGsi12Ne4a
    # TCVJBOcgklbQA_i297Ch23h_Ff",page_id:"1"}
    # 下一页的cursor
    # "start": "0",
    # "end": "1575187199",
    # "cursor": "AQHR9edSmoelr_rijkg7whU1RqQDsd
    # 17uxUjkfq61vZE3YZTuFwX2GjFtjfgDCQc1wRqYtj
    # Lu-6I3KCZm0emjg1b5SMxz0exUh45-SNw8otCu34ZL0bwCwpPZM1fM0-8mcrz",
    # "page_id": "2"
    # 找cursor要兼容这两种
    _re_cursor = re.compile(
        r'"?start"?:\s*?"\d+",\s*?"?end"?:\s*?"\d+",\s*?"?cursor"?:\s*?"([^"]+?)",\s*?"?page_id"?:\s*?"\d+?"',
        re.S)

    # {"secret":"ZbofSD_fhEiOd_-o_dSNsYju-0VENXtY","encrypted":"AYm99ZtzFcFV75QiMGJ5yNOXN_AEOjxVlO3ih_TpQipWOa3-EXi_IFf-Mpe6kau7py5ODXZE5JVLNoJl_hRAkHZklBUfItD9B8WDqdDGSd4swA"}
    _re_ajax = re.compile(r'{"secret":".+?","encrypted":"(.+?)"}', re.S)

    # "id": "adp_FeedStoryUFIRootQueryRelayPreloader_5dcd4ea1160723820350336"
    # ["AsyncDataPreloader"],[{"id":"adp_FeedStoryUFIRootQueryRelayPreloader_5dce175381a4e6c84831273"}]
    _re_feedstory_id = re.compile(
        r'\["AsyncDataPreloader"\],\s*?\[{\s*?"id":\s*?"(adp_FeedStoryUFIRootQueryRelayPreloader_\w+?)"',
        re.S)

    # </span><abbr data-store="&#123;&quot;time&quot;:1566488826,&quot;short&quot;:false,&quot;forceseconds&quot;:false&#125;" data-sigil="timestamp">Aug 22</abbr><span aria-hidden="true">
    # <abbr title="11/7/19, 9:44 AM"
    # data-utime="1573091093" data-shorten="1"
    # class="_5ptz timestamp livetimestamp"><span
    #     class="timestampContent">46
    #     mins</span></abbr>
    # _re_posttime = re.compile(
    #     r'data-store=".*?:(\d+),[^>]+?data-sigil="timestamp">', re.S)
    # %I:%M %p （%p是AM PM）
    _re_posttime = re.compile(
        r'<abbr title="([^"]+?)".*?data-utime="(\d+?)".*?<span\s*?class="timestampContent".*?</abbr>',
        re.S)

    # 这个是找背景图
    # style="background:#d8dce6 url(&#039;https\\3a //scontent-lax3-1.xx.fbcdn.net/v/t1.0-1/cp0/e15/q65/p120x120/70029453_143670380368831_9031142305846788096_n.jpg?_nc_cat\\3d 104\\26 efg\\3d eyJpIjoidCJ9\\26 _nc_oc\\3d AQmryCQMxpD0ROJntDeYbf0cRURc_ez40QJRD3jtwh60UK2XBAQEktHEUWGkkKR-dNE\\26 _nc_ht\\3d scontent-lax3-1.xx\\26 oh\\3d 42b947dcdf15c0f5fdcd188692a13c51\\26 oe\\3d 5E49337F&#039;)
    _re_backgroud = re.compile(
        r'background.*?url\((\'|&#039;)(https.+?)(\'|&#039;)\)', re.S)

    # 找图片
    _re_imgs = re.compile(r'', re.S)

    #########################################old
    # 视频要清晰度高的，然后在链接后加上 '&bytestart=0'就可以下载完整视频
    # "https://scontent-lax3-1.xx.fbcdn.net/v/t39.24130-6/69247412_114264479700880_5597869476747371480_n.mp4?_nc_cat=111&efg=eyJ2ZW5jb2RlX3RhZyI6Im9lcF9oZCJ9&_nc_oc=AQk5FNDvjzFUVtF64iWbJqS_aDzVHthfm-hocj_eqg_xEhxnW8RPscMCSe1pvf7sQ24&_nc_ht=scontent-lax3-1.xx&oh=b385a905b7fdfc70c7867837b9eec4f8&oe=5E2BA37E"
    # "https:\/\/video-lax3-1.xx.fbcdn.net\/v\/t42.9040-2\/62392756_2422199041343326_2489563233187266560_n.mp4?_nc_cat=111&efg=eyJ2ZW5jb2RlX3RhZyI6InN2ZV9zZCJ9&_nc_oc=AQm-sIqd1s8TeRrY49V7_PqSo_ncOg-ckkqBOi9h-arSQ19qrftPQnMhPVzQZT87HXA&_nc_ht=video-lax3-1.xx&oh=11a92b34c7a9c1335eb4469d1d672457&oe=5DAAE6A6"
    _re_videos = re.compile(
        r'"(https:(\\)?/(\\)?/(scontent|video)[^"]+?\.mp4?[^"]+?)"', re.S)

    # :top_level_post_id.144283490307520:
    _re_article = re.compile(r'(<article.+?</article>)', re.S)

    # mf_story_key.663058600891086:top_level_post_id.144283490307520:
    _re_article_id = re.compile(
        r'(mf_story_key.*?\d+(:|&quot)top_level_post_id.*?\d+)(:|&)', re.S)

    _re_story_html = re.compile(
        r'!--\s*?(<div[^!]+?id="jumper.+?)\s*?-->.*?(bigPipe.beforePageletArrive\("timeline_jumper_story_pagelet.*?<script>require\("TimeSlice"\).*?</script>)\s+?',
        re.S)
    _re_story = re.compile(r'!--\s*?(<div[^!]+?id="jumper.+?)\s*?-->', re.S)
    _re_storyj = re.compile(r'(<div[^!]+?id="jumper[^!]+?)', re.S)

    # https://scontent-lax3-1.xx.fbcdn.net/v/t1.0-0/p526x296/69804278_111868563515833_4365636361470869504_o.jpg?_nc_cat=111&_nc_oc=AQnj4Ka86udFWxRClRIoRuUr7zSwr4Rv6v0kCkGrpASpoYHJCxjt8Ws2jy4S2lJtik0&_nc_ht=scontent-lax3-1.xx&oh=98af744837c171e612e99d423d3c8a8f&oe=5E30E27C
    _re_rsc_name = re.compile(r'/([^/]+?)(\?|$)', re.S)

    _re_story_text_replace = re.compile(r'\s{2,}')

    _re_comments = re.compile(r'bigPipe.onPageletArrive\(({.+?})\);', re.S)
    _re_comments2 = re.compile(
        r'result:\s*?{\s*?data:\s*?({.+}\s*?}),\s*?incremental_chunks', re.S)

    # more comments docid
    # params: {
    #     operationKind: "query",
    #     name: "UFI2CommentsProviderPaginationQuery",
    #     id: "2711243315563730", # 取这个id
    #     text: null,
    #     metadata: {}
    # }

    # 最外层是__d("UFI2CommentsProviderPaginationQuery.graphql"
    # params: {
    #     id: "4629548627085906",
    #     metadata: {},
    #     name: "UFI2CommentsProviderPaginationQuery",
    #     operationKind: "query",
    #     text: null
    # }
    _docid_more_comments: str = None
    _docid_more_comments_locker = threading.RLock()
    # _re_docid_more_comments = re.compile(
    #     r'name:\s*?"UFI2CommentsProviderPaginationQuery",\s*?id:\s*?"(\d+?)",',
    #     re.S)
    _re_docid_more_comments = re.compile(
        r'__d\("UFI2CommentsProviderPaginationQuery.graphql".*?params:\s*?(.*?name:\s*?"UFI2CommentsProviderPaginationQuery".*?\s*?})', re.S)

    def __init__(self, task: IscoutTask):
        super(FBPosts, self).__init__(task)

    def _get_posts_by_userid(self,
                             task: IscoutTask,
                             userid: str,
                             reason: str = None,
                             timerange: int = 30) -> iter:
        """get fb posts by userid"""
        try:
            hostuser: NetworkProfile = self._get_user_by_userid(userid)
            if not isinstance(hostuser, NetworkProfile):
                return

            for post in self._get_posts(task,
                                        hostuser,
                                        reason,
                                        timerange=timerange):
                yield post

        except Exception as ex:
            self._logger.error("Get Posts by userid error: {}".format(ex.args))

    def _get_posts_by_url(self,
                          task: IscoutTask,
                          userurl: str,
                          reason: str = None,
                          timerange: int = 30) -> iter:
        """get fb posts by user url"""
        try:
            hostuser: NetworkProfile = self._get_user_by_url(userurl)
            if not isinstance(hostuser, NetworkProfile):
                return

            for post in self._get_posts(task,
                                        hostuser,
                                        reason,
                                        timerange=timerange):
                yield post

        except Exception as ex:
            self._logger.error("Get Posts by userurl error: {}".format(
                ex.args))

    def _get_posts(self,
                   task: IscoutTask,
                   hostuser: NetworkProfile,
                   reason: str = None,
                   timerange: int = 30) -> iter:
        """get fb posts by user profile"""
        try:
            if not isinstance(hostuser, NetworkProfile):
                return

            for post in self._get_posts_sub(task,
                                            hostuser,
                                            reason,
                                            timerange=timerange):
                # post: NetworkProfile = ct
                yield post

        except Exception as ex:
            self._logger.error("Get contacts by userurl error: {}".format(
                ex.args))

    def _build_posts_url(self,
                         userid,
                         username,
                         userurl,
                         vanity,
                         page,
                         collection_token: str = None,
                         cursor: str = None,
                         pagelet_token: str = None,
                         lst_ts: str = None,
                         isfirst: bool = False) -> str:
        url: str = None

        if isfirst:
            # https://www.facebook.com/ajax/pagelet/generic.php/ProfileTimelineProtilesPaginationPagelet?fb_dtsg_ag=AQwZJOAdAe1Bw48MpRGFqEpQuRMoCHb2JrE6_NQyGj-b4g%3AAQwx71YOkoRje8Xm8GycF_uftCaESTXgyli1CPvPombYuQ&ajaxpipe=1&ajaxpipe_token=AXhv89vm2T6XU_ki&no_script_path=1&data=%7B%22profile_id%22%3A100022728466187%2C%22id%22%3A%22100022728466187%22%2C%22sk%22%3A%22timeline%22%2C%22profile_has_parallel_pagelets%22%3Afalse%2C%22tab_key%22%3A%22timeline%22%2C%22target_id%22%3A%22timeline_small_column%22%2C%22count%22%3A1%2C%22page_index%22%3A1%2C%22section_types%22%3A[%22friends%22%2C%22life_events%22%2C%22fun_fact_answers%22]%2C%22buffer%22%3A100%2C%22pager_fired_on_init%22%3Atrue%7D&__user=100009403685520&__a=1&__dyn=7AgNe-4am2d2u6aJGeFxqeCwKyaGey8jheC263GdwIhE98nyUdU6Cu5RyUdE98K7HzEa8iwgUOdwJyFEeopDAzUO5UlwpUiwBx61zwzwnqwaWum0KpEtxy5UrwCwhodoK7UaU-1uUkBzVEgwsEgy8ix62HUa9A4-3Cfz8-4U-58bU-5oy2K2eE4ah1LzHAy8424UG1uz8ox28y8rwUxmexp2Utwwx-2y8xa3q5829wKG2q4U7uewBzUuxy5po&__csr=&__req=fetchstream_1&__be=1&__pc=PHASED%3ADEFAULT&dpr=1&__rev=1001281339&__s=o8etkq%3Afu0owt%3A4skd15&__hsi=6746748870241198274-0&jazoest=28049&__spin_r=1001281339&__spin_b=trunk&__spin_t=1570765977&__adt=1&ajaxpipe_fetch_stream=1
            # data = (
            #     '{"profile_id":' + userid + ',"id":"' + userid +
            #     '","sk":"timeline","profile_has_parallel_pagelets":false,"tab_key":"timeline","target_id":"timeline_small_column","count":1,"page_index":1,"section_types":["friends","life_events","fun_fact_answers"],"buffer":100,"pager_fired_on_init":true}'
            # )
            # url = (
            #     'https://www.facebook.com/ajax/pagelet/generic.php/ProfileTimelineProtilesPaginationPagelet?fb_dtsg_ag='
            #     + parse.quote(self.fb_dtsg_ag) +
            #     '&ajaxpipe=1&ajaxpipe_token=' + self.ajaxpipe_token +
            #     '&no_script_path=1&data=' + parse.quote(data) + '&__user=' +
            #     self._userid +
            #     '&__a=1&__csr=&__req=fetchstream_1&__be=1&__pc=PHASED%3ADEFAULT&dpr=1&__rev='
            #     + self._rev +
            #     '&__hsi=' +  # '&__s=' + parse.quote(self._s) + # 这个__s没找到
            #     self.hsi + '&jazoest=' + self.jazoest + '&__spin_r=' +
            #     self._rev + '&__spin_b=trunk&__spin_t=' + self._spin_t +
            #     '&__adt=1&ajaxpipe_fetch_stream=1')
            # 第一次直接就是主页里
            url = userurl
        else:
            # https://www.facebook.com/ajax/pagelet/generic.php/ProfileTimelineJumperStoriesPagelet?fb_dtsg_ag=AQzTBAKoP6RWI-scf_FpnIb7nnFBzoASy8b-wPk4xAs1fg%3AAQx9h_PywZR_KjhLIba9eqBiIZ6IsOdF01a5745BSIvBpw&ajaxpipe=1&ajaxpipe_token=AXhju2I44qAhABaN&no_script_path=1&data=%7B%22profile_id%22%3A%22100015608551408%22%2C%22vanity%22%3A%22judy.jasso.77%22%2C%22sk%22%3A%22timeline%22%2C%22profile_has_parallel_pagelets%22%3A%22%22%2C%22tab_key%22%3A%22timeline%22%2C%22target_id%22%3A%22timeline_story_container_100015608551408%22%2C%22pager_target_id%22%3A%22timeline_pager_container_100015608551408%22%2C%22start%22%3A%220%22%2C%22end%22%3A%221572591599%22%2C%22cursor%22%3A%22AQHRpjfeGYQdbw_fvwywLFrM1Qvk-6Bl_MIYVX35HX4VOB7kqveR-ZNBwzvWC24lTg8kk7qOXI2DLiCuGAgXpcjnpdtKpHc09PqeMv4RXbGBGvkSJdnhPHXTEKW-NvNCIi2E%22%2C%22page_id%22%3A%221%22%7D&__user=100009403685520&__a=1&__dyn=7AgNe-4am2d2u6aJGeFxqeCwKyaGey8jheC263GdwIhE98nyUdUaofVUnmbxK5WwADK7HzEa8iGu3yczoboGq4e2p1yuifz8nxm1Dxa2m4o6e2e1tG7ElwupVo2VKEtxy5UrwCG12wRyUvwHzU5XximfKEgwsEgy8ix62HUvy9A4-2e5o-cBKm4U-58bU-5oy2K2eE4ah4xrzHAy8aElxeaCzU4ucxy48y8xK3yeCzEmgK7o88vwEy8iwSxi1swIwKG2q4U7u8BwBzUuxy5po&__csr=&__req=fetchstream_1&__be=1&__pc=PHASED%3ADEFAULT&dpr=1&__rev=1001317759&__s=zqlse7%3A844brb%3Ags1lwz&__hsi=6749401266571238710-0&jazoest=27924&__spin_r=1001317759&__spin_b=trunk&__spin_t=1571467432&__adt=1&ajaxpipe_fetch_stream=1

            # {"profile_id":"100040780699272","vanity":"haley.kersey.16","sk":"timeline","profile_has_parallel_pagelets":"","tab_key":"timeline","target_id":"timeline_story_container_100040780699272","pager_target_id":"timeline_pager_container_100040780699272","start":"0","end":"1572591599","cursor":"AQHRsRXfa2YP6yX9ZrBOitM-494S8xuACUxK-cptNFDJXklI14GSPAZnMkSzqt9Ra33NkXkJZSks2bQX268aDu-l0xXohj4gXg650vR3xXMGlw_qIPgWGHNClzUB1gCRDmLa","page_id":"1"}
            if vanity is None:
                data = '{"profile_id":"' + userid + '","id":"' + userid + '","sk":"timeline","profile_has_parallel_pagelets":"","tab_key":"timeline","target_id":"timeline_story_container_' + userid + '","pager_target_id":"timeline_pager_container_' + userid + '","start":"0","end":"' + str(
                    helper_time.ts_since_1970(10) +
                    10000000  # 这个表示当前时间一个月后的时间戳
                ) + '","cursor":"' + parse.quote(
                    cursor) + '","page_id":"' + str(page) + '"}'
            else:
                # data = '{"profile_id":"' + userid + '","vanity":"' + vanity + '","sk":"timeline","profile_has_parallel_pagelets":"","tab_key":"timeline","target_id":"timeline_story_container_' + userid + '","pager_target_id":"timeline_pager_container_' + userid + '","start":"0","end":"' + str(
                #     helper_time.ts_since_1970(10) +
                #     10000000  # 这个表示当前时间一个月后的时间戳
                # ) + '","cursor":"' + parse.quote(
                #     cursor) + '","page_id":"' + str(page) + '"}'

                data = '{"profile_id":"' + userid + '","vanity":"' + vanity + '","sk":"timeline","profile_has_parallel_pagelets":"","tab_key":"timeline","target_id":"timeline_story_container_' + userid + '","pager_target_id":"timeline_pager_container_' + userid + '","start":"0","end":"' + str(
                    helper_time.ts_since_1970(10) +
                    10000000  # 这个表示当前时间一个月后的时间戳
                ) + '","cursor":"' + parse.quote(
                    cursor) + '","page_id":"' + str(page) + '"}'

            url = 'https://www.facebook.com/ajax/pagelet/generic.php/ProfileTimelineJumperStoriesPagelet?fb_dtsg_ag=' + parse.quote(
                self.fb_dtsg_ag
            ) + '&ajaxpipe=1&ajaxpipe_token=' + parse.quote(
                self.ajaxpipe_token
            ) + '&no_script_path=1&data=' + parse.quote(
                data
            ) + '&__user=' + self._userid + '&__a=1&__csr=&__req=fetchstream_4&__be=1&__pc=PHASED:DEFAULT&dpr=1&__rev=' + self._rev + '&__hsi=' + self.hsi + '&jazoest=' + self.jazoest + '&__spin_r=' + self._rev + '&__spin_b=trunk&__spin_t=' + self._spin_t + '&ajaxpipe_fetch_stream=1'  # &__adt=4

        return url

    def _get_posts_sub(self,
                       task: IscoutTask,
                       hostuser: NetworkProfile,
                       reason: str = None,
                       timerange: int = 30) -> iter:
        """手机+PC浏览器结合版\n"""
        try:
            if not isinstance(hostuser, NetworkProfile):
                self._logger.error("Invalid hostuser for getting Posts")
                return

            if hostuser.url is None or hostuser.url == "":
                hostuser.url = 'https://www.facebook.com/profile.php?id={}'.format(
                    hostuser._userid)

            vanity = None
            m = self._re_vanity.search(hostuser.url)
            if not m is None:
                vanity = m.group(1).strip()
                if vanity == "profile.php":
                    vanity = None

            # murl = hostuser.url.replace('www', 'm')
            cursor = None

            totalcount = 0  #用于先写死只获取前100个POST
            not_in_timerange_cnt: int = 0
            page = 0
            got: bool = False
            curr_page_ct_cnt = 0
            collection_token: str = None
            pagelet_token: str = None
            lst_ts: str = str(helper_time.ts_since_1970(10))
            isfirst: bool = True
            nextpage: bool = True
            existposts: dict = {}
            while nextpage:
                try:
                    # # 尝试跳转手机端网页
                    # mhtml = self._ha.getstring(murl,
                    #                            headers="""
                    # accept: */*
                    # accept-encoding: gzip, deflate
                    # accept-language: en-US,en;q=0.9,zh;q=0.8
                    # cache-control: no-cache
                    # pragma: no-cache
                    # referer: {}
                    # sec-fetch-mode: cors
                    # sec-fetch-site: same-origin
                    # user-agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Mobile Safari/537.36
                    # x-requested-with: XMLHttpRequest
                    # x-response-format: JSONStream""".format(murl))
                    # if mhtml is None or mhtml == "":
                    #     return
                    # m = self._re_m_cursor.search(mhtml)
                    # if m is None:
                    #     # self._logger.error(
                    #     #     "Match m-cursor failed:\ntaskid:{}\nbatchid:{}\nhostuser:{}\nhostuserurl:{}"
                    #     #     .format(task.taskid, task.batchid,
                    #     #             hostuser.nickname, hostuser.url))
                    #     nextpage = False
                    # else:
                    #     cursor = m.group(2).strip()
                    #     murl = "https://m.facebook.com/profile/timeline/stream/?" + m.group(
                    #         1).strip()

                    url = self._build_posts_url(hostuser._userid,
                                                hostuser.nickname,
                                                hostuser.url, vanity, page,
                                                collection_token, cursor,
                                                pagelet_token, lst_ts, isfirst)

                    html = self._ha.getstring(url,
                                              headers='''
                    accept: */*
                    accept-encoding: gzip, deflate
                    accept-language: en-US,en;q=0.9
                    cache-control: no-cache
                    pragma: no-cache
                    referer: {}
                    sec-fetch-mode: same-origin
                    sec-fetch-site: same-origin
                    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36
                    viewport-width: 1600'''.format(hostuser.url))

                    if collection_token is None:
                        # aria-controls=\"pagelet_timeline_app_collection_100012401268356:2356318349:2\"
                        m = re.search(
                            r'pagelet_timeline_app_collection_([\d:]+?)\\"',
                            html, re.S)
                        if not m is None:
                            # 100012401268356:2356318349:2
                            collection_token = m.group(1).rstrip()
                    if pagelet_token is None:
                        # "pagelet_token":"AWv9jIWdg5s52Nof1GKmH2bepQJzpLGdiuqTT299-mCLaJbofF9UT2MQtTo4Dk75kr8"
                        succ, pagelet_token = helper_str.substringif(
                            html, 'pagelet_token":"', '"')

                    # 第一次进来的html里的
                    # ,end:"1575187199",cursor:"AQHRCsR
                    # HqleZpitW_pLn1TW5kI5g5GXOjAtMUO1L
                    # Teik1PlM4pP0CxCKEuJoc2_V281DTyW-E
                    # -znuu7cGvTVfPD59oJb5rfXAGsi12Ne4a
                    # TCVJBOcgklbQA_i297Ch23h_Ff",page_id:"1"}
                    # 下一页的cursor
                    # "start": "0",
                    # "end": "1575187199",
                    # "cursor": "AQHR9edSmoelr_rijkg7whU1RqQDsd
                    # 17uxUjkfq61vZE3YZTuFwX2GjFtjfgDCQc1wRqYtj
                    # Lu-6I3KCZm0emjg1b5SMxz0exUh45-SNw8otCu34ZL0bwCwpPZM1fM0-8mcrz",
                    # "page_id": "2"

                    succ: bool = False
                    if isfirst:
                        # 第一页要把cursor置为空，
                        # 否则就跳过了前两条POST
                        cursor = ''
                    else:
                        m = self._re_cursor.search(html)
                        if m is None:
                            nextpage = False
                        else:
                            cursor = m.group(1)
                            if cursor is None or cursor == "":
                                nextpage = False

                    got = False
                    curr_page_ct_cnt = 0

                    if page == 0:  # 第一页是html，很难解析，第二页有第一页重复的
                        continue

                    # 传入existposts，函数里面需要自行去重
                    for data in self._parse_posts(task, hostuser, html, reason,
                                                  existposts, timerange):

                        if isinstance(data, NetworkPost) and data.isroot:
                            curr_page_ct_cnt += 1
                            totalcount += 1
                            # 此处统一过滤，以便在一整页都没有符合
                            # 条件的post的时候退出循环
                            # 只过滤主POSTs，要判断是否为isroot
                            if not self._is_post_in_timerange(
                                    hostuser, data, timerange=timerange):
                                self._logger.info(
                                    "Post of [{}({})] on page {} is not in time range: {}"
                                    .format(hostuser.nickname,
                                            hostuser._userid, page,
                                            data._postid))
                                not_in_timerange_cnt += 1
                            else:
                                #只要不连续出现有在时间范围内的，就重置标记
                                not_in_timerange_cnt = 0

                        if not got:
                            got = True

                        # 先把最后拿到的这个返回
                        yield data

                        # 再判断时间范围
                        if totalcount >= 100:
                            break
                        if not_in_timerange_cnt >= 10:
                            self._logger.info(
                                "Continuously 10 Posts of [{}({})] not in time range, break"
                                .format(hostuser.nickname, hostuser._userid))
                            break

                    if got:
                        self._logger.info(
                            "Got posts of [{}({})] on page {}, {} posts found".
                            format(hostuser.nickname, hostuser._userid, page,
                                   curr_page_ct_cnt))

                    if not isfirst and (not got or curr_page_ct_cnt < 1):
                        break
                    if not isfirst and cursor is None:
                        break

                    if totalcount >= 100:
                        break

                except Exception:
                    self._logger.error(
                        "Get Posts on page {} error:\nuserid={}\nusername={}\nerror:{}"
                        .format(page, hostuser._userid, hostuser.nickname,
                                traceback.format_exc()))
                finally:
                    isfirst = False
                    page += 1
                    time.sleep(0.5)

            self._logger.info(
                "Get user {}({}) post complete, {} posts found.".format(
                    hostuser.nickname, hostuser._userid, totalcount))

        except Exception:
            self._logger.error(
                "Get fb posts error:\nuserid={}\nusername={}\nerror:{}".format(
                    hostuser._userid, hostuser.nickname,
                    traceback.format_exc()))

    def _is_post_in_timerange(self,
                              hostuser: NetworkProfile,
                              data: NetworkPost,
                              timerange: int = 30) -> bool:
        """判断POST是否在时间范围内"""
        res: bool = False
        try:
            if not isinstance(data.posttime_datetime, datetime.datetime):
                return res

            timedelta = datetime.datetime.utcnow() - data.posttime_datetime
            if timedelta.days > timerange:
                return res
            res = True
        except Exception:
            self._logger.info(
                "Judge if Post is in time range error: {}({})".format(
                    hostuser.nickname, hostuser._userid))
        return res

    def _extract_content_seg(self, jseg: dict,
                             hostuser: NetworkProfile) -> str:
        """判断seg是否包含master_post内容，返回master_post的 content，
        没找到返回None """
        html: str = None
        try:

            if not jseg.__contains__('content') or \
                not jseg['content'].__contains__('payload'):
                return html

            jpayload = jseg['content']['payload']
            if jpayload is None or len(jpayload) < 1:
                return html

            if not jpayload.__contains__("id"):
                return html

            jid = jpayload['id']
            if not isinstance(jid, str) or jid == '':
                return html

            if not jid.__contains__('timeline_jumper_story_pagelet_') or \
            not jseg.__contains__('content') or \
            not jseg['content'].__contains__("payload") or \
            not jseg['content']['payload'].__contains__('content'):
                return html
            jcont = jseg['content']['payload']['content']
            if jcont is None or len(jcont) != 1:
                return html
            if not jcont.__contains__(jid):
                return html

            html = jcont[jid]

        except Exception:
            self._logger.error(
                "Get post master seg error:\nuserid={}\nusername={}\nerror:{}".
                format(hostuser._userid, hostuser.nickname,
                       traceback.format_exc()))
        return html

    def _extract_comments_seg(self, jseg: dict,
                              hostuser: NetworkProfile) -> dict:
        """判断seg是否包含评论、视频部分，并返回评论、视频部分seg，
        没找到返回None"""
        res: dict = None
        try:

            if not jseg.__contains__('content') or \
                not jseg['content'].__contains__('payload'):
                return res

            jpayload = jseg['content']['payload']
            if jpayload is None or len(jpayload) < 1:
                return res

            if not jpayload.__contains__("id"):
                return res

            jid = jpayload['id']
            if not isinstance(jid, str) or jid == '':
                return res

            # 视频块
            # 评论块
            # not jid.__contains__('FeedStoryUFIRootQueryRelayPreloader_') or \
            if not jpayload.__contains__('jsmods') or \
                not jpayload['jsmods'].__contains__('pre_display_requires'):
                return res
            jpre = jpayload['jsmods']['pre_display_requires']
            if jpre is None or len(jpre) < 1:
                return res
            for jdata in jpre:
                if not isinstance(jdata, list):
                    continue
                for jdata1 in jdata:
                    if not isinstance(jdata1, list):
                        continue
                    for jdata2 in jdata1:
                        if not isinstance(jdata2, dict):
                            continue
                        if not jdata2.__contains__('__bbox') or \
                            not jdata2['__bbox'].__contains__('result') or \
                            not jdata2['__bbox']['result'].__contains__('data') or \
                            not jdata2['__bbox']['result']['data'].__contains__('feedback'):
                            continue
                        # res = jdata2['__bbox']['result']['data']['feedback']
                        # 只取到__bbox这一层,__bbox下的variables后面会用到
                        res = jdata2['__bbox']
                        break
                    if not res is None:
                        break
                if not res is None:
                    break

        except Exception:
            self._logger.error(
                "Get post comments seg error:\nuserid={}\nusername={}\nerror:{}"
                .format(hostuser._userid, hostuser.nickname,
                        traceback.format_exc()))
        return res

    def _parse_posts(self,
                     task: IscoutTask,
                     hostuser: NetworkProfile,
                     html,
                     reason,
                     existposts: dict,
                     timerange: int = 30) -> iter:
        """按顺序拼凑出完整的post"""
        try:
            segs = html.split('/*<!-- fetch-stream -->*/')
            if segs is None or len(segs) < 1:
                return

            # 拿每个payload的id并存储
            master_posts = {}
            slave_posts = {}
            for seg in segs:
                try:
                    if not isinstance(seg, str) or seg == "":
                        continue

                    jseg = json.loads(seg)
                    if jseg is None:
                        continue

                    # 拿 segid
                    if not jseg.__contains__('content') or \
                        not jseg['content'].__contains__('payload'):
                        continue
                    jpayload = jseg['content']['payload']
                    if jpayload is None or len(jpayload) < 1:
                        continue
                    if not jpayload.__contains__("id"):
                        continue
                    jid = jpayload['id']
                    if not isinstance(jid, str) or jid == '':
                        continue

                    if jid.__contains__('timeline_jumper_story_pagelet_'):
                        master_posts[jid] = seg
                    elif jid.__contains__(
                            'FeedStoryUFIRootQueryRelayPreloader_'):
                        slave_posts[jid] = seg

                except Exception:
                    self._logger.error(
                        "Parse one POST seg error:\nuserid={}\nusername={}\nerror:{}"
                        .format(hostuser._userid, hostuser.nickname,
                                traceback.format_exc()))

            # 根据id关联master和slave POSTs
            # timeline_jumper_story_pagelet_
            # FeedStoryUFIRootQueryRelayPreloader_
            # "id": "adp_FeedStoryUFIRootQueryRelayPreloader_5dcd4ea1160723820350336"
            sorted_posts = {}
            for mid, seg in master_posts.items():
                try:
                    jseg = json.loads(seg)
                    if not sorted_posts.__contains__(mid):
                        sorted_posts[mid] = (jseg, [])
                    for m in self._re_feedstory_id.finditer(seg):
                        if m is None:
                            continue
                        slave_pid = m.group(1).strip()
                        if slave_posts.__contains__(slave_pid):
                            sorted_posts[mid][1].append(
                                json.loads(slave_posts[slave_pid]))

                except Exception:
                    self._logger.error(
                        "Sort one POST seg error:\nuserid={}\nusername={}\nerror:{}"
                        .format(hostuser._userid, hostuser.nickname,
                                traceback.format_exc()))

            # 解析
            for jseg_master, jseg_slaves in sorted_posts.values():
                for data in self._parse_post_group(task,
                                                   hostuser,
                                                   jseg_master,
                                                   jseg_slaves,
                                                   reason,
                                                   existposts,
                                                   timerange=timerange):
                    yield data

        except Exception:
            self._logger.error(
                "Find segs for one post error:\nuserid={}\nusername={}\nerror:{}"
                .format(hostuser._userid, hostuser.nickname,
                        traceback.format_exc()))

    def _parse_post_group(self,
                          task: IscoutTask,
                          hostuser: NetworkProfile,
                          jseg_master: dict,
                          jseg_slaves: list,
                          reason,
                          existposts: dict,
                          timerange: int = 30) -> iter:
        """"""
        try:
            post_master: NetworkPost = None
            for data in self._parse_master_post(task,
                                                hostuser,
                                                jseg_master,
                                                reason,
                                                existposts,
                                                timerange=timerange):
                if isinstance(data, NetworkPost):
                    post_master = data
                    self._logger.info("Got post of [{}({})]: {}".format(
                        hostuser.nickname, hostuser._userid, data._postid))
                yield data

            if post_master is None:
                return

            for jslave in jseg_slaves:
                for data in self._parse_slave_post(task,
                                                   hostuser,
                                                   post_master,
                                                   jslave,
                                                   reason,
                                                   existposts,
                                                   timerange=timerange):
                    # 这外面不能管POSTs的依赖关系，里面有递归关联
                    # if isinstance(data, NetworkPost):
                    #     data.isroot = False
                    #     data.parentpostid = post_master._postid
                    yield data

        except Exception:
            self._logger.error(
                "Parse post group error:\nuserid={}\nusername={}\nerror:{}".
                format(hostuser._userid, hostuser.nickname,
                       traceback.format_exc()))

    def _parse_master_post(self,
                           task: IscoutTask,
                           hostuser: NetworkProfile,
                           jseg: dict,
                           reason,
                           existposts: dict,
                           timerange: int = 30) -> iter:
        """parse master post"""
        try:
            if not isinstance(jseg, dict):
                self._logger.error(
                    "Invalid map obj for parse master post:\nuserid={}\nusername={}"
                    .format(hostuser._userid, hostuser.nickname))
                return

            # content = self._extract_content_seg(jseg, hostuser)
            # if content is None or content == "":
            #     return

            for data in self._parse_post_content(task,
                                                 hostuser,
                                                 jseg,
                                                 reason,
                                                 existposts,
                                                 timerange=timerange):
                yield data

        except Exception:
            self._logger.error(
                "Parse fb master_posts one story error:\nuserid={}\nusername={}\nerror:{}"
                .format(hostuser._userid, hostuser.nickname,
                        traceback.format_exc()))

    def _parse_slave_post(self,
                          task: IscoutTask,
                          hostuser: NetworkProfile,
                          post_master: NetworkPost,
                          jseg: dict,
                          reason,
                          existposts: dict,
                          timerange: int = 30) -> iter:
        """parse master post"""
        try:

            if not isinstance(jseg, dict):
                self._logger.error(
                    "Invalid map obj for parse slave post:\nuserid={}\nusername={}"
                    .format(hostuser._userid, hostuser.nickname))
                return

            jbbox = self._extract_comments_seg(jseg, hostuser)
            if not jbbox.__contains__('result') or \
                    not jbbox['result'].__contains__('data') or \
                    not jbbox['result']['data'].__contains__('feedback'):
                return
            jfeedback = jbbox['result']['data']['feedback']
            if jfeedback is None:
                return

            # 拿真实 postid
            if jfeedback.__contains__("id"):
                tmp = jfeedback["id"]
                try:
                    post_master.postid = helper_str.base64_decode(tmp)

                except Exception:
                    self._logger.debug(
                        "Get real postid failed:\nuserid={}\nusername={}".
                        format(hostuser._userid, hostuser.nickname))

            # 点赞数
            if jfeedback.__contains__('reaction_count') and \
                jfeedback['reaction_count'].__contains__('count'):
                likecount = jfeedback['reaction_count']['count']
                if isinstance(likecount, int):
                    post_master.likecount = likecount
                    if likecount:
                        self._get_post_likes(tmp, post_master)

            # 主POST点赞的人员列表
            # 获取每一个点赞的人会有一个单独的请求，需要docid
            # 只有等后面把整个fb功能合并了再看怎么玩
            # 上面实现了


            # 评论数
            if jfeedback.__contains__("comment_count") and \
                jfeedback['comment_count'].__contains__('total_count'):
                post_master.replycount = jfeedback['comment_count'][
                    'total_count']

            # 评论块
            for data in self._parse_post_comments(task,
                                                  hostuser,
                                                  post_master,
                                                  jbbox,
                                                  reason,
                                                  existposts,
                                                  timerange=timerange):
                yield data

        except Exception:
            self._logger.error(
                "Parse fb slave_posts one story error:\nuserid={}\nusername={}\nerror:{}"
                .format(hostuser._userid, hostuser.nickname,
                        traceback.format_exc()))

    def _get_post_likes(self, postid, post_master):
        res = []
        try:
            url = f'https://www.facebook.com/ufi/reaction/profile/dialog/?ft_ent_identifier={postid}&fb_dtsg_ag={self.fb_dtsg_ag}&__a=1'
            headers = """
Host: www.facebook.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2
Accept-Encoding: gzip, deflate
Connection: keep-alive
Cookie: wd=1440x480; fr=1irS58koELtHY7EU1.AWWVNkcKFZdouvs9Vd9A36d0e10.BfF-g8.eq.F8Z.0.0.BfHm1q.AWWK0Laj; sb=POgXXxyJQMGeAZXHaVMZCHe2; datr=POgXX0sf3wDUty3Sl-TuWB7N; c_user=100036843820101; xs=50%3AhoD3h_4d7PGqjQ%3A2%3A1595498189%3A744%3A1314; spin=r.1002420508_b.trunk_t.1595829604_s.1_v.2_; presence=EDvF3EtimeF1595829735EuserFA21B36843820101A2EstateFDutF1595829735381CEchF_7bCC; act=1595829846717%2F2
Upgrade-Insecure-Requests: 1
Cache-Control: max-age=0
TE: Trailers"""
            html = self._ha.getstring(url, headers=headers)
            groups = re.findall(r'class=\\"_5i_q\\">.*?title=\\"(.*?)\\".*?user.php\?id=(\d+)', html)
            if groups:
                for group in groups:
                    nickname, userid = group
                    one = NetworkProfile(nickname, userid, "facebook")
                    one.nickname = nickname
                    post_master.set_likes(one)
        except Exception:
            self._logger.error('Got post likes fail: {}, {}'.format(postid, traceback.format_exc()))

################################
# post content

    def _parse_post_content(self,
                            task: IscoutTask,
                            hostuser: NetworkProfile,
                            jseg: dict,
                            reason,
                            existposts: dict,
                            timerange: int = 30) -> iter:
        """parse the post content part"""
        try:
            if not isinstance(jseg, dict):
                return
            if not isinstance(existposts, dict):
                self._logger.error("Invalid existposts dict")
                return

            content = self._extract_content_seg(jseg, hostuser)
            if content is None or content == "":
                return
            if not isinstance(timerange, int) or timerange < 1:
                return

            hdoc: etree._Element = None
            try:
                hdoc: etree._Element = etree.XML(content, etree.XMLParser())
            except Exception:
                hdoc = None
                self._logger.debug(
                    "Parse fb posts one story error1:\nuserid={}\nusername={}\nerror:{}"
                    .format(hostuser._userid, hostuser.nickname,
                            traceback.format_exc()))
            if hdoc is None:
                try:
                    hdoc = etree.XML(
                        content,
                        etree.XMLParser(recover=True, resolve_entities=False))
                except Exception:
                    hdoc = None
                    self._logger.debug(
                        "Parse fb posts one story error2:\nuserid={}\nusername={}\nerror:{}"
                        .format(hostuser._userid, hostuser.nickname,
                                traceback.format_exc()))

            if hdoc is None:
                self._logger.error(
                    "Parse fb posts one story failed:\nuserid={}\nusername={}".
                    format(hostuser._userid, hostuser.nickname))
                return

            # postid
            postid = hdoc.get('id')
            if postid is None or postid == "":
                return

            post: NetworkPost = NetworkPost(postid, self._SOURCE,
                                            hostuser._userid)
            post.nickname = hostuser.nickname

            # post time
            # 根据posttime时间范围过滤
            # 连续10个post不在时间范围则退出
            # %I:%M %p （%p是AM PM）
            # m = self._re_posttime.search(content)
            ts = helper_str.substring(postid, 'jumper_', '_S')
            if ts is None:
                self._logger.info(
                    "Get posttime failed, user={}({}), postid: {}".format(
                        hostuser.nickname, hostuser._userid, postid))
                return
            else:
                dt_now = datetime.datetime.utcnow()
                dt_post = datetime.datetime.utcfromtimestamp(int(ts))
                timedelta = dt_now - dt_post
                post.posttime_datetime = dt_post
                post.posttime = dt_post.strftime('%Y-%m-%d %H:%M:%S')
                if timedelta.days > timerange:
                    return

            # 已拿到过的post去重丢弃。
            if existposts.__contains__(postid):
                return
            else:
                existposts[postid] = None

            # text
            txt = ''
            for t in hdoc.itertext():
                t: str = t.strip()
                t = self._re_story_text_replace.sub(' ', t)
                if t == '':
                    continue
                txt += t + ' '

            # imags
            imgids = {}  #图片去重
            for ximg in hdoc.findall('.//img'):
                try:
                    # <img src=这个是头像图片也有的
                    # <img data-src=这个才是POST中的照片
                    srcurl = ximg.get('data-src')
                    if srcurl is None or srcurl == "":
                        srcurl = ximg.get('src')
                        if srcurl is None or srcurl == '':
                            continue

                    # img url
                    srcurl = parse.unquote(srcurl)
                    # 过滤p50x50的小图
                    if srcurl.__contains__('/p50x50/'):
                        continue
                    m = self._re_rsc_name.search(srcurl)
                    rscname = None
                    if not m is None:
                        rscname = m.group(1).strip()
                    if rscname is None or rscname == '':
                        continue

                    rsc = NetworkResource(task, 'zplus', srcurl, 'facebook',
                                          EResourceType.Picture)
                    rsc.filename = rscname
                    rsc.resourceid = rscname
                    if rsc.filename.__contains__('.'):
                        rsc.extension = rsc.filename.split('.')[-1]

                    # image reduplicate
                    if imgids.__contains__(rscname):
                        continue
                    else:
                        imgids[rscname] = None

                    # alt
                    alt = ximg.get('alt')
                    if not alt is None and alt != "":
                        alt: str = alt.strip()
                        alt = self._re_story_text_replace.sub(' ', alt)
                        if alt == '':
                            continue
                        txt += alt + ' '
                    # stream
                    rsc.stream = self._ha.get_response_stream(srcurl,
                                                              headers='''
                    accept: image/png, image/svg+xml, image/*; q=0.8, */*; q=0.5
                    accept-encoding: gzip, deflate
                    accept-language: en-US,en;q=0.9
                    cache-control: no-cache
                    pragma: no-cache
                    referer: https://www.facebook.com
                    sec-fetch-mode: cors
                    sec-fetch-site: same-origin
                    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36
                    viewport-width: 1600''')

                    # 验证图片大小
                    if len(rsc.stream) < 50:
                        rsc.stream.close()
                        continue

                    post.set_resource(rsc)
                    self._logger.info(
                        "Got image resource of [{}({})]: {}".format(
                            hostuser.nickname, hostuser._userid, rsc.filename))
                    yield rsc

                except Exception:
                    self._logger.error(
                        "Get image resource error: {}({}) {}".format(
                            hostuser.nickname, hostuser._userid,
                            traceback.format_exc()))

            # videos
            for data in self._parse_videos(task, hostuser, post, jseg, reason,
                                           existposts):
                yield data

            # text放在这赋值是因为资源数据的标签中可能附带文本
            # 需要一起加上
            post.text = txt

            yield post

        except Exception:
            self._logger.error(
                "Parse fb post content error:\nuserid={}\nusername={}\nerror:{}"
                .format(hostuser._userid, hostuser.nickname,
                        traceback.format_exc()))

    # def _parse_imgs(
    #         self,
    #         task: IscoutTask,
    #         hostuser: NetworkProfile,
    #         post: NetworkPost,
    #         hdoc: etree._Element,
    #         reason,
    #         existposts: dict,
    # ) -> iter:
    #     """parse imgs"""
    #     try:
    #         pass
    #     except Exception:
    #         self._logger.error(
    #             "Parse fb post imgs error:\nuserid={}\nusername={}\nerror:{}".
    #             format(hostuser._userid, hostuser.nickname,
    #                    traceback.format_exc()))

    def _parse_videos(
            self,
            task: IscoutTask,
            hostuser: NetworkProfile,
            post: NetworkPost,
            jseg: dict,
            reason,
            existposts: dict,
    ) -> iter:
        """parse videos"""
        try:
            if not isinstance(jseg, dict):
                return

            jstr: str = json.dumps(jseg)
            vedioids = {}  #视频去重
            if isinstance(jstr, str) and jstr != "":
                for mvideo in self._re_videos.finditer(jstr):
                    try:
                        if mvideo is None:
                            continue
                        urlvdo = mvideo.group(1).strip().replace(
                            '\\', '') + '&bytestart=0'
                        m = self._re_rsc_name.search(urlvdo)
                        rscname = None
                        if not m is None:
                            rscname = m.group(1).strip()
                        # vedio reduplicate
                        if vedioids.__contains__(rscname):
                            continue
                        else:
                            vedioids[rscname] = None

                        rsc = NetworkResource(task, 'zplus', urlvdo,
                                              self._SOURCE,
                                              EResourceType.Video)
                        rsc.filename = rscname
                        rsc.resourceid = rscname
                        if rsc.filename.__contains__('.'):
                            rsc.extension = rsc.filename.split('.')[-1]
                        # rsc._resourcetype = EResourceType.Video

                        rsc.stream = self._ha.get_response_stream(urlvdo,
                                                                  headers="""
                        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
                        accept-encoding: gzip, deflate
                        accept-language: en-US,en;q=0.9
                        cache-control: no-cache
                        pragma: no-cache
                        sec-fetch-mode: navigate
                        sec-fetch-site: none
                        sec-fetch-user: ?1
                        upgrade-insecure-requests: 1
                        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"""
                                                                  )
                        # 验证视频大小
                        if len(rsc.stream) < 100:
                            rsc.stream.close()
                            continue

                        post.set_resource(rsc)
                        self._logger.info(
                            "Got video resource of [{}({})]: {} {}kb".format(
                                hostuser.nickname, hostuser._userid,
                                rsc.filename, int(len(rsc.stream) / 1024)))
                        yield rsc
                    except Exception:
                        self._logger.error(
                            "Get video resource error: {}({}) {}".format(
                                hostuser.nickname, hostuser._userid,
                                traceback.format_exc()))

        except Exception:
            self._logger.error(
                "Parse fb post videos error:\nuserid={}\nusername={}\nerror:{}"
                .format(hostuser._userid, hostuser.nickname,
                        traceback.format_exc()))

################################
# post likes/comments

    def _parse_post_comments(self,
                             task: IscoutTask,
                             hostuser: NetworkProfile,
                             post_master: NetworkPost,
                             jbbox: dict,
                             reason,
                             existposts: dict,
                             timerange: int = 30) -> iter:
        """解析评论段，其中可能包含主POST的视频等资源，所以
        需要传入父评论 post_master"""
        try:
            if not jbbox.__contains__('result') or \
                    not jbbox['result'].__contains__('data') or \
                    not jbbox['result']['data'].__contains__('feedback'):
                return
            jfeedback = jbbox['result']['data']['feedback']

            if not isinstance(jfeedback, dict):
                return

            if not jfeedback.__contains__("display_comments") or \
                not jfeedback['display_comments'].__contains__('edges'):
                return

            edges = jfeedback['display_comments']['edges']
            if edges is None or len(edges) < 1:
                return

            # 当前页
            jvar = jbbox['variables']
            for jedge in edges:
                try:
                    for data in self._parse_one_comment(task,
                                                        hostuser,
                                                        post_master,
                                                        jedge,
                                                        jvar,
                                                        reason,
                                                        existposts,
                                                        timerange=timerange):
                        yield data
                except Exception:
                    self._logger.error(
                        "Parse fb post one comment error:\nuserid={}\nusername={}\nerror:{}"
                        .format(hostuser._userid, hostuser.nickname,
                                traceback.format_exc()))

            # return
            # 此功能暂未实现，往后排
            # 加载更多评论
            for data in self._load_more_comments(task,
                                                 hostuser,
                                                 post_master,
                                                 jbbox,
                                                 reason,
                                                 existposts,
                                                 timerange=timerange):
                yield data

        except Exception:
            self._logger.error(
                "Parse fb post comments error:\nuserid={}\nusername={}\nerror:{}"
                .format(hostuser._userid, hostuser.nickname,
                        traceback.format_exc()))

    def _load_more_comments(self,
                            task: IscoutTask,
                            hostuser: NetworkProfile,
                            post_master: NetworkPost,
                            jbbox: dict,
                            reason,
                            existposts: dict,
                            timerange: int = 30) -> iter:
        """load more comments"""
        try:
            if not jbbox.__contains__('result') or \
                    not jbbox['result'].__contains__('data') or \
                    not jbbox['result']['data'].__contains__('feedback'):
                return
            jfeedback = jbbox['result']['data']['feedback']

            # has_next_page为true, variables的after为end_cursor, first为after_count, last=null
            # has_previous_page为true, variables的before为start_cursor, before_count为after_count, first=null
            # 同时为true需要发两个请求分别处理
            if not jfeedback['display_comments'].__contains__('page_info'):
                return
            jpage = jfeedback['display_comments']['page_info']
            if not jpage.__contains__('has_next_page') or \
                not jpage.__contains__('end_cursor'):
                return
            if not jpage.__contains__('has_previous_page') or \
                not jpage.__contains__('start_cursor'):
                return
            has_next_page = jpage['has_next_page']
            has_previous_page = jpage['has_previous_page']
            if has_next_page == False and has_previous_page == False:
                return
            endcursor = '"' + jpage['end_cursor'] + '"'
            startcursor = '"' + jpage['start_cursor'] + '"'
            after_count = jfeedback['display_comments']['after_count']
            before_count = jfeedback['display_comments']['before_count']
            page_size = jfeedback['display_comments']['page_size']

            # POST请求体的 docid 在 js里面，要搜一下
            docid = self._get_more_comments_docid()
            if docid is None:
                return

            # 请求更多评论
            # av=100013325533097&__user=100013325533097&__a=1&__dyn=7AgNeS4amaAxd2u6aJGeFxqeCwDKEyGzEyfiheC263GdwIhE98nyUdUaofVUnnyorxuE99XyEjKewExaawUz8S2SVFEgU9A69V8-cxu5od8cEiwBx61zwzxOm3GEuxm1VDBwm8owJDx6WxS68nxK48gjG12BwLyUG58aU-1uUkGE-Wx28CwoGzku4EhwG-7UylxfwzAx2fz9rBxefxi2iazUlVEaUK5WwgF4im4equV8y2G5ojyFE-17z8Gdx28y8rwUzFEW5AbxS22cxa78K8xa3q1fwxwIxy5qwCxe1Ty9o9o-7Eoxmm&__csr=&__req=y&__pc=PHASED%3ADEFAULT&dpr=1&__rev=1001430624&__s=3tlah4%3Ah9em22%3Afvhvb8&__hsi=6759445430640164813-0&fb_dtsg=AQHR4ELVbwec%3AAQEOIzEkWgRc&jazoest=22094&__spin_r=1001430624&__spin_b=trunk&__spin_t=1573717743&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=UFI2CommentsProviderPaginationQuery&variables=%7B%22after%22%3A%22AQHRZqy1NxuVxIDV1Hq_8En9esiiw-_gb4WElUCgHougZwcLrorusVe8jbqRFNc6G4_AZXT7-ILfRzX0d4M66TbmvA%22%2C%22before%22%3Anull%2C%22commentProfilePictureSizeDepth0%22%3A32%2C%22commentProfilePictureSizeDepth1%22%3A20%2C%22displayCommentsFeedbackContext%22%3A%22%7B%5C%22bump_reason%5C%22%3A0%2C%5C%22comment_expand_mode%5C%22%3A2%2C%5C%22comment_permalink_args%5C%22%3A%7B%5C%22comment_id%5C%22%3Anull%2C%5C%22reply_comment_id%5C%22%3Anull%2C%5C%22filter_non_supporters%5C%22%3Anull%7D%2C%5C%22interesting_comment_fbids%5C%22%3A%5B%5D%2C%5C%22is_location_from_search%5C%22%3Afalse%2C%5C%22last_seen_time%5C%22%3Anull%2C%5C%22log_ranked_comment_impressions%5C%22%3Afalse%2C%5C%22probability_to_comment%5C%22%3A0%2C%5C%22story_location%5C%22%3A4%2C%5C%22story_type%5C%22%3A0%7D%22%2C%22displayCommentsContextEnableComment%22%3Afalse%2C%22displayCommentsContextIsAdPreview%22%3Afalse%2C%22displayCommentsContextIsAggregatedShare%22%3Afalse%2C%22displayCommentsContextIsStorySet%22%3Afalse%2C%22feedLocation%22%3A%22TIMELINE%22%2C%22feedbackID%22%3A%22ZmVlZGJhY2s6MjQyMTUzMzIzODE3MDEwOQ%3D%3D%22%2C%22feedbackSource%22%3A21%2C%22first%22%3A1%2C%22focusCommentID%22%3Anull%2C%22includeNestedComments%22%3Atrue%2C%22isInitialFetch%22%3Afalse%2C%22isComet%22%3Afalse%2C%22containerIsFeedStory%22%3Atrue%2C%22containerIsWorkplace%22%3Afalse%2C%22containerIsLiveStory%22%3Afalse%2C%22containerIsTahoe%22%3Afalse%2C%22last%22%3Anull%2C%22scale%22%3A1%2C%22topLevelViewOption%22%3Anull%2C%22useDefaultActor%22%3Atrue%2C%22viewOption%22%3Anull%2C%22UFI2CommentsProvider_commentsKey%22%3Anull%7D&doc_id=2711243315563730
            # {\"bump_reason\":0,\"comment_expand_mode\":2,\"comment_permalink_args\":{\"comment_id\":null,\"reply_comment_id\":null,\"filter_non_supporters\":null},\"interesting_comment_fbids\":[],\"is_location_from_search\":false,\"last_seen_time\":null,\"log_ranked_comment_impressions\":false,\"probability_to_comment\":0,\"story_location\":4,\"story_type\":0}
            jvar = jbbox['variables']
            displayCommentsFeedbackContext: str = jvar['displayCommentsFeedbackContext']
            displayCommentsFeedbackContext = displayCommentsFeedbackContext.replace('\"', '\\"')
            feedbackID = jvar['feedbackTargetID']
            feedbackSource = jvar['feedbackSource']
            # 展开上方的评论
            first = after_count if after_count <= page_size else page_size
            while has_next_page:
                has_next_page = False
                variables = '{' + f'"after":{endcursor},"before":null,"displayCommentsFeedbackContext":"{displayCommentsFeedbackContext}","displayCommentsContextEnableComment":false,"displayCommentsContextIsAdPreview":false,"displayCommentsContextIsAggregatedShare":false,"displayCommentsContextIsStorySet":false,"feedLocation":"TIMELINE","feedbackID":"{feedbackID}","feedbackSource":{feedbackSource},"first":{first},"focusCommentID":null,"includeNestedComments":true,"isInitialFetch":false,"isComet":false,"containerIsFeedStory":true,"containerIsWorkplace":false,"containerIsLiveStory":false,"containerIsTahoe":false,"last":null,"scale":1,"topLevelViewOption":null,"useDefaultActor":true,"viewOption":null,"UFI2CommentsProvider_commentsKey":null' + '}'
                postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__hsi={self.hsi}&__comet_req=0&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=UFI2CommentsProviderPaginationQuery&variables=' + parse.quote(
                    variables) + f'&doc_id={docid}'
                url = 'https://www.facebook.com/api/graphql/'
                html = self._ha.getstring(url, postdata,
                                          headers="""
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9,zh;q=0.8
                cache-control: no-cache
                content-length: {}
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                referer: {}
                sec-fetch-dest: empty
                sec-fetch-mode: cors
                sec-fetch-site: same-origin
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                """.format(len(postdata), hostuser.url))
                jextra_comment = json.loads(html)
                if not jextra_comment.__contains__('data') or \
                        not jextra_comment['data'].__contains__('feedback'):
                    break
                jfeedback = jextra_comment['data']['feedback']
                if not jfeedback.__contains__('display_comments') or \
                    not jfeedback['display_comments'].__contains__('edges'):
                    break
                edges = jfeedback['display_comments']['edges']
                if edges is None or len(edges) < 1:
                    break
                # 如果还有折叠的评论
                if jfeedback['display_comments'].__contains__('page_info'):
                    jpage = jfeedback['display_comments']['page_info']
                    if jpage['has_next_page'] == 'true' or jpage['has_next_page'] is True:
                        has_next_page = True
                        endcursor = '"' + jpage['end_cursor'] + '"'
                        after_count = jfeedback['display_comments']['after_count']
                        page_size = jfeedback['display_comments']['page_size']
                        first = after_count if after_count <= page_size else page_size
                for jedge in edges:
                    try:
                        for data in self._parse_one_comment(task,
                                                            hostuser,
                                                            post_master,
                                                            jedge,
                                                            jvar,
                                                            reason,
                                                            existposts,
                                                            timerange=timerange):
                            yield data
                    except Exception:
                        self._logger.error(
                            "Parse fb post one comment error:\nuserid={}\nusername={}\nerror:{}"
                            .format(hostuser._userid, hostuser.nickname,
                                    traceback.format_exc()))
            # 展开下方的评论
            last = before_count if before_count <= page_size else page_size
            while has_previous_page:
                has_previous_page = False
                variables = '{' + f'"after":null,"before":{startcursor},"displayCommentsFeedbackContext":"{displayCommentsFeedbackContext}","displayCommentsContextEnableComment":false,"displayCommentsContextIsAdPreview":false,"displayCommentsContextIsAggregatedShare":false,"displayCommentsContextIsStorySet":false,"feedLocation":"TIMELINE","feedbackID":"{feedbackID}","feedbackSource":{feedbackSource},"first":null,"focusCommentID":null,"includeNestedComments":true,"isInitialFetch":false,"isComet":false,"containerIsFeedStory":true,"containerIsWorkplace":false,"containerIsLiveStory":false,"containerIsTahoe":false,"last":{last},"scale":1,"topLevelViewOption":null,"useDefaultActor":true,"viewOption":null,"UFI2CommentsProvider_commentsKey":null' + '}'
                postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__hsi={self.hsi}&__comet_req=0&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=UFI2CommentsProviderPaginationQuery&variables=' + parse.quote(
                    variables) + f'&doc_id={docid}'
                url = 'https://www.facebook.com/api/graphql/'
                html = self._ha.getstring(url, postdata,
                                          headers="""
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9,zh;q=0.8
                cache-control: no-cache
                content-length: {}
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                referer: {}
                sec-fetch-dest: empty
                sec-fetch-mode: cors
                sec-fetch-site: same-origin
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                """.format(len(postdata), hostuser.url))
                jextra_comment = json.loads(html)
                if not jextra_comment.__contains__('data') or \
                        not jextra_comment['data'].__contains__('feedback'):
                    return
                jfeedback = jextra_comment['data']['feedback']
                if not jfeedback.__contains__('display_comments') or \
                    not jfeedback['display_comments'].__contains__('edges'):
                    return
                edges = jfeedback['display_comments']['edges']
                if edges is None or len(edges) < 1:
                    return
                # 如果还有折叠的评论
                if jfeedback['display_comments'].__contains__('page_info'):
                    jpage = jfeedback['display_comments']['page_info']
                    if jpage['has_previous_page'] == 'true' or jpage['has_previous_page'] is True:
                        has_previous_page = True
                        startcursor = '"' + jpage['start_cursor'] + '"'
                        before_count = jfeedback['display_comments']['before_count']
                        page_size = jfeedback['display_comments']['page_size']
                        last = before_count if before_count <= page_size else page_size
                for jedge in edges:
                    try:
                        for data in self._parse_one_comment(task,
                                                            hostuser,
                                                            post_master,
                                                            jedge,
                                                            jvar,
                                                            reason,
                                                            existposts,
                                                            timerange=timerange):
                            yield data
                    except Exception:
                        self._logger.error(
                            "Parse fb post one comment error:\nuserid={}\nusername={}\nerror:{}"
                                .format(hostuser._userid, hostuser.nickname,
                                        traceback.format_exc()))
        except Exception:
            self._logger.error(
                "Load more comments error:\nuserid={}\nusername={}\nerror:{}".
                format(hostuser._userid, hostuser.nickname,
                       traceback.format_exc()))

    def _get_more_comments_docid(self) -> str:
        """"""
        try:
            # params: {
            #     operationKind: "query",
            #     name: "UFI2CommentsProviderPaginationQuery",
            #     id: "2711243315563730", # 取这个id
            #     text: null,
            #     metadata: {}
            # }
            if not FBPosts._docid_more_comments is None:
                return FBPosts._docid_more_comments

            with FBPosts._docid_more_comments_locker:
                for urljs, js in self._get_js_resources():
                    try:
                        if not js.__contains__(
                                'UFI2CommentsProviderPaginationQuery'):
                            continue

                        m = self._re_docid_more_comments.search(js)
                        if m is None:
                            continue

                        params = m.group(1)
                        # params: {
                        #     id: "4629548627085906",
                        #     metadata: {},
                        #     name: "UFI2CommentsProviderPaginationQuery",
                        #     operationKind: "query",
                        #     text: null
                        # }
                        FBPosts._docid_more_comments = re.search(r'id:\s*?"(\d+)"', params).group(1)
                        return FBPosts._docid_more_comments

                    except Exception:
                        self._logger.error(
                            "Access docid for more comments in one js file error: {}"
                            .format(traceback.format_exc()))

        except Exception:
            self._logger.error(
                "Access docid for more comments error: {}".format(
                    traceback.format_exc()))

    def _parse_one_comment(self,
                           task: IscoutTask,
                           hostuser: NetworkProfile,
                           post_master: NetworkPost,
                           jedge: dict,
                           jvar: dict,
                           reason,
                           existposts: dict,
                           timerange: int = 30) -> iter:
        """parse one comments"""
        try:
            if not isinstance(jedge, dict):
                return

            if not jedge.__contains__('node'):
                return

            jnode = jedge['node']
            if jnode is None:
                return

            # commentid
            cid: str = None
            if not jnode.__contains__('id'):
                return
            sid = jnode['id']
            if not isinstance(sid, str):
                return
            try:
                cid: str = helper_str.base64_decode(sid)
            except Exception:
                self._logger.error(
                    "Parse fb comment id error:\nuserid={}\nusername={}\nerror:{}"
                    .format(hostuser._userid, hostuser.nickname,
                            traceback.format_exc()))

            # author
            authorid: str = None
            authorname: str = None
            if not jnode.__contains__('author'):
                return
            jauther = jnode['author']
            if jauther is None:
                return
            if not jauther.__contains__("id"):
                return
            authorid = jauther['id']
            if not jauther.__contains__('name'):
                return
            authorname = jauther['name']

            # createtime 必要字段
            posttime: str = None
            if not jnode.__contains__('created_time'):
                return
            sct = jnode['created_time']
            if not isinstance(sct, int):
                return
            posttime = helper_time.timespan_to_datestr(sct)

            # 构建comment
            comment: NetworkPost = NetworkPost(cid,
                                               self._SOURCE,
                                               authorid,
                                               isroot=False)
            comment.nickname = authorname
            comment.posttime = posttime
            comment.parentpostid = post_master.postid

            # 构建profile
            author: NetworkProfile = NetworkProfile(authorname, authorid,
                                                    self._SOURCE)

            # author profile_pic
            if jauther.__contains__('profile_picture_depth_0') and \
                jauther['profile_picture_depth_0'].__contains__('uri'):
                purl: str = jauther['profile_picture_depth_0']['uri']
                pic_data = self._ha.get_response_data(purl,
                                                      headers="""
                accept: image/webp,image/apng,image/*,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9,zh;q=0.8
                cache-control: no-cache
                pragma: no-cache
                referer: https://www.facebook.com/
                sec-fetch-mode: no-cors
                sec-fetch-site: cross-site
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"""
                                                      )
                if isinstance(pic_data, bytes) and len(pic_data) > 1:
                    author.set_profile_pic(pic_data)

            # author url
            if jauther.__contains__('url'):
                author.url = jauther['url']

            yield author  # 返回作者

            # posturl
            if jnode.__contains__('url'):
                comment.posturl = jnode['url']

            # 正文
            if jnode.__contains__('body') and \
                not jnode['body'] is None and \
                jnode['body'].__contains__('text'):
                comment.text = jnode['body']['text']

            # 评论附带的附件图片视频等
            jatt = jnode.get('attachments')
            atts = {}  # 用于去重
            if not jatt is None and len(jatt) > 0:
                for jat in jatt:
                    try:
                        if jat is None or len(jat) < 1:
                            continue
                        if not jat.__contains__('url'):
                            continue

                        rscurl, rsctype = self._get_attachments_type_and_url(
                            jat)

                        # 可能是一个外链网页，不是图片
                        # 但没法处理，只能下载下来
                        rscurl = jat['url']

                        m = self._re_rsc_name.search(rscurl)
                        rscname = None
                        if not m is None:
                            rscname = m.group(1).strip()
                        # vedio reduplicate
                        if atts.__contains__(rscname):
                            continue
                        else:
                            atts[rscname] = None

                        rsc = NetworkResource(task, 'zplus', rscurl,
                                              self._SOURCE, rsctype)
                        rsc.filename = rscname
                        rsc.resourceid = rscname
                        if rsc.filename.__contains__('.'):
                            rsc.extension = rsc.filename.split('.')[-1]
                        # rsc._resourcetype = rsctype

                        rsc.stream = self._ha.get_response_stream(rscurl,
                                                                  headers="""
                        accept: image/webp,image/apng,image/*,*/*;q=0.8
                        accept-encoding: gzip, deflate
                        accept-language: en-US,en;q=0.9,zh;q=0.8
                        cache-control: no-cache
                        pragma: no-cache
                        referer: https://www.facebook.com/
                        sec-fetch-mode: no-cors
                        sec-fetch-site: cross-site
                        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"""
                                                                  )

                        # 验证资源大小
                        if len(rsc.stream) < 50:
                            rsc.stream.close()
                            continue

                        comment.set_resource(rsc)
                        self._logger.info(
                            "Got image resource of [{}({})]: {}".format(
                                hostuser.nickname, hostuser._userid,
                                rsc.filename))
                        yield rsc

                    except Exception:
                        self._logger.debug(
                            "Parse fb post one comment attachment error:\nuserid={}\nusername={}\nerror:{}"
                            .format(hostuser._userid, hostuser.nickname,
                                    traceback.format_exc()))

            # 拿评论的 内部json段，其包含点赞数、评论的评论等
            jfeedback: dict = None
            if jnode.__contains__("feedback"):
                jfeedback = jnode['feedback']

            # 如果没拿到，就直接返回comment
            if jfeedback is None:
                yield comment
                return

            # 拿到了就继续拿额外信息

            # 点赞数
            if jfeedback.__contains__('top_reactions') and \
                jfeedback['top_reactions'].__contains__('edges'):
                jed_inner = jfeedback['top_reactions']['edges']
                if not jed_inner is None and len(jed_inner) > 0:
                    reaction_count = 0
                    for jed in jed_inner:
                        try:
                            if jed.__contains__('reaction_count'):
                                tmp = jed['reaction_count']
                                if isinstance(tmp, int):
                                    reaction_count += tmp
                        except Exception:
                            self._logger.debug(
                                "Parse fb post one comment like count error:\nuserid={}\nusername={}\nerror:{}"
                                .format(hostuser._userid, hostuser.nickname,
                                        traceback.format_exc()))
                    comment.likecount = reaction_count

            # 评论POST点赞的人员列表
            # 需要单独发请求获取

            # 回复数
            # if jfeedback.__contains__('comment_count') and \
            #     jfeedback['comment_count'].__contains__('total_count'):
            #     comment.replycount = jfeedback['comment_count']['total_count']
            if jfeedback.__contains__('display_comments') and \
                jfeedback['display_comments'].__contains__('count'):
                comment.replycount = jfeedback['display_comments']['count']

            yield comment

            # return  # 暂时不拿评论的评论，因为要docid，需要合并之前的facebook

            # 获取评论的评论，递归
            if comment.replycount <= 0:
                return

            # 这个要 docid，要合并一下之前的

            docid = self._get_more_comments_docid()
            if docid is None:
                return
            # 拿cursor
            if not jfeedback['display_comments'].__contains__('page_info'):
                return
            jpage = jfeedback['display_comments']['page_info']
            if not jpage.__contains__('has_next_page') or \
                    not jpage.__contains__('end_cursor'):
                return
            startcursor = jpage['start_cursor']
            if startcursor is None or startcursor == "":
                return
            endcursor = jpage['end_cursor']
            if endcursor is None or endcursor == "":
                return
            feedbackID = jfeedback['id']
            displayCommentsFeedbackContext = jvar['displayCommentsFeedbackContext']
            displayCommentsFeedbackContext = displayCommentsFeedbackContext.replace('\"', '\\"')
            feedbackSource = jvar['feedbackSource']
            has_next_page = True
            # 第一次after设为null，表示从第一条评论的评论开始拉取
            after = 'null'
            first = comment.replycount if comment.replycount <= 50 else 50
            while has_next_page:
                has_next_page = False
                url = 'https://www.facebook.com/api/graphql/'
                variables = '{' + f'"after":{after},"before":null,"displayCommentsFeedbackContext":"{displayCommentsFeedbackContext}","displayCommentsContextEnableComment":false,"displayCommentsContextIsAdPreview":false,"displayCommentsContextIsAggregatedShare":false,"displayCommentsContextIsStorySet":false,"feedLocation":"TIMELINE","feedbackID":"{feedbackID}","feedbackSource":{feedbackSource},"first":{first},"focusCommentID":null,"includeNestedComments":true,"isInitialFetch":false,"isComet":false,"containerIsFeedStory":true,"containerIsWorkplace":false,"containerIsLiveStory":false,"containerIsTahoe":false,"last":null,"scale":1,"topLevelViewOption":null,"useDefaultActor":true,"viewOption":null,"UFI2CommentsProvider_commentsKey":null' + '}'
                postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__hsi={self.hsi}&__comet_req=0&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=UFI2CommentsProviderPaginationQuery&variables=' + parse.quote(
                    variables) + f'&doc_id={docid}'
                html = self._ha.getstring(url, postdata,
                                          headers="""
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9,zh;q=0.8
                cache-control: no-cache
                content-length: {}
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                referer: {}
                sec-fetch-dest: empty
                sec-fetch-mode: cors
                sec-fetch-site: same-origin
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                """.format(len(postdata), hostuser.url))
                jreply_comment = json.loads(html)
                if not jreply_comment.__contains__('data') or \
                        not jreply_comment['data'].__contains__('feedback'):
                    return
                jfeedback = jreply_comment['data']['feedback']
                if not jfeedback.__contains__('display_comments') or \
                        not jfeedback['display_comments'].__contains__('edges'):
                    return
                edges = jfeedback['display_comments']['edges']
                if edges is None or len(edges) < 1:
                    return
                # 判断是否有下一页，并获取after和first参数
                if jfeedback['display_comments'].__contains__('page_info'):
                    jreply_page = jfeedback['display_comments']['page_info']
                    if jreply_page['has_next_page'] == 'true' or jreply_page['has_next_page'] == True:
                        has_next_page = True
                        after = '"' + jreply_page['end_cursor'] + '"'
                        after_count = jfeedback['display_comments']['after_count']
                        page_size = jfeedback['display_comments']['page_size']
                        first = after_count if after_count <= page_size else page_size
                for jedge in edges:
                    try:
                        for data in self._parse_reply_comment(task,
                                                            hostuser,
                                                            cid,
                                                            jedge,
                                                            reason,
                                                            existposts,
                                                            timerange=timerange):
                            yield data
                    except Exception:
                        self._logger.error(
                            "Parse fb post one comment error:\nuserid={}\nusername={}\nerror:{}"
                                .format(hostuser._userid, hostuser.nickname,
                                        traceback.format_exc()))

        except Exception:
            self._logger.error(
                "Parse fb post one comment error1:\nuserid={}\nusername={}\nerror:{}"
                .format(hostuser._userid, hostuser.nickname,
                        traceback.format_exc()))

    def _parse_reply_comment(self,
                           task: IscoutTask,
                           hostuser: NetworkProfile,
                           parentcommentid: str,
                           jedge: dict,
                           reason,
                           existposts: dict,
                           timerange: int = 30) -> iter:
        """parse reply comments"""
        try:
            if not isinstance(jedge, dict):
                return

            if not jedge.__contains__('node'):
                return

            jnode = jedge['node']
            if jnode is None:
                return

            # commentid
            cid: str = None
            if not jnode.__contains__('id'):
                return
            sid = jnode['id']
            if not isinstance(sid, str):
                return
            try:
                cid: str = helper_str.base64_decode(sid)
            except Exception:
                self._logger.error(
                    "Parse fb comment id error:\nuserid={}\nusername={}\nerror:{}"
                    .format(hostuser._userid, hostuser.nickname,
                            traceback.format_exc()))

            # author
            authorid: str = None
            authorname: str = None
            if not jnode.__contains__('author'):
                return
            jauther = jnode['author']
            if jauther is None:
                return
            if not jauther.__contains__("id"):
                return
            authorid = jauther['id']
            if not jauther.__contains__('name'):
                return
            authorname = jauther['name']

            # createtime 必要字段
            posttime: str = None
            if not jnode.__contains__('created_time'):
                return
            sct = jnode['created_time']
            if not isinstance(sct, int):
                return
            posttime = helper_time.timespan_to_datestr(sct)

            # 构建comment
            comment: NetworkPost = NetworkPost(cid,
                                               self._SOURCE,
                                               authorid,
                                               isroot=False)
            comment.nickname = authorname
            comment.posttime = posttime
            comment.parentpostid = parentcommentid

            # 构建profile
            author: NetworkProfile = NetworkProfile(authorname, authorid,
                                                    self._SOURCE)

            # author profile_pic
            if jauther.__contains__('profile_picture_depth_0') and \
                jauther['profile_picture_depth_0'].__contains__('uri'):
                purl: str = jauther['profile_picture_depth_0']['uri']
                pic_data = self._ha.get_response_data(purl,
                                                      headers="""
                accept: image/webp,image/apng,image/*,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9,zh;q=0.8
                cache-control: no-cache
                pragma: no-cache
                referer: https://www.facebook.com/
                sec-fetch-mode: no-cors
                sec-fetch-site: cross-site
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"""
                                                      )
                if isinstance(pic_data, bytes) and len(pic_data) > 1:
                    author.set_profile_pic(pic_data)

            # author url
            if jauther.__contains__('url'):
                author.url = jauther['url']

            yield author  # 返回作者

            # posturl
            if jnode.__contains__('url'):
                comment.posturl = jnode['url']

            # 正文
            if jnode.__contains__('body') and \
                not jnode['body'] is None and \
                jnode['body'].__contains__('text'):
                comment.text = jnode['body']['text']

            # 评论附带的附件图片视频等
            jatt = jnode.get('attachments')
            atts = {}  # 用于去重
            if not jatt is None and len(jatt) > 0:
                for jat in jatt:
                    try:
                        if jat is None or len(jat) < 1:
                            continue
                        if not jat.__contains__('url'):
                            continue

                        rscurl, rsctype = self._get_attachments_type_and_url(
                            jat)

                        # 可能是一个外链网页，不是图片
                        # 但没法处理，只能下载下来
                        rscurl = jat['url']

                        m = self._re_rsc_name.search(rscurl)
                        rscname = None
                        if not m is None:
                            rscname = m.group(1).strip()
                        # vedio reduplicate
                        if atts.__contains__(rscname):
                            continue
                        else:
                            atts[rscname] = None

                        rsc = NetworkResource(task, 'zplus', rscurl,
                                              self._SOURCE, rsctype)
                        rsc.filename = rscname
                        rsc.resourceid = rscname
                        if rsc.filename.__contains__('.'):
                            rsc.extension = rsc.filename.split('.')[-1]
                        # rsc._resourcetype = rsctype

                        rsc.stream = self._ha.get_response_stream(rscurl,
                                                                  headers="""
                        accept: image/webp,image/apng,image/*,*/*;q=0.8
                        accept-encoding: gzip, deflate
                        accept-language: en-US,en;q=0.9,zh;q=0.8
                        cache-control: no-cache
                        pragma: no-cache
                        referer: https://www.facebook.com/
                        sec-fetch-mode: no-cors
                        sec-fetch-site: cross-site
                        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36"""
                                                                  )

                        # 验证资源大小
                        if len(rsc.stream) < 50:
                            rsc.stream.close()
                            continue

                        comment.set_resource(rsc)
                        self._logger.info(
                            "Got image resource of [{}({})]: {}".format(
                                hostuser.nickname, hostuser._userid,
                                rsc.filename))
                        yield rsc

                    except Exception:
                        self._logger.debug(
                            "Parse fb post one comment attachment error:\nuserid={}\nusername={}\nerror:{}"
                            .format(hostuser._userid, hostuser.nickname,
                                    traceback.format_exc()))

            # 拿评论的 内部json段，其包含点赞数、评论的评论等
            jfeedback: dict = None
            if jnode.__contains__("feedback"):
                jfeedback = jnode['feedback']

            # 如果没拿到，就直接返回comment
            if jfeedback is None:
                yield comment
                return

            # 拿到了就继续拿额外信息

            # 点赞数
            if jfeedback.__contains__('top_reactions') and \
                jfeedback['top_reactions'].__contains__('edges'):
                jed_inner = jfeedback['top_reactions']['edges']
                if not jed_inner is None and len(jed_inner) > 0:
                    reaction_count = 0
                    for jed in jed_inner:
                        try:
                            if jed.__contains__('reaction_count'):
                                tmp = jed['reaction_count']
                                if isinstance(tmp, int):
                                    reaction_count += tmp
                        except Exception:
                            self._logger.debug(
                                "Parse fb post one comment like count error:\nuserid={}\nusername={}\nerror:{}"
                                .format(hostuser._userid, hostuser.nickname,
                                        traceback.format_exc()))
                    comment.likecount = reaction_count

            yield comment

        except Exception:
            self._logger.error(
                "Parse fb post one comment error1:\nuserid={}\nusername={}\nerror:{}"
                .format(hostuser._userid, hostuser.nickname,
                        traceback.format_exc()))

    def _get_attachments_type_and_url(self, jat: dict) -> (str, EResourceType):
        """从messenger消息json attachments 中解析附件url，并解析数据类型，
        返回(str, EResourceType)"""
        url: str = None
        rsctype: EResourceType = EResourceType.Other_Text

        if not isinstance(jat, dict) or not any(jat):
            return (url, None)
        try:

            if not jat.__contains__('url'):
                return (url, None)
            url = jat['url']

            if not jat.__contains__('media') or not jat['media'].__contains__(
                    '__typename'):
                return (url, None)
            rsctypestr = jat['media']['__typename']

            if rsctypestr == 'Sticker' or \
                rsctypestr =='MessageAnimatedImage' or \
                rsctypestr =='MessageImage':
                rsctype = EResourceType.Picture
            elif rsctypestr == 'MessageVideo' or \
                rsctypestr == 'MessageVideo':
                rsctype = EResourceType.Video
            elif rsctypestr == 'MessageFile':
                rsctype = EResourceType.Other_Text
            else:
                # GenericAttachmentMedia
                # ArticleContextActionLink
                rsctypestr = EResourceType.Url

        except Exception:
            self._logger.error("Get attachment url error: {}".format(
                traceback.format_exc()))
            url = None
        return (url, rsctype)


################################

    def _parse_post_(self,
                     task: IscoutTask,
                     hostuser: NetworkProfile,
                     strstory: str,
                     existposts: dict,
                     strstoryhtml: str = None,
                     timerange: int = 30) -> iter:
        """parse stories from str div\n
        param existposts: 已存在的POSTid列表，用于去重\n
        param strstory: POST的文本和图片部分html\n
        param strstoryhtml: jsmods部分，包含视频、评论等"""
        try:
            if not isinstance(existposts, dict):
                self._logger.error("Invalid existposts dict")
                return
            if strstory is None or strstory == "":
                return
            if not isinstance(timerange, int) or timerange < 1:
                return

            hdoc: etree._Element = None
            try:
                hdoc: etree._Element = etree.XML(strstory, etree.XMLParser())
            except Exception:
                hdoc = None
                self._logger.debug(
                    "Parse fb posts one story error1:\nuserid={}\nusername={}\nerror:{}"
                    .format(hostuser._userid, hostuser.nickname,
                            traceback.format_exc()))
            if hdoc is None:
                try:
                    hdoc = etree.XML(
                        strstory,
                        etree.XMLParser(recover=True, resolve_entities=False))
                except Exception:
                    hdoc = None
                    self._logger.debug(
                        "Parse fb posts one story error2:\nuserid={}\nusername={}\nerror:{}"
                        .format(hostuser._userid, hostuser.nickname,
                                traceback.format_exc()))

            if hdoc is None:
                self._logger.error(
                    "Parse fb posts one story failed:\nuserid={}\nusername={}".
                    format(hostuser._userid, hostuser.nickname))
                return

            # postid
            postid = hdoc.get('id')
            if postid is None or postid == "":
                return

            post: NetworkPost = NetworkPost(postid, self._SOURCE,
                                            hostuser._userid)

            # post time
            # 根据posttime时间范围过滤
            # 连续10个post不在时间范围则退出
            # %I:%M %p （%p是AM PM）
            m = self._re_posttime.search(strstory)
            if m is None:
                self._logger.info(
                    "Get posttime failed, user={}({}), postid: {}".format(
                        hostuser.nickname, hostuser._userid, postid))
                yield post
                return
            else:
                # strtime = m.group(1).strip()
                ts = m.group(2).strip()
                if not ts.isnumeric():
                    self._logger.info(
                        "Get posttime failed1, user={}({}), postid: {}".format(
                            hostuser.nickname, hostuser._userid, postid))
                    yield post
                    return
                else:
                    ts = int(ts)
                dt_now = datetime.datetime.utcnow()
                dt_post = datetime.datetime.utcfromtimestamp(ts)
                timedelta = dt_now - dt_post
                post.posttime_datetime = dt_post
                post.posttime = dt_post.strftime('%Y-%m-%d %H:%M:%S')
                if timedelta.days > timerange:
                    yield post
                    return

            # 已拿到过的post去重丢弃。
            if existposts.__contains__(postid):
                return
            else:
                existposts[postid] = None

            # text
            txt = ''
            for t in hdoc.itertext():
                t: str = t.strip()
                t = self._re_story_text_replace.sub(' ', t)
                if t == '':
                    continue
                txt += t + ' '

            # imags
            imgids = {}  #图片去重
            for ximg in hdoc.findall('.//img'):
                try:
                    # <img src=这个是头像图片也有的
                    # <img data-src=这个才是POST中的照片
                    srcurl = ximg.get('data-src')
                    if srcurl is None or srcurl == "":
                        srcurl = ximg.get('src')
                        if srcurl is None or srcurl == '':
                            continue

                    # img url
                    srcurl = parse.unquote(srcurl)
                    # 过滤p50x50的小图
                    if srcurl.__contains__('/p50x50/'):
                        continue
                    m = self._re_rsc_name.search(srcurl)
                    rscname = None
                    if not m is None:
                        rscname = m.group(1).strip()

                    rsc = NetworkResource(task, 'zplus', srcurl, 'facebook',
                                          EResourceType.Picture)
                    rsc.filename = rscname
                    rsc.resourceid = rscname
                    if rsc.filename.__contains__('.'):
                        rsc.extension = rsc.filename.split('.')[-1]

                    # image reduplicate
                    if imgids.__contains__(rscname):
                        continue
                    else:
                        imgids[rscname] = None

                    # alt
                    alt = ximg.get('alt')
                    if not alt is None and alt != "":
                        alt: str = alt.strip()
                        alt = self._re_story_text_replace.sub(' ', alt)
                        if alt == '':
                            continue
                        txt += alt + ' '
                    # stream
                    rsc.stream = self._ha.get_response_stream(srcurl,
                                                              headers='''
                    accept: image/png, image/svg+xml, image/*; q=0.8, */*; q=0.5
                    accept-encoding: gzip, deflate
                    accept-language: en-US,en;q=0.9
                    cache-control: no-cache
                    pragma: no-cache
                    referer: https://www.facebook.com
                    sec-fetch-mode: cors
                    sec-fetch-site: same-origin
                    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36
                    viewport-width: 1600''')

                    # 验证图片大小
                    if len(rsc.stream) < 20:
                        rsc.stream.close()
                        continue

                    post.set_resource(rsc)
                    self._logger.info(
                        "Got image resource of [{}({})]: {}".format(
                            hostuser.nickname, hostuser._userid, rsc.filename))
                    yield rsc

                except Exception:
                    self._logger.error(
                        "Get image resource error: {}({}) {}".format(
                            hostuser.nickname, hostuser._userid,
                            traceback.format_exc()))

            # get videos 这是当前POST中带的所有视频
            vedioids = {}  #视频去重
            if isinstance(strstoryhtml, str) and strstoryhtml != "":
                for mvideo in self._re_videos.finditer(strstoryhtml):
                    try:
                        if mvideo is None:
                            continue
                        urlvdo = mvideo.group(1).strip().replace(
                            '\\', '') + '&bytestart=0'
                        m = self._re_rsc_name.search(urlvdo)
                        rscname = None
                        if not m is None:
                            rscname = m.group(1).strip()
                        # vedio reduplicate
                        if vedioids.__contains__(rscname):
                            continue
                        else:
                            vedioids[rscname] = None

                        rsc = NetworkResource(task, 'zplus', urlvdo,
                                              'facebook', EResourceType.Video)
                        rsc.filename = rscname
                        rsc.resourceid = rscname
                        if rsc.filename.__contains__('.'):
                            rsc.extension = rsc.filename.split('.')[-1]
                        rsc._resourcetype = EResourceType.Video.value

                        rsc.stream = self._ha.get_response_stream(urlvdo,
                                                                  headers="""
                        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
                        accept-encoding: gzip, deflate, br
                        accept-language: en-US,en;q=0.9
                        cache-control: no-cache
                        pragma: no-cache
                        sec-fetch-mode: navigate
                        sec-fetch-site: none
                        sec-fetch-user: ?1
                        upgrade-insecure-requests: 1
                        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"""
                                                                  )
                        # 验证视频大小
                        if len(rsc.stream) < 100:
                            rsc.stream.close()
                            continue

                        post.set_resource(rsc)
                        self._logger.info(
                            "Got video resource of [{}({})]: {} {}kb".format(
                                hostuser.nickname, hostuser._userid,
                                rsc.filename, int(len(rsc.stream) / 1024)))
                        yield rsc
                    except Exception:
                        self._logger.error(
                            "Get video resource error: {}({}) {}".format(
                                hostuser.nickname, hostuser._userid,
                                traceback.format_exc()))

            # text放在这赋值是因为资源数据的标签中可能附带文本
            # 需要一起加上
            post.text = txt

            self._logger.info("Got post of [{}({})]: {}".format(
                hostuser.nickname, hostuser._userid, post._postid))
            yield post

            # comments
            jcontent = json.loads(strstoryhtml)
            if jcontent is None:
                return
            if not jcontent.__contains__('content') or not jcontent[
                    'content'].__contains__('payload') or not jcontent[
                        'content']['payload'].__contains__('jsmods'):
                return
            jsmods = jcontent['content']['payload']['jsmods']
            if not jsmods.__contains__('pre_display_requires'):
                return

            m = self._re_comments.search(strstoryhtml)
            if m is None:
                return

            jsobj = m.group(1)
            m = self._re_comments2.search(strstoryhtml)
            if m is None:
                return
            js = None
            try:
                js = helper_str.parse_js(jsobj)
            except Exception:
                self._logger.debug(
                    "Parse fb post one comments json error:\nuserid={}\nusername={}\nerror:{}"
                    .format(hostuser._userid, hostuser.nickname,
                            traceback.format_exc()))
            if js is None:
                return

            tmp = js['jsmods']['pre_display_requires']
            if tmp is None:
                return

        except Exception:
            self._logger.error(
                "Parse fb posts one story error:\nuserid={}\nusername={}\nerror:{}"
                .format(hostuser._userid, hostuser.nickname,
                        traceback.format_exc()))
