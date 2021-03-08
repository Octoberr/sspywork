"""
爬取tom邮箱
create by judy 2018/11/22
modify by judy 2019/03/05
资源下载采用commonbaby 库的ha
"""
import json
import random
import re
import time
import traceback
from datetime import datetime
import pytz
from urllib.parse import urlencode, quote_plus, unquote

import requests
from commonbaby.httpaccess import ResponseIO
from commonbaby.helpers import helper_str
from requests.api import head

from datacontract.idowndataset.task import Task
from idownclient.clientdatafeedback import CONTACT, CONTACT_ONE, EML, Folder, PROFILE, EGender, IdownLoginLog_ONE
from idownclient.spider.appcfg import AppCfg
from .spidermailbase import SpiderMailBase


class SpiderTom(SpiderMailBase):
    def __init__(self, tsk: Task, appcfg: AppCfg, clientid):
        super(SpiderTom, self).__init__(tsk, appcfg, clientid)
        # 定义自己要使用的字段
        self._usr = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
            'Mozilla/5.0 (Linux; U; Android 4.0; en-us; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Mobile Safari/537.36'
        ]
        self._index = 'https://mail.tom.com/'
        self._headers = {
            # 'Cookie': self.cookie,
            'User-Agent':
            random.choice(self._usr),
            'X-Forwarded-For':
            '%s.%s.%s.%s' % (random.randint(0, 255), random.randint(
                0, 255), random.randint(0, 255), random.randint(0, 255))
        }
        self._indexurl = 'https://mail.tom.com/webmail/main/index.action'

    def _pwd_login(self) -> bool:
        """
        账号密码登陆
        :return:
        """
        login_status = False
        try:
            loginurl = 'https://mail.tom.com/webmail/login/loginService.action'
            formdata = f'username={quote_plus(self.task.account)}&password={self.task.password}&indexLogin=true'
            self._ha.getstring(loginurl, req_data=formdata,
                               headers='''
            Accept: application/json, text/javascript, */*; q=0.01
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Content-Length: {}
            Content-Type: application/x-www-form-urlencoded
            Host: mail.tom.com
            Origin: https://mail.tom.com
            Referer: https://mail.tom.com/?lang=zh_CN
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
            X-Requested-With: XMLHttpRequest'''.format(len(formdata)))

            # res = s.post(loginurl, data=formdata, allow_redirects=False)

            # if 'Location' in res.headers:
            #     cookiedict = res.cookies.get_dict()
            #     cookie_string = ';'.join(
            #         [str(x) + '=' + str(y) for x, y in cookiedict.items()])
            #     self.task.cookie = cookie_string
            # 验证cookie的有效性
            change_pemplate_url = 'https://mail.tom.com/webmail/mailFacade/changePemplate.action'
            formdata = 'domain=web.mail.tom.com&fromSource=mail.tom.com&tab=0'
            self._ha.getstring(change_pemplate_url, req_data=formdata,
                               headers='''
            Accept: */*
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Content-Length: 53
            Content-Type: application/x-www-form-urlencoded
            Host: mail.tom.com
            Origin: https://mail.tom.com
            Referer: https://mail.tom.com/?lang=zh_CN
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
            X-Requested-With: XMLHttpRequest''')

            html = self._ha.getstring('https://mail.tom.com/webmail/main/index.action',
                                      headers='''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Host: mail.tom.com
            Referer: https://mail.tom.com/?lang=zh_CN
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36''')

            if 'top-account' in html and 'top-setting' in html:
                login_status = True
            # s.post(change_pemplate_url, data=formdata, headers=headers)
            # cookiedict = s.cookies.get_dict()
            # cookiestr = ';'.join([str(x) + '=' + str(y) for x, y in cookiedict.items()])
            # self.task.cookie = cookiestr
            # login_status = self._cookie_login()
        except Exception as ex:
            self._logger.error('Account_pwd login error, err: {}'.format(
                traceback.format_exc()))
            self._write_log_back("账密登录失败: {}".format(ex.args))
        return login_status

    def _cookie_login(self) -> bool:
        login_status = False
        # self._headers['Cookie'] = self.task.cookie
        try:
            self._ha._managedCookie.add_cookies(".tom.com", self.task.cookie)
            pindex = 'https://mail.tom.com/webmail/main/index.action'
            html = self._ha.getstring(pindex,
                                      headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Host: mail.tom.com
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
            """)
            try:
                if not 'top-account' in html or not 'top-setting' in html:
                    return login_status
            except Exception as e:
                return login_status

            login_status = True

        except Exception:
            # 访问网络出错
            self._logger.error("Cookie login error, err: {}".format(
                traceback.format_exc()))
        return login_status

    def __get_userid(self, htmltext):
        re_userid = re.compile('[0-9a-zA-Z_]{0,19}@tom.com')
        all_u = re_userid.findall(htmltext)
        if len(all_u) != 0:
            self._userid = all_u[0]
        else:
            if self.task.account is not None:
                self._userid = self.task.account
        return

    def _get_profile(self):
        self._headers['Cookie'] = self.task.cookie
        try:
            html = self._ha.getstring(self._indexurl,
                                      headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: en-US,en;q=0.9
            Cache-Control: no-cache
            Connection: keep-alive
            Pragma: no-cache
            Sec-Fetch-Dest: document
            Sec-Fetch-Mode: navigate
            Sec-Fetch-Site: none
            Sec-Fetch-User: ?1
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"""
                                      )
            # indexres = requests.get(self._indexurl, headers=self._headers)
            # index_text = indexres.text
            self.__get_userid(html)
            unixtime = int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)
            pindex = 'https://mail.tom.com/webmail/preference/getUserProfile.action'
            formdata = {'_ts': str(unixtime)}
            # r = requests.post(pindex, headers=self._headers, data=formdata)
            html = self._ha.getstring(pindex,
                                      req_data='',
                                      json=formdata,
                                      headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: en-US,en;q=0.9
            Cache-Control: no-cache
            Connection: keep-alive
            Pragma: no-cache
            Sec-Fetch-Dest: document
            Sec-Fetch-Mode: navigate
            Sec-Fetch-Site: none
            Sec-Fetch-User: ?1
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"""
                                      )
            if html is None or html == "":
                profile = PROFILE(self._clientid, self.task, self.task.apptype,
                                  self._userid)
                yield profile
            else:
                prodata = json.loads(html).get('result', {})
                if len(prodata) == 0:
                    return
                profile = PROFILE(self._clientid, self.task, self.task.apptype,
                                  self._userid)
                profile.birthday = prodata.get('birthday')
                profile.nickname = prodata.get('name')
                gender = prodata.get('gender')
                if gender is not None:
                    if gender == '2':
                        profile.gender = EGender.Male
                    elif gender == '3':
                        profile.gender = EGender.Female
                profile.region = prodata.get('province')
                profile.address = prodata.get('city')
                profile.phone = prodata.get('mobileNumber')
                yield profile
        except Exception:
            self._logger.error("Get profile error, err: {}".format(
                traceback.format_exc()))
            return

    def _get_contacts(self):
        self._headers['Cookie'] = self.task.cookie
        contacturl = 'https://mail.tom.com/webmail/contact/querycontact.action'
        formdata = {'type': 'searchContacts', 'contactname': ''}
        try:
            # r = requests.post(contacturl, headers=self._headers, data=formdata)
            html = self._ha.getstring(
                contacturl,
                req_data="type=searchContacts&contactname=",
                headers="""
            Accept: application/json, text/javascript, */*; q=0.01
            Accept-Encoding: gzip, deflate
            Accept-Language: en-US,en;q=0.9
            Cache-Control: no-cache
            Connection: keep-alive
            Content-Length: 32
            Content-Type: application/x-www-form-urlencoded
            Origin: https://mail.tom.com
            Pragma: no-cache
            Referer: https://mail.tom.com/webmail/main/index.action
            Sec-Fetch-Dest: empty
            Sec-Fetch-Mode: cors
            Sec-Fetch-Site: same-origin
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36
            X-Requested-With: XMLHttpRequest""")
            condata = json.loads(html).get('result', {})
            if len(condata) == 0:
                return
            contact = CONTACT(self._clientid, self.task, self.task.apptype)
            for el in condata:
                eldict = {k: v for k, v in el.items() if v is not None}
                contactid = eldict.get('contactId')
                if contactid is not None:
                    contact_one = CONTACT_ONE(self._userid, contactid,
                                              self.task, self.task.apptype)
                    contact_one.nickname = eldict.get('contactName')
                    contact_one.email = eldict.get('contactEmail')
                    contact_one.append_details(eldict)
                    contact.append_innerdata(contact_one)
            if contact.innerdata_len == 0:
                return
            else:
                yield contact
        except Exception:
            self._logger.error("Get contact error, err: {}".format(
                traceback.format_exc()))
            return

    def _get_folders(self) -> iter:
        folderurl = 'https://mail.tom.com/webmail/query/folderinfo.action?type=all_brief'
        try:
            html = self._ha.getstring(folderurl,
                                      headers="""
            Accept: application/json, text/javascript, */*; q=0.01
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Host: mail.tom.com
            Referer: http://mail.tom.com/webmail/main/index.action
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.193 Safari/537.36
            X-Requested-With: XMLHttpRequest""")
            result = json.loads(html).get('result')
            if result is None or not result.__contains__('mailList'):
                return
            maillist: list = result['mailList']
            if len(maillist) == 0:
                return
            for mailbox in maillist:
                f = Folder()
                f.name = mailbox['viewName']
                f.mailcount = mailbox['msgCount']
                yield f
        except Exception:
            self._logger.error("Get folder error, err: {}".format(
                traceback.format_exc()))
            return

    def _get_mails(self, folder: Folder) -> iter:
        """
        获取所有的邮件类表并，获取eml格式的邮件并保存为文件在本地
        """
        self._headers['Cookie'] = self.task.cookie
        url = 'https://mail.tom.com/webmail/query/queryfolder.action'
        formdata = {'folderName': '{}'.format(folder.name), 'currentPage': '1'}
        reqdata = f"folderName={folder.name}&currentPage=1"
        try:
            # res = requests.post(url,
            #                     headers=self._headers,
            #                     data=formdata,
            #                     timeout=60)
            html = self._ha.getstring(
                url,
                req_data=reqdata,
                #   json=formdata,
                timeout=60,
                headers="""
                Accept: application/json, text/javascript, */*; q=0.01
                Accept-Encoding: gzip, deflate
                Accept-Language: en-US,en;q=0.9
                Cache-Control: no-cache
                Connection: keep-alive
                Content-Type: application/x-www-form-urlencoded
                Origin: https://mail.tom.com
                Pragma: no-cache
                Referer: https://mail.tom.com/webmail/main/index.action
                Sec-Fetch-Dest: empty
                Sec-Fetch-Mode: cors
                Sec-Fetch-Site: same-origin
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36
                X-Requested-With: XMLHttpRequest""")
            resdict = json.loads(html)
            totalpage = resdict['result']['totalPage']
            for i in range(int(totalpage)):
                # formdata['currentPage'] = i + 1
                reqdata = f"folderName={folder.name}&currentPage={i+1}"
                # data = requests.post(url, headers=self._headers, data=formdata)
                html = self._ha.getstring(
                    url,
                    req_data=reqdata,
                    #   json=formdata,
                    timeout=60,
                    headers="""
                    Accept: application/json, text/javascript, */*; q=0.01
                    Accept-Encoding: gzip, deflate
                    Accept-Language: en-US,en;q=0.9
                    Cache-Control: no-cache
                    Connection: keep-alive
                    Content-Type: application/x-www-form-urlencoded
                    Origin: https://mail.tom.com
                    Pragma: no-cache
                    Referer: https://mail.tom.com/webmail/main/index.action
                    Sec-Fetch-Dest: empty
                    Sec-Fetch-Mode: cors
                    Sec-Fetch-Site: same-origin
                    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36
                    X-Requested-With: XMLHttpRequest""")
                dictres = json.loads(html)
                pagelist = dictres['result']['pageList']
                for mail in pagelist:
                    maildata = self.__getemlfile(mail)
                    if maildata is None or not mail.__contains__(
                            'messageid') or mail["messageid"] is None:
                        self._logger.info("Skip invalid email: {}".format(
                            mail.get("subject")))
                        continue
                    eml = EML(self._clientid, self.task, self._userid,
                              mail['messageid'], folder, self.task.apptype)
                    eml.io_stream = maildata[0]
                    eml.stream_length = maildata[1]
                    yield eml
        except Exception:
            self._logger.error("Downloading all mails error, err: {}".format(
                traceback.format_exc()))
            return

    def __getemlfile(self, mail):
        # 获取eml格式的邮件
        url = 'https://mail.tom.com/webmail/readmail/rawcontent.action'
        headers = '''
        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
        Accept-Encoding: gzip, deflate
        Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
        Cache-Control: no-cache
        Content-Type: application/x-www-form-urlencoded
        Host: mail.tom.com
        Origin: https://mail.tom.com
        Pragma: no-cache
        Proxy-Connection: keep-alive
        Referer: https://mail.tom.com/webmail/main/index.action
        Upgrade-Insecure-Requests: 1
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
        '''
        formdata = {
            'filename': mail['subject'],
            'uid': mail['uid'],
            'uuid': '',
            'folderName': mail['folderName'],
            'partId': '',
            'suffix': '',
            'subject': '',
            'coremail': 'newmail',
        }
        parms = urlencode(formdata, quote_via=quote_plus)
        try:
            # res = requests.post(url, headers=self._headers, data=formdata)
            # eml = BytesIO(res.content)
            # eml = self._ha.get_response_stream(url, req_data=parms, headers=headers)
            # return eml
            resp: ResponseIO = self._ha.get_response_stream(url,
                                                            headers=headers,
                                                            req_data=parms,
                                                            timeout=60)
            # stream_length = resp.headers.get('Content-Length', 0)
            # eml = ResponseIO(resp)
            return resp, 0
        except Exception:
            self._logger.error("Downloading a mail error, err: {}".format(
                traceback.format_exc()))
            return None

    def _get_loginlog(self) -> iter:
        self._headers['Cookie'] = self.task.cookie
        url = 'https://mail.tom.com/webmail/preference/showLoginHistory.action'
        try:
            # r = requests.get(url, headers=self._headers)
            html = self._ha.getstring(url,
                                      headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: en-US,en;q=0.9
            Cache-Control: no-cache
            Connection: keep-alive
            Pragma: no-cache
            Sec-Fetch-Dest: document
            Sec-Fetch-Mode: navigate
            Sec-Fetch-Site: none
            Sec-Fetch-User: ?1
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36"""
                                      )
            res_text = html
            alltd = re.compile("\<td\>(.+)\<\/td\>")
            all_td = alltd.findall(res_text)
            new = zip(all_td[::3], all_td[1::3], all_td[2::3])
            for l_one in new:
                login_log_one = IdownLoginLog_ONE(self.task, self.task.apptype,
                                                  self._userid)
                login_log_one.ip = l_one[2]
                login_log_one.region = l_one[1]
                strtime_to_time = time.strptime(l_one[0], "%Y年%m月%d日 %H:%M:%S")
                login_log_one.logintime = time.strftime(
                    "%Y-%m-%d %H:%M:%S", strtime_to_time)
                yield login_log_one
        except Exception:
            self._logger.error(
                f"Downloading loginlogerror, err:{traceback.format_exc()}")
            return
