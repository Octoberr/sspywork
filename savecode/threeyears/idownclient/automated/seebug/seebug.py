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
            driver.get('https://www.seebug.org/')
            time.sleep(2)
            cookies = driver.get_cookies()
            l_cookie = ''
            for cookie in cookies:
                l_cookie = l_cookie + cookie['name'] + '=' + cookie['value'] + '; '
                if cookie['name'] == '__jsl_clearance':
                    ic = True
            self.cookie = l_cookie
            # print(self.cookie)
            self.ha._managedCookie.add_cookies('.seebug.org', self.cookie)
            if ic:
                self._logger.info('Got cookie success!')
            driver.close()
        except Exception:
            self._logger.error('Got cookie fail: {}'.format(traceback.format_exc()))
            
    def get_bug(self):
        page = 0
        max_page = None
        while True:
            page += 1
            fail_time = 0
            while True:
                url = f'https://www.seebug.org/vuldb/vulnerabilities?page={page}'
                html = self.ha.getstring(url, headers="""
                Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
                Accept-Encoding: gzip, deflate, br
                Accept-Language: zh-CN,zh;q=0.9
                Cache-Control: no-cache
                Connection: keep-alive
                Host: www.seebug.org
                Pragma: no-cache
                Upgrade-Insecure-Requests: 1
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36""")
                if '您访问频率太高，请稍候再试。' in html:
                    print(f'您访问频率太高，请稍候再试。{fail_time} * 5s')
                    fail_time += 1
                    if fail_time == 5:
                        print('Fail time outnumber 5!')
                        break
                    time.sleep(5)
                else:
                    break
            soup = BeautifulSoup(html, 'lxml')
            tbody = soup.select('tbody tr')
            if not max_page:
                max_page = soup.select_one('#J-jump-form input').attrs['max']
            for tr in tbody:
                self.bug_detail(tr, url)
            if int(max_page) <= page:
                break

    def bug_detail(self, tr, referer):
        try:

            b_url = 'https://www.seebug.org' + tr.select_one('td a').attrs['href']
            name = tr.select_one('.vul-title-wrapper a').get_text()
            datasource = 'seebug'
            id = tr.select_one('td a').get_text()
            date_published = tr.select_one('.text-center.datetime.hidden-sm.hidden-xs').get_text()
            tooltip = tr.select_one('[data-toggle="tooltip"]').attrs['data-original-title']
            if tooltip == '高危':
                level = 3
            elif tooltip == '中危':
                level = 2
            else:
                level = 1
            fail_time = 0
            res = ExpDB(name, datasource, id, date_published, 0)
            while True:
                b_html = self.ha.getstring(b_url, headers=f"""
                            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
                            Accept-Encoding: gzip, deflate, br
                            Accept-Language: zh-CN,zh;q=0.9
                            Cache-Control: no-cache
                            Connection: keep-alive
                            Host: www.seebug.org
                            Pragma: no-cache
                            Referer: {referer}
                            Upgrade-Insecure-Requests: 1
                            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36""")
                if '您访问频率太高，请稍候再试。' in b_html:
                    fail_time += 1
                    print(f'您访问频率太高，请稍候再试。{fail_time} * 45s')
                    if fail_time == 5:
                        print('Fail time outnumber 5!')
                        break
                    t = random.randint(30, 60)
                    time.sleep(t)
                else:
                    break
            b_soup = BeautifulSoup(b_html, 'lxml')
            try:
                file_data = b_soup.select_one('#j-md-detail').get_text()
                if '登录后查看' not in file_data:
                    description = f'datasource: seebug\nid: {id}\nname: {name}\nurl:{b_url}\n'
                    self.write_text_string(description, file_data, 'iscan_expdb_doc')
            except:
                pass
            tags = []
            try:
                tag_type = b_soup.select('.bug-msg .col-md-4')[1].select_one('dd').get_text()
                tags.append(tag_type)
                res.tags = tags
            except:
                pass
            target = []
            try:
                tar = {}
                ta_type = b_soup.select_one('.hover-scroll a').get_text().replace('\n', '')
                ta_type = re.sub(r'\s{2,}', '', ta_type)
                tar['type'] = ta_type
                try:
                    version = b_soup.select_one('.hover-scroll').get_text()
                    version = substring(version, '(', ')')
                    tar['version'] = {'list': version}
                except:
                    pass
                target.append(tar)
                res.target = target
            except:
                pass

            cve_id = b_soup.select('.bug-msg .col-md-4')[2].select_one('dd').get_text()
            code = []
            if '补充' not in cve_id:
                cve = {}
                cve['code_type'] = 'cve'
                cve['code'] = cve_id.replace('\n', '')
                code.append(cve)
                res.code = code
            author = {}
            author['name'] = b_soup.select('.bug-msg .col-md-4')[1].select('dd')[3].get_text()
            author['name'] = re.sub(r'\s{2,}', '', author['name'])
            res['author'] = author
            try:
                poc = b_soup.select_one('#J-poc').get_text()
                description = f'datasource: seebug\nid: {id}\nname: {name}\nurl:{b_url}\n'
                self.write_text_string(description, poc, 'iscan_expdb_exp')
            except:
                pass

            print(name, datasource, id, date_published, tooltip, level, tags, code, author)
            time.sleep(3)
        except Exception:
            self._logger.error('Got bug detail fail: {}'.format(traceback.format_exc()))

    def start(self):
        self.get_bug()