"""
QQ邮箱的spider
create by judy
2018/12/26

update qq spider
将邮件下载改为httpaccess
"""
import binascii
import datetime
import hashlib
import random
import re
import time
import traceback
import cv2
import numpy as np

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from sys import platform
from idownclient.config_spiders import webdriver_path_debian, webdriver_path_win

import requests
from bs4 import BeautifulSoup
from commonbaby.httpaccess import ResponseIO
from commonbaby.helpers.helper_str import substring

from idownclient.clientdatafeedback import CONTACT_ONE, CONTACT, EML, Folder, PROFILE, IdownLoginLog_ONE
from .spidermailbase import SpiderMailBase


class SpiderQq(SpiderMailBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderQq, self).__init__(task, appcfg, clientid)
        self._usragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)' \
                         ' Chrome/70.0.3538.102 Safari/537.36'
        self._headers = {
            'User-Agent': self._usragent,
            'X-Forwarded-For': '%s.%s.%s.%s' % (
                random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        }
        self._html = None
        self._sid = None

    def get_md5_string(self, my_string):
        m = hashlib.md5()
        m.update(my_string.encode('utf-8'))
        return m.hexdigest()

    def jcode_b(self, b):
        B = len(b)
        E = 0
        a = (B + 10) % 8
        if a != 0:
            a = 8 - a

    def get_incode_c(self, l_16string):
        b = b''
        for c in range(len(l_16string) // 2):
            s = l_16string[c * 2:c * 2 + 2]
            b += bytearray.fromhex(s)
        return b

    def encryptqqwd(self, password, salt, vcode):
        o = self.get_md5_string(password)
        s = binascii.hexlify(vcode.upper().encode()).decode()
        a = str(int(str(len(s) // 2), 16))
        while len(a) < 4:
            a = "0" + a
        l_16_string = o + salt + a + s
        # print(l_16_string)

    def get_sault(self, txt):
        idx1 = txt.index('(')
        idx2 = txt.index(')')
        txt = txt[idx1 + 1:idx2]
        titems = txt.split(',')
        strsalt = titems[2].strip().strip("'")
        sitems = strsalt.split('\\x')
        bs = ''
        for s in sitems:
            if s is None or s == '':
                continue
            bs = bs + s
        return bs

    def pwdlogin__(self, account, password):
        s = requests.session()
        s.headers.update(self._headers)
        login_index = s.get("https://mail.qq.com/cgi-bin/loginpage")
        # print(s.cookies.get_dict())
        # print(login_index.text)
        re_xlogin_url = re.compile("\<iframe id\=\"login_frame\" name\=\"login_frame\" .+ src\=\"(.+)\"\>\<\/iframe\> ")
        xlogin_url = re_xlogin_url.search(login_index.text)
        if not xlogin_url:
            self._logger.warn("loggin error, xlogin_url is None")
        xlogin = xlogin_url.group(1)
        xlogin_res = s.get(xlogin)
        xlogin_res.encoding = 'utf-8'
        x_res = xlogin_res.text
        re_surl = re.compile("s_url\:\"(.+?)\"")
        surl_res = re_surl.search(x_res)
        surl = surl_res.group(1)
        re_href = re.compile("href\:\"(.+?)\"")
        href_res = re_href.search(x_res)
        href = href_res.group(1)
        re_version = re.compile("version\:\"(.+?)\"")
        version_res = re_version.search(x_res)
        version = version_res.group(1)
        re_appid = re.compile("appid\:encodeURIComponent\(\"(\d+)\"\)")
        appid_res = re_appid.search(x_res)
        appid = appid_res.group(1)
        re_pt_ver_md5 = re.compile("pt_ver_md5\:\"(\w+)\"")
        pt_ver_md5_res = re_pt_ver_md5.search(x_res)
        pt_ver_md5 = pt_ver_md5_res.group(1)
        re_lang = re.compile("lang\:encodeURIComponent\(\"(\d+)\"\)")
        lang_res = re_lang.search(x_res)
        lang = lang_res.group(1)
        re_ptui_version = re.compile("ptui_version\:encodeURIComponent\(\"(\d+)\"\)")
        ptui_version_res = re_ptui_version.search(x_res)
        ptui_version = ptui_version_res.group(1)
        pt_login_sig = s.cookies.get('pt_login_sig')
        login_check_url = f'https://ssl.ptlogin2.qq.com/check?' \
            f'regmaster=&pt_tea=2&pt_vcode=0&uin={account}&' \
            f'appid={appid}&js_ver={ptui_version}&js_type=1&' \
            f'login_sig={pt_login_sig}&u1={surl}&' \
            f'r=0.4375877124053{random.randint(1000, 9999)}&pt_uistyle=25'
        login_check_res = s.get(login_check_url)
        # print(login_check_res.text)
        re_puticheckvc = re.compile("\(.+\)")
        # print(login_check_res.text)
        txt = login_check_res.text
        salt = self.get_sault(txt)
        puticheckvc = re_puticheckvc.search(login_check_res.text)
        if not puticheckvc:
            self._logger.error("登陆失败，可能需要验证码")
            self._write_log_back("登陆失败，可能需要验证码")
        puti_data = eval(puticheckvc.group())
        if len(puti_data) != 5:
            self._logger.error("登陆数据缺少，登陆失败")
        vcode = puti_data[1]  # 验证码
        # salt = puti_data[2]  # 用于密码加密的随机码
        pt_random_salt = puti_data[4]  # 我也不用去关心这是啥了
        en_pwd = self.encryptqqwd(password, salt, vcode)

    def get_ditance(self, target, template):
        """滑动验证码识别"""
        target = abs(255 - target)
        # 模板匹配
        result = cv2.matchTemplate(target, template, cv2.TM_CCOEFF_NORMED)
        mn_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        top_left = max_loc
        # 距离换算(原图680*390,显示280*161), 滑块距离图片边缘约20
        distance = top_left[0] * (280 / 680) - 21
        return distance

    def ease_out_expo(self, x):
        """轨迹函数"""
        if x == 1:
            return 1
        else:
            return 1 - pow(2, -10 * x)

    def get_tracks(self, distance, seconds):
        """输出鼠标路径"""
        tracks = [0]
        offsets = [0]
        for t in np.arange(0.0, seconds, 0.1):
            offset = round(self.ease_out_expo(t / seconds) * distance)
            tracks.append(offset - offsets[-1])
            offsets.append(offset)
        return offsets, tracks

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
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-dev-shm-usage')
            # 修改页面加载策略(normal, eager, none), 不然无头模式下get很慢
            # 本地测试eager很快，但是在vps里面会出现加载不完全的问题，还是使用normal模式
            caps = DesiredCapabilities().CHROME
            # caps["pageLoadStrategy"] = "eager"
            caps["pageLoadStrategy"] = "normal"
            driver = webdriver.Chrome(options=chrome_options, desired_capabilities=caps, executable_path=driver_path)
            wait = WebDriverWait(driver, 10)

            login_url = 'https://mail.qq.com/'
            driver.get(login_url)
            wait.until(EC.presence_of_element_located((By.ID, "login_frame")), message='login_frame not found')
            driver.switch_to.frame('login_frame')
            wait.until(EC.presence_of_element_located((By.ID, "u")), message='u not found')
            wait.until(EC.presence_of_element_located((By.ID, "p")), message='p not found')
            driver.find_element_by_id('u').send_keys(self.task.account)
            driver.find_element_by_id('p').send_keys(self.task.password)
            # 输入完要等一下在点按钮
            time.sleep(1)
            driver.find_element_by_id('login_button').click()
            driver.implicitly_wait(10)
            # 加3秒等待再判断current_url
            time.sleep(3)
            if driver.current_url == login_url:
                retry_count = 0
                driver.switch_to.default_content()
                wait.until(EC.presence_of_element_located((By.ID, "login_frame")), message='login_frame not found')
                driver.switch_to.frame('login_frame')
                wait.until(EC.presence_of_element_located((By.ID, "tcaptcha_iframe")), message='tcaptcha not found')
                driver.switch_to.frame('tcaptcha_iframe')
                while True:
                    # 缺口图
                    element = wait.until(EC.presence_of_element_located((By.ID, "slideBg")), message='slideBg not found')
                    big_url = element.get_attribute('src')
                    img1_b = requests.get(big_url).content
                    img1 = cv2.imdecode(np.asarray(bytearray(img1_b), dtype='uint8'), 0)
                    # 滑块图
                    element = wait.until(EC.presence_of_element_located((By.ID, "slideBlock")), message='slideBlock not found')
                    small_url = element.get_attribute('src')
                    img2_b = requests.get(small_url).content
                    img2 = cv2.imdecode(np.asarray(bytearray(img2_b), dtype='uint8'), 0)
                    # 识别并计算轨迹, 滑动
                    distance = self.get_ditance(img2, img1)
                    element = driver.find_element_by_id('tcaptcha_drag_button')
                    ActionChains(driver).click_and_hold(element).perform()
                    time.sleep(0.5)
                    offsets, tracks = self.get_tracks(distance, 2)
                    for x in tracks:
                        ActionChains(driver).move_by_offset(x, 0).perform()
                    ActionChains(driver).pause(0.5).release().perform()
                    time.sleep(3)
                    if driver.current_url != login_url and self.task.account in driver.page_source:
                        cookies = ''
                        for cookie in driver.get_cookies():
                            cookies = cookies + cookie['name'] + '=' + cookie['value'] + ';'
                        self.task.cookie = cookies
                        res = self._cookie_login()
                        break
                    else:
                        driver.switch_to.default_content()
                        driver.switch_to.frame('login_frame')
                        if 'tcaptcha_iframe' in driver.page_source:
                            # 重试两次
                            retry_count += 1
                            if retry_count >= 3:
                                self._logger.error('Pwd login failed,recognize verification code failed')
                                self._write_log_back("Pwd login failed,recognize verification code failed")
                                break
                            self._logger.info('Slide verification code fail, retry:{}'.format(retry_count))
                            driver.switch_to.frame("tcaptcha_iframe")
                            driver.find_element_by_id('e_reload').click()
                            time.sleep(3)
                            continue
                        else:
                            self._logger.error("Login failed, account or password is wrong, or more validation required")
                            self._write_log_back("登录失败，账密不对或者需要其他验证（手机或者二维码）")
                            break
            else:
                if self.task.account in driver.page_source:
                    cookies = ''
                    for cookie in driver.get_cookies():
                        cookies = cookies + cookie['name'] + '=' + cookie['value'] + ';'
                    self.task.cookie = cookies
                    res = self._cookie_login()
                else:
                    self._logger.error("Pwd login failed, current title {}".format(driver.title))
            driver.quit()
        except Exception as ex:
            self._logger.error("Pwd login error, err: {}".format(ex))
            self._write_log_back("账密登录失败: {}".format(ex.args))
        return res

    def _cookie_login(self) -> bool:
        res = False
        url = "https://mail.qq.com/cgi-bin/login"

        querystring = {"vt": "passport", "vm": "wpt", "ft": "loginpage", "target": ""}

        payload = ""
        headers = {
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache,no-cache",
            'cookie': self.task.cookie,
            'pragma': "no-cache",
            'referer': "https://mail.qq.com/",
            'upgrade-insecure-requests': "1",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        }

        try:
            response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

            index_txt = response.text
            if "设置" in index_txt and "退出" in index_txt and "关联其他QQ邮箱":
                self._html = index_txt
                re_sid = re.compile("sid\=(.+?)\&")
                sid = re_sid.search(self._html)
                self._sid = sid.group(1)
                self._userid = substring(index_txt, '关联其他QQ邮箱">', '<')
                res = True
                # 设置cookie
                self._ha._managedCookie.add_cookies('qq.com', self.task.cookie)
        except Exception:
            self._logger.error(f"Cookie login error, err:{traceback.format_exc()}")
        finally:
            return res

    def _get_profile(self) -> iter:
        if self._html is None:
            url = "https://mail.qq.com/cgi-bin/login"

            querystring = {"vt": "passport", "vm": "wpt", "ft": "loginpage", "target": ""}

            payload = ""
            headers = {
                'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                'accept-encoding': "gzip, deflate, br",
                'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
                'cache-control': "no-cache,no-cache",
                'cookie': self.task.cookie,
                'pragma': "no-cache",
                'referer': "https://mail.qq.com/",
                'upgrade-insecure-requests': "1",
                'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
            }

            try:
                response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

                index_txt = response.text
                if "设置" in index_txt and "退出" in index_txt and "关联其他QQ邮箱":
                    self._logger.info("登陆成功，cookie有效")
                    self._html = index_txt
                    re_sid = re.compile("sid\=(.+?)\&")
                    sid = re_sid.search(self._html)
                    self._sid = sid.group(1)
            except Exception:
                self._logger.error(f"Get profile error, err:{traceback.format_exc()}")
        try:
            re_userid = re.compile("\<span id\=\"useraddr\" .*?\>(.+?)\<\/span\>")
            s_userid = re_userid.search(self._html)
            userid = s_userid.group(1)
            self._userid = userid
            re_username = re.compile("\<b id\=\"useralias\"\>(.+?)\<\/b\>")
            s_username = re_username.search(self._html)
            username = s_username.group(1)
            p_data = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
            p_data.nickname = username
            yield p_data
        except Exception:
            self._logger.error(f"Get profile data error, err:{traceback.format_exc()}")

    def _get_contacts(self) -> iter:
        url = "https://mail.qq.com/cgi-bin/laddr_list?" \
              "sid={}&operate=view&t=contact&view=normal&loc=frame_html,,,23".format(self._sid)
        headers = {
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache,no-cache",
            'cookie': self.task.cookie,
            'pragma': "no-cache",
            'referer': "https://mail.qq.com/cgi-bin/frame_html?sid=FknE0k6DwoitPnIu&r=95be65ae9c260d6737411fa709d80de3",
            'upgrade-insecure-requests': "1",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        }

        try:
            response = requests.request("GET", url, headers=headers)
            contact_list = response.text
            re_all_name = re.compile("\<span class\=\"name tf\"\>(.+?)\<\/span\>")
            allname = re_all_name.findall(contact_list)
            re_all_email = re.compile("\<span class\=\"email tf\">(.+?)\<\/span\>")
            allemail = re_all_email.findall(contact_list)
            contact_all = CONTACT(self._clientid, self.task, self.task.apptype)
            for c_one in range(len(allname)):
                if c_one == 0:
                    continue
                contact_one = CONTACT_ONE(self._userid, allemail[c_one], self.task, self.task.apptype)
                contact_one.nickname = allname[c_one]
                contact_one.email = allemail[c_one]
                contact_all.append_innerdata(contact_one)
            if contact_all.innerdata_len > 0:
                yield contact_all
        except Exception:
            self._logger.error(f"Get contacts data error, err:{traceback.format_exc()}")

    def _get_loginlog(self) -> iter:
        pagenum = 1
        headers = {
            'accept': "*/*",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache,no-cache",
            'cookie': self.task.cookie,
            'pragma': "no-cache",
            'referer': "https://mail.qq.com/zh_CN/htmledition/ajax_proxy.html?mail.qq.com&v=140521",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        }
        while pagenum < 6:
            try:
                log_url = "https://mail.qq.com/cgi-bin/help_static_login?" \
                          "sid={}&type=0&page={}&loc=%3C![CDATA[]]%3E&" \
                          "r=0.37144177025{}".format(self._sid, pagenum, random.randint(1000, 9999))
                response = requests.request("GET", log_url, headers=headers)
                log_text = response.text
                for log_o in self.__parse_login_log(log_text):
                    yield log_o
                pagenum += 1
            except Exception:
                self._logger.error(f"Get login log data error, err:{traceback.format_exc()}")

    def __parse_login_log(self, log_text):
        s = BeautifulSoup(log_text, "lxml")
        alltrs = s.find_all('tr')
        log_date = None
        for tr in alltrs[1:]:
            all_td = tr.find_all('td')
            if len(all_td) == 1:
                get_date = all_td[0].string
                log_date = get_date
            elif len(all_td) == 4:
                login_time = self.__formate_datetime(log_date, all_td[0].string)
                if login_time is None:
                    continue
                login_one = IdownLoginLog_ONE(self.task, self.task.apptype, self._userid)
                # ip和登陆地址无法获取
                login_one.ip = 'cant access'
                login_one.region = 'cant access'
                login_one.logintime = login_time
                login_country = all_td[1].string
                login_one.region = login_country
                login_type = all_td[2].string
                login_one.logintype = login_type
                sebei = all_td[3].string
                if sebei is not None:
                    login_device = sebei
                    login_one.platform = login_device
                yield login_one

    def __formate_datetime(self, unf_date, unf_time):
        today = datetime.date.today()
        if unf_date == '今天':
            log_date = str(today)
        elif unf_date == '昨天':
            log_date = str(today - datetime.timedelta(days=1))
        elif unf_date == '前天':
            log_date = str(today - datetime.timedelta(days=2))
        else:
            a = time.strptime(unf_date, '%m月%d日')
            if a.tm_mon > today.month:
                get_year = today.year - 1
            else:
                get_year = today.year
            log_date = f"{get_year}-{a.tm_mon}-{a.tm_mday}"
        if unf_time.startswith("上午"):
            datestr = unf_time[2:]
        elif unf_time.startswith("中午"):
            if int(unf_time[2:4]) > 10:
                datestr = unf_time[2:]
            elif int(unf_time[2:4]) < 3:
                datestr = f"{int(unf_time[2:4]) + 12}{unf_time[-3:]}"
        elif unf_time.startswith("下午"):
            datestr = f"{int(unf_time[2:4]) + 12}{unf_time[-3:]}"
        elif unf_time.startswith("晚上"):
            datestr = f"{int(unf_time[2:4]) + 12}{unf_time[-3:]}"
        else:
            self._logger.info(f"Unrecorded time {unf_time}")
            return None
        now_date = f"{log_date} {datestr + ':00'}"
        return now_date

    def _get_folders(self) -> iter:
        url = "https://mail.qq.com/cgi-bin/folderlist?t=folderlist_setting&s=null&info=true&sid={}".format(self._sid)
        headers = {
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache,no-cache",
            'cookie': self.task.cookie,
            'pragma': "no-cache",
            'referer': "https://mail.qq.com/",
            'upgrade-insecure-requests': "1",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
        }
        try:
            response = requests.request("GET", url, headers=headers)
            re_allfolder = re.compile('<span\s*?id="folder_(\d+?)_[^"]*?"\s*?>\s*?(.*?)</span')
            all_folder = re_allfolder.findall(response.text)
            for folderinfo in all_folder:
                id = folderinfo[0]
                if id == '11':
                    continue
                name = folderinfo[1]
                folder_one = Folder()
                folder_one.folderid = id
                folder_one.name = name
                yield folder_one
        except Exception:
            self._logger.error(f"Get folder data error, err:{traceback.format_exc()}")

    def _get_mails(self, folder: Folder) -> iter:
        pagenum = 0
        pagecount = 10  # 初始值随便给
        nextpage = True
        headers = {
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache,no-cache",
            'cookie': self.task.cookie,
            'pragma': "no-cache",
            'referer': "https://mail.qq.com/cgi-bin/frame_html?sid=LHMRQd34yoCnbiJ_&r=c8d8fa46b4a22664132d900770e7f25f",
            'upgrade-insecure-requests': "1",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        }
        while pagenum <= pagecount or nextpage is True:
            if nextpage is False:
                break
            url = "https://mail.qq.com/cgi-bin/mail_list"

            querystring = {"sid": self._sid, "folderid": f"{folder.folderid}", "folderkey": f"{folder.folderid}",
                           "page": f"{pagenum}", "s": "inbox",
                           "topmails": "0", "showinboxtop": "1", "ver": "952875.0", "cachemod": "maillist",
                           "cacheage": "7200", "r": ""}

            response = requests.request("GET", url, headers=headers, params=querystring)
            res_text = response.text
            # re_allcount = re.compile("\<script \>document\.write\((\d+) \+ 1\)\;\<\/script\> 页        \&nbsp\;")
            # pagecount = re_allcount.search(res_text).group(1)
            re_mail_info = re.compile("\<nobr t\=\"6\" mailid=\"(.+?)\"")
            all_mail_info = re_mail_info.findall(res_text)
            for mailone in all_mail_info:
                eml = EML(self._clientid, self.task, self._userid, mailone, folder, self.task.apptype)
                eml_info = self.download_mail(mailone)
                eml.io_stream = eml_info[0]
                eml.stream_length = eml_info[1]
                time.sleep(1)
                yield eml
            if "下一页" not in res_text or "nextpage" not in res_text:
                nextpage = False
            pagenum += 1

    def download_mail(self, mailid):
        url = "https://mail.qq.com/cgi-bin/readmail?" \
              "sid={}&mailid={}&action=downloademl".format(self._sid, mailid)
        headers = '''
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9,en;q=0.8
            cache-control: no-cache,no-cache
            pragma: no-cache
            referer: https://mail.qq.com/
            upgrade-insecure-requests: 1
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36
        '''
        # response = requests.request("GET", url, headers=headers, stream=True)
        # response.raw.decode_content = True
        # return response.raw
        # eml = self._ha.get_response_stream(url, headers=headers)
        # return eml
        resp = self._ha.get_response(url, headers=headers)
        stream_length = resp.headers.get('Content-Length', 0)
        eml = ResponseIO(resp)
        return eml, stream_length
