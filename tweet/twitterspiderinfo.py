"""
爬取twitter的信息
create by swm 2019/06/29
"""
from commonbaby.httpaccess.httpaccess import HttpAccess
from bs4 import BeautifulSoup
import re


class TwitterSpider(object):

    def __init__(self):
        self._ha = HttpAccess()
        cookie = '''
        personalization_id="v1_pmt2sntu/a8PCORtco8eVg=="; guest_id=v1%3A156194413511829253; ct0=6bb1b8031784f711388377a485cd5bf9; _ga=GA1.2.1901222848.1561944140; _gid=GA1.2.214369962.1561944140; ads_prefs="HBERAAA="; kdt=l6Dkc64O0CPl4qCVtYAuXjXrtxkII2VUjRNqMOfT; remember_checked_on=1; _twitter_sess=BAh7CiIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7ADoPY3JlYXRlZF9hdGwrCGsaIKtrAToMY3NyZl9p%250AZCIlNzIyZDlhODdlMTVjYjU3MTRkYTBlY2Y4NGQ5MDQzMjQ6B2lkIiVjZTgw%250ANDQ0ZmIyOTAyY2U0MjQ0NjI4ZTFmNjU0MjgwOToJdXNlcmwrCQHglUis2NwN--8ae08c231e9599f1c5868e6518664b987d936c79; twid="u=998911451833163777"; auth_token=3378bb7bfd90d8bfb9de00b7fb7110633a256852; csrf_same_site_set=1; lang=en; csrf_same_site=1; _gat=1
        '''
        self._ha._managedCookie.add_cookies('twitter.com', cookie)

    def get_first_page_info(self):
        """
        获取第一页的信息
        :return:
        """
        url = 'https://twitter.com/Google/followers'
        headers = '''
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9,en;q=0.8
cache-control: no-cache
pragma: no-cache
referer: https://twitter.com/login
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36
        '''
        restring = self._ha.getstring(url, headers=headers)
        # print(restring)
        soup = BeautifulSoup(restring, 'lxml')
        all_divs = soup.find_all('div', attrs={'class': 'user-actions btn-group not-following not-muting '})
        pass

    def search(self):
        url = "https://twitter.com/GEMoving"

        headers = '''
        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9,en;q=0.8
cache-control: no-cache
cookie: guest_id=v1%3A155921858819307425; _ga=GA1.2.999014813.1559218592; tfw_exp=0; kdt=0XTnTydp2g3vpbnSflAWv3kKb1zxBLeoftN3fQgd; remember_checked_on=0; csrf_same_site_set=1; csrf_same_site=1; personalization_id="v1_bHstwWEgjYsaq0IVqrj60Q=="; external_referer=padhuUp37zjgzgv1mFWxJ12Ozwit7owX|0|8e8t2xd8A2w%3D; ads_prefs="HBERAAA="; ct0=4fc617a6fb32b387a3d51da28a37910f; _gid=GA1.2.84942800.1562234004; twid="u=998911451833163777"; auth_token=f75059e44a60f7e68d723ded8571c6938c50c23b; _twitter_sess=BAh7CiIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7ADoPY3JlYXRlZF9hdGwrCKsZZ7xrAToMY3NyZl9p%250AZCIlNjAzZjE0NTU0ZjM1NWZlNjZhMmU1YWIyZDEzMzUxOTg6B2lkIiUxODU2%250AZWRhNWM0NjNhNzAyODM3YjJiMTFkNjlmOGY3NzoJdXNlcmwrCQHglUis2NwN--ba48cd0cf7d091fda283e2eb1f9e75fb2d4cd73c; lang=en; _gat=1
pragma: no-cache
referer: https://twitter.com/search?q=%E9%82%93%E7%B4%AB%E6%A3%8B&src=typd
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36
        '''
        restring = self._ha.getstring(url, headers=headers)
        soup = BeautifulSoup(restring, 'lxml')
        all_divs = soup.find_all('div', attrs={'class': 'user-actions btn-group not-following not-muting '})
        pass





if __name__ == '__main__':
    t = TwitterSpider()
    # t.get_first_page_info()
    t.search()