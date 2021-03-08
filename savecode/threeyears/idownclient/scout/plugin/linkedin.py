# coding:gbk
"""
LinkedIN
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
from ...clientdatafeedback.scoutdatafeedback import NetworkProfile
from ...clientdatafeedback.scoutdatafeedback import NetworkId

class LinkedIn(ScoutPlugBase):
    """LinkedIn: ��Ӣ"""

    _init_locker = threading.RLock()
    _initialed: bool = False
    _cookie = {}

    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        self.task = task
        self._ha: HttpAccess = HttpAccess()
        self._host: str = '.linkedin.com'
        self._login()
        if LinkedIn._cookie:
            for key, value in LinkedIn._cookie.items():
                self._ha._managedCookie.add_cookies(key, value)
        self._first_page()

    def _login(self):
        """��ʼ������ҳ��"""
        try:
            if not LinkedIn._initialed:
                chrome_options = ChromeOptions()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('blink-settings=imagesEnabled=false')
                # chrome_options.add_argument('--no-sandbox')
                driver = webdriver.Chrome(chrome_options=chrome_options)
                account = 'nmsb21cn@21cn.com'
                password = '18381095282qaz'
                driver.get('https://www.linkedin.com/')
                if '<meta name="seoBeaconWorkerUrl" ' in driver.page_source:
                    driver.find_element_by_css_selector('body > nav > a.nav__button-secondary').click()
                    act = driver.find_element_by_css_selector('#username')
                    pwd = driver.find_element_by_css_selector('#password')
                    submit = driver.find_element_by_css_selector(
                        '#app__container > main > div > form > div.login__form_action_container > button')
                else:
                    act = driver.find_element_by_css_selector('#login-email')
                    pwd = driver.find_element_by_css_selector('#login-password')
                    submit = driver.find_element_by_css_selector('#login-submit')
                act.send_keys(account)
                pwd.send_keys(password)
                submit.click()
                time.sleep(2)

                if '���������ַ' not in driver.page_source:
                    cookie = driver.get_cookies()
                    l_cookie = ''
                    w_cookie = ''
                    for cookie in cookie:
                        # cookie = json.loads(cookie)
                        if cookie['domain'] == '.linkedin.com':
                            l_cookie = l_cookie + cookie['name'] + '=' + cookie['value'] + '; '
                        else:
                            w_cookie = w_cookie + cookie['name'] + '=' + cookie['value'] + '; '
                    LinkedIn._cookie['.linkedin.com'] = l_cookie
                    LinkedIn._cookie['www.linkedin.com'] = w_cookie
                    LinkedIn._initialed = True
                    self._logger.info('Login success, get cookie sucess!')
                    driver.close()
                    return True
                else:
                    self._logger.info('Login fail!')
                    driver.close()
                    return False

        except Exception:
            self._logger.error("Login error: {}".format(traceback.format_exc()))

    def search_keyword(self, keyword, level) -> iter:
        """���ؼ��������û���
        :keyword  Ӣ�������� �գ� ���������� �����м��ÿո����
        �����û�����ֶΣ� (userid,nickname,userurl,"LinkedIn")"""
        try:
            if ' ' in keyword:
                if self._dif_keyword(keyword):
                    lastName, firstName = keyword.split(' ', 1)
                else:
                    firstName, lastName = keyword.split(' ', 1)
            else:
                lastName = ''
                firstName = keyword
            lastName = quote_plus(lastName)
            firstName = quote_plus(firstName)
            page = 0
            while True:
                page += 1
                url1 = f'https://www.linkedin.com/search/results/people/?firstName={quote_plus(firstName)}&lastName={quote_plus(lastName)}&origin=SEO_PSERP&page={page}'
                headers = """
                Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
                Accept-Encoding: gzip, deflate, br
                Accept-Language: zh-CN,zh;q=0.9
                Cache-Control: max-age=0
                Connection: keep-alive
                Host: www.linkedin.com
                Upgrade-Insecure-Requests: 1
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"""
                html1 = self._ha.getstring(url1, headers=headers)
                # html1 = ha.getstring(url1, headers=headers)
                soup = BeautifulSoup(html1, 'lxml')
                dic = re.findall(r'({"data":{"metadata".*?")\n', str(soup))[0]
                jshtml = json.loads(dic)
                elements = jshtml['data']['elements'][1]['elements']
                if elements:
                    for element in elements:
                        userid = element['publicIdentifier']
                        nickname = element['title']['text']
                        userurl = 'https://www.linkedin.com/in/' + userid
                        res = NetworkId(self.task, level, keyword)
                        res.url = userurl
                        res.userid = userid
                        res.source = 'LinkedIn'
                        res.reason = 'LinkedIn ������Ա'
                        yield res
                else:
                    break
        except Exception:
            self._logger.error('Search keyword fail: {}'.format(traceback.format_exc()))

    def get_user_profile(self, userurl, level) -> dict:
        """��ȡ�û���������"""
        try:
            headers = """
                       accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
                       accept-encoding: gzip, deflate, br
                       accept-language: zh-CN,zh;q=0.9
                       cache-control: max-age=0
                       upgrade-insecure-requests: 1
                       user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"""
            html = self._ha.getstring(userurl, headers=headers)
            # html = ha.getstring('https://www.linkedin.com/in/%E6%9D%B0-%E6%9D%8E-180015a4/', headers=headers)
            soup = BeautifulSoup(html, 'lxml')
            dic = re.findall(r'({"data":{"\*profile".*?"}]})', str(soup))[0]
            jshtml = json.loads(dic)
            detail = {}
            works = []
            infos = []
            educations = []
            volunteers = []
            for include in jshtml['included']:
                keys = include.keys()
                if 'lastName' in keys and 'headline' in keys and 'locationName' in keys:
                    info = {}
                    info['lastName'] = include['lastName']
                    info['firstName'] = include['firstName']
                    info['headline'] = include['headline']
                    info['locationName'] = include['locationName']
                    info['industryName'] = include['industryName']
                    info['summary'] = include['summary']
                    info['maidenName'] = include['maidenName']
                    infos.append(info)
                if 'company' in keys and 'companyName' in keys and 'geoLocationName' in keys and 'timePeriod' in keys:
                    comp = {}
                    comp['companyName'] = include['companyName']
                    comp['geoLocationName'] = include['geoLocationName']
                    comp['position'] = include['title']
                    try:
                        comp['startDate'] = str(include['timePeriod']['startDate']['year'])
                        if 'month' in include['timePeriod']['startDate'].keys():
                            comp['startDate'] = comp['startDate'] + '-' + str(
                                include['timePeriod']['startDate']['month'])
                        if 'endDate' in include['timePeriod'].keys():
                            comp['endDate'] = str(include['timePeriod']['endDate']['year'])
                            if 'month' in include['timePeriod']['endDate'].keys():
                                comp['endDate'] = comp['endDate'] + '-' + str(include['timePeriod']['endDate']['month'])
                        else:
                            comp['endDate'] = 'Now'
                    except:
                        pass
                    comp['description'] = include['description']
                    works.append(comp)

                if "degreeName" in keys and 'schoolName' in keys:
                    education = {}
                    education['schoolName'] = include['schoolName']
                    education['fieldOfStudy'] = include['fieldOfStudy']
                    education['degreeName'] = include['degreeName']
                    try:
                        education['startDate'] = str(include['timePeriod']['startDate']['year'])
                        if 'month' in include['timePeriod']['startDate'].keys():
                            education['startDate'] = education['startDate'] + '-' + str(
                                include['timePeriod']['startDate']['month'])
                        if 'endDate' in include['timePeriod'].keys():
                            education['endDate'] = str(include['timePeriod']['endDate']['year'])
                            if 'month' in include['timePeriod']['endDate'].keys():
                                education['endDate'] = education['endDate'] + '-' + str(
                                    include['timePeriod']['endDate']['month'])
                        else:
                            education['endDate'] = 'Now'
                    except:
                        pass
                    educations.append(education)

                if 'role' in keys and 'companyName' in keys:
                    volunteer = {}
                    volunteer['role'] = include['role']
                    volunteer['companyName'] = include['companyName']
                    try:
                        volunteer['startDate'] = str(include['timePeriod']['startDate']['year'])
                        if 'month' in include['timePeriod']['startDate'].keys():
                            volunteer['startDate'] = volunteer['startDate'] + '-' + str(
                                include['timePeriod']['startDate'][
                                    'month'])
                        if 'endDate' in include['timePeriod'].keys():
                            volunteer['endDate'] = str(include['timePeriod']['endDate']['year'])
                            if 'month' in include['timePeriod']['endDate'].keys():
                                volunteer['endDate'] = volunteer['endDate'] + '-' + str(
                                    include['timePeriod']['endDate'][
                                        'month'])
                        else:
                            volunteer['endDate'] = 'Now'
                    except:
                        pass
                    volunteer['description'] = include['description']
                    volunteers.append(volunteer)
                else:
                    continue
            detail['info'] = infos
            detail['work'] = works
            detail['education'] = educations
            detail['volunteer'] = volunteers
            uniqueid = userurl.split('/in/')[-1]
            res = NetworIdkProfile(self.task, level, userurl, uniqueid, 'LinkedIn')
            res.details = json.dumps(detail)
            res.address = detail['info'][0]['locationName']
            yield res
        except Exception:
            self._logger.error('Got user profile fail: {}'.format(traceback.format_exc()))

    def _first_page(self):
        try:
            url = 'https://www.linkedin.com/'
            headers = """
            Host: www.linkedin.com
            Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """
            html = self._ha.getstring(url, headers=headers)
            if '���������ַ' not in html:
                self._logger.info('_Cookie is effective!Initialization success!')
                return True
            else:
                self._logger.warn('_Cookie lose efficacy!')
                return False
        except Exception:
            self._logger.error('First page fail: {}'.format(traceback.format_exc()))

    def _dif_keyword(self, keyword) -> bool:
        """���keyword���Ƿ��������"""
        zhmodel = re.compile(u'[\u4e00-\u9fa5]')  # �������
        match = zhmodel.search(keyword)
        if match:
            return True
        else:
            return False


