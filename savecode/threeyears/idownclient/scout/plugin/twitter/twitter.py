"""
twitter的信息搜索
目前twitter还有搜索接口可以使用
所以不需要登录能拿大部分的信息
create by judy 2019/08/19
正常现代版twitter已经无法拿到东西 这种方式已经弃用
走selenium也无法将数据拿全，因为twitter本身对每个ip有流量限制和机器人验证
就导致爬取难度变得很难
但是呢我们常说说再光鲜亮丽的东西背后的东西都是一团糟，再强大的人内心也有脆弱的地方，换种方式就发现迎刃而解了
update by judy 2020/09/15
"""
import json

import requests
from bs4 import BeautifulSoup

from datacontract.iscoutdataset import IscoutTask
from ....clientdatafeedback.scoutdatafeedback import NetworkProfile


class Twitter(object):
    def __init__(self, task: IscoutTask):
        self.task = task
        self.source = 'twitter'
        # https://twitter.com/search?f=users&vertical=default&q=jaychou&src=typd
        self.basic_url = 'https://twitter.com/search'
        self.ha = requests.session()
        # 初始化一些header和cookie
        self.ha.get(self.basic_url)
        # 要去个人网站拿点东西, https://twitter.com/JayChouUpdates
        self.twitter_url = 'https://twitter.com/'

    def __get_details(self, name, signature):
        """
        获取tweet的一些详细信息，需要根据名字进入页面
        :param name:
        :param signature:
        :return:
        """
        details = {}
        details['signature'] = signature
        try:
            url = self.twitter_url + name
            res = requests.get(url)
            html = res.text
            soup = BeautifulSoup(html, 'lxml')
            loc_div = soup.find('div',
                                attrs={'class': 'ProfileHeaderCard-location'})
            if loc_div is not None:
                loc_text = loc_div.text.replace('\n', '').strip()
                details['location'] = loc_text

            link_div = soup.find('div',
                                 attrs={'class': 'ProfileHeaderCard-url'})
            if link_div is not None:
                link_text_a = link_div.find('a')
                if link_text_a is not None:
                    link_text = link_text_a.attrs.get('title')
                    details['home_page_link'] = link_text

            all_ul = soup.find('ul', attrs={'class': 'ProfileNav-list'})
            if all_ul is not None:
                tweet_li = all_ul.find(
                    'li', attrs={'class': 'ProfileNav-item--tweets'})
                if tweet_li is not None:
                    tweet_a = tweet_li.find('a')
                    if tweet_a is not None:
                        tweet = tweet_a.attrs.get('title')
                        details['tweet'] = tweet

                following_li = all_ul.find(
                    'li', attrs={'class': 'ProfileNav-item--following'})
                if following_li is not None:
                    following_a = following_li.find('a')
                    if following_a is not None:
                        following = following_a.attrs.get('title')
                        details['following'] = following

                follower_li = all_ul.find(
                    'li', attrs={'class': 'ProfileNav-item--followers'})
                if follower_li is not None:
                    follower_a = follower_li.find('a')
                    if follower_a is not None:
                        follower = follower_a.attrs.get('title')
                        details['follower'] = follower

                likes_li = all_ul.find(
                    'li', attrs={'class': 'ProfileNav-item--favorites'})
                if likes_li is not None:
                    likes_a = likes_li.find('a')
                    if likes_a is not None:
                        likes = likes_a.attrs.get('title')
                        details['likes'] = likes
        except Exception as ex:
            print(f"Get {name} twitter info error, err:{ex}")
        finally:
            details_str = json.dumps(details, ensure_ascii=False)
        return details_str

    def __parse_profile(self, html: str, level) -> list:
        """
        解析用户信息
        :param html:
        :return:
        """
        soup = BeautifulSoup(html, 'lxml')
        alldiv = soup.find('div',
                           attrs={'class': 'GridTimeline-items has-items'})
        if alldiv is None:
            print("Nothing get on twitter")
        # 不去拿下一页了，因为本身是关联搜索，后面再看吧，原本没登陆信息就拿不完
        # min_position = alldiv.attrs.get('data-min-position')
        all_info_divs = alldiv.find_all(
            'div', attrs={'class': 'ProfileCard js-actionable-user'})
        if len(all_info_divs) == 0:
            print("Find nobady on twitter")
        for div in all_info_divs:
            try:
                name = div.attrs.get('data-screen-name')
                unid = div.attrs.get('data-user-id')
                p_div = div.find('p')
                if p_div is not None:
                    p_text = p_div.text
                else:
                    p_text = None
                # profile = NetworIdkProfile(self.task, level, name, unid,
                #                            self.source)
                profile = NetworkProfile(name, unid, self.source)
                detail = self.__get_details(name, p_text)
                profile.details = detail
                yield profile
            except Exception as err:
                print(f"Twitter get profile error, err:{err}")
                continue

    def get_profile(self, level, mail_account):
        """
        根据邮箱去查询networkid,有可能不是邮箱账号
        但是肯定会给一个关键字
        :param level:
        :param mail_account:
        :return:
        """
        key_word: str = mail_account
        # 处理下邮箱账号
        if '@' in key_word:
            key_word = key_word[:key_word.index('@')]
        # 拿首页
        url = f'{self.basic_url}?f=users&vertical=default&q={key_word}&src=typd'
        response = self.ha.get(url)
        host_res = response.text
        for p_inf in self.__parse_profile(host_res, level):
            yield p_inf
