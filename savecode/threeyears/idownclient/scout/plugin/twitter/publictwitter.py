"""
land和public是分开的
create by judy 2020/09/15
"""
import json
import time
from time import sleep
import traceback
from datetime import datetime
from commonbaby.countrycodes import NO

import requests
from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring

from datacontract import IscoutTask

# 引用networkid的数据结构
from idownclient.clientdatafeedback.scoutdatafeedback import NetworkPost, EResourceType
from .twitterbase import TwitterBase


class PublicTwitter(TwitterBase):
    def __init__(self, task: IscoutTask):
        TwitterBase.__init__(self, task)

    def parse_twitter(self, userid, tweet_dict: dict):
        """
        新版本的twitter爬虫拿到的是json数据，所以直接解析json就可以了
        modify by judy 20201204
        """
        for key, value in tweet_dict.items():
            try:
                tweet_id = key
                twitter = NetworkPost(tweet_id, self.source, userid)
                self._logger.info(f"Parse tweets info, get a tweet, tweetid:{tweet_id}")
                # 完整的twitter文字
                full_text = value.get("full_text")
                twitter.text = full_text
                # 时间
                created_at = value.get("created_at")
                if created_at is not None or created_at != "":
                    time_datetime = datetime.strptime(
                        created_at, "%a %b %d %H:%M:%S %z %Y"
                    )
                    datestr = time_datetime.strftime("%Y-%m-%d %H:%M:%S")
                    twitter.posttime = datestr
                # 回复数
                reply_count = value.get("reply_count")
                twitter.replycount = reply_count
                # 点赞数
                favorite_count = value.get("favorite_count")
                twitter.likecount = favorite_count
                # 拿媒体信息，没有就算了
                media_info = value.get("extended_entities", {}).get("media")
                if isinstance(media_info, list) and len(media_info) != 0:
                    for media in media_info:
                        url = media.get("url")
                        twitter.posturl = url
                        media_type = media.get("type")
                        if media_type == "photo":
                            mtype = EResourceType.Picture
                            mextension = "jpg"
                            # 下载地址
                            media_url = media.get("media_url_https")
                            # media_url = media.get('media_url_http')
                        elif media_type == "video":
                            # 先把图片下载下来
                            mtype = EResourceType.Picture
                            mextension = "jpg"
                            # 下载地址
                            media_url = media.get("media_url_https")
                            # self._logger.info(
                            #     f"Tweet has a media, type:{vextension}, url:{vmedia_url}, tweetid:{tweet_id}"
                            # )
                            # vtype = EResourceType.Picture
                            # vextension = "jpg"
                            # # 下载地址
                            # vmedia_url = media.get("media_url_https")
                            # self._logger.info(
                            #     f"Tweet has a media, type:{vextension}, url:{vmedia_url}, tweetid:{tweet_id}"
                            # )
                            # v_media_data = self._get_network_resource(
                            #     vmedia_url, vtype, extension=vextension
                            # )
                            # if v_media_data is not None:
                            #     twitter.set_resource(v_media_data)
                            #     # 资源文件也得回去
                            #     self._logger.info(
                            #         f"Get tweet media success, type:{vextension}, url:{vmedia_url}, tweetid:{tweet_id}"
                            #     )
                            #     yield v_media_data
                            # mtype = EResourceType.Video
                            # video_info = media.get("video_info")
                            # variants = video_info.get("variants")
                            # if not isinstance(variants, list) or len(variants) == 0:
                            #     self._logger.error("Cannot get video info")
                            #     continue
                            # media_url = variants[0].get("url")
                            # mextension = "mp4"
                        else:
                            self._logger.error(
                                "Unknown resource type, please contact developer add"
                            )
                            mtype = EResourceType.Other_Text
                            mextension = "jpg"
                            # 下载地址
                            media_url = media.get("media_url_https")
                        self._logger.info(
                            f"Tweet has a media, type:{mextension}, url:{media_url}, tweetid:{tweet_id}"
                        )
                        media_data = self._get_network_resource(
                            media_url, mtype, extension=mextension
                        )
                        if media_data is not None:
                            twitter.set_resource(media_data)
                            # 资源文件也得回去
                            self._logger.info(
                                f"Get tweet media success, type:{mextension}, url:{media_url}, tweetid:{tweet_id}"
                            )
                            yield media_data
                yield twitter
            except:
                self._logger.error(
                    f"Parse tweet error\ntweet:{value}\nerror:{traceback.format_exc()}"
                )

    def get_twitter(self, userid, reason=None) -> iter:
        """
        public twitter入口
        先将一些basic url和headers准备好
        修改为新版的twitter by judy 20201204
        """
        sa = requests.Session()
        sa.proxies = self.proxydict
        search_url = "https://twitter.com/search"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate",
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
            "accept-encoding": "gzip, deflate",
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
        user = sj["data"]["user"]
        rest_id = user.get("rest_id")
        if rest_id is None or rest_id == "":
            self._logger.info(f"Cant get userid by {userid}, please check the username")
            return
        tweeturl = f"https://api.twitter.com/2/timeline/media/{rest_id}.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&include_can_media_tag=1&skip_status=1&cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_quote_count=true&include_reply_count=1&tweet_mode=extended&include_entities=true&include_user_entities=true&include_ext_media_color=true&include_ext_media_availability=true&send_error_codes=true&simple_quoted_tweet=true&count=20&ext=mediaStats%2ChighlightedLabel"
        tweet_response = sa.get(url=tweeturl, headers=headers1)
        if tweet_response is None or tweet_response.status_code != 200:
            return
        tweet_res = tweet_response.text
        tweet_dict = json.loads(tweet_res)
        tweets: dict = tweet_dict.get("globalObjects").get("tweets")
        if tweets is None or tweets.__len__() == 0:
            return
        self._logger.info(f"Get tweet info, start to parse, userid:{userid}")
        for tweet in self.parse_twitter(userid, tweets):
            yield tweet

    def public(self, userid: str, reason=None):
        """
        这里分开的逻辑是使用landing的个人数据去拿那个人公开的twittter信息
        是，确实是，我知道这个需求奇葩，到现在都还没有想明白为啥要这样
        先把这个接口做了吧
        这个主要返回的是post和resource
        2019/10/16现在逻辑修改后就合理许多了
        拿特定的userid去拿指定的twitter
        :param userid:
        :param reason:
        :return:
        """
        for data in self.get_twitter(userid, reason):
            yield data
