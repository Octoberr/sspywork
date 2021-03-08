# coding=gbk
import json
import queue
import threading
import time
import re
import traceback
import random

from selenium.webdriver import ChromeOptions
from selenium import webdriver

from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import HttpAccess

from datacontract.automateddataset import EAutoType
from idownclient.automated.autopluginbase import AutoPluginBase
from idownclient.clientdatafeedback.autodatafeedback import ExpDB


class Seebug(AutoPluginBase):
    tasktype = EAutoType.EXPDB

    def __init__(self):
        AutoPluginBase.__init__(self)
        self.ha = HttpAccess()
        self._get_cookie()

    def _get_cookie(self):
        try:
            ic = False
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('blink-settings=imagesEnabled=false')
            # chrome_options.add_argument('--no-sandbox')
            driver = webdriver.Chrome(chrome_options=chrome_options)
            success = False
            check_num = 1
            while True:
                try:
                    driver.get('https://cn.0day.today/')
                    time.sleep(5 * check_num)
                    driver.find_element_by_css_selector(
                        'body > div > div.agree > div:nth-child(9) > div:nth-child(3) > form > input').click()
                    success = True
                    break
                except:
                    check_num += 1
                    if check_num == 4:
                        break
            if success:
                cookies = driver.get_cookies()
                l_cookie = ''
                for cookie in cookies:
                    l_cookie = l_cookie + cookie['name'] + '=' + cookie['value'] + '; '
                if ic:
                    self._logger.info('Got cookie success!')
                    self.ha._managedCookie.add_cookies('0day.today', l_cookie)
            else:
                self._logger.info('Got cookie fail!')
            driver.close()
        except Exception:
            self._logger.error('Got cookie fail: {}'.format(traceback.format_exc()))

    def get_bug(self):
        failnum = 0
        while True:
            url = 'https://cn.0day.today/platforms'
            headers = """
            Host: cn.0day.today
            Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Accept-Language: zh-CN,zh;q=0.9
            """
            html = self.ha.getstring(url, headers=headers)
            if "value='是的我同意'" in html or 'Just a moment...' in html:
                failnum += 1
                if failnum > 3:
                    self._logger.error('Requsts fail over 3 times!')
                    return
                self._logger.info('Cookie lose efficacy!')
                self._get_cookie()
            else:
                break
        soup = BeautifulSoup(html, 'lxml')
        tables = soup.select('.category_title a')
        for a in tables:
            href = a.attrs['href']
            if href == '/platforms' or href == '/webapps':
                continue
            url0 = 'https://cn.0day.today' + href
            page = 0
            last_url = None
            while True:
                page += 1
                url = url0 + '/' + str(page)
                html = self.ha.getstring(url, headers=f"""
        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
        accept-language: zh-CN,zh;q=0.9
        cache-control: no-cache
        pragma: no-cache
        referer: {url0}
        upgrade-insecure-requests: 1
        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36""")
                soup = BeautifulSoup(html, 'lxml')
                exploits = soup.select('.ExploitTableContent')
                for exploit in exploits:
                    d_href = exploit.select_one('h3 a').attrs['href']
                    id = d_href.split('/')[-1]
                    if self.is_data_unique(str(id) + '0day'):
                        return
                    name = exploit.select_one('h3 a').get_text()

                    if '你可以免费使用此漏洞利用' in str(exploit):
                        detail, referer = self.get_description(href, url)
                        if detail:
                            description = f'datasource: 0day\nid: {id}\nname: {name}\nurl:{url}\n'
                            self.write_text_string(description, detail, 'iscan_expdb_doc')
                    else:
                        continue

                    date = exploit.select_one('.td a').get_text()
                    date_d = date.split('-')[0]
                    date_y = date.split('-')[-1]
                    date = date_y + date.replace(date_d, '').replace(date_y, '') + date_d
                    verified = soup.select_one('.tips_verified_')
                    if verified:
                        verified = 0
                    else:
                        verified = 1
                    level_t = substring(str(exploit), "class='tips_risk_color_", "'>安全风险级别")
                    if level_t in ['0', '1']:
                        level = 1
                    elif level_t == '2':
                        level = 2
                    else:
                        level = 3
                    res = ExpDB(name, '0day', id, date, verified)
                    res.level = level
                    res, poc, url = self.get_detail(id, referer, res)
                    description = f'datasource: seebug\nid: {id}\nname: {name}\nurl:{url}\n'
                    self.write_text_string(description, poc, 'iscan_expdb_exp')
                    self.write_text(res, 'iscan_expdb')
                    self.store_data_unique(str(id) + '0day')

                if not last_url:
                    last_url = 'https://cn.0day.today' + soup.select('.pages a')[-1].attrs['href']
                if last_url == url:
                    break


    def get_description(self, href, referer):
        try:
            d_url = 'https://cn.0day.today/exploit' + href
            html = self.ha.getstring(d_url, headers=f"""
    accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
    accept-language: zh-CN,zh;q=0.9
    cache-control: no-cache
    pragma: no-cache
    referer: {referer}
    upgrade-insecure-requests: 1
    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36""")
            description = ''
            if "<div class='td'>描述</div>" in html:
                try:
                    description = re.findall(r"<div class='td'>描述</div>.*?>(.*?)</div>", html, re.S)[0]
                except Exception:
                    self._logger.error('Get description fail: {}'.format(traceback.format_exc()))
            return description, d_url
        except Exception:
            self._logger.error(f'Description fail:{traceback.format_exc()}')

    def get_detail(self, id, referer, res):
        try:
            e_url = 'https://cn.0day.today/exploit/' + id
            e_html = self.ha.getstring(e_url, headers=f"""
    accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
    accept-language: zh-CN,zh;q=0.9
    cache-control: no-cache
    pragma: no-cache
    referer: {referer}
    upgrade-insecure-requests: 1
    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36""")
            e_soup = BeautifulSoup(e_html, 'lxml')
            l1 = e_soup.select(
                "[style='float:left; width:150px; overflow:hidden; margin:5px 0px 0px 0px;']")
            author = {}
            author['name'] = l1[0].get_text()
            tags = []
            target = {}
            target['type'] = l1[1].get_text()
            target['platform'] = l1[2].get_text()
            tags.append(self.tag_mapping(target['type']))
            l3 = e_soup.select("[style='float:left; margin:5px 0px 0px 0px;']")
            code = []
            co = {}
            co['code_type'] = '0day-ID'
            co['code'] = l3[0].get_text()
            code.append(co)
            try:
                co['code_type'] = 'cve'
                co['code'] = l3[1].get_text(' ')
                code.append(co)
            except:
                pass
            res.tags = tags
            res.target = target
            res.author = author
            res.code = code
            poc = e_soup.select_one('pre').get_text()
            return res, poc, e_url
        except Exception:
            self._logger.error(f'ID: {id} get detail fail:{traceback.format_exc()}')

    def start(self):
        self.get_bug()