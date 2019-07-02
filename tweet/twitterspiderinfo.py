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
        url = "https://twitter.com/search?f=users&q=porn&src=typd"

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
        soup = BeautifulSoup(restring, 'lxml')
        all_divs = soup.find_all('div', attrs={'class': 'user-actions btn-group not-following not-muting '})
        pass



if __name__ == '__main__':
    t = TwitterSpider()
    # t.get_first_page_info()
    t.search()