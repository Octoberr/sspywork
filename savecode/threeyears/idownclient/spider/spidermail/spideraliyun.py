"""
阿里云邮箱爬虫
create by judy 20190109
"""
import datetime
import json
import time
import traceback
import pytz
from urllib.parse import quote_plus
from sys import platform
from idownclient.config_spiders import webdriver_path_debian, webdriver_path_win
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait

from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess import HttpAccess, ResponseIO

from .spidermailbase import SpiderMailBase
from ...clientdatafeedback import CONTACT_ONE, CONTACT, EML, Folder, PROFILE


class SpiderAliyun(SpiderMailBase):

    def __init__(self, tsk, appcfg, clientid):
        super(SpiderAliyun, self).__init__(tsk, appcfg, clientid)

    def _get_csrf(self):
        cookiedic = self._ha.cookies.get_dict()
        _csrf_token_ = cookiedic['_csrf_token_']
        _root_token_ = cookiedic['alimail_browser_instance']
        return _csrf_token_, _root_token_

    def _pwd_login(self) -> bool:
        res = False
        try:
            if platform == 'linux' or platform == 'linux2':
                driver_path = webdriver_path_debian
            elif platform == 'win32':
                driver_path = webdriver_path_win
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('blink-settings=imagesEnabled=false')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-dev-shm-usagenmsbsohu123')
            driver = webdriver.Chrome(options=chrome_options, executable_path=driver_path)
            driver.get('https://mail.aliyun.com/alimail/auth/login')
            wait = WebDriverWait(driver, 10)
            wait.until(lambda diver: driver.find_element_by_xpath('//iframe[@id="alibaba-login-box"]'),
                       message='load login page fail!')
            driver.switch_to.frame('alibaba-login-box')
            account = self.task.account.split('@')[0]
            driver.find_element_by_xpath('//input[@id="fm-login-id"]').send_keys(account)
            driver.find_element_by_xpath('//input[@id="fm-login-password"]').send_keys(self.task.password)
            driver.find_element_by_xpath('//input[@id="fm-login-submit"]').click()
            wait.until(lambda diver: driver.find_element_by_xpath("//*[text()='我的邮箱']"),
                       message='enter homepage fail!')
            cookies = ''
            for cookie in driver.get_cookies():
                cookies = cookies + cookie['name'] + '=' + cookie['value'] + ';'
            driver.quit()
            self._ha._managedCookie.add_cookies('aliyun.com', cookies)
            res = self._cookie_login()
        except Exception as ex:
            self._logger.error("Pwd login error, err: {}".format(ex))
            self._write_log_back("账密登录失败: {}".format(ex.args))
        return res

    def _cookie_login(self) -> bool:
        try:
            csrf, _root_token_ = self._get_csrf()
            url = 'https://mail.aliyun.com/alimail/getStartupInfo?tpl=v5&_csrf_token_={}'.format(csrf)
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: mail.aliyun.com
Pragma: no-cache
Referer: https://mail.aliyun.com/alimail/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            _root_token_ = substring(html, '"browserSessionKey":"', '"')
            if "browserSessionKey" in html:
                self.owner = substring(html, '"email":"', '"')
                self.userid = substring(html, '"email":"', '"') + '-aliyun'
                return True
            else:
                return False
        except:
            return False

    def _get_profile(self) -> iter:
        try:
            csrf, _root_token_ = self._get_csrf()
            url = 'https://mail.aliyun.com/alimail/getStartupInfo?tpl=v5&_csrf_token_={}'.format(csrf)
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: mail.aliyun.com
Pragma: no-cache
Referer: https://mail.aliyun.com/alimail/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            res = PROFILE(self._clientid, self.task, self.task.apptype, self.userid)
            res.email = substring(html, '"email":"', '"')
            res.nickname = substring(html, '"displayName":"', '"')
            yield res
        except Exception:
            self._logger.error('{} got profile fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_contacts(self) -> iter:
        try:
            _csrf_token_, _root_token_ = self._get_csrf()

            url = 'https://mail.aliyun.com/alimail/ajax/mms/queryMimeItems.txt?_timestamp_={}'.format(
                int(datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000))
            data = f"_csrf_token_={_csrf_token_}&_root_token_=&_refer_hash_=&storageOwner={self.owner}%40aliyun.com&storageType=alimail_mt_personalcontact&query=%7B%22tagId%22%3A%22100000004%22%7D&offset=0&length=20"
            html = self._ha.getstring(url, req_data=data, headers=f"""
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 273
Content-Type: application/x-www-form-urlencoded
Host: mail.aliyun.com
Origin: https://mail.aliyun.com
Pragma: no-cache
Referer: https://mail.aliyun.com/alimail/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest""")
            if not html or "dataList" not in html:
                # 'logger.LogInformation($"{strAccount} Get contact list failed: {html}");
                return None
            jshtml = json.loads(html)
            res = CONTACT(self._clientid, self.task, self.task.apptype)
            for contact in jshtml['dataList']:

                contactid = contact['baseInfo']['id']
                res_one = CONTACT_ONE(self.userid, contactid, self.task, self.task.apptype)
                res_one.email = contact['baseInfo']['email']
                res_one.nickname = contact['baseInfo']['name']
                try:
                    for phoneInfo in jshtml['fieldList']:
                        if phoneInfo['name'] == 'mobilePhone':
                            res.phone = phoneInfo['value']
                except:
                    pass
                res.append_innerdata(res_one)
            if res.innerdata_len > 0:
                yield res
        except Exception:
            self._logger.error("Got contacts error, err:{}".format(traceback.format_exc()))

    def _get_folders(self) -> iter:
        dic = {'1': '已发送', '2': '收件箱', '3': '垃圾邮件', '5': '草稿箱', '6': '已删除', '11': '重要邮件'}
        for id in dic:
            res = Folder()
            res.folderid = id
            res.name = dic[id]
            yield res

    def _get_mails(self, folder: Folder) -> iter:
        try:
            _csrf_token_, _root_token_ = self._get_csrf()
            foder = folder.folderid
            url = 'https://mail.aliyun.com/alimail/ajax/mail/queryMailList.txt?_timestamp_={}'.format(
                int(datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000))
            if foder == '11':
                postdata = f'showFrom=0&query=%7B%22tagIds%22%3A%5B%22{foder}%22%5D%7D&fragment=1&offset=0&length=75&curIncrementId=0&forceReturnData=1&_csrf_token_={_csrf_token_}&_root_token_={_root_token_}&_refer_hash_=h%3DWyJmbV8yIixbIjIiLCIiLHsiZklkIjoiMSJ9LHsibGFiZWwiOiLpgq7ku7YifV1d&_tpl_=v5'
            else:
                postdata = f'showFrom=0&query=%7B%22folderIds%22%3A%5B%22{foder}%22%5D%7D&fragment=1&offset=0&length=75&curIncrementId=0&forceReturnData=1&_csrf_token_={_csrf_token_}&_root_token_={_root_token_}&_refer_hash_=h%3DWyJmbV8yIixbIjIiLCIiLHsiZklkIjoiMSJ9LHsibGFiZWwiOiLpgq7ku7YifV1d&_tpl_=v5'
            html = self._ha.getstring(url, req_data=postdata, headers="""
Accept:*/*
Accept-Encoding:gzip, deflate, br
Accept-Language:zh-CN,zh;q=0.8
Cache-Control:no-cache
Connection:keep-alive
Content-Type:application/x-www-form-urlencoded
Origin:https://mail.aliyun.com
Pragma:no-cache
Referer:https://mail.aliyun.com/alimail/
X-Requested-With:XMLHttpRequest""")
            if 'dataList' not in html:
                return None
            jshtml = json.loads(html)
            for data in jshtml['dataList']:
                mailid = data['mailId']
                res_one = EML(self._clientid, self.task, self.userid, mailid, folder, self.task.apptype)
                res_one.owner = data['owner']
                res_one.provider = data['from']['email']
                sendtime = data['timestamp'] / 1000
                res_one.sendetime = datetime.datetime.fromtimestamp(sendtime)
                mailid = quote_plus(mailid)
                url = 'https://mail.aliyun.com/alimail/internalLinks/downloadMail?id={}&charset='.format(mailid)
                headers = """
                Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                Accept-Encoding: gzip, deflate, br
                Accept-Language: zh-CN,zh;q=0.9
                Cache-Control: no-cache
                Connection: keep-alive
                Host: mail.aliyun.com
                Pragma: no-cache
                Referer: https://mail.aliyun.com/alimail/
                Upgrade-Insecure-Requests: 1
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
                resp = self._ha.get_response(url, headers=headers)
                # 返回的headers里面没有Content-Length，自己设置
                if 'K' in data['clientExtraInfo']['displaySize']:
                    resp.headers['Content-Length'] = int(data['clientExtraInfo']['displaySize'][:-2]) * 1024
                elif 'M' in data['clientExtraInfo']['displaySize']:
                    resp.headers['Content-Length'] = int(float(data['clientExtraInfo']['displaySize'][:-2])) * 1024 * 1024

                res_one.stream_length = resp.headers.get('Content-Length', 0)
                response = ResponseIO(resp)
                if response:
                    res_one.io_stream = response
                yield res_one
        except Exception:
            self._logger.error('{} Got mails fail: {}'.format(self.userid, traceback.format_exc()))
