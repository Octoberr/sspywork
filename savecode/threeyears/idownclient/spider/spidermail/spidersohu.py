"""
验证手机号是否注册了搜狐邮箱
20181023
"""
import json
import time
import traceback
import re
import pytz

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidermailbase import SpiderMailBase
from datetime import datetime
from sys import platform
from idownclient.config_spiders import webdriver_path_debian, webdriver_path_win
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait


class SpiderSohu(SpiderMailBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderSohu, self).__init__(task, appcfg, clientid)

    def _check_registration(self):
        """
        查询手机号是否注册了搜狐邮箱
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            t1 = int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)
            t2 = int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)
            url = f'https://v4.passport.sohu.com/i/cookie/common?callback=passport403_cb{t1}&_={t2}'
            headers = f"""
Host: v4.passport.sohu.com
Connection: keep-alive
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
Accept: */*
Referer: https://mail.sohu.com/fe/
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cookie: a=123; t={t1}
"""
            html = self._ha.getstring(url, headers=headers)

            url = f"https://v4.passport.sohu.com/i/verify/email?t={t2}&email={self.task.phone}%40sohu.com&etype=mobile"
            headers = """
Host: v4.passport.sohu.com
Connection: keep-alive
Pragma: no-cache
Cache-Control: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
"""
            response = self._ha.getstring(url=url, headers=headers)

            if 'message":"email already has bind"' in response:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail.', t, EBackResult.CheckRegisterdFail)
        return

    def _cookie_login(self) -> bool:
        res = False
        try:
            self._ha._managedCookie.add_cookies('sohu.com', self.task.cookie)
            # lt_ui会让之后的请求返回超时错误
            self._ha.cookies.set('lt_ui', None)
            headers = '''
            Accept: application/json, text/plain, */*
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Host: mail.sohu.com
            Origin: https://mail.sohu.com
            Referer: https://mail.sohu.com/fe/
            Sec-Fetch-Dest: empty
            Sec-Fetch-Mode: cors
            Sec-Fetch-Site: same-origin
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36
            '''
            url = 'https://mail.sohu.com/fe/login/callback'
            html = self._ha.getstring(url, req_data='', headers=headers)
            json_res = json.loads(html)
            if json_res['msg'] != 'login success' or json_res['status'] != 200:
                return res

            url = 'https://mail.sohu.com/fe/user/newdata/'
            html = self._ha.getstring(url, headers=headers)
            json_res = json.loads(html)
            if json_res['msg'] != 'success' or json_res['status'] != 200:
                return res
            self._userid = json_res['data']['email']
            if not self._userid:
                return res
            res = True
        except Exception:
            self._logger.error(f"Cookie login error, err:{traceback.format_exc()}")
        return res

    def _pwd_login(self) -> bool:
        res = False
        try:
            if platform == 'linux' or platform == 'linux2':
                driver_path = webdriver_path_debian
            elif platform == 'win32':
                driver_path = webdriver_path_win
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('lang=zh_CN.UTF-8')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('blink-settings=imagesEnabled=false')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(options=chrome_options, executable_path=driver_path)
            driver.get('https://mail.sohu.com/fe/#/login')
            wait = WebDriverWait(driver, 10)
            wait.until(lambda diver: driver.find_element_by_xpath('//input[@value="登 录"]'),
                       message='load login page fail!')
            driver.find_element_by_xpath('//input[@ng-model="account"]').send_keys(self.task.account)
            driver.find_element_by_xpath('//input[@ng-model="pwd"]').send_keys(self.task.password)
            driver.find_element_by_xpath('//input[@value="登 录"]').click()
            wait.until(lambda diver: driver.current_url == 'https://mail.sohu.com/fe/#/homepage',
                       message='enter homepage fail!')
            cookies = ''
            for cookie in driver.get_cookies():
                cookies = cookies + cookie['name'] + '=' + cookie['value'] + ';'
            self._ha._managedCookie.add_cookies('sohu.com', cookies)
            driver.quit()
            res = self._cookie_login()
        except Exception as ex:
            self._logger.error("Pwd login error, err: {}".format(ex))
            self._write_log_back("账密登录失败: {}".format(ex.args))
        return res
