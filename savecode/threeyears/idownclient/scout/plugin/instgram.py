"""
instgram
"""
import re
import threading
import traceback
import time
import json

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from commonbaby.httpaccess.httpaccess import HttpAccess
from commonbaby.helpers.helper_str import substring
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .scoutplugbase import ScoutPlugBase
from datacontract.iscoutdataset import IscoutTask
from ...clientdatafeedback.scoutdatafeedback import NetworIdkProfile
from ...clientdatafeedback.scoutdatafeedback import NetworkId


class Instagram(ScoutPlugBase):
    _initialed: bool = False
    _cookie = {}

    def __init__(self, task:IscoutTask):
        ScoutPlugBase.__init__(self)
        self.task = task
        self._ha: HttpAccess = HttpAccess()
        self._host: str = '.instagram.com'
        self._login()
        if Instagram._cookie:
            self._ha._managedCookie.add_cookies(self._host, Instagram._cookie)

    def search_keyword(self, keyword, level) -> iter:
        """按关键字搜索用户"""
        try:
            url = f'https://www.instagram.com/web/search/topsearch/?context=blended&query={keyword}&include_reel=true'
            headers = """
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9
            cache-control: no-cache
            pragma: no-cache
            upgrade-insecure-requests: 1
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            jshtml = json.loads(html)
            if jshtml['users']:
                for user in jshtml['users']:
                    try:
                        nickname = user['user']['username']
                        res = NetworkId(self.task, level, nickname)
                        res.userid = nickname
                        res.url = 'https://www.instagram.com/' + nickname
                        res.source = 'Instagram'
                        res.reason = 'Instagram 关键字搜索用户'
                        yield res
                    except:
                        continue
        except Exception:
            self._logger.error('Instagram search keyword fail: {}'.format(traceback.format_exc()))


    def get_user_profile(self, url, level):
        """获取用户个人详情
        :url 用户主页url"""
        try:
            headers = """
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9
            cache-control: no-cache
            pragma: no-cache
            referer: https://www.instagram.com/?hl=zh-cn
            upgrade-insecure-requests: 1
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            soup = BeautifulSoup(html, 'lxml')
            data = substring(html, 'window._sharedData = ', ';')
            # print(data)
            jsdata = json.loads(data)
            us = jsdata['entry_data']['ProfilePage'][0]['graphql']['user']
            nickname = us['username']
            res = NetworIdkProfile(self.task, level, nickname, us['id'], 'Instagram')
            res.nickename = nickname
            dic = {}
            detail = {}
            detail['content'] = soup.select_one('[name="description"]').attrs['content']
            detail['full_name'] = us['full_name']
            detail['is_verified'] = us['is_verified']
            detail['edge_followed_by'] = us['edge_followed_by']['count']
            detail['edge_follow'] = us['edge_follow']['count']
            detail['description'] = us['biography']
            dic['info'] = []
            dic['info'].append(detail)
            res.details = json.dumps(dic)
            yield res
        except Exception:
            self._logger.error('Instagram get user profile fail: {}'.format(traceback.format_exc()))

    def _login(self):
        """登陆接口"""
        try:
            if not Instagram._initialed:
                account = '+8618381095282'
                password = '18381095282qaz'
                chrome_options = ChromeOptions()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('blink-settings=imagesEnabled=false')
                # chrome_options.add_argument('--no-sandbox')
                driver = webdriver.Chrome(chrome_options=chrome_options)
                driver.get('https://www.instagram.com/accounts/login/?hl=zh-cn&source=auth_switcher')
                act = driver.find_element_by_css_selector(
                    '#react-root > section > main > div > article > div > div:nth-child(1) > div > form > div:nth-child(2) > div > label > input')
                pwd = driver.find_element_by_css_selector(
                    '#react-root > section > main > div > article > div > div:nth-child(1) > div > form > div:nth-child(3) > div > label > input')
                but = driver.find_element_by_css_selector(
                    '#react-root > section > main > div > article > div > div:nth-child(1) > div > form > div:nth-child(4)')
                act.send_keys(account)
                pwd.send_keys(password)
                but.click()
                time.sleep(2)
                cookie_l = driver.get_cookies()
                l_cookie = ''
                for cookie in cookie_l:
                    # cookie = json.loads(cookie)
                    l_cookie = l_cookie + cookie['name'] + '=' + cookie['value'] + '; '
                Instagram._cookie = l_cookie
                Instagram._initialed = True
                driver.close()
        except Exception:
            self._logger.error('Login fail: {}'.format(traceback.format_exc()))


