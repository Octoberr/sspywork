"""
nojs的twitter即将不支持
所以需要开发web版的twitter
"""
import json
import requests
from commonbaby.helpers.helper_str import substring
from urllib.parse import quote_plus


class Twitter(object):

    luminati_proxy_dict = {
        "http": "http://lum-customer-hl_d08f7ef9-zone-static:cyg5pnh9hnlw@zproxy.lum-superproxy.io:22225",
        "https": "http://lum-customer-hl_d08f7ef9-zone-static:cyg5pnh9hnlw@zproxy.lum-superproxy.io:22225",
    }

    def __init__(self) -> None:
        pass

    def get_search_ids(self, key_word):
        """
        获取搜索的id
        """
        sa = requests.Session()
        sa.proxies = self.luminati_proxy_dict
        search_url = "https://twitter.com/search"
        url1 = f"{search_url}?f=users&vertical=default&q={key_word}&src=typd"
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
        search_response = sa.get(search_url, headers=headers)
        html1 = search_response.text
        gt = substring(html1, 'decodeURIComponent("gt=', ";")
        url = f"https://api.twitter.com/2/search/adaptive.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&include_can_media_tag=1&skip_status=1&cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_quote_count=true&include_reply_count=1&tweet_mode=extended&include_entities=true&include_user_entities=true&include_ext_media_color=true&include_ext_media_availability=true&send_error_codes=true&simple_quoted_tweet=true&q={quote_plus(key_word)}&vertical=default&result_filter=user&count=20&query_source=typd&pc=1&spelling_corrections=1&ext=mediaStats%2ChighlightedLabel"
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
        response = sa.get(url, headers=headers)
        if response is None or response.status_code != 200:
            return
        jtext = response.text
        sj = json.loads(jtext)
        users = sj["globalObjects"]["users"]
        if not users:
            self._logger.info("Search nothing in twitter!")
            return None
        for key, value in sj["globalObjects"]["users"].items():
            data = value["screen_name"]
            print(data)

    def search_user_by_id(self, screen_name):
        sa = requests.Session()
        sa.proxies = self.luminati_proxy_dict
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
        search_response = sa.get(search_url, headers=headers)
        html1 = search_response.text
        gt = substring(html1, 'decodeURIComponent("gt=', ";")
        # userurl = f"https://api.twitter.com/graphql/esn6mjj-y68fNAj45x5IYA/UserByScreenName?variables=%7B%22{screen_name}%22%3A%22joebiden%22%2C%22withHighlightedLabel%22%3Atrue%7D"
        userurl = f"https://api.twitter.com/graphql/esn6mjj-y68fNAj45x5IYA/UserByScreenName?variables=%7B%22screen_name%22%3A%22{screen_name}%22%2C%22withHighlightedLabel%22%3Atrue%7D"
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
        response = sa.get(userurl, headers=headers1)
        text = response.text
        print(text)

    def get_tweet(self, screenname):
        """
        拿推文
        根据screen_name先拿userid然后根据userid去拿tweet
        """
        sa = requests.Session()
        sa.proxies = self.luminati_proxy_dict
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
        search_response = sa.get(search_url, headers=headers)
        html1 = search_response.text
        gt = substring(html1, 'decodeURIComponent("gt=', ";")
        userurl = f"https://api.twitter.com/graphql/esn6mjj-y68fNAj45x5IYA/UserByScreenName?variables=%7B%22screen_name%22%3A%22{screenname}%22%2C%22withHighlightedLabel%22%3Atrue%7D"
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
        response = sa.get(userurl, headers=headers1)
        if response is None or response.status_code != 200:
            return
        jtext = response.text
        sj = json.loads(jtext)
        user = sj["data"]["user"]
        userid = user.get("rest_id")
        if userid is None or userid == "":
            print(f"Cant get userid by {screenname}, please check the username")
        tweeturl = f"https://api.twitter.com/2/timeline/media/{userid}.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&include_can_media_tag=1&skip_status=1&cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_quote_count=true&include_reply_count=1&tweet_mode=extended&include_entities=true&include_user_entities=true&include_ext_media_color=true&include_ext_media_availability=true&send_error_codes=true&simple_quoted_tweet=true&count=20&ext=mediaStats%2ChighlightedLabel"
        tweet_res = sa.get(url=tweeturl, headers=headers1)
        print(tweet_res.status_code)
        print(tweet_res.text)

    def get_complete_tweet(self):
        """
        一个人发的连续的tweet，测试版，看能不能多获取
        """
        sa = requests.Session()
        sa.proxies = self.luminati_proxy_dict
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
        search_response = sa.get(search_url, headers=headers)
        html1 = search_response.text
        gt = substring(html1, 'decodeURIComponent("gt=', ";")

        url = "https://twitter.com/i/api/2/timeline/profile/939091.json?include_profile_interstitial_type=1&include_blocking=1&include_blocked_by=1&include_followed_by=1&include_want_retweets=1&include_mute_edge=1&include_can_dm=1&include_can_media_tag=1&skip_status=1&cards_platform=Web-12&include_cards=1&include_ext_alt_text=true&include_quote_count=true&include_reply_count=1&tweet_mode=extended&include_entities=true&include_user_entities=true&include_ext_media_color=true&include_ext_media_availability=true&send_error_codes=true&simple_quoted_tweet=true&include_tweet_replies=false&count=50&userId=939091&ext=mediaStats%2ChighlightedLabel"

        headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9",
            "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "referer": "https://twitter.com/JoeBiden",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36",
            "x-guest-token": f"{gt}",
            "x-twitter-active-user": "yes",
            "x-twitter-client-language": "zh-cn",
        }

        response = sa.get(url, headers=headers)

        print(response.text)


if __name__ == "__main__":
    tw = Twitter()
    # tw.get_search_ids("trump")
    # tw.search_user_by_id("realdonaldtrump")
    # tw.get_tweet("JoeBiden")
    tw.get_complete_tweet()
