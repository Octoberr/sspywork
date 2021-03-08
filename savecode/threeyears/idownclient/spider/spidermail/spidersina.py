"""
验证手机号是否注册了新浪邮箱
20181023
add sina spider by judy
2018/12/26

update by judy 2019/03/07
统一下载使用ha
"""
import base64
import binascii
import datetime
import json
import random
import re
import time
import traceback
import pytz
from urllib import parse

import requests
import rsa
from commonbaby.httpaccess import ResponseIO

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from idownclient.clientdatafeedback import CONTACT_ONE, CONTACT, EML, Folder, PROFILE
from .spidermailbase import SpiderMailBase


class SpiderSina(SpiderMailBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderSina, self).__init__(task, appcfg, clientid)
        self._usragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)' \
                         ' Chrome/70.0.3538.102 Safari/537.36'
        self._headers = {
            'User-Agent': self._usragent,
            'X-Forwarded-For': '%s.%s.%s.%s' % (
                random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        }
        self._html = None

    def _check_registration(self):
        """
        查询手机号是否注册了新浪邮箱
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            t1 = int(datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)
            url = f'https://mail.sina.com.cn/register/chkmail.php'
            headers = f"""
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 43
Content-type: application/x-www-form-urlencoded;charset=UTF-8
Host: mail.sina.com.cn
Origin: https://mail.sina.com.cn
Pragma: no-cache
Referer: https://mail.sina.com.cn/register/regmail.php
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"""
            postdata = f'mail={self.task.phone}%40sina.cn&ts={t1}'
            response = self._ha.getstring(url, headers=headers, req_data=postdata)

            if 'sg":"mailname_exists"' in response:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return

    def _get_rsa_string(self, message: str, rsadata: str):
        weibo_rsa_e = 65537
        key = rsa.PublicKey(int(rsadata, 16), weibo_rsa_e)
        encropy_pwd = rsa.encrypt(message.encode(), key)
        b16_content = binascii.b2a_hex(encropy_pwd)
        outtext = b16_content.decode('utf-8')
        return outtext

    def _get_account_string(self, account):
        a = base64.b64encode(parse.quote_plus(account).encode())
        return a.decode()

    def _pwd_login(self) -> bool:
        res = False
        try:
            s = requests.session()
            s.headers.update(self._headers)
            s.get('https://mail.sina.com.cn/')
            prelogin_url = "https://login.sina.com.cn/sso/prelogin.php"
            prelogin_querystring = {"entry": "cnmail", "callback": "sinaSSOController.preloginCallBack",
                                    "su": self._get_account_string(self.task.account), "rsakt": "mod",
                                    "client": "ssologin.js(v1.4.19)",
                                    "_": str(int(datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000))}
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Host': 'login.sina.com.cn',
                'Referer': 'https://mail.sina.com.cn/',
                'Sec-Fetch-Dest': 'script',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-site',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
            }
            prelogin_response = requests.request("GET", prelogin_url, params=prelogin_querystring, headers=headers)
            re_predata = re.compile('\{.+\}')
            s_predata = re_predata.search(prelogin_response.text)
            if not s_predata:
                return res
            predata = s_predata.group()
            predata_json = json.loads(predata)
            if predata_json.get('retcode') != 0:
                return res
            passstring = "{}\t{}\n{}".format(predata_json.get('servertime'), predata_json.get('nonce'),
                                             self.task.password)
            now_time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
            login_url = f'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)' \
                f'&_={int(now_time * 1000)}'
            login_payload = {
                'entry': "freemail",
                'gateway': "1",
                'from': "",
                'savestate': "0",
                'qrcode_flag': "false",
                'useticket': "0",
                'pagerefer': "",
                'su': "{}".format(self._get_account_string(self.task.account)),
                'service': "sso",
                'servertime': f"{predata_json.get('servertime')}",
                'nonce': f"{predata_json.get('nonce')}",
                'pwencode': "rsa2",
                'rsakv': f"{predata_json.get('rsakv')}",
                'sp': "{}".format(self._get_rsa_string(passstring, predata_json.get('pubkey'))),
                'sr': "1440*900",
                'encoding': "UTF-8",
                'cdult': "3",
                'domain': "sina.com.cn",
                'prelt': "219",
                'returntype': "TEXT",
            }
            login_res = s.post(login_url, data=login_payload)
            json_text = json.loads(login_res.text)
            retcode = json_text.get('retcode')
            if retcode != '0':
                reason = json_text.get('reason')
                self._logger.error(repr(reason))
                self._write_log_back(repr(reason))
                return res
            curl_urls = json_text.get('crossDomainUrlList')
            if curl_urls is None or curl_urls == '':
                self._logger.error("Login failed, account or password is wrong!")
                self._write_log_back("登录失败，账号密码可能有误")
                return res
            for c_url in curl_urls:
                s.get(c_url)
            index_url = f'https://mail.sina.com.cn/cgi-bin/sla.php?' \
                f'a={int(now_time * 1000)}&b={int(now_time * 1000)}&c=0&ssl=0'
            s.get(index_url)
            newcookiedict = s.cookies.get_dict()
            newcookiestr = ';'.join([str(x) + '=' + str(y) for x, y in newcookiedict.items()])
            self.task.cookie = newcookiestr
            # 验证拿到cookie的有效性
            res = self._cookie_login()
        except Exception as ex:
            self._logger.error(f"PWD login error, err:{traceback.format_exc()}")
            self._write_log_back("账密登录失败: {}".format(ex.args))
        finally:
            return res

    def _cookie_login(self) -> bool:
        res = False
        try:
            url = "http://m0.mail.sina.com.cn/classic/index.php"
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Cookie': self.task.cookie,
                'Host': 'm0.mail.sina.com.cn',
                'Pragma': 'no-cache',
                'Referer': 'https://m0.mail.sina.com.cn/classic/index.php',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
            }
            response = requests.request("GET", url, headers=headers)
            res_text = response.text
            if "您好" in res_text and "退出" in res_text:
                res = True
                self._html = res_text
                self._ha._managedCookie.add_cookies('sina.com.cn', self.task.cookie)
        except Exception:
            self._logger.error(f"Cookie Login error, err:{traceback.format_exc()}")
        finally:
            return res

    def _get_profile(self) -> iter:
        try:
            if self._html is None:
                url = "http://m0.mail.sina.com.cn/classic/index.php"
                headers = {
                    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    'Accept-Encoding': "gzip, deflate",
                    'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
                    'Cache-Control': "no-cache",
                    'Cookie': self.task.cookie,
                    'Host': "m0.mail.sina.com.cn",
                    'Pragma': "no-cache",
                    'Proxy-Connection': "keep-alive",
                    'Upgrade-Insecure-Requests': "1",
                    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",

                }
                response = requests.request("GET", url, headers=headers)
                res_text = response.text
                if "您好" in res_text and "设置" in res_text and "收件夹" in res_text:
                    print("登陆成功， cookie 有效")
                    print(res_text)
                    self._html = res_text
            re_userid = re.compile('"uid"\:"(.*?\@sina\.com)"')
            re_username = re.compile('"username":"(.*?)"')
            userid = re_userid.search(self._html)
            username = re_username.search(self._html)
            if not userid:
                self._userid = self.uname_str
            else:
                self._userid = userid.group(1)
            pdata = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
            if username:
                pdata.nickname = username.group(1)
            yield pdata
        except Exception:
            self._logger.error(f"Get profile error, err:{traceback.format_exc()}")

    def _get_contacts(self) -> iter:
        url = "http://m0.mail.sina.com.cn/wa.php"
        querystring = {"a": "list_contact"}
        payload = {
            'gid': '0',
            'sort_item': 'letter',
            'sort_type': 'desc'
        }
        headers = {
            'Accept': "*/*",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Content-type': "application/x-www-form-urlencoded;charset=UTF-8",
            'Cookie': self.task.cookie,
            'Host': "m0.mail.sina.com.cn",
            'Origin': "http://m0.mail.sina.com.cn",
            'Pragma': "no-cache",
            'Proxy-Connection': "keep-alive",
            'Referer': "http://m0.mail.sina.com.cn/classic/index.php",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/71.0.3578.98 Safari/537.36"
        }
        try:
            response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
            res_json_text = json.loads(response.text)
            if res_json_text.get('errno') != 0:
                self._logger.error("Get contact list error!")
                return
            contacts_data = res_json_text.get('data')
            if contacts_data is None:
                self._logger.error("No contacts data")
                return
            contacts = contacts_data.get('contact')
            if contacts is None or len(contacts) == 0:
                self._logger.error("No contacts data")
                return
            con_all = CONTACT(self._clientid, self.task, self.task.apptype)
            for con in contacts:
                uid = con.get('uid')
                name = con.get('name')
                email = con.get('email')
                con_one = CONTACT_ONE(self._userid, uid, self.task, self.task.apptype)
                con_one.nickname = name
                con_one.email = email
                con_all.append_innerdata(con_one)
            if con_all.innerdata_len > 0:
                yield con_all
        except Exception:
            self._logger.error(f"Got contacts error, err:{traceback.format_exc()}")

    def _get_folders(self) -> iter:
        url = "http://m0.mail.sina.com.cn/wa.php"
        querystring = {"a": "list_folder", "calltype": "auto"}
        payload = {
            'sactioncount': 'AppMailIndex5_lt1:1, mailList_new_20: 431'
        }
        headers = {
            'Accept': "*/*",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Content-type': "application/x-www-form-urlencoded;charset=UTF-8",
            'Cookie': self.task.cookie,
            'Host': "m0.mail.sina.com.cn",
            'Origin': "http://m0.mail.sina.com.cn",
            'Pragma': "no-cache",
            'Proxy-Connection': "keep-alive",
            'Referer': "http://m0.mail.sina.com.cn/classic/index.php",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/71.0.3578.98 Safari/537.36"
        }
        try:
            response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
            res_json = json.loads(response.text)
            if res_json.get('errno') != 0:
                self._logger.error("Got folder errror!")
                return
            folders_data = res_json.get('data')
            for folder in folders_data:
                id = folder.get('id')
                fname = folder.get('fname')
                if id == 'all':
                    # 分了文件夹就不用再下载所有邮件了
                    continue
                f = Folder()
                f.name = repr(fname)
                f.folderid = id
                yield f
        except Exception:
            self._logger.error(f"Get folder info error, err:{traceback.format_exc()}")

    def _get_mails(self, folder: Folder) -> iter:
        error_times = 0
        current_page = 1
        all_pagenum = 1000
        mail_url = 'http://m0.mail.sina.com.cn/wa.php?a=list_mail'
        headers = {
            'Accept': "*/*",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Content-Length': "98",
            'Content-type': "application/x-www-form-urlencoded;charset=UTF-8",
            'Cookie': self.task.cookie,
            'Host': "m0.mail.sina.com.cn",
            'Origin': "http://m0.mail.sina.com.cn",
            'Pragma': "no-cache",
            'Proxy-Connection': "keep-alive",
            'Referer': "http://m0.mail.sina.com.cn/classic/index.php",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        }
        while True:
            try:
                if current_page >= all_pagenum:
                    break
                payload_data = {
                    'fid': '{}'.format(folder.folderid),
                    'order': 'htime',
                    'sorttype': 'desc',
                    'type': '0',
                    'pageno': '{}'.format(current_page),
                    'tag': '-1',
                    'webmail': '1'
                }
                response = requests.request("POST", mail_url, data=payload_data, headers=headers)
                mail_data_json = json.loads(response.text)
                if not mail_data_json.get('result'):
                    break
                if mail_data_json.get('errno') != 0:
                    break
                mail_data = mail_data_json.get('data')
                all_pagenum = mail_data.get('pagenum')
                maillist = mail_data.get('maillist')
                if len(maillist) == 0:
                    self._logger.info("No mail in mail list")
                    break
                for mail_info in maillist:
                    mailid = mail_info[0]
                    eml = EML(self._clientid, self.task, self._userid, mailid, folder, self.task.apptype)
                    eml.sendtime = datetime.datetime.fromtimestamp(mail_info[4])
                    eml.subject = mail_info[3]
                    eml.provider = mail_info[1]
                    eml.owner = mail_info[2]
                    eml_info = self.__download_mails(folder.folderid, mailid)
                    eml.io_stream = eml_info[0]
                    eml.stream_length = eml_info[1]
                    time.sleep(5)  # 防止取邮件的频率过快
                    yield eml
                if current_page == all_pagenum:
                    break
                else:
                    current_page += 1
            except Exception:
                if error_times >= 5:
                    break
                self._logger.error(f"Get mail or download mail error, err:{traceback.format_exc()}")
                error_times += 1
                continue

    def __download_mails(self, folderid, mailid):
        url = "http://m0.mail.sina.com.cn/classic/read_mid.php"

        querystring = {"fid": "{}".format(folderid), "mid": "{}".format(mailid),
                       "ts": "{}".format(str(int(datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)))}
        headers = '''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
            Cache-Control: no-cache
            Host: m0.mail.sina.com.cn
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Referer: http://m0.mail.sina.com.cn/classic/index.php
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36
        '''

        resp = self._ha.get_response(url, headers=headers, params=querystring)
        stream_length = resp.headers.get('Content-Length', 0)
        eml = ResponseIO(resp)
        return eml, stream_length
