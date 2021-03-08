"""facebook search userid"""

# -*- coding:utf-8 -*-

import html as ht
import re
import time
import traceback
from urllib import parse
from datetime import datetime
import pytz
import json

from bs4 import BeautifulSoup
from commonbaby.helpers import helper_str, helper_time
from lxml import etree

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import NetworkProfile
from .fblogin import FBLogin

# 两次人员搜索之间的间隔时间（秒），搜太快会被 temporarily blocked.
search_interval: float = 2  # 秒
last_search_timestamp: int = -1  # 本地时间戳


def _check_interval(func):
    """检查两次搜索之间的间隔时间\n
    两次人员搜索之间的间隔时间（秒），搜太快会被 temporarily blocked."""
    def do_func(*args, **kwargs):
        currtimestamp = datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
        global last_search_timestamp
        while currtimestamp - last_search_timestamp < search_interval:
            time.sleep(0.1)

        last_search_timestamp = currtimestamp
        return func(*args, **kwargs)

    return do_func


class FBProfile_new(FBLogin):
    """facebook search userid"""

    def __init__(self, task: IscoutTask):
        super(FBProfile_new, self).__init__(task)

####################################
# ensure user

    def _get_user_by_userid_v1(self,
                               userid: str,
                               reason: str = None,
                               get_profile_pic: bool = True,
                               recursive: int = 0) -> NetworkProfile:
        """ensure a user by userid\n
        param recursive: 内部参数，不用管"""
        try:
            url: str = "https://www.facebook.com/profile.php?id={}".format(
                userid)
            return self._get_user_by_url_v1(url,
                                            reason,
                                            get_profile_pic,
                                            recursive=recursive)

        except Exception:
            self._logger.error("Get user by userid error: {}".format(
                traceback.format_exc()))

    def _get_user_by_url_v1(self,
                            userurl: str,
                            reason: str = None,
                            get_profile_pic: bool = False,
                            recursive: int = 0) -> NetworkProfile:
        """ensure the user by user url\n
        param recursive: 内部参数，不用管"""
        res: NetworkProfile = None
        try:
            html, redir = self._ha.getstring_unredirect(userurl,
                                                        headers="""
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9
            cache-control: no-cache
            content-type: application/x-www-form-urlencoded
            origin: https://www.facebook.com
            pragma: no-cache
            referer: https://www.facebook.com/search/people/?q={}&epa=SERP_TAB
            sec-fetch-mode: cors
            sec-fetch-site: same-origin
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36"""
                                                        )

            if not redir is None and not redir == "":
                html = self._ha.getstring(redir,
                                          headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9
                cache-control: no-cache
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                pragma: no-cache
                referer: https://www.facebook.com/search/people/?q={}&epa=SERP_TAB
                sec-fetch-mode: cors
                sec-fetch-site: same-origin
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36"""
                                          )
                userurl = redir

            if html is None:
                self._logger.error(
                    "Access user homepage failed: {}".format(userurl))
                return res

            if html.__contains__("You’re Temporarily Blocked"):
                # 被暂时屏蔽了，就递归等待，每次等10秒
                # 等待2分钟（120秒）还没好就放弃，返回None
                # 后面需要搞账号池来解决此问题？
                if recursive >= 12:
                    self._logger.info(
                        "Search too fast, You’re Temporarily Blocked over 120s, give up."
                    )
                    return None
                self._logger.info(
                    "Search too fast, You’re Temporarily Blocked, sleep 10s")
                time.sleep(10)
                recursive += 1
                res = self._get_user_by_url_v1(userurl,
                                               reason=reason,
                                               get_profile_pic=get_profile_pic,
                                               recursive=recursive)
                return res

            # {"viewerID":"100054477585089","userVanity":"","userID":"100006113837332"}
            userid: str = None
            succ, userid = helper_str.substringif(html, '"userID":"', '"')
            if not succ:
                self._logger.error("Match userid failed: {}".format(userurl))

            # <title>Kavishka D Wijesooriya</title>
            username: str = None
            succ, username = helper_str.substringif(html, '<title>', '</title>')
            if not succ:
                self._logger.error("Match username failed: {}".format(userurl))
                return res

            res = NetworkProfile(username, userid, self._SOURCE)
            res.url = userurl
            if not reason is None:
                res.reason = reason
            else:
                res.reason = self._dtools.landing_facebook

            # profile photo
            # "profilePicNormal":{"uri":"*******"},
            if get_profile_pic:
                succ, pic_url = helper_str.substringif(html, '"profilePicNormal":{"uri":"', '"}')
                if not succ:
                    self._logger.error("Get profile pic failed: {}".format(userurl))
                    return res
                try:
                    pic_url = pic_url.replace('\\', '')
                    pic = self._ha.get_response_stream(pic_url)
                    res._profile_pic = helper_str.base64bytes(pic.read())
                except:
                    pass
        except Exception:
            self._logger.error("Get user by url error: {}".format(
                traceback.format_exc()))
        return res

####################################
# get profile detail

    @_check_interval
    def _get_profile_detail_userid_v1(self,
                                      userid: str,
                                      reason: str = None,
                                      recursive: int = 0,
                                      get_profile_pic: bool = False
                                      ) -> NetworkProfile:
        """get user profile detail.\n
        param recursive: 内部参数，不用管"""
        try:
            url: str = "https://www.facebook.com/profile.php?id={}".format(
                userid)
            return self._get_profile_detail_userurl_v1(
                url,
                reason,
                recursive=recursive,
                get_profile_pic=get_profile_pic)

        except Exception:
            self._logger.error("Get profile detail by userid error: {}".format(
                traceback.format_exc()))

    @_check_interval
    def _get_profile_detail_userurl_v1(self,
                                       userurl: str,
                                       reason: str = None,
                                       recursive: int = 0,
                                       get_profile_pic: bool = False
                                       ) -> NetworkProfile:
        """get user profile detail.\n
        param recursive: 内部参数，不用管"""
        res: NetworkProfile = None
        try:

            res = self._get_user_by_url_v1(userurl,
                                           reason,
                                           get_profile_pic=get_profile_pic,
                                           recursive=recursive)
            if not isinstance(res, NetworkProfile):
                return res

            res = self._get_profile_detail_v1(res, reason, recursive=recursive)

            self._logger.info("Got user profile detail: {} {}".format(
                res.nickname, res.url))

        except Exception:
            self._logger.error(
                "Get profile detail of user: {} failed: {}".format(
                    userurl, traceback.format_exc()))
        return res

    @_check_interval
    def _get_profile_detail_v1(self,
                               profile: NetworkProfile,
                               reason: str = None,
                               recursive: int = 0) -> NetworkProfile:
        """get user profile detail.\n
        param recursive: 内部参数，不用管"""
        try:
            if not isinstance(profile, NetworkProfile):
                self._logger.error(
                    "Invalid NetworkProfile for getting profile detail.")
                return None

            docid_dict = self._get_docid_dict()
            if docid_dict == {} or docid_dict is None:
                self._logger.error("Get docid failed")
                return None

            params: dict = self._get_profile_params_v1(profile, docid_dict)
            self._get_profile_about_v1(profile, params, docid_dict)

            self._logger.info("Got user profile detail: {} {}".format(
                profile.nickname, profile.url))

        except Exception:
            self._logger.error(
                "Get profile detail of user: {} failed: {}".format(
                    profile.url, traceback.format_exc()))
        return profile

    def _get_profile_params_v1(self, profile: NetworkProfile,
                               docid_dict: dict) -> dict:
        """
        先通过navigation获取工作与学历的参数,之后其他的参数可以直接在graphql里面全部取到
        return:
           params: {'collectionToken':[], rawSectionToken: str, sectionToken: str}
        """
        try:
            # build route_url
            path = profile.url[len('https://www.facebook.com'):]
            # 统一去掉结尾/,方便处理
            if path.endswith('/'):
                path = path[:-1]
            # https://www.facebook.com/profile.php?id=100006113837332&sk=about_work_and_education
            if profile.url.startswith('https://www.facebook.com/profile.php?id='):
                route_url = path + '&sk=about_work_and_education'
            # https://www.facebook.com/JollyGreenGiant33/about_work_and_education
            else:
                route_url = path + '/about_work_and_education'

            # 先请求navigation
            params = {}
            url = 'https://www.facebook.com/ajax/navigation/'
            postdata = f'client_previous_actor_id={self._userid}&route_url={parse.quote_plus(route_url)}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}'
            html = self._ha.getstring(url, postdata,
                                      headers="""
                        accept: */*
                        accept-encoding: gzip, deflate
                        accept-language: en-US,en;q=0.9
                        content-type: application/x-www-form-urlencoded
                        origin: https://www.facebook.com
                        sec-fetch-dest: empty
                        sec-fetch-mode: cors
                        sec-fetch-site: same-origin
                        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36
                        """)
            # for (;;);{.....}
            res = json.loads(html[html.index('{'):])
            props = res['payload']['payload']['result']['exports']['rootView']['props']
            collection_token = props['collectionToken']
            params['rawSectionToken'] = props['rawSectionToken']
            params['sectionToken'] = props['sectionToken']
            # 等会请求graphql的时候再添加
            params['collectionToken'] = []

            # 请求graphql
            url = 'https://www.facebook.com/api/graphql/'
            variables = '{' + f'"appSectionFeedKey":"ProfileCometAppSectionFeed_timeline_nav_app_sections__{params["rawSectionToken"]}","collectionToken":"{collection_token}","rawSectionToken":"{params["rawSectionToken"]}","scale":1,"sectionToken":"{params["sectionToken"]}","userID":"{profile._userid}"' + '}'
            postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=ProfileCometAboutAppSectionQuery&variables=' + parse.quote(
                variables) + f'&doc_id={docid_dict["ProfileCometAboutAppSectionQuery"]}'
            html = self._ha.getstring(url, postdata,
                                      headers="""
                                    accept: */*
                                    accept-encoding: gzip, deflate
                                    accept-language: en-US,en;q=0.9,zh;q=0.8
                                    content-length: {}
                                    content-type: application/x-www-form-urlencoded
                                    origin: https://www.facebook.com
                                    sec-fetch-dest: empty
                                    sec-fetch-mode: cors
                                    sec-fetch-site: same-origin
                                    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                                    """.format(len(postdata)))
            resp_infos = html.splitlines()
            for info in resp_infos:
                json_info = json.loads(info)
                if not 'label' in json_info:
                    nodes: list = json_info['data']['user']['about_app_sections']['nodes']
                    nodes = nodes[0]['all_collections']['nodes']
                    for node in nodes:
                        # 概览的资料都能从其他请求拿到，不需要
                        if node['name'] != '概览' and node['name'] != '生活纪事':
                            params['collectionToken'].append(node['id'])
            return params
        except Exception:
            self._logger.error(
                "Get profile detail params of user: {} failed: {}".format(
                    profile.url, traceback.format_exc()))

    def _get_profile_about_v1(self, profile: NetworkProfile,
                              params: dict,
                              docid_dict: dict):
        """取得用户简介中的全部资料"""
        try:
            for collection_token in params['collectionToken']:
                url = 'https://www.facebook.com/api/graphql/'
                variables = '{' + f'"appSectionFeedKey":"ProfileCometAppSectionFeed_timeline_nav_app_sections__{params["rawSectionToken"]}","collectionToken":"{collection_token}","rawSectionToken":"{params["rawSectionToken"]}","scale":1,"sectionToken":"{params["sectionToken"]}","userID":"{profile._userid}"' + '}'
                postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=ProfileCometAboutAppSectionQuery&variables=' + parse.quote(
                    variables) + f'&doc_id={docid_dict["ProfileCometAboutAppSectionQuery"]}'
                html = self._ha.getstring(url, postdata,
                                          headers="""
                            accept: */*
                            accept-encoding: gzip, deflate
                            accept-language: en-US,en;q=0.9,zh;q=0.8
                            content-length: {}
                            content-type: application/x-www-form-urlencoded
                            origin: https://www.facebook.com
                            sec-fetch-dest: empty
                            sec-fetch-mode: cors
                            sec-fetch-site: same-origin
                            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                            """.format(len(postdata)))
                resp_infos = html.splitlines()
                detail = {}
                for info in resp_infos:
                    json_info = json.loads(info)
                    if not 'label' in json_info:
                        continue
                    elif json_info['label'] == 'ProfileCometAboutAppSectionQuery$defer$ProfileCometAboutAppSectionContent_appSection':
                        nodes: list = json_info['data']['activeCollections']['nodes']
                        profile_field_sections: list = nodes[0]['style_renderer']['profile_field_sections']
                        for field in profile_field_sections:
                            # 一级标题：工作，大学，居住地，基本信息等
                            first_title = field['title']['text']
                            nodes = field['profile_fields']['nodes']
                            # 这些一级标题下的资料有单独分类eg：居住地下有家乡、所在地、城市，以子分类为detail的key
                            if first_title in ['居住地', '联系方式', '网站和社交链接', '基本信息', '家庭成员', '其他名字']:
                                for node in nodes:
                                    if not 'list_item_groups' in node or node['list_item_groups'] == []:
                                        continue
                                    if not 'list_items' in node['list_item_groups'][0] or \
                                            node['list_item_groups'][0]['list_items'] == []:
                                        continue
                                    # 子分类
                                    second_title = node['list_item_groups'][0]['list_items'][0]['text']['text']
                                    content = node['title']['text']
                                    detail[second_title] = content
                                    # 看下有没有url链接,link_url为空的话就在ranges里面找
                                    ranges = node['title']['ranges']
                                    link_url = node['link_url']
                                    if not link_url is None:
                                        detail[second_title + '_url'] = link_url
                                    else:
                                        for rg in ranges:
                                            if 'entity' in rg and 'url' in rg['entity']:
                                                if not rg['entity']['url'] is None:
                                                    detail[second_title + '_url'] = rg['entity']['url']
                            # 直接以一级标题为key
                            else:
                                # 初始化一个序号，因为同一个标题下可能有多条内容：eg：大学，工作
                                idx = 0
                                for node in nodes:
                                    if 'field' in node['renderer'] and 'text_content' in node['renderer']['field']:
                                        if not node['renderer']['field']['text_content'] is None:
                                            content = node['renderer']['field']['text_content']['text']
                                        else:
                                            content = node['renderer']['field']['title']['text']
                                    else:
                                        content = node['title']['text']
                                    detail[first_title + str(idx)] = content
                                    # 看下有没有url链接
                                    ranges = node['title']['ranges']
                                    link_url = node['link_url']
                                    if not link_url is None:
                                        detail[first_title + str(idx) + '_url'] = link_url
                                    else:
                                        for rg in ranges:
                                            if 'entity' in rg and 'url' in rg['entity']:
                                                if not rg['entity']['url'] is None:
                                                    detail[first_title + str(idx) + '_url'] = rg['entity']['url']
                                    idx += 1
                if len(detail) > 0:
                    profile.set_details(**detail)
        except Exception:
            self._logger.error(
                "Get profile about failed: username:{} url:{}\nerror: {}".
                    format(profile._networkid, profile.url,
                           traceback.format_exc()))
