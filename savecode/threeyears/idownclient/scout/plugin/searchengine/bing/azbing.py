"""
使用微软云服务的Api去爬取bing的信息
create by judy
2019/11/14
"""
import requests
from idownclient.config_spiders import bingapikey


class AzBingApi(object):

    @classmethod
    def bing_web_search(cls, query: str, offset: int, count=10):
        """
        query是查询的语句
        offset是用于翻页的参数，设置的默认一页为10条数据，所以第一页是0，第二页就是10，以此类推
        返回的是一个字典，里面包含了url和其他的一些信息
        :param count:
        :param query:
        :param offset:
        :return:
        """
        subscription_key = bingapikey.get('key')
        if subscription_key is None or subscription_key == '':
            raise Exception("Error Azure key.")

        search_url = "https://api.cognitive.microsoft.com/bing/v7.0/search"

        headers = {"Ocp-Apim-Subscription-Key": subscription_key}
        params = {"q": query, 'count': count, 'offset': offset, "textDecorations": True, "textFormat": "HTML"}
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        webpages = search_results.get('webPages', {})
        values = webpages.get('value', [])
        for value in values:
            yield value

# 返回的数据类似于
# {
#     "id": "https://api.cognitive.microsoft.com/api/v7/#WebPages.0",
#     "name": "冰动娱乐",
#     "url": "http://www.playcool.com/sub3.shtml",
#     "isFamilyFriendly": true,
#     "displayUrl": "www.playcool.com/sub3.shtml",
#     "snippet": "《海战世界》是由冰动娱乐集结数十名来自德、美等国拥有军工背景的资深战争游戏研发人员，以及300余名来自《中途岛之战》《荣誉勋章：太平洋战役》《猎杀潜航》系列经典海战单机游戏的原班人马，历时4年打造的一款大型tps二战纪实海战网游。",
#     "dateLastCrawled": "2019-11-05T03:52:00.0000000Z",
#     "language": "zh_chs",
#     "isNavigational": false
# }
