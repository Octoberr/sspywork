"""
直接获取推文的方法失效了
而使用webdriver会被验证是否为机器人，而且也不太好拿取框架
https://mobile.twitter.com/realDonaldTrump
"""
from datetime import datetime
import requests
import time
from bs4 import BeautifulSoup

home_url = 'https://mobile.twitter.com/'
ha = requests.session()

userid = 'realDonaldTrump'

headers1 = {
    'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    'accept-encoding': "gzip, deflate, br",
    'accept-language': "en-US,en;q=0.9,en;q=0.8",
    'cache-control': "no-cache,no-cache",
    'content-length': "0",
    'content-type': "application/x-www-form-urlencoded",
    'origin': "https://mobile.twitter.com",
    'pragma': "no-cache",
    'referer': f"https://mobile.twitter.com/{userid}?p=s",
    'sec-fetch-mode': "navigate",
    'sec-fetch-site': "same-origin",
    'sec-fetch-user': "?1",
    'upgrade-insecure-requests': "1",
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
}
ha.headers.update(headers1)
nojs_url = f'https://mobile.twitter.com/i/nojs_router?path=%2F{userid}%3Fp%3Ds'
ha.post(nojs_url)
# 这里暂停的原因是等待它自己跳转
time.sleep(3)

actual_url = home_url + userid
res = ha.get(actual_url)
html = res.text
soup = BeautifulSoup(html, 'lxml')
# 这一页的tweets
tweet_tables = soup.find_all('table', attrs={'class': 'tweet'})
for tweet in tweet_tables:
    all_trs = tweet.find_all('tr')
    # 就选最后一个去详情页那数据，只能拿少量的数据，这个如果最后报错了再选一个attr里面没有值的
    tr = all_trs[-1]
    if len(tr.attrs) > 0:
        continue
    td = tr.find('td')
    if td is None: continue
    a = td.find('a')
    if a is None: continue
    href = a.attrs.get('href')
    detail_url = home_url.strip('/') + href

    ####################################################
    # 去拿信息
    tweet_res = ha.get('https://mobile.twitter.com/IvankaTrump/status/1309276267926224897?p=v')
    tweet_html = tweet_res.text
    tweet_soup = BeautifulSoup(tweet_html, 'lxml')
    tweet_table = tweet_soup.find('table', attrs={'class': 'main-tweet'})
    if tweet_table is None: continue
    tweet_trs = tweet_table.find_all('tr')
    tweet_tr = tweet_trs[1]

    text_div = tweet_tr.find('div', attrs={'class': 'tweet-text'})
    tweet_id = text_div.attrs.get('data-id')

    tweet_text = text_div.text.strip()

    complete_url_a = text_div.find('a', attrs={'class': 'twitter_external_link dir-ltr tco-link'})
    url_text = complete_url_a.text
    complete_url = complete_url_a.attrs.get('title')

    a = tweet_text.replace(url_text, complete_url)

    print(a)

    time_div = tweet_tr.find('div', attrs={'class': 'metadata'})

    s_time_str = time_div.find('a').text
    des = datetime.strptime(s_time_str, '%I:%M %p - %d %b %Y')
    des_str = des.strftime('%Y-%m-%d %H:%M:%S')

    auto_div = tweet_tr.find('div', attrs={'class': 'media'})
    if auto_div is not None:
        imgs = auto_div.find_all('img')
        for img in imgs:
            imgsrc = img.attrs.get('src')

print("yes")
