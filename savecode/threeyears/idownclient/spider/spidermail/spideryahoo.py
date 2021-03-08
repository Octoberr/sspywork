import datetime
import json
import re
import time
import traceback
import pytz
import uuid

from bs4 import BeautifulSoup
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess import ResponseIO
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from sys import platform
from idownclient.config_spiders import webdriver_path_debian, webdriver_path_win

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidermailbase import SpiderMailBase
from ...clientdatafeedback import EML, Folder, PROFILE, RESOURCES, EResourceType, ESign, EGender, CONTACT, CONTACT_ONE


class SpiderYahoo(SpiderMailBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderYahoo, self).__init__(task, appcfg, clientid)
        self.appid = None
        self.mailWssid = None
        self.boxesid = None
        self.homepage = ''
        self.max_id = 0
        self.uuid = uuid.uuid1()

    def _check_registration(self):
        """
        查询手机号是否注册了mailyahoo
        :param account:
        :return:
        """
        t = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
        array = time.localtime(t)
        t = time.strftime('%Y-%m-%d %H:%M:%S', array)
        try:
            url = "https://login.yahoo.com"
            r = self._ha.getstring(url, headers="""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: login.yahoo.com
Pragma: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")
            pattern = re.compile(r'name="acrumb" value="(.*?)"')
            acrumb = pattern.findall(r)[0]
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
bucket: mbr-rapid-beacon
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 129
content-type: application/x-www-form-urlencoded; charset=UTF-8
Host: login.yahoo.com
Origin: https://login.yahoo.com
Pragma: no-cache
Referer: https://login.yahoo.com/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            postdata = f'acrumb={acrumb}&sessionIndex=QQ--&countryCodeIntl=CN&username={self.task.phone}&passwd=&signin=%E4%B8%8B%E4%B8%80%E6%AD%A5&persistent=y'
            response = self._ha.getstring(url=url, req_data=postdata, headers=headers)
            if '"error":false,"location' in response:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Uber check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail.', t, EBackResult.CheckRegisterdFail)
        return

    def _cookie_login(self):
        res = False
        try:
            if self.task.cookie:
                self._ha._managedCookie.add_cookies('.yahoo.com', self.task.cookie)
            url = 'https://mail.yahoo.com/'
            headers = """
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9
            cache-control: no-cache
            pragma: no-cache
            referer: https://mail.yahoo.com/d/folders/1
            upgrade-insecure-requests: 1
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            self.homepage = html
            self.max_id = substring(html, '"messages":[{"id":"', '"')
            self.mailWssid = substring(html, '"mailWssid":"', '"').encode().decode('unicode_escape')
            self.appid = substring(html, '"appId":"', '"')
            self.boxesid = substring(html, '"allMailboxes":[{"id":"', '"')
            self._userid = substring(html, '"email":"', '"')
            if not self._userid or not self.mailWssid or not self.boxesid or not self.appid:
                return res
            self._username = self._userid
            res = True
        except Exception:
            self._logger.error(f'cookielogin fail: {traceback.format_exc()}')
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
            chrome_options.add_argument('blink-settings=imagesEnabled=false')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=driver_path)
            wait = WebDriverWait(driver, 10)
            driver.get('https://login.yahoo.com/?.src=ym&.partner=none&.lang=de-DE&.intl=de&.done=https%3A%2F%2Fmail.yahoo.com%2Fd%3F.intl%3Dde%26.lang%3Dde-DE%26.partner%3Dnone%26.src%3Dfp')
            time.sleep(3)
            before_url = driver.current_url
            driver.find_element_by_id("login-username").send_keys(self.task.account)
            driver.find_element_by_css_selector("#login-signin").click()
            time.sleep(3)
            post_url = driver.current_url
            if before_url == post_url:
                self._logger.info('Account is wrong!')
                self._write_log_back("登录失败，Account is wrong!")
                return res
            wait.until(EC.presence_of_element_located((By.ID, "login-passwd")), message='login-passed not found')
            driver.find_element_by_id("login-passwd").send_keys(self.task.password)
            driver.find_element_by_id("login-signin").click()
            time.sleep(3)
            end_url = driver.current_url
            if post_url == end_url:
                self._logger.info('Password is wrong!')
                self._write_log_back("登录失败，Password is wrong!")
                return res
            if end_url.startswith('https://login.yahoo.com/account/challenge/challenge-selector'):
                self._logger.info('需要进行验证')
                self._write_log_back("登录失败，需要进行验证")
                return res
            cookie_l = driver.get_cookies()
            l_cookie = ''
            for cookie in cookie_l:
                l_cookie = l_cookie + cookie['name'] + '=' + cookie['value'] + '; '
            self.task.cookie = l_cookie
            res = self._cookie_login()
        except Exception as ex:
            self._logger.error('Pwd login fail: {}'.format(traceback.format_exc()))
            self._write_log_back("账密登录失败: {}".format(ex.args))
        return res

    def _get_folders(self):
        # dic = {'1': 'Inbox', '2': 'Sent', '3': 'Draft', '4': 'Trash', '6': 'Bulk', '21': 'Archive'}
        try:
            soup = BeautifulSoup(self.homepage, 'lxml')
            lis = soup.select('[style="padding:0 0 0 0px"]')
            if not lis:
                self._logger.info('Got mail folder is none!')
            for li in lis:
                total = substring(str(li), 'data-test-total-count="', '"')
                if not total or not int(total):
                    continue
                total = int(total)
                id = substring(str(li), '/d/folders/', '?')
                if not id:
                    id = substring(str(li), '/d/folders/', '"')
                name = li.select_one('.rtlI_dz_sSg')
                if not id or not name:
                    continue
                res = Folder()
                res.folderid = id
                res.name = name.get_text()
                res.mailcount = total
                yield res
        except Exception:
            self._logger.error('Got folder fail:{}'.format(traceback.format_exc()))

    def _get_mails(self, folder: Folder):
        try:
            offset = -100
            while True:
                offset += 100
                url = f'https://mail.yahoo.com/ws/v3/mailboxes/@.id=={self.boxesid}/messages/@.select==q?q=folderId%3A{folder.folderid}%20acctId%3A1%20groupBy%3AconversationId%20count%3A100%20offset%3A{offset}%20-folderType%3A(SYNC)-folderType%3A(INVISIBLE)%20-sort%3Adate'
                headers = """accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
sec-fetch-dest: document
sec-fetch-mode: navigate
sec-fetch-site: none
sec-fetch-user: ?1
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"""
                html = self._ha.getstring(url, headers=headers)
                try:
                    sj = json.loads(html)
                except:
                    self._logger.error('Got mail list fail: {}'.format(traceback.format_exc()))
                    return None
                conversations = sj['result']['messages']
                if not conversations:
                    return None
                for conversation in conversations:
                    res = self._mail_detail(folder, conversation)
                    yield res
        except:
            self._logger.error('Got mail fail: {}'.format(traceback.format_exc()))

    def _mail_detail(self, folder, message: json):
        try:
            mailid = message['id']
            res = EML(self._clientid, self.task, self._userid, mailid, folder, self.task.apptype)
            try:
                res.subject = message["headers"]["subject"]
            except:
                pass
            try:
                res.provider = message["headers"]["from"][0]["email"]
            except:
                pass
            try:
                res.owner = message["headers"]["to"][0]["email"]
            except:
                pass
            t = message["headers"]["date"]
            res.sendtime = datetime.datetime.fromtimestamp(int(t))

            url = f'https://apis.mail.yahoo.com/ws/v3/mailboxes/@.id=={self.boxesid}/messages/@.id=={mailid}/content/rawplaintext?appId=YMailNorrin&ymreqid=5b0965ee-2f08-96e1-1cbc-4800cc01b300&wssid={self.mailWssid}'
            headers = """
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
referer: https://mail.yahoo.com/
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            resp = self._ha.get_response(url, headers=headers)
            res.stream_length = resp.headers.get('Content-Length', 0)
            res.io_stream = ResponseIO(resp)
            return res
        except Exception:
            self._logger.error('Mail: {} got fail: {}'.format(folder.folderid, traceback.format_exc()))

    def _get_profile(self):
        try:
            url = 'https://login.yahoo.com/account/personalinfo'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: login.yahoo.com
Pragma: no-cache
Referer: https://login.yahoo.com/account/preferences
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            soup = BeautifulSoup(html, 'lxml')
            res = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
            try:
                res.account = re.findall(r'Yahoo accounts:.*?\((.*?)\)"', html)[0]
            except:
                res.account = self._username
            gender = soup.select_one('[selected="selected"]')['value']
            if gender == 'male':
                res.gender = EGender.Male
            elif gender == 'female':
                res.gender = EGender.Female
            else:
                res.gender = EGender.Unknown
            birthday = soup.select_one('#birthday .txt').get_text().replace('\n', '')
            res.birthday = re.sub(r'\s{2,}', '', birthday)
            res.nickname = soup.select_one('#txt-nickname').get_text()
            try:
                photourl = soup.select_one('.default-image-content #default-image').attrs['src']
                profilepic: RESOURCES = RESOURCES(self._clientid, self.task, photourl, EResourceType.Picture,
                                                  self.task.apptype)

                resp_stream: ResponseIO = self._ha.get_response_stream(photourl)
                profilepic.io_stream = resp_stream
                profilepic.filename = photourl.rsplit('/', 1)[-1]
                profilepic.sign = ESign.PicUrl
                res.append_resource(profilepic)
                yield profilepic
            except Exception:
                self._logger.error('Got photo fail: {}'.format(traceback.format_exc()))
            yield res
        except Exception:
            self._logger.error('{} got profile fail {}'.format(self._userid, traceback.format_exc()))

    def _get_contacts(self) -> iter:
        # count=-1意思是全部拉
        contacturl = f'https://data.mail.yahoo.com/xobni/v4/contacts/alpha?count=-1&group_by=1&ymreqid={self.uuid}&appId={self.appid}&mailboxid={self.boxesid}&mailboxId={self.boxesid}&mailboxemail={self._userid}&mailboxtype=FREE'
        try:
            html = self._ha.getstring(contacturl,headers="""
            accept: application/json
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9
            origin: https://mail.yahoo.com
            referer: https://mail.yahoo.com/
            sec-fetch-dest: empty
            sec-fetch-mode: cors
            sec-fetch-site: same-site
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
            x_oath_ns: yahoo""")
            contactdata: dict = json.loads(html)
            if contactdata['count'] == 0:
                return
            contact_all = CONTACT(self._clientid, self.task, self.task.apptype)
            contactlist = contactdata['contact_rank_list']
            for contactrank in contactlist:
                contacts = contactrank['contacts']
                for line_one in contacts:
                    contactid = line_one.get('id')
                    if contactid is None:
                        continue
                    contact_one = CONTACT_ONE(self._userid, contactid,
                                              self.task, self.task.apptype)
                    contact_one.nickname = line_one.get('name')
                    endpoints: list = line_one['endpoints']
                    for info in endpoints:
                        if info.__contains__('ep'):
                            ep: str = info['ep']
                            if ep.startswith('smtp:'):
                                contact_one.email = ep[5:]
                            elif ep.startswith('tel:'):
                                contact_one.phone = ep[3:]
                    contact_all.append_innerdata(contact_one)
            if contact_all.innerdata_len == 0:
                return
            else:
                yield contact_all
        except Exception:
            self._logger.error("Get contact error, err: {}".format(
                traceback.format_exc()))
            return
