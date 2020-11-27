"""
google搜索重新开发或者是
googlesearch使用代理
"""

import requests
from urllib.parse import quote_plus, urlparse, parse_qs

url_home = "https://www.google.%(tld)s/"
# 搜索当前关键字
url_search = "https://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&" \
             "btnG=Google+Search&tbs=%(tbs)s&safe=%(safe)s&tbm=%(tpe)s&" \
             "cr=%(country)s"

# 搜索下一页
url_next_page = "https://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&" \
                "start=%(start)d&tbs=%(tbs)s&safe=%(safe)s&tbm=%(tpe)s&" \
                "cr=%(country)s"

url_search_num = "https://www.google.%(tld)s/search?hl=%(lang)s&q=%(query)s&" \
                 "num=%(num)d&btnG=Google+Search&tbs=%(tbs)s&safe=%(safe)s&" \
                 "tbm=%(tpe)s&cr=%(country)s"
url_next_page_num = "https://www.google.%(tld)s/search?hl=%(lang)s&" \
                    "q=%(query)s&num=%(num)d&start=%(start)d&tbs=%(tbs)s&" \
                    "safe=%(safe)s&tbm=%(tpe)s&cr=%(country)s"
url_parameters = ('hl', 'q', 'num', 'btnG', 'start', 'tbs', 'safe', 'tbm', 'cr')

burl = 'https://www.google.com/'

sa = requests.Session()

headers = {
  'accept': ' text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
  'accept-encoding': ' gzip, deflate, br',
  'accept-language': ' en-US,en;q=0.9',
  'cache-control': ' no-cache',
  'pragma': ' no-cache',
  'sec-fetch-dest': ' document',
  'sec-fetch-mode': ' navigate',
  'sec-fetch-site': ' none',
  'sec-fetch-user': ' ?1',
  'upgrade-insecure-requests': ' 1',
  'user-agent': ' Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
}

res = sa.get(burl)
print(res.text)