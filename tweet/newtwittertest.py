"""
这里主要是拿推文的一些信息
create by swm 2019/11/06
"""
import requests
from bs4 import BeautifulSoup
import re

_header = {'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}

sa = requests.session()
burl = 'https://twitter.com/'
# 加载首页的cookie
sa.get(burl)
sa.headers.update(_header)
home_page = f'https://twitter.com/Pornhub'

res = sa.get(home_page)
html = res.text
soup = BeautifulSoup(html, 'lxml')


tweet_div = soup.find('div', attrs={'class': 'stream-container'})

all_lis = tweet_div.find_all('li', attrs={'class': 'js-stream-item'})

foot_div = {'回复':0,'转推':0, '喜欢':0}

for li in all_lis:
    # 拿评论点赞赞的div
    # foot_div = li.find('div', attrs={'class': 'ProfileTweet-actionList'})
    # a = foot_div.text.strip().replace('\n', '')
    # h = re.search('回复(\d+)', a)
    # if h:
    #     print(h.group(1))
    #
    # z = re.search('转推(\d+)', a)
    # if z:
    #     print(z.group(1))
    # x = re.search('喜欢(\d+)', a)
    # if x:
    #     print(x.group(1))
    foot_div = li.find('div', attrs={'class': 'stream-item-footer'})
    reply_div = foot_div.find('div', attrs={'class': 'ProfileTweet-action--reply'})
    if reply_div is not None:
        reply_num = reply_div.text
        print(reply_num)
    favorite_div = foot_div.find('div', attrs={'class': 'ProfileTweet-action--favorite'})
    if favorite_div is not None:
        favorite_num = favorite_div.text
        print(favorite_num)

    break
