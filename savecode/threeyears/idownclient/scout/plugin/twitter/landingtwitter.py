"""
landding twetter
获取twitter的用户信息
create by judy 20200915
"""
from datetime import datetime
from commonbaby import proxy
from idownclient.scout.plugin import twitter
import json
import re
import time
import traceback
from urllib.parse import quote_plus


import requests
from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import HttpAccess

from datacontract import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import NetworkProfile
from .twitterbase import TwitterBase


class LandingTwitter(TwitterBase):
    def __init__(self, task: IscoutTask):
        TwitterBase.__init__(self, task)
        self._home_url = "https://mobile.twitter.com/"
        # 做一下限制，following和follower都只拿1000条
        self.count = 0
        # 测试使用200个
        self.count_limit = 200

    def __get_avater(self, img_src):
        """
        将个人头像的图片base64
        :param img_src:
        :return:
        """
        res = None
        try:
            res = requests.get(img_src, proxies=self.proxydict)
            b_data = res.content
            return b_data
            # str_data = helper_str.base64bytes(b_data)
            # return '?utf-8?b?' + str_data
        except:
            self._logger.error(f"Download avater error,er:{traceback.format_exc()}")
        return res

    def get_following(self, userid, ha: requests.session(), keyword):
        """
        旧版插件已经失效，新版插件目前来看还拿不到following by judy 20201130
        """
        pass

    def get_follower(self, userid, ha: requests.session(), keyword):
        """
        旧版插件已经失效，新版插件目前来看还拿不到 follower by judy 20201130
        """
        pass

    def get_user_info(self, userid: str, keyword, type=None) -> NetworkProfile:
        """
        这里根据twitter唯一的screen-name去拿信息
        这里不仅会拿当前用户的基本信息，也会去拿搜索到用户的信息
        马上就要没有这个方法了 by judy 20201130
        这个方法修改为获取指定userid的信息
        :param userid:
        :param keyword: 这个主要作用是封装profile
        :return:
        """
        profile = None
        try:
            sa = requests.Session()
            sa.proxies = self.proxydict
            search_url = "https://twitter.com/search"
            headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "zh-CN,zh;q=0.9",
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36""",',
            }
            search_response = sa.get(search_url, headers=headers, timeout=10)
            html1 = search_response.text
            gt = substring(html1, 'decodeURIComponent("gt=', ";")
            userurl = f"https://api.twitter.com/graphql/esn6mjj-y68fNAj45x5IYA/UserByScreenName?variables=%7B%22screen_name%22%3A%22{userid}%22%2C%22withHighlightedLabel%22%3Atrue%7D"
            headers1 = {
                "accept": "*/*",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "zh-CN,zh;q=0.9",
                "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
                "cache-control": "no-cache",
                "content-type": "application/json",
                "origin": "https://twitter.com",
                "pragma": "no-cache",
                "referer": "https://twitter.com/",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36",
                "x-guest-token": f"{gt}",
                "x-twitter-active-user": "yes",
                "x-twitter-client-language": "zh-cn",
            }
            response = sa.get(userurl, headers=headers1, timeout=10)
            if response is None or response.status_code != 200:
                return
            jtext = response.text
            sj = json.loads(jtext)
            user = sj["data"]["user"]["legacy"]
            if not isinstance(user, dict) or user.__len__() == 0:
                self._logger.info(f"Landing twitter with {keyword}, but got nothing")
                return
            userid = user.get("screen_name")
            if userid is None:
                return
            profile = NetworkProfile(keyword, userid, self.source)
            # 头像，https和http
            profile_image_url_https = user.get("profile_image_url_https")
            # profile_image_url = user.get('profile_image_url')
            if profile_image_url_https is not None and profile_image_url_https != "":
                ar = self.__get_avater(profile_image_url_https)
                if ar is not None:
                    profile.set_profile_pic(ar)
                    self._logger.info(
                        f"Get a img src:{profile_image_url_https}, userid:{userid}"
                    )
            # 昵称
            name = user.get("name")
            self._logger.info(f"Get a nick name:{name}, userid:{userid}")
            profile.nickname = name
            # 地理位置，这个就不一定有了
            location = user.get("location")
            if location is not None and location != "":
                self._logger.info(f"Get a loc info:{location}, userid:{userid}")
                profile.address = location
            # 个性签名，这个也可能会没有
            description = user.get("description")
            if description is not None and description != "":
                self._logger.info(f"Get a signature:{description}, userid:{userid}")
                profile.set_details(description=description)
            # 拿推文数，关注者数和被关注者数,这个也是可能没有，所以这些东西放detail里
            followers_count = user.get("followers_count")
            if isinstance(followers_count, int):
                profile.set_details(followers=followers_count)
            friends_count = user.get("friends_count")
            if isinstance(friends_count, int):
                profile.set_details(following=friends_count)
            # 拿一个加入twitter的时间
            created_at = user.get("created_at")
            if created_at is not None and created_at != "":
                time_datetime = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                datestr = time_datetime.strftime("%Y-%m-%d %H:%M:%S")
                profile.set_details(created_at=datestr)
        except:
            self._logger.error(f"Landing twitter error\nerr:{traceback.format_exc()}")
        return profile

    def landing_userid(self, level, userid, reason=None):
        """
        给指定的userid，然后去拿这个指定userid的信息
        修改为新版获取指定userid的方法
        :param level:
        :param userid:
        :param reason:
        :return:
        """
        p_info: NetworkProfile = self.get_user_info(userid, userid)
        if p_info is not None:
            p_info.reason = reason
            return p_info

    def __landing_profile(self, keyword, reason, idxstart=0, idxstop=10):
        """
        新版twitter可以直接获取到搜索的profile
        但是同样的也没法多拿
        create by judy 20201130
        """
        sa = requests.Session()
        sa.proxies = self.proxydict
        search_url = "https://twitter.com/search"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36""",',
        }
        search_response = sa.get(search_url, headers=headers, timeout=10)
        html1 = search_response.text
        gt = substring(html1, 'decodeURIComponent("gt=', ";")
        url = f"https://api.twitter.com/2/search/adaptive.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&include_can_media_tag=1&skip_status=1&cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_quote_count=true&include_reply_count=1&tweet_mode=extended&include_entities=true&include_user_entities=true&include_ext_media_color=true&include_ext_media_availability=true&send_error_codes=true&simple_quoted_tweet=true&q={quote_plus(keyword)}&vertical=default&result_filter=user&count=20&query_source=typd&pc=1&spelling_corrections=1&ext=mediaStats%2ChighlightedLabel"
        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9",
            "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "cache-control": "no-cache",
            "origin": "https://twitter.com",
            "pragma": "no-cache",
            "referer": "https://twitter.com/search?f=users&vertical=default&q=%E6%9D%8E%E5%AD%90%E6%9F%92&src=typd",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36",
            "x-guest-token": f"{gt}",
            "x-twitter-active-user": "yes",
            "x-twitter-client-language": "zh-cn",
        }
        response = sa.get(url, headers=headers, timeout=10)
        if response is None or response.status_code != 200:
            return
        jtext = response.text
        sj = json.loads(jtext)
        users = sj["globalObjects"]["users"]
        if not isinstance(users, dict) or users.__len__() == 0:
            self._logger.info(f"Landing twitter with {keyword}, but got nothing")
            return
        for key, value in users.items():
            if idxstart >= idxstop:
                break
            try:
                uinfo: dict = value
                if not isinstance(uinfo, dict) or uinfo.__len__() == 0:
                    continue
                # 接下来就是获取user的信息
                userid = uinfo.get("screen_name")
                # 主页链接，add by judy 20201212
                url = f"https://twitter.com/{userid}"
                if userid is None:
                    continue
                profile = NetworkProfile(keyword, userid, self.source)
                profile.url = url
                profile.reason = reason
                # 头像，https和http
                profile_image_url_https = uinfo.get("profile_image_url_https")
                # profile_image_url = uinfo.get('profile_image_url')
                if (
                    profile_image_url_https is not None
                    and profile_image_url_https != ""
                ):
                    ar = self.__get_avater(profile_image_url_https)
                    if ar is not None:
                        profile.set_profile_pic(ar)
                        self._logger.info(
                            f"Get a img src:{profile_image_url_https}, userid:{userid}"
                        )
                # 昵称
                name = uinfo.get("name")
                self._logger.info(f"Get a nick name:{name}, userid:{userid}")
                profile.nickname = name
                # 地理位置，这个就不一定有了
                location = uinfo.get("location")
                if location is not None and location != "":
                    self._logger.info(f"Get a loc info:{location}, userid:{userid}")
                    profile.address = location
                # 个性签名，这个也可能会没有
                description = uinfo.get("description")
                if description is not None and description != "":
                    self._logger.info(f"Get a signature:{description}, userid:{userid}")
                    profile.set_details(description=description)
                # 拿推文数，关注者数和被关注者数,这个也是可能没有，所以这些东西放detail里
                followers_count = uinfo.get("followers_count")
                if isinstance(followers_count, int):
                    profile.set_details(followers=followers_count)
                friends_count = uinfo.get("friends_count")
                if isinstance(friends_count, int):
                    profile.set_details(following=friends_count)
                # 拿一个加入twitter的时间
                created_at = uinfo.get("created_at")
                if created_at is not None and created_at != "":
                    time_datetime = datetime.strptime(
                        created_at, "%a %b %d %H:%M:%S %z %Y"
                    )
                    datestr = time_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    profile.set_details(created_at=datestr)
                yield profile
                idxstart += 1
            except:
                self._logger.error(
                    f"Parser twitter info error\nerr:{traceback.format_exc()}"
                )
                continue

    def landing(self, level, email, reason=None, idxstart=0, idxstop=10):
        """
        这个接口是给外部的，落地账号详情主要是拿用户信息，
        业务逻辑设计的接口是这样，
        但是这样将简单的事情变复杂了吧
        主要返回的数据是profile
        :param level:
        :param email:
        :param reason:
        :return:
        """
        # 先把email的@去掉，然后使用前缀去搜索
        keyword = email
        if "@" in email:
            keyword = email.split("@")[0]
        self._logger.info(f"Landing twitter keyword:{keyword}")
        for l_data in self.__landing_profile(
            keyword, reason, idxstart=idxstart, idxstop=idxstop
        ):
            yield l_data

    def landing_url(self, level, url, reason=None):
        """
        给指定的url，然后去拿这个指定的url的信息,
        twitter和其他landing不一样需要特定的userid去拿信息
        :param level:
        :param url:
        :param reason:
        :return:
        """
        re_userid = re.compile("https://twitter.com/(.+)")
        re_res = re_userid.search(url)
        if re_res:
            userid = re_res.group(1)
            p_info: NetworkProfile = self.get_user_info(userid, url)
            if p_info is not None:
                p_info.reason = reason
                return p_info
