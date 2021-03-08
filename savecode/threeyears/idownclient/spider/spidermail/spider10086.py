"""
spider mail 10086

update by judy 2019/03/06
更改统一下载为ha

增加接口 update by judy 2019/03/22
logout by judy 2019/03/22
"""

import datetime
import json
import random
import re
import time
import traceback
from hashlib import sha1
import pytz

import requests
from commonbaby.httpaccess import ResponseIO
from retrying import retry

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import Task
from idownclient.clientdatafeedback import CONTACT_ONE, CONTACT, EML, Folder, PROFILE, IdownLoginLog_ONE,EGender
from idownclient.spider.appcfg import AppCfg
from .spidermailbase import SpiderMailBase


class Spider10086(SpiderMailBase):

    def __init__(self, tsk: Task, appcfg: AppCfg, clientid):
        super(Spider10086, self).__init__(tsk, appcfg, clientid)
        self._usragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)' \
                         ' Chrome/70.0.3538.102 Safari/537.36'
        self._headers = {
            'User-Agent': self._usragent,
            'X-Forwarded-For': '%s.%s.%s.%s' % (
                random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        }
        if self.task.account is not None:
            r_name = re.compile("\d+")
            self.task.account = r_name.findall(self.task.account)[0]
        self._html = None

    def _check_registration(self):
        """
        这个189没法检测账号是否注册
        :return:
        """
        self._write_task_back(ECommandStatus.Succeed, "10086邮箱，移动用户默认已经注册，手机号直接登陆默认注册")
        return

    def _online_check(self):
        """
        检测账号是否在线
        网页登陆默认账号都不在线
        :return:
        """
        return False

    def _logout(self):
        log_res = False
        url = "https://mail.10086.cn/login/Logout.aspx"

        querystring = {"sid": self._get_cookie_sid(), "redirect": "http://mail.10086.cn/logout.htm"}

        headers = {
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache,no-cache",
            'cookie': self.task.cookie,
            'pragma': "no-cache",
            'referer': f"https://appmail.mail.10086.cn/m2015/html/index.html?sid={self._get_cookie_sid()}&rnd=447&tab=&comefrom=54&v=25&k=6089&resource=indexLogin&cguid={self._get_cookie_cguid()}&mtime=763&h=1",
            'upgrade-insecure-requests': "1",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36"
        }

        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            response.encoding = 'utf-8'
            if '您已成功退出139邮箱。' in response.text:
                log_res = True
                self._logger.info("退出登录成功")
        except:
            self._logger.error(f"Logout error, error:{traceback.format_exc()}")
        return log_res

    def _sms_login(self) -> bool:
        res = False
        try:
            s = requests.session()
            s.headers.update(self._headers)
            i_r = s.get('http://mail.10086.cn/')
            res_text = i_r.text
            r_web_ver = re.compile('data-val="(\d+)"')
            all_web_ver = r_web_ver.findall(res_text)
            if len(all_web_ver) != 0:
                web_ver = all_web_ver[0]
            else:
                web_ver = '25'
            r_fv = re.compile('&_fv=(\d)')
            all_fv = r_fv.findall(res_text)
            if len(all_fv) != 0:
                r_fv = all_fv[0]
            else:
                r_fv = '4'
            sms_url = 'http://mail.10086.cn/s?func=login:sendSmsCode&cguid={}' \
                      '&randnum=0.458516852023'.format(self._get_guid(), random.randint(1000, 9999))
            payload = '<object><string name="loginName">{}</string><string name="fv">{}</string>' \
                      '<string name="clientId">1003</string><string name="version">1.0</string>' \
                      '<string name="verifyCode"></string></object>'.format(self.task.phone, r_fv)
            s.post(sms_url, data=payload)
            vercode = self._get_vercode()
            sms_login_url = 'https://mail.10086.cn/Login/Login.ashx?_fv={}&cguid={}' \
                            '&_={}&resource=indexLogin'.format(r_fv, self._get_guid(), self._get_sha1(self.task.phone))
            formdata = {
                'UserName': self.task.phone,
                'passOld': '',
                'auto': 'on',
                'webVersion': web_ver,
                'loginFailureUrl': 'http://mail.10086.cn/default.html?smsLogin=1',
                'Password': self._get_sha1('fetion.com.cn:{}'.format(vercode)),
                'authType': 2
            }
            s.post(sms_login_url, data=formdata)
            cookiedict = s.cookies.get_dict()
            if 'Os_SSo_Sid' in cookiedict:
                index_url = 'https://appmail.mail.10086.cn/m2015/html/index.html' \
                            '?sid={}&tab=mailbox_1&resource=indexLogin&' \
                            'cguid={}'.format(cookiedict['Os_SSo_Sid'], self._get_guid())
                s.get(index_url)
                cookiedict = s.cookies.get_dict()
                cookiestr = ';'.join([str(x) + '=' + str(y) for x, y in cookiedict.items()])
                self.task.cookie = cookiestr
                res = self._cookie_login()
        except Exception as err:
            self._logger.error("Sms login fail, please check reason and try again, err:{}".format(err))
        return res

    def _pwd_login(self) -> bool:
        res = False
        s = requests.session()
        # 保存初始cookie
        s.headers.update(self._headers)
        try:
            i_r = s.get('http://mail.10086.cn/')
            res_text = i_r.text
            r_web_ver = re.compile('data-val="(\d+)"')
            all_web_ver = r_web_ver.findall(res_text)
            if len(all_web_ver) != 0:
                web_ver = all_web_ver[0]
            else:
                web_ver = '25'
            r_fv = re.compile('&_fv=(\d)')
            all_fv = r_fv.findall(res_text)
            if len(all_fv) != 0:
                r_fv = all_fv[0]
            else:
                r_fv = '4'
            login_url = 'https://mail.10086.cn/Login/Login.ashx?' \
                        '_fv={}&cguid={}&_={}' \
                        '&resource=indexLogin'.format(r_fv, self._get_guid(), self._get_sha1(self.task.account))
            formdata = {
                'UserName': self.task.account,
                'passOld': '',
                'auto': 'on',
                'webVersion': web_ver,
                'Password': self._get_sha1('fetion.com.cn:{}'.format(self.task.password)),
                'authType': '2'
            }
            s.post(login_url, data=formdata)
            cookiedict = s.cookies.get_dict()
            if 'Os_SSo_Sid' in cookiedict:
                index_url = 'https://appmail.mail.10086.cn/m2015/html/index.html' \
                            '?sid={}&tab=mailbox_1&resource=indexLogin&' \
                            'cguid={}'.format(cookiedict['Os_SSo_Sid'], self._get_guid())
                r = s.get(index_url)
                cookiedict = s.cookies.get_dict()
                cookiestr = ';'.join([str(x) + '=' + str(y) for x, y in cookiedict.items()])
                self.task.cookie = cookiestr
                # 检查cookie的有效性
                res = self._cookie_login()
        except Exception as ex:
            self._logger.error("Pwd login error, err: {}".format(ex))
            self._write_log_back("账密登录失败: {}".format(ex.args))
        return res

    def _cookie_login(self) -> bool:
        res = False
        sid = self._get_cookie_sid()
        if sid is None:
            self._logger.error("Cookie login sid cannot be None!")
            return False
        cguid = self._get_cookie_cguid()
        index_url = 'https://appmail.mail.10086.cn/m2015/html/index.html' \
                    '?sid={}&tab=mailbox_1&resource=indexLogin&cguid={}'.format(sid, cguid)
        headers = {
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache",
            'cookie': ''.format(self.task.cookie),
            'pragma': "no-cache",
            'referer': "http://mail.10086.cn/",
            'upgrade-insecure-requests': "1",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/70.0.3538.102 Safari/537.36",
        }
        try:
            res_index = requests.get(index_url, headers=headers)
            res_index.encoding = 'utf-8'
            response = res_index.text
            if '收件箱' in response and '设置' in response:
                url = f"https://appmail.mail.10086.cn/m2012server/home?Protocol=https%3A&positionCode=web_210&sid={sid}&from=preload"
                headers = {
                    'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
                    'accept-encoding': "gzip, deflate, br",
                    'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
                    'cache-control': "no-cache,no-cache",
                    'cookie': self.task.cookie,
                    'pragma': "no-cache",
                    'referer': index_url,
                    'upgrade-insecure-requests': "1",
                    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36"
                }
                new_response = requests.request("GET", url, headers=headers)
                new_response.encoding = 'utf-8'
                logonres = new_response.text
                if 'rmInitDataConfig' in logonres and '"code":"S_OK"' in logonres:
                    res = True
                    self._html = logonres
                    # 增加cookie到ha
                    self._ha._managedCookie.add_cookies('mail.10086.cn', self.task.cookie)
        except Exception as err:
            self._logger.error("Cookie login error, err: {}".format(err))
        return res

    def _get_cookie_usernumber(self):
        r_usernumber = re.compile(r'Login_UserNumber=(\d+);')
        usernumber = r_usernumber.search(self.task.cookie)
        if usernumber:
            return usernumber.group(1)
        else:
            return None

    def _get_cookie_sid(self):
        r_sid = re.compile(r'Os_SSo_Sid=(\w+)')
        sid = r_sid.search(self.task.cookie)
        if sid:
            return sid.group(1)
        else:
            return None

    def _get_cookie_cguid(self):
        r_cguid = re.compile('_139_index_login=(\d+)')
        cguid = r_cguid.search(self.task.cookie)
        if cguid:
            return cguid.group(1)
        else:
            return self._get_guid()

    def _get_guid(self):
        """
        获取guid
        格式: 小时+分+秒+毫秒+4位随机数
        :return:
        """
        now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        res = '{}{}{}'.format(now.strftime("%H%M%S"), str(now.microsecond)[:3],
                              random.randint(1000, 9999))
        return res

    def _get_sha1(self, account):
        srcbytes = account.encode("ascii")
        s = sha1()
        s.update(srcbytes)
        srcres = s.hexdigest()
        return srcres

    def _get_folders(self) -> iter:
        r_folder = re.compile('var rmInitDataConfig = (.*);')
        sid = self._get_cookie_sid()
        if sid is None:
            self._logger.error("Cant get sid from cookie!")
            return
        cguid = self._get_cookie_cguid()
        url = "https://appmail.mail.10086.cn/m2012server/home"

        querystring = {"Protocol": "https%3A", "positionCode": "web_210",
                       "sid": sid, "from": "preload"}

        headers = {
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache,no-cache",
            'cookie': self.task.cookie,
            'pragma': "no-cache",
            'referer': 'https://appmail.mail.10086.cn/m2015/html/index.html?sid={}&tab=mailbox_1&resource=indexLogin&cguid={}'.format(
                sid, cguid),
            'upgrade-insecure-requests': "1",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/70.0.3538.102 Safari/537.36"
        }
        try:
            response = requests.request("GET", url, headers=headers, params=querystring)
            response.encoding = 'utf-8'
            logonres = response.text
            folder = r_folder.search(logonres)
            if folder:
                folder_json = json.loads(folder.group(1))
                for f_one in self._get_folder(folder_json):
                    yield f_one
        except Exception as err:
            self._logger.error("Get Email folder error, err: {}".format(err))
            return

    def _get_folder(self, folder_jsondata):
        if folder_jsondata is None or folder_jsondata == '':
            return
        folder_list = folder_jsondata['var']['folderList']
        for folder in folder_list:
            if folder['stats']['messageCount'] == 0:
                continue
            f_one = Folder()
            f_one.name = folder['name']
            f_one.folderid = folder['fid']
            yield f_one

    def _get_mails(self, folder: Folder) -> iter:
        sid = self._get_cookie_sid()
        if sid is None:
            self._logger.error("Cannot get sid from cookie!")
        cguid = self._get_cookie_cguid()
        url = 'https://appmail.mail.10086.cn/s?func=mbox:listMessages&sid={}&&comefrom=54&cguid={}'.format(sid, cguid)
        payload = '<object>\n    <int name="fid">{}</int>\n    <string name="order">receiveDate</string>\n    ' \
                  '<string name="desc">1</string>\n    <int name="start">1</int>\n    ' \
                  '<int name="total">2000</int>\n    <string name="topFlag">top</string>\n    ' \
                  '<int name="sessionEnable">2</int>\n</object>'.format(folder.folderid)
        payload = payload.encode('ascii')
        headers = {
            'accept': "*/*",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache,no-cache",
            'content-length': "{}".format(len(payload)),
            'Content-Type': "text/xml",
            'cookie': self.task.cookie,
            'origin': "https://appmail.mail.10086.cn",
            'pragma': "no-cache",
            'referer': 'https://appmail.mail.10086.cn/m2015/html/index.html?sid={}&tab=mailbox_1&resource=indexLogin&cguid={}'.format(
                sid, cguid),
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/70.0.3538.102 Safari/537.36"
        }

        try:
            response = requests.request("POST", url, data=payload, headers=headers)
            response.encoding = 'utf-8'
            all_mail_list = response.text
            if 'code' in all_mail_list and 'S_OK' in all_mail_list:
                jsonstr = re.sub('\'', '\"', all_mail_list)
                mail_list_data = json.loads(jsonstr)
                mail_list = mail_list_data.get('var')
                if mail_list is not None and len(mail_list) != 0:
                    for mail in mail_list:
                        if mail.get('mid') is None:
                            continue
                        mail_data = self._get_mail(mail, sid)
                        if mail_data is not None:
                            eml = EML(self._clientid, self.task, self._userid, mail['mid'], folder, self.task.apptype)
                            eml.io_stream = mail_data[0]
                            eml.stream_length = mail_data[1]
                            yield eml
        except Exception as err:
            self._logger.error("Get mail error, err: {}".format(err))
            return

    @retry(stop_max_attempt_number=10, wait_fixed=60000)
    def _get_mail(self, mailinfo: dict, sid):
        url = 'https://appmail.mail.10086.cn/RmWeb/mail?func=mbox:downloadMessages&' \
              'sid={}&&comefrom=54&mid={}'.format(sid, mailinfo['mid'])
        headers = f'''
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9,en;q=0.8
            cache-control: no-cache,no-cache
            pragma: no-cache
            upgrade-insecure-requests: 1
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
'''
        time.sleep(30)
        resp = self._ha.get_response(url, headers=headers)
        stream_length = resp.headers.get('Content-Length', 0)
        eml = ResponseIO(resp)
        return eml, stream_length

    def _get_contacts(self):
        sid = self._get_cookie_sid()
        if sid is None:
            self._logger.error("Cannot get sid from cookie!")
            return
        cguid = self._get_cookie_cguid()
        url = 'https://smsrebuild1.mail.10086.cn/addrsvr/GetGroupList?' \
              'sid={}&formattype=json&&comefrom=54&cguid={}'.format(sid, cguid)
        payload = '<object>\n    <int name="Random">0.664775298109{}</int>\n</object>'.format(
            random.randint(10000, 99999))
        payload = payload.encode('ascii')
        headers = {
            'accept': "*/*",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache,no-cache",
            'content-length': "64",
            'Content-Type': "text/xml",
            'cookie': self.task.cookie,
            'origin': "https://smsrebuild1.mail.10086.cn",
            'pragma': "no-cache",
            'referer': "https://smsrebuild1.mail.10086.cn//proxy.htm",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/70.0.3538.102 Safari/537.36"
        }

        try:
            response = requests.request("POST", url, data=payload, headers=headers)
            contract_json = json.loads(response.text)
            if contract_json.get('code') == "S_OK":
                all_contact_id = contract_json.get('var').get('All').get('id')
                contact = CONTACT(self._clientid, self.task, self.task.apptype)
                for a_contact in self.__get_contacts(all_contact_id):
                    contact.append_innerdata(a_contact)
                if contact.innerdata_len != 0:
                    yield contact
        except Exception as err:
            self._logger.error("Downloading contacts error, err: {}".format(err))
            return

    def __get_contacts(self, groupid):
        sid = self._get_cookie_sid()
        if sid is None:
            self._logger.error("Cannot get sid from cookie")
            return
        cguid = self._get_cookie_cguid()
        url = 'https://smsrebuild1.mail.10086.cn/addrsvr/GetContactsList?' \
              'sid={}&formattype=json&&comefrom=54&cguid={}'.format(sid, cguid)
        payload = '<object>\r\n  <string name="GroupId">{}</string>\r\n  <string name="Keyword" />\r\n  ' \
                  '<string name="Letter">All</string>\r\n  <string name="Filter" />\r\n  ' \
                  '<string name="Sort">name</string>\r\n  <string name="SortType" />\r\n ' \
                  ' <string name="Start">0</string>\r\n  <string name="End">1000</string>\r\n' \
                  '</object>'.format(groupid)
        payload = payload.encode('ascii')
        headers = {
            'accept': "*/*",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache,no-cache",
            'content-length': "290",
            'Content-Type': "text/xml",
            'cookie': self.task.cookie,
            'origin': "https://smsrebuild1.mail.10086.cn",
            'pragma': "no-cache",
            'referer': "https://smsrebuild1.mail.10086.cn//proxy.htm",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/70.0.3538.102 Safari/537.36",
        }

        try:
            response = requests.request("POST", url, data=payload, headers=headers)
            res_json = json.loads(response.text)
            if res_json.get('code') == "S_OK":
                for con in res_json.get('var').get('list'):
                    contactid = con.get('serialId')
                    if contactid is not None:
                        contact_one = CONTACT_ONE(self._userid, contactid, self.task, self.task.apptype)
                        contact_one.nickname = con.get('name')
                        contact_one.email = con.get('email')
                        if con.get('mobile') is not None and con.get('mobile') != '':
                            contact_one.phone = con.get('mobile')
                        contact_one.append_details(con)
                        yield contact_one
        except Exception as err:
            self._logger.error("Get a contact error, err: {}".format(err))
            return

    def _get_profile(self):
        usernumber = self._get_cookie_usernumber()
        if usernumber is None:
            self._logger.error("Cannot get user number from cookie!")
            return
        sid = self._get_cookie_sid()
        if sid is None:
            self._logger.error("Cannot get sid from cookie!")
            return
        cguid = self._get_cookie_cguid()
        userinfo_url = 'https://smsrebuild1.mail.10086.cn/addrsvr/QueryUserInfo' \
                    '?sid={}&formattype=json&cguid={}'.format(sid, cguid)
        payload = '<QueryUserInfo><UserNumber>86{}</UserNumber></QueryUserInfo>'.format(usernumber)
        payload = payload.encode('ascii')
        headers = {
            'accept': "*/*",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9",
            'cache-control': "no-cache",
            'cookie': self.task.cookie,
            'pragma': "no-cache",
            'referer': "https://smsrebuild1.mail.10086.cn//proxy.htm",
            'origin': 'https://smsrebuild1.mail.10086.cn',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/70.0.3538.102 Safari/537.36",
        }
        try:
            response_text = requests.request("POST", userinfo_url, data=payload, headers=headers).text
            QueryUserInfoResp = re.search(r'QueryUserInfoResp=(.*)', response_text).group(1)
            userinfo_json = json.loads(QueryUserInfoResp)
            if userinfo_json["ResultCode"] == '0' and userinfo_json["ResultMsg"] == 'successful':
                userinfo = userinfo_json.get('UserInfo')[0]
                self._userid = usernumber + '@139.com'
                profile = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
                profile.nickname = userinfo['c'] if 'c' in userinfo else None
                gender_dict = {'0': EGender.Male, '1': EGender.Female, '2': EGender.Unknown}
                profile.gender = gender_dict[userinfo['f']] if 'f' in userinfo else None
                if 'g' in userinfo and 'h' in userinfo and 'j' in userinfo and 'k' in userinfo:
                    profile.address = userinfo['g'] + userinfo['h'] + userinfo['j'] + userinfo['k']
                profile.phone = userinfo['p'] if 'p' in userinfo else None
                profile.birthday = userinfo['o'] if 'o' in userinfo else None
                profile.email = userinfo['y'] if 'y' in userinfo else None
                yield profile
            # re_proinfo = re.compile('var addrQueryUserInfo = (.*?);')
            # proinfo = re_proinfo.search(self._html).group(1)
            # jsondata = json.loads(proinfo)
            # userinfo = jsondata.get('UserInfo')[0]
            # id = userinfo.get('y')
            # self._userid = id
            # name = userinfo.get('un')
            # profile = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
            # profile.nickname = name
            # yield profile

        except:
            self._logger.error(f"Download 10086 profile error,err:{traceback.format_exc()}")

    @retry(stop_max_attempt_number=10, wait_fixed=10000)
    def _get_loginlog(self) -> iter:
        sid = self._get_cookie_sid()
        if sid is None:
            self._logger.error("Cannot get sid from cookie")
            return
        cguid = self._get_cookie_cguid()
        url = f'https://smsrebuild1.mail.10086.cn/setting/s?func=user:loginHistory&sid={sid}&cguid={cguid}'
        headers = {
            'accept': "*/*",
            'accept-encoding': "gzip, deflate, br",
            'accept-language': "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control': "no-cache,no-cache",
            'content-length': "50",
            'content-type': "application/xml",
            'cookie': self.task.cookie,
            'origin': "https://smsrebuild1.mail.10086.cn",
            'pragma': "no-cache",
            'referer': "https://smsrebuild1.mail.10086.cn//proxy.htm",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36",
        }
        payload = '<object>\r\n  <int name="dateType">30</int>\r\n</object>'
        payload = payload.encode('ascii')
        try:
            s = requests.post(url, headers=headers, data=payload)
            res_text = s.text
            res_json = json.loads(res_text)
            if res_json.get('code') == 'S_OK':
                for login_log_one in self.__get_loginlog(res_json.get('var')):
                    yield login_log_one

        except:
            pass

    def __get_loginlog(self, log_data: dict):
        datalist = log_data.get('datalist')
        if datalist is None or len(datalist) == 0:
            return
        for line in datalist:
            log_one = IdownLoginLog_ONE(self.task, self.task.apptype, self._userid)
            log_one.ip = line.get('IP')
            log_one.logintime = line.get('loginDate')
            log_one.region = line.get('city')
            yield log_one
