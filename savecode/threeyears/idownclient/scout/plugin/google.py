"""
google
"""
import json
import re
import threading
import time
import traceback
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from commonbaby.design import SingletonDecorator
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import HttpAccess
from selenium import webdriver
from selenium.webdriver import ChromeOptions

# from ...clientdatafeedback.scoutdatafeedback import NetworkProfile
from .scoutplugbase import ScoutPlugBase


@SingletonDecorator
class Google(ScoutPlugBase):
    """搜索引擎"""
    def __init__(self):
        ScoutPlugBase.__init__(self)
        self.ha = HttpAccess()
        self.proxy_List = []
        self.is_first = True
        self.cookie = 'CGIC=InZ0ZXh0L2h0bWwsYXBwbGljYXRpb24veGh0bWwreG1sLGFwcGxpY2F0aW9uL3htbDtxPTAuOSxpbWFnZS93ZWJwLGltYWdlL2FwbmcsKi8qO3E9MC44LGFwcGxpY2F0aW9uL3NpZ25lZC1leGNoYW5nZTt2PWIz; HSID=AJAuKs_OF4zjl_QiH; SSID=AOt5d7crf8ErXjqt5; APISID=ywI9lJQCGtyX_UgX/AVPHvH0i8rRjLpy3q; SAPISID=qPfZ04-88QBXo551/Aw4J_YiM8bTsz4m9H; CONSENT=YES+CN.zh-CN+; SEARCH_SAMESITE=CgQI3o0B; _gcl_au=1.1.423014040.1568171077; NID=188=gkZ2tXD8e7EWvfFwVQ9g0g5Ny1h2S1gY62TzUODI6ypQxzhcyqwfRgkZxnuA9c1kHGpLn9XDvmuJN4_kBEPJYoLSmv_USmqai_6IYBQ9RxxBYr5HXlDo60sFVnUMFqU9L9Im9jeVWz8KjdzAWdMaXDwAlUN7VZbILOZ8qm_0etxVhmAyGNvBzBI9C3ZvCG3M6OV6Gc3e0QoTqtsq87egQ8cjl-riBP-A9hPp8v5_SCohQA; SID=oge9GlNhzXILiY9MW_P2brb9HPE0noiUCwKqq4Z-w4IFcUYyBLodJCIIfQl8R8IqgQclJQ.; 1P_JAR=2019-09-20-06; SIDCC=AN0-TYu9Bf7Mrwg4TJmxordC1vli8GeqPk_MiHeE-3rahVe8d0bVfvQcfHx9GiSL3t_0JBmJQd0'

    def dic_cookie(self):
        cookie_dic = {}
        for i in self.cookie.split('; '):
            cookie_dic["domain"] = '.google.com'
            cookie_dic['name'], cookie_dic['value'] = i.split('=', 1)
            self.driver.add_cookie(cookie_dic)

    def start_driver(self):
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('blink-settings=imagesEnabled=false')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        self.driver.get('https://www.google.com')
        self.driver.set_page_load_timeout(10)
        self.is_first = True

    def search_keyword(self, keyword, reason) -> iter:
        """
        google搜索引擎搜索关键字，返回SearchEngine对象\n
        :param keyword: google搜索关键字\n
        :return: yield Searchengine\n
        """
        yield None
        self.start_driver()
        start = 0
        all_url = []
        url = 'https://www.google.com/'
        while True:
            try:
                if self.is_first:
                    # self.driver.get(f'https://www.google.com/search?ei=RoAZXYhlgbDxBYfOlPgG&q={oq}&oq={oq}&start={start}&gs_l=psy-ab.3...0.0..65950...0.0..0.0.0.......0......gws-wiz.B5VbKuFMsb0')
                    self.driver.get(url)
                    self.driver.find_element_by_css_selector(
                        '#tsf > div:nth-child(2) > div > div.RNNXgb > div > div.a4bIc > input'
                    ).send_keys(keyword)
                    try:
                        self.driver.find_element_by_xpath(
                            '//*[@id="tsf"]/div[2]/div/div[3]/center/input[1]'
                        ).click()
                    except:
                        self.driver.find_element_by_xpath(
                            '//*[@id="tsf"]/div[2]/div/div[2]/div[2]/div[2]/center/input[1]'
                        ).click()
                    self.is_first = False
                else:
                    self.driver.get(url)

                html = self.driver.page_source
            except:
                self.driver.close()
                break

            soup = BeautifulSoup(html, 'lxml')
            res = soup.select('.bkWMgd .g')
            if not res:
                break
            for r in res:
                try:
                    href = r.select_one('.rc .r a').attrs['href']

                    if href not in all_url:
                        all_url.append(href)
                    else:
                        continue
                except:
                    continue

            if '下一页' not in html:
                break
            url = self.driver.current_url
            start += 10
            if start == 10:
                url = url + f'&start={start}'
            else:
                url = re.sub(r'&start=\d+', f'&start={start}', url)

        return all_url

    def url(self):
        pass
