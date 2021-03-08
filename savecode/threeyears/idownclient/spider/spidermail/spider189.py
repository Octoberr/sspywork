"""
189邮箱爬虫
create by judy 2018/11/26

update by judy 2019/03/06
统一更改为ha

补齐了注册，在线监测，退出登录接口
update by judy 2019/03/21
"""
import binascii
import datetime
import json
import random
import re
import time
import traceback
import pytz

import requests
from commonbaby.httpaccess import ResponseIO
from commonbaby.helpers import helper_str
from Crypto.Cipher import PKCS1_v1_5 as Cipher_PKCS1_v1_5
from Crypto.PublicKey import RSA

from datacontract.idowndataset.task import Task, ECommandStatus
from idownclient.clientdatafeedback import CONTACT_ONE, CONTACT, EML, Folder, PROFILE
from idownclient.spider.appcfg import AppCfg
from .spidermailbase import SpiderMailBase


class Spider189(SpiderMailBase):

    def __init__(self, tsk: Task, appcfg: AppCfg, clientid):
        super(Spider189, self).__init__(tsk, appcfg, clientid)
        self._usragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)' \
                         ' Chrome/70.0.3538.102 Safari/537.36'
        self._headers = {
            'User-Agent': self._usragent,
            # 'X-Forwarded-For': '%s.%s.%s.%s' % (
            #     random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        }
        self._public_key = None
        self._index_html: str = None

    def _get_rsa_string(self, text: str):
        keyPub = RSA.importKey(self._public_key)  # import the public key
        cipher = Cipher_PKCS1_v1_5.new(keyPub)
        cipher_text = cipher.encrypt(text.encode())  # now we have the cipher
        b16_text = binascii.b2a_hex(cipher_text)
        outtext = b16_text.decode('utf-8')
        return outtext

    def _check_registration(self):
        """
        这个189没法检测账号是否注册
        :return:
        """
        self._write_task_back(ECommandStatus.Succeed, "189邮箱无法检测账号是否注册")
        return

    def _online_check(self):
        """
        检测账号是否在线
        :return:
        """
        return False

    def _logout(self):
        """
        退出登录
        :return:
        """
        logout_res = False

        url = "https://webmail30.189.cn/w2/logon/unifyPlatformLogout.do"

        querystring = {"puserId": "", "uuserId": "1100160976945",
                       "noCache": f"0.{''.join([str(random.choice(range(10))) for _ in range(16)])}"}

        headers = {
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Connection': "keep-alive",
            'Cookie': self.task.cookie,
            'Host': "webmail30.189.cn",
            'Pragma': "no-cache",
            'Referer': "https://webmail30.189.cn/w2/logon/signOn.do",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"
        }
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            response.encoding = 'utf-8'
            res_text = response.text
            if '退出登录' in res_text and '重新登录' in res_text:
                logout_res = True
                self._logger.info("退出登录成功")
        except:
            self._logger.error(f"Error logout in 189, err:{traceback.format_exc()}")
        return logout_res

    def _sms_login(self) -> bool:
        res = False
        try:
            s = requests.session()
            s.headers.update(self._headers)
            s.get('https://webmail30.189.cn/w2/')
            check_phone_url = 'https://open.e.189.cn/api/logbox/oauth2/smsNeedcaptcha.do'
            check_data = {
                'mobile': '{RSA}' + self._get_rsa_string(self.task.phone),
                'appKey': '189mail'
            }
            check_res = s.post(check_phone_url, data=check_data)
            if check_res.text != '1':
                self._logger.error("The Phone number is invalid, or may be need picture code.")
                return res
            # 发验证码前的判断
            need_captcha_url = 'https://open.e.189.cn/api/logbox/oauth2/smsNeedcaptcha.do'
            need_captcha_res = s.post(need_captcha_url, data=check_data)
            if need_captcha_res.text != '1':
                self._logger.error("Cant send vertifycode anymore!")
                return res
            # 发送验证码
            send_sms_code_url = 'https://open.e.189.cn/api/logbox/oauth2/web/sendSmsCode.do'
            send_sms_code_data = {
                'mobile': '{RSA}' + self._get_rsa_string(self.task.phone),
                'appKey': '189mail',
                'captchaToken': '',
                'validateCode': '',
            }
            send_sms_code_res = s.post(send_sms_code_url, send_sms_code_data)
            send_sms_code_res_text = json.loads(send_sms_code_res.text)
            if send_sms_code_res_text.get('msg') != 'success':
                self._logger.error("Send vercode failed!")
                return res
            vercode = self._get_vercode()
            login_submit_url = 'https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do'
            login_submit_heades = {
                "Host": 'open.e.189.cn',
                "Origin": 'https://open.e.189.cn',
                "Referer": 'https://open.e.189.cn/api/logbox/oauth2/unifyAccountLogin.do?appId=189mail&version=v1.0&clientType=10010&paras=3297EEE6060FFB0FEC4DAD25767C33BD0114B673283033EE13676681A75BA3EF0A7A92E41D3CB3B206A89E21F3F799DF21A7B1B5B4B4863BBE11BAB44B93F5A31255EA680C3231E49AC0DFFEF1F998CCC814CED67A0D21C461002C591A46A043928E8E1F8C3C6EF928CAEB735BA84D028161D21655ACC3D25A0544DF27F76060EDE880805266BAD125ABC3B10E0D5D6AAFA8C3967FED093480618BC30B148FBB5323E0AC8B6CCC025CE7B7A9507D5FEF&sign=66EA9E7F26A9B3C1D30AD7918F2938B4D712DABC&format=redirect'
            }
            s.headers.update(login_submit_heades)
            login_submit_data = {
                'appKey': "189mail",
                'accountType': "01",
                'userName': self.task.phone,
                'password': vercode,
                'validateCode': "",
                'captchaToken': "0ed855e01e4643eea5fff45b901136a2jpt2owd8",
                'returnUrl': "https://webmail30.189.cn/w2/logon/unifyPlatformLogonReturn.do",
                'mailSuffix': "@189.cn",
                'dynamicCheck': "TRUE",
                'clientType': "10010",
                'cb_SaveName': "0",
                'isOauth2': "false",
                'state': ""
            }
            login_submit_res = s.post(login_submit_url, data=login_submit_data)
            login_submit_text = json.loads(login_submit_res.text)
            if login_submit_text.get('toUrl') is None:
                self._logger.error("Send login info failed!")
                return res
            tourl = login_submit_text.get('toUrl')
            # 跳转1
            news = requests.session()
            news.headers.update(self._headers)
            news.get('https://webmail30.189.cn/w2/')
            news.get(tourl)
            newcookiedict = news.cookies.get_dict()
            newcookiestr = ';'.join([str(x) + '=' + str(y) for x, y in newcookiedict.items()])
            self.task.cookie = newcookiestr
            # 检查cookie的有效性
            res = self._cookie_login()
        except Exception:
            self._logger.log(f'Sms login error, err:{traceback.format_exc()}')
        finally:
            return res

    def _pwd_login(self) -> bool:
        res = False
        # re_account = re.compile('\d+')
        # _account = re_account.findall(self.task.account)[0]
        try:
            # s = requests.session()
            # s.headers.update(self._headers)
            # response = s.get('https://webmail30.189.cn/w2/')
            # res_text = response.text
            # # 需要去拿两个id,paramId和captchaToken
            # re_pmid = re.compile(r'var paramId = "(.+?)";')
            # f_pmid = re_pmid.search(res_text)
            # if f_pmid:
            #     pmid = f_pmid.group(1)
            # re_capt = re.compile(r'<input type="hidden" name="captchaToken" value="(.+?)" tabindex="-1">')
            # f_capt = re_capt.search(res_text)
            # if f_capt:
            #     capt = f_capt.group(1)
            s = requests.session()
            unify_login_url = 'https://webmail30.189.cn/w2/logon/UnifyLogin.do'
            headers = {
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Connection': 'keep-alive',
                    'Host': 'webmail30.189.cn',
                    'Referer': 'https://webmail30.189.cn/w2/',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
            }
            response_url = s.get(unify_login_url, headers=headers).text

            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Host': 'open.e.189.cn',
                'Referer': 'https://webmail30.189.cn/',
                'Sec-Fetch-Dest': 'iframe',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
            }
            html = s.get(response_url, headers=headers).text
            paramid = re.search(r'var paramId = "(.*?)"', html).group(1)
            lt = re.search(r'var lt = "(.*?)"', html).group(1)
            reqid = re.search(r'var reqId = "(.*?)"', html).group(1)
            captcha_token = re.search(r'name=\'captchaToken\' value=\'(.*?)\'', html).group(1)
            return_url = re.search(r'returnUrl = \'(.*?)\'', html).group(1)

            encrypt_conf_url = 'https://open.e.189.cn/api/logbox/config/encryptConf.do'
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Host': 'open.e.189.cn',
                'Origin': 'https://open.e.189.cn',
                'Referer': response_url,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
            }
            data = {'appId': '189mail'}
            encrypt_conf = s.post(encrypt_conf_url, data=data, headers=headers).text
            pre = helper_str.substring(encrypt_conf, '"pre":"', '"')
            pubkey = helper_str.substring(encrypt_conf, '"pubKey":"', '"')
            self._public_key = '-----BEGIN RSA PUBLIC KEY-----' + '\n' + pubkey + '\n' + '-----END RSA PUBLIC KEY-----'
            needcaptcha_url = 'https://open.e.189.cn/api/logbox/oauth2/needcaptcha.do'
            needcaptcha_data = {
                'accountType': '01',
                'userName': pre + self._get_rsa_string(self.task.account),
                'appKey': '189mail'
            }
            needcaptcha_res = s.post(needcaptcha_url, data=needcaptcha_data)
            if needcaptcha_res.text != '0':
                self._logger.error("Login too often, please try again later!")
                self._write_task_back(ECommandStatus.Failed, "登陆太频繁需要输入图片验证码，请稍后重试")
                self._write_log_back("登陆太频繁需要输入图片验证码，请稍后重试")
                return res
            login_submit_url = 'https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do'
            login_submit_data = {
                'appKey': "189mail",
                'accountType': "01",
                'userName': pre + self._get_rsa_string(self.task.account),
                'password': pre + self._get_rsa_string(self.task.password),
                'validateCode': "",
                'captchaToken': captcha_token,
                'returnUrl': return_url,
                'mailSuffix': "@189.cn",
                'dynamicCheck': "FALSE",
                'clientType': "10010",
                'cb_SaveName': "0",
                'isOauth2': "false",
                'state': "",
                'paramId': paramid,
            }
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Host': 'open.e.189.cn',
                'lt': lt,
                'REQID': reqid,
                'Origin': 'https://open.e.189.cn',
                'Referer': response_url,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
            }
            login_submit_res = s.post(login_submit_url, data=login_submit_data, headers=headers)
            login_submit_text = json.loads(login_submit_res.text)
            if login_submit_text.get('toUrl') is None:
                self._logger.error("Send login info failed!")
                return res
            tourl = login_submit_text.get('toUrl')
            # 跳转1
            # news = requests.session()
            # news.headers.update(self._headers)
            # news.get('https://webmail30.189.cn/w2/')
            # news.get(tourl)
            # newcookiedict = news.cookies.get_dict()
            # newcookiestr = ';'.join([str(x) + '=' + str(y) for x, y in newcookiedict.items()])
            # self.task.cookie = newcookiestr
            s.get(tourl)
            s.get('https://webmail30.189.cn/w2/logon/signOn.do?t={}'.format(
                int(datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)
            ))
            cookiedict = s.cookies.get_dict()
            cookiestr = ';'.join([str(x) + '=' + str(y) for x, y in cookiedict.items()])
            self.task.cookie = cookiestr
            # 检查cookie的有效性
            res = self._cookie_login()
        except Exception as ex:
            self._logger.error(f"Login error, err:{traceback.format_exc()}")
            self._write_log_back("账密登录失败: {}".format(ex.args))
        finally:
            return res

    def _cookie_login(self) -> bool:
        res = False
        t = int(datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)
        try:
            start_url = 'https://webmail30.189.cn/w2/'
            s = requests.session()
            s.headers.update(self._headers)
            s.get(start_url)
            login_url = f'https://webmail30.189.cn/w2/logon/signOn.do?t={t}'
            s.headers.update({'Cookie': self.task.cookie})
            r = s.get(login_url)
            res_text = r.text
            if '收件箱' in res_text and '退出' in res_text:
                res = True
                self._index_html = res_text
                self._ha._managedCookie.add_cookies('189.cn', self.task.cookie)
        except Exception:
            self._logger.error(f'Cookie login error, err:{traceback.format_exc()}')
        finally:
            return res

    def _get_profile(self):
        url = 'https://webmail30.189.cn/w2/option/showAccount.do'
        now_time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
        headers = {
            'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
            'Accept': "application/json, text/javascript, */*; q=0.01",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Connection': "keep-alive",
            'Content-Length': "27",
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
            'Cookie': self.task.cookie,
            'csId': "3cf18c9d43a2c30e59805d3c3d6ee122",
            'Host': "webmail30.189.cn",
            'Origin': "https://webmail30.189.cn",
            'Pragma': "no-cache",
            'Referer': f"https://webmail30.189.cn/w2/logon/signOn.do?t={int(now_time*1000)}",
            'Sec-Fetch-Mode': "cors",
            'Sec-Fetch-Site': "same-origin",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36",
            'X-Requested-With': "XMLHttpRequest"
        }
        data = {'noCache': f'0.2735603709650913{random.randint(0, 9)}'}
        try:
            response = requests.post(url, headers=headers, data=data)
            if response.status_code == 200:
                res_text = response.text
                res_json = json.loads(res_text)
                userid = res_json.get('accountEmail')
                self._userid = userid + '@189.cn'
                p_data = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
                if self.task.account is None:
                    self.task.account = self._userid  # 目前在去重的这个方法里，account是不能为空的
                email = userid + '@189.cn'
                p_data.email = email
                # 这里可以拿到头像的base64，不过为了避免节外生枝所以还是先注释掉
                # headpic = res_json.get('smtpOpenUrl')
                yield p_data
        except:
            self._logger.info(f"Get profile error, err:{traceback.format_exc()}")

    def _get_contacts(self) -> iter:
        pagenum = 1
        error_times = 0  # 防止一直出错，出现死循环,允许尝试5次
        contact_url = 'https://webmail30.189.cn/w2/contact/showManList.do'
        contact_headers = {
            'Accept': "application/json, text/javascript, */*; q=0.01",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Connection': "keep-alive",
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
            'Cookie': self.task.cookie,
            'Host': "webmail30.189.cn",
            'Origin': "https://webmail30.189.cn",
            'Pragma': "no-cache",
            'Referer': "https://webmail30.189.cn/w2/logon/signOn.do",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
            'X-Requested-With': "XMLHttpRequest",
        }
        contact_all = CONTACT(self._clientid, self.task, self.task.apptype)
        while True:
            try:
                contact_payload = {
                    'noCache': '0.{}'.format(''.join([str(random.choice(range(10))) for _ in range(16)])),
                    'pageNum': f'{pagenum}'
                }
                contact_res = requests.post(contact_url, data=contact_payload, headers=contact_headers)
                contact_json_data = json.loads(contact_res.text)
                real_page = contact_json_data.get('pageNum')
                if real_page is None or real_page < pagenum or len(contact_json_data.get('linkmanList')) == 0:
                    # 联系人获取完成，打破循环
                    break
                for contact_one in self._get_contact(contact_json_data):
                    contact_all.append_innerdata(contact_one)
                pagenum += 1
                time.sleep(1)
            except Exception:
                if error_times >= 5:
                    break
                self._logger.error(f"Get {pagenum} page contact error, err:{traceback.format_exc()}")
                error_times += 1
                time.sleep(3)  # 出错一次睡眠3秒，避免频繁出错导致cookie失效
                continue
        if contact_all.innerdata_len > 0:
            yield contact_all

    def _get_contact(self, contact_data: json) -> iter:
        contact_all = contact_data.get('linkmanList')
        gname_map: dict = contact_data.get('uuidGuuidGnameMap')
        if contact_all is None or len(contact_all) == 0:
            self._logger.error("No contact in this account.")
            return
        for line_one in contact_all:
            contact_id = line_one.get('uuid')
            data_one = CONTACT_ONE(self._userid, contact_id, self.task, self.task.apptype)
            data_one.phone = line_one.get('mobile')
            data_one.email = line_one.get('email')
            data_one.nickname = line_one.get('name')
            data_one.group = gname_map[contact_id][0][0]['groupName']
            yield data_one

    def _get_folders(self) -> iter:
        try:
            re_folder_all = re.compile('<option value="(\d+)">(\w+)</option>')
            if self._index_html is None:
                start_url = 'https://webmail30.189.cn/w2/'
                s = requests.session()
                s.headers.update(self._headers)
                s.get(start_url)
                login_url = 'https://webmail30.189.cn/w2/logon/signOn.do'
                s.headers.update({'Cookie': self.task.cookie})
                r = s.get(login_url)
                res_text = r.text
                if '收件箱' in res_text and 'window.globalValues=' in res_text and '"code":0' in res_text:
                    self._index_html = res_text
            if self._index_html is None or self._index_html == '':
                return
            folder_all = re_folder_all.findall(self._index_html)
            if len(folder_all) == 0:
                return
            for folder_one in folder_all:
                fone = Folder()
                fone.name = folder_one[1]
                fone.folderid = folder_one[0]
                yield fone
        except Exception:
            self._logger.error(f'Get folder error, err:{traceback.format_exc()}')
            return

    def _get_mails(self, folder: Folder) -> iter:
        pagenum = 1
        error_times = 0  # 防止一直出错，出现死循环,允许尝试5次
        url = "https://webmail30.189.cn/w2/mail/listMail.do"
        headers = {
            'Accept': "application/json, text/javascript, */*; q=0.01",
            'Accept-Encoding': "gzip, deflate, br",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Connection': "keep-alive",
            'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
            'Cookie': self.task.cookie,
            'Host': "webmail30.189.cn",
            'Origin': "https://webmail30.189.cn",
            'Pragma': "no-cache",
            'Referer': "https://webmail30.189.cn/w2/logon/signOn.do",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
            'X-Requested-With': "XMLHttpRequest"
        }
        while True:
            try:
                payload = {
                    'noCache': f'0.64658327988{random.randint(10000, 99999)}',
                    'labelId': f'{folder.folderid}',
                    'pageNum': f'{pagenum}'
                }
                mails_res = requests.post(url, data=payload, headers=headers)
                mails_res_json = json.loads(mails_res.text)
                real_page = mails_res_json.get('pageNum')
                if real_page is None or real_page < pagenum or len(mails_res_json.get('mailMap')) == 0:
                    # 当前文件夹邮件获取完成，打破循环
                    break
                for a_mail in self.__get_mails(mails_res_json, folder):
                    yield a_mail
                pagenum += 1
                time.sleep(5)  # 防止查询邮箱的频率过快而被封
            except Exception:
                if error_times > 5:
                    break
                self._logger.error(f'Get {pagenum} mails error, err:{traceback.format_exc()}')
                error_times += 1
                continue

    def __get_mails(self, mails_info: dict, folder: Folder):
        mails = mails_info.get('mailMap')
        if mails is None or len(mails) == 0:
            return
        for k, mail in mails.items():
            try:
                mailid = mail.get('messageId')
                msid = mail.get('msId')
                newmail = mail.get('newMail')
                eml = EML(self._clientid, self.task, self._userid, mailid, folder, self.task.apptype)
                if newmail:
                    eml.state = 0
                else:
                    eml.state = 1
                eml.provider = mail.get('sender')
                sendtime = mail.get('sendDate')
                if sendtime is not None and sendtime != '':
                    eml.sendtime = datetime.datetime.fromtimestamp(sendtime // 1000)
                eml.subject = mail.get('subject')
                eml_info = self.__get_mail_streams(mailid, msid)
                eml.io_stream = eml_info[0]
                eml.stream_length = eml_info[1]
                time.sleep(5)  # 防止取邮件的频率过快
                yield eml
            except Exception:
                self._logger.error(f'Get {mailid} email error, err:{traceback.format_exc()}')
                continue

    def __get_mail_streams(self, mailid, msid):
        url = "https://webmail30.189.cn/w2/downLoadAttachNormal.do"
        querystring = {
            "messageid": mailid,
            "msid": msid,
            "partid": "9999"
        }
        headers = '''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
            Cache-Control: no-cache
            Connection: keep-alive
            Host: webmail30.189.cn
            Pragma: no-cache
            Referer: https://webmail30.189.cn/w2/logon/signOn.do
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36
        '''
        resp = self._ha.get_response(url, headers=headers, params=querystring)
        stream_length = resp.headers.get('Content-Length', 0)
        eml = ResponseIO(resp)
        return eml, stream_length
