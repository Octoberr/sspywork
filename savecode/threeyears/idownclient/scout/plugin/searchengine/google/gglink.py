"""
使用google搜索关键字
返回搜索的url
因为不使用代理直接搜索会被封ip
所以就需要使用代理
by judy 20200930
"""
import time
import traceback
from bs4 import BeautifulSoup

import requests
import os
import random
from urllib.parse import quote_plus, urlparse, parse_qs
from commonbaby.mslog import MsLogger, MsLogManager
from proxymanagement.proxymngr import ProxyMngr


class GGlink(object):
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
    USER_AGENT = 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0)'

    try:
        install_folder = os.path.abspath(os.path.split(__file__)[0])
        try:
            user_agents_file = os.path.join(install_folder, 'user_agents.txt.gz')
            import gzip
            fp = gzip.open(user_agents_file, 'rb')
            try:
                user_agents_list = [_.strip() for _ in fp.readlines()]
            finally:
                fp.close()
                del fp
        except Exception:
            user_agents_file = os.path.join(install_folder, 'user_agents.txt')
            with open(user_agents_file) as fp:
                user_agents_list = [_.strip() for _ in fp.readlines()]
    except Exception:
        user_agents_list = [USER_AGENT]

    _logger: MsLogger = MsLogManager.get_logger("GGlink")

    @classmethod
    def get_random_user_agent(cls):
        """
        Get a random user agent string.

        :rtype: str
        :return: Random user agent string.
        """
        useragent_b = random.choice(cls.user_agents_list)
        if isinstance(useragent_b, bytes):
            useragent = useragent_b.decode('utf-8')
        else:
            useragent = useragent_b
        return useragent

    @classmethod
    def get_page(cls, url, sa: requests.Session, proxydict=None):
        """
        Request the given URL and return the response page, using the cookie jar.

        :param str url: URL to retrieve.
        :param str sa: User agent for the HTTP requests.
            Use None for the default.

        :rtype: str
        :return: Web page retrieved for the given URL.

        :raises IOError: An exception is raised on error.
        :raises urllib2.URLError: An exception is raised on error.
        :raises urllib2.HTTPError: An exception is raised on error.
        """
        html = None
        try:
            response = sa.get(url, proxies=proxydict, timeout=10)
            html = response.text
        except:
            cls._logger.error(f"Get {url} error\n{traceback.format_exc()}")
        return html

    @classmethod
    def filter_result(cls, link):
        try:
            # Decode hidden URLs.
            if link.startswith('/url?'):
                o = urlparse(link, 'http')
                link = parse_qs(o.query)['q'][0]

            # Valid results are absolute URLs not pointing to a Google domain,
            # like images.google.com or googleusercontent.com for example.
            # TODO this could be improved!
            o = urlparse(link, 'http')
            if o.netloc and 'google' not in o.netloc:
                return link

        # On error, return None.
        except Exception:
            pass

    @classmethod
    def search(cls, query, tld='com', lang='en', tbs='0', safe='off', num=10, start=0,
               stop=None, domains=None, pause=2.0, tpe='', country='',
               extra_params=None, user_agent=None, proxydict: dict = None):
        """
        自己编写的google搜索程序采用代理
        """
        if not isinstance(proxydict, dict):
            proxydict = ProxyMngr.get_static_proxy()
            # cls._logger.debug(f"Google Search recommended to use proxydict")
        hashes = set()
        count = 0
        query = quote_plus(query)
        if not extra_params:
            extra_params = {}
        for builtin_param in cls.url_parameters:
            if builtin_param in extra_params.keys():
                raise ValueError(
                    'GET parameter "%s" is overlapping with \
                    the built-in GET parameter',
                    builtin_param
                )
        sa = requests.Session()
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': cls.get_random_user_agent()
        }
        # 先去拿首页保存下cookie
        sa.headers.update(headers)
        # 测试使用，不用代理
        # sa.get(cls.url_home % vars(), timeout=10)
        # sa.get(cls.url_home % vars(), proxies=proxydict, timeout=10)
        if start:
            if num == 10:
                url = cls.url_next_page % vars()
            else:
                url = cls.url_next_page_num % vars()
        else:
            if num == 10:
                url = cls.url_search % vars()
            else:
                url = cls.url_search_num % vars()

        while not stop or count < stop:
            last_count = count
            for k, v in extra_params.items():
                k = quote_plus(k)
                v = quote_plus(v)
                url = url + ('&%s=%s' % (k, v))

            time.sleep(pause)

            html = cls.get_page(url, sa, proxydict=proxydict)
            soup = BeautifulSoup(html, 'html.parser')
            try:
                anchors = soup.find(id='search').findAll('a')
                # Sometimes (depending on the User-agent) there is
                # no id "search" in html response...
            except AttributeError:
                # Remove links of the top bar.
                gbar = soup.find(id='gbar')
                if gbar:
                    gbar.clear()
                anchors = soup.findAll('a')
            # Process every anchored URL.
            for a in anchors:

                # Get the URL from the anchor tag.
                try:
                    link = a['href']
                except KeyError:
                    continue

                # Filter invalid links and links pointing to Google itself.
                link = cls.filter_result(link)
                if not link:
                    continue

                # Discard repeated results.
                h = hash(link)
                if h in hashes:
                    continue
                hashes.add(h)

                # Yield the result.
                yield link

                # Increase the results counter.
                # If we reached the limit, stop.
                count += 1
                if stop and count >= stop:
                    return

            # End if there are no more results.
            # XXX TODO review this logic, not sure if this is still true!
            if last_count == count:
                break

            # Prepare the URL for the next request.
            start += num
            if num == 10:
                url = cls.url_next_page % vars()
            else:
                url = cls.url_next_page_num % vars()
