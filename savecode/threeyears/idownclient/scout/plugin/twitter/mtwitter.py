"""
现代版的twitter不登录根本拿不到信息
但是能禁用js后会发现神奇的东西
create by judy 2019/09/11
目前来看通过正常手段去拿tweet的方式已经失效，所以尝试使用禁用js后的tweet
by judy 2020/09/11
"""
import datetime
import json
import re
import time
import traceback

import pytz

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from commonbaby.httpaccess.httpaccess import HttpAccess
from commonbaby.helpers.helper_str import substring

from datacontract import IscoutTask
# 引用networkid的数据结构
from idownclient.clientdatafeedback.scoutdatafeedback import NetworkProfile, NetworkPost, \
    NetworkResource, EResourceType
from ..scoutplugbase import ScoutPlugBase


class MTwitter(ScoutPlugBase):

    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        # 中文header
        self._header = {'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}

        self._home_url = 'https://mobile.twitter.com/'
        # 这个session是为了保证整个会话的cookie不会改变，确保能拿到数据
        # self._ha = requests.session()
        # self._ha.headers.update(self._header)
        # 而且需要先去访问下首页将基础的header拿到
        # self._ha.get(self._home_url)

        # 匹配纯数字，类似于点赞数，转发数喜欢数
        self._re_num = re.compile('\d+')




        # 爬取推文的当前变量作用域
        self.has_next = False

    def __prc_time(self, source_time) -> int:
        """
        解析时间，三种格式
        7h
        sep 8
        5 sep 17
        返回的时间精确到年 月 日就行了
        -----------------------------改了
        :param source_time:
        :return:
        """
        if source_time is None or source_time == '':
            raise Exception('Tweet time cant be None')

        time_stamp = int(source_time)
        return time_stamp



    def __parse_a_twitter_li(self, li: BeautifulSoup, userid):
        """
        这个方法就只拿来解析推文的html
        这里用来获取用户的推文信息
        :param li:
        :param userid: 用来构建post
        :return:
        """
        try:
            tweet_id = li.attrs.get('data-item-id')
            # id为空表示的是这条tweet没有的，不知道为啥会混在这里面
            if tweet_id is None:
                return
            self._logger.info(f"Get a twitter:{tweet_id}")
            twitter = NetworkPost(tweet_id, self.source, userid)
            # twitter的头是必不可能为空的，那TM为空了我就没法了，玩个锤子
            # SB为空了
            # 不怪你，你没有看见那个
            tweet_div: BeautifulSoup = li.find('div', attrs={'class': 'stream-item-header'})
            # 这个也是必不可能为空的
            if tweet_div is None:
                return
            s_time_div = tweet_div.find('span', attrs={'class': '_timestamp'})
            # 没法这个divTMD为空了我能怎么办
            if s_time_div is None:
                return
            s_time = s_time_div.attrs.get('data-time')
            time_int = self.__prc_time(s_time)
            if self.time_now - time_int > self.time_limit:
                self._logger.info(f"The Tweet exceeds the time limit, unix time:{time_int}")
                self.has_next = False
                return

            # 时间赋值
            twitter.posttime = datetime.datetime.fromtimestamp(time_int).strftime('%Y-%m-%d %H:%M:%S')

            # 拿推文,这个可能会为空，因为有些twitter可能没有文字描述
            text_div = li.find('div', attrs={'class': 'js-tweet-text-container'})
            if text_div is not None:
                p_div = text_div.find('p')
                p_text = p_div.text.strip().replace('…', '')
                # 推文内容赋值
                twitter.text = p_text
            # 下载资源文件，先去拿资源文件的div这样万一没有拿到东西也没有事
            # 这个东西是可能为空的，既然这东西可能为空你TM还直接去拿，傻了？
            auto_div: BeautifulSoup = li.find('div', attrs={'class': 'AdaptiveMediaOuterContainer'})
            # 目前分析的是video的下载地址不对，无法获取下来，所以现在尽量把图片全拿下来
            if auto_div is not None:
                imgs = auto_div.find_all('img')
                # 去拿twitter的图片
                for img in imgs:
                    imgsrc = img.attrs.get('src')
                    r_data = self.__get_network_resource(imgsrc)
                    if r_data is not None:
                        twitter.set_resource(r_data)
                        yield r_data

            # 然后去拿最后的东西，什么点赞数啊，转发数呀
            foot_div = li.find('div', attrs={'class': 'stream-item-footer'})
            if foot_div is not None:
                # 回复数,可能会为空，表示没有回复数
                reply_div = foot_div.find('div', attrs={'class': 'ProfileTweet-action--reply'})
                if reply_div is not None:
                    reply_num = reply_div.text
                    r_num = self._re_num.search(reply_num)
                    if r_num:
                        repnum = r_num.group()
                        twitter.replycount = repnum
                # 转发数 转发数现在没有用，但是留着吧，万一呢
                # forward_div = foot_div.find('div', attrs={'class': 'ProfileTweet-action--retweet'})
                # if forward_div is not None:
                #     forward_num = forward_div.text
                #     f_num = self._re_num.search(forward_num)
                #     if f_num:
                #         fwnum = f_num.group()
                # 点赞数
                favorite_div = foot_div.find('div', attrs={'class': 'ProfileTweet-action--favorite'})
                if favorite_div is not None:
                    favorite_num = favorite_div.text
                    fav_num = self._re_num.search(favorite_num)
                    if fav_num:
                        favnum = fav_num.group()
                        twitter.likecount = favnum
            yield twitter
        except:
            # 这里只用来解析一条tweet，如果解析出错不要了就不要了
            self._logger.error(f"Parse twitter error, err:{traceback.format_exc()}")

    def get_twitter(self, userid: str, reason):
        """
        这里是去拿取指定用户的推文
        会根据command里面的时间条件限制来
        默认是今年一个月内的
        目前是先去实现功能
        :param userid:
        :param reason:
        :return:
        """
        # userid = userid
        self._logger.info(f"Start get user twitter, userid:{userid}")
        # 去twitter现在的首页那
        sa = requests.session()
        burl = 'https://twitter.com/'
        # 加载首页的cookie
        sa.get(burl)
        sa.headers.update(self._header)
        self.has_next = True
        home_page = f'{burl}{userid}'

        res = sa.get(home_page)
        html = res.text
        soup = BeautifulSoup(html, 'lxml')
        # 这个tweet也是可能没有的，有些新账号或者是没有发过twitter的账号就没有数据
        # 忘了是不是要带后面的空格
        # tweet_div = soup.find('div', attrs={'class': 'stream-container  '})
        tweet_div = soup.find('div', attrs={'class': 'stream-container'})
        if tweet_div is None:
            self._logger.info(f"Get nothing of twitter,userid:{userid}, url:{home_page}")
            return
        self._logger.info(f"Get tweet,userid:{userid}")
        # 这里先去把下一页找到,max是当前位置，min是下一页的位置
        min_position = tweet_div.attrs.get('data-min-position')
        if min_position is not None:
            self.has_next = True
            next_page = f'https://twitter.com/i/profiles/show/{userid}/timeline/tweets?include_available_features=1&' \
                        f'include_entities=1&max_position={min_position}&reset_error_state=false'
        # 然后下面才是去解析twitter,无论是首页还是，使用接口返回的数据都是在li里面提取
        # 拿取twitter的动态有时间限制，所以可能会提前结束
        all_li = tweet_div.find_all('li', attrs={'class': 'js-stream-item'})
        # 双循环==，最不想看见的东西
        # 这里拿首页的推文，全部去取一下，除了置顶的tweet，剩下都是按照时间顺序来的
        # 所以这个可以决定是否需要去拿下一页，也不用决定几个超过时间限制就不拿了
        for li in all_li:
            for data in self.__parse_a_twitter_li(li, userid):
                yield data
        # 能拿到继续走, 可以这样写， has_next不一定拿得到
        while self.has_next:
            try:
                res = sa.get(next_page)
                res_dict = json.loads(res.text)
                # 先拿下一页
                has_next = res_dict.get('has_more_items')
                if has_next:
                    res_min = res_dict.get('min_position')
                    # 这两个东西相同可能表示已经拿到最后一页了
                    if res_min == min_position:
                        self.has_next = False
                        break
                    min_position = res_min
                    next_page = f'https://twitter.com/i/profiles/show/{userid}/timeline/tweets?include_available_features=1&' \
                                f'include_entities=1&max_position={min_position}&reset_error_state=false'
                html = res_dict.get('items_html')
                soup = BeautifulSoup(html, 'lxml')
                all_li = soup.find_all('li')
                for li in all_li:
                    for data in self.__parse_a_twitter_li(li, userid):
                        yield data
                    if not self.has_next:
                        break
            except:
                # 先尝试这样处理吧，后面出错次数多了再跳出循环
                self._logger.error(f"Get next twitter page error, err:{traceback}, url:{next_page}")
                break
            finally:
                time.sleep(1)






            # return img_src


# if __name__ == '__main__':
#     mt = MTwitter()
# mt.get_user_info('JayChouUpdates') ok
# mt.get_twitter('JayChouUpdates') ok
# mt.search_user('jaychou') ok
# mt.get_following('JayChouUpdates') ok
# mt.get_follower('JayChouUpdates') ok
