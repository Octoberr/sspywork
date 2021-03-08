"""
邮件下载update by judy 2019/03/05
"""
import base64
import json
import re
import time
import traceback
import urllib.parse
from datetime import datetime

import pytz
import requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from commonbaby.httpaccess import ResponseIO, Response
from commonbaby.helpers.helper_str import substring

from idownclient.clientdatafeedback import CONTACT_ONE, CONTACT, EML, Folder, PROFILE
from .spidermailbase import SpiderMailBase


class Spider126(SpiderMailBase):

    def __init__(self, task, appcfg, clientid):
        super(Spider126, self).__init__(task, appcfg, clientid)
        self._html = None
        self.sid = None
        self._pubkey = '''-----BEGIN RSA PUBLIC KEY-----
                    MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC5gsH+AA4XWONB5TDcUd+xCz7ejOFHZKlcZDx+pF1i7Gsvi1vjyJoQhRtRSn950x498VUkx7rUxg1/ScBVfrRxQOZ8xFBye3pjAzfb22+RCuYApSVpJ3OO3KsEuKExftz9oFBv3ejxPlYc5yq7YiBO8XlTnQN0Sa4R4qhPO3I2MQIDAQAB
                    -----END RSA PUBLIC KEY-----'''

    def _check_registration(self):
        """
        查询手机号是否注册了126邮箱
        :param account:
        :return:
        """
        res = False
        isreg = re.compile(r'{"code":201,', re.S)
        ua = "http://reg.email.163.com/unireg/call.do?cmd=register.entrance&from=163mail_right"
        url = "http://reg.email.163.com/unireg/call.do?cmd=added.mobilemail.checkBinding"
        data = {
            'mobile': self.task.account
        }
        s = requests.Session()
        r = s.get(ua)
        response = s.post(url=url, data=data)
        signup = isreg.search(response.text)
        if signup:
            # 匹配的注册信息返回True
            # print(signup.group())
            res = True
        return res

    def _get_sid(self):
        res = None
        sid = self._ha.cookies.get('Coremail')
        if not sid:
            return res

        if '%' in sid:
            sid = substring(sid, '%', '%')

        return sid

    def _get_rsa_string(self, text: str):
        keyPub = RSA.importKey(self._pubkey)
        cipher = PKCS1_v1_5.new(keyPub)
        cipher_text = cipher.encrypt(text.encode())
        b64_text = base64.b64encode(cipher_text)
        outtext = b64_text.decode('utf-8')
        return outtext

    def _pwd_login(self) -> bool:
        res = False
        try:
            # 获取pkid
            url = 'https://mimg.127.net/p/freemail/index/unified/static/2020/js/126.9e47109b361efa5b05cc.js'
            headers = '''
            Referer: https://mail.126.com/
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'''
            resp_js = self._ha.getstring(url, headers=headers)
            pkid = re.search(r'promark:"(.*?)"', resp_js).group(1)

            # 获取cookie，不然gt_url返回不正确
            ini_url = 'https://passport.126.com/dl/ini?pd=mail126&pkid={}&pkht=mail.126.com'.format(pkid)
            self._ha.getstring(ini_url)

            # 获取tk参数
            un = urllib.parse.quote_plus(self.task.account)
            gt_url = 'https://passport.126.com/dl/gt?un={}&pkid={}&pd=mail126'.format(un, pkid)
            headers = '''
            Accept: */*
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Host: passport.126.com
            Sec-Fetch-Dest: document
            Sec-Fetch-Mode: navigate
            Sec-Fetch-Site: none
            Sec-Fetch-User: ?1
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36
            '''
            resp_json = self._ha.getstring(gt_url, headers=headers)
            tk = re.search(r'"tk":"(.*?)"', resp_json).group(1)

            # 提交账号密码
            l_url = 'https://passport.126.com/dl/l'
            payload = {
                'channel': '0',
                'd': '10',
                'domains': '163.com',
                'l': '0',
                'pd': 'mail126',
                'pkid': pkid,
                'pw': self._get_rsa_string(self.task.password),
                'pwdKeyUp': '1',
                'rtid': '75PuaEp9EDcFQ1BYguYuKAs3ZgamFCsz',
                't': str(int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)),
                'tk': tk,
                'topURL': 'https://mail.126.com/',
                'un': self.task.account
            }
            headers = '''
            Accept: */*
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Host: passport.126.com
            Origin: https://passport.126.com
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36
            '''
            # 加0.5等待时间，不然ret会返回409
            time.sleep(0.5)
            resp_json = self._ha.getstring(l_url, req_data='', json=payload, headers=headers)
            ret = json.loads(resp_json)['ret']
            if ret != '201':
                if ret == '445':
                    msg = "Pwd login error: {}".format(ret) + ' 需要验证码'
                    self._logger.error(msg)
                    self._write_log_back(msg)
                else:
                    self._logger.error("Pwd login error: {}".format(ret))
                return res

            # 登陆主页
            ntesdoor_url = 'https://mail.126.com/entry/cgi/ntesdoor?'
            data = '''
            style: -1
            df: mail163_letter
            allssl: true
            net: 
            language: -1
            from: web
            race: 
            iframe: 1
            url2: https://mail.126.com/errorpage/error126.htm
            product: mail126'''
            headers = '''
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9
            cache-control: max-age=0
            origin: https://mail.126.com
            referer: https://mail.126.com/
            sec-fetch-dest: iframe
            sec-fetch-mode: navigate
            sec-fetch-site: same-origin
            sec-fetch-user: ?1
            upgrade-insecure-requests: 1
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'''
            resp: Response = self._ha.get_response(ntesdoor_url, req_data=data, headers=headers)
            res = self._cookie_login()
        except Exception as ex:
            self._logger.error("Pwd login error, err: {}".format(ex))
            self._write_log_back("账密登录失败: {}".format(ex.args))
        return res

    def _cookie_login(self) -> bool:
        res = False
        try:
            self._ha._managedCookie.add_cookies('126.com', self.task.cookie)
            self.sid = self._get_sid()
            if self.sid is None:
                self._logger.error("Coremail.Cookie not found")
                return res

            url = f'https://mail.126.com/js6/main.jsp?sid={self.sid}&df=mail126_letter'

            headers = '''User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36'''
            html = self._ha.getstring(url, headers=headers)
            if not html.__contains__('已发送'):
                return res
            self._userid = substring(html, "uid=", "&")
            if not self._userid:
                return res
            res = True
        except Exception:
            self._logger.error(f"Cookie login error, err:{traceback.format_exc()}")
        return res

    def _get_profile(self) -> iter:
        self.__before_download()
        if self._html is None:
            if self.sid is None:
                self._logger.error("Invalid cookie")

            url = "https://mail.126.com/js6/main.jsp"
            querystring = {"sid": self.sid, "df": "mail126_letter"}
            headers = '''
                Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                Accept-Encoding: gzip, deflate
                Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
                Cache-Control: no-cache
                Connection: keep-alive
                Host: mail.126.com
                Pragma: no-cache
                Upgrade-Insecure-Requests: 1
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36
            '''

            res_text = self._ha.getstring(url, headers=headers, params=querystring)
            if "已发送" in res_text:
                self._html = res_text
        try:
            re_uid = re.compile('uid:\'(.+?)\',suid')
            uid = re_uid.search(self._html)
            self._userid = uid.group(1)
            re_username = re.compile("'true_name':'(.+?)'")
            u_name = re_username.search(self._html)
            p_data = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
            if u_name:
                p_data.nickname = u_name.group(1)
            yield p_data
        except Exception:
            self._logger.error(f"Get profile info error, err:{traceback.format_exc()}")

    def _get_contacts(self) -> iter:
        if self.sid is None:
            self._logger.error("Invalid cookie")
        url = "https://mail.126.com/contacts/call.do"

        querystring = {"uid": self._userid, "sid": self.sid, "from": "webmail",
                       "cmd": "newapi.getContacts", "vcardver": "3.0", "ctype": "all",
                       "attachinfos": "yellowpage,frequentContacts", "freContLim": "20"}

        payload = '''order=[{"field":"N","desc":"false"}]'''
        headers = f'''
            Accept: */*
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
            Cache-Control: no-cache
            Connection: keep-alive
            Content-type: application/x-www-form-urlencoded
            Host: mail.126.com
            Origin: https://mail.126.com
            Pragma: no-cache
            Referer: https://mail.126.com/js6/main.jsp?sid={self.sid}&df=mail126_letter
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36
        '''

        try:
            res_test = self._ha.getstring(url, req_data=payload, headers=headers, params=querystring)

            res_text_json = json.loads(res_test)
            if res_text_json.get('code') != 200:
                self._logger.error(f"Get contacts error, err:{traceback.format_exc()}")
                return
            con_list = res_text_json.get('data').get('contacts')
            if con_list is None or len(con_list) == 0:
                return
            groups_dict = {}
            groups = res_text_json.get('data').get('groups')
            for group in groups:
                group_cid = group['CID']
                group_name = group['N']
                groups_dict[group_cid] = group_name
            con_all = CONTACT(self._clientid, self.task, self.task.apptype)
            for one in con_list:
                name = one.get('FN')
                mail = one.get('EMAIL;type=INTERNET;type=pref')
                con_one = CONTACT_ONE(self._userid, mail, self.task, self.task.apptype)
                con_one.email = mail
                con_one.nickname = name
                if 'GROUPING' in one:
                    # 一个人可能有多个分组,用空格隔开
                    groupings = one.get('GROUPING').split(';')
                    for i in range(len(groupings)):
                        groupings[i] = groups_dict[groupings[i]]
                    group_names = ' '.join(groupings)
                    con_one.group = '=?utf-8?b?' + str(base64.b64encode(group_names.encode('utf-8')), 'utf-8')
                con_all.append_innerdata(con_one)
            if con_all.innerdata_len > 0:
                yield con_all
        except Exception:
            self._logger.error(f"Get contact error, err:{traceback.format_exc()}")

    def _get_folders(self) -> iter:
        try:
            if self._html is None:
                if self.sid is None:
                    self._logger.error("Invalid cookie")
                url = "https://mail.126.com/js6/main.jsp"

                querystring = {"sid": self.sid, "df": "mail126_letter"}
                headers = '''
                        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                        Accept-Encoding: gzip, deflate, br
                        Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
                        Cache-Control: no-cache
                        Connection: keep-alive
                        Host: mail.126.com
                        Pragma: no-cache
                        Upgrade-Insecure-Requests: 1
                        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36
                    '''

                res_text = self._ha.getstring(url, headers=headers, params=querystring)
                if "已发送" in res_text:
                    self._html = res_text
            re_id = re.compile("'id':(\d+),")
            ids_all = re_id.findall(self._html)
            re_name = re.compile("'name':'(.+?)',")
            name_all = re_name.findall(self._html)
            for folder_num in range(len(ids_all)):
                folder = Folder()
                folder.folderid = ids_all[folder_num]
                folder.name = name_all[folder_num]
                yield folder
        except Exception:
            self._logger.error(f"Get folder info error, err:{traceback.format_exc()}")

    def _get_mails(self, folder: Folder) -> iter:
        get_mail_num = 0
        if self.sid is None:
            self._logger.error("Invalid cookie")
        url = "https://mail.126.com/js6/s"

        querystring = {"sid": self.sid, "func": "mbox:listMessages"}
        while True:
            payload_data = '<?xml version="1.0"?><object><int name="fid">{}</int>' \
                           '<string name="order">date</string><boolean name="desc">true</boolean>' \
                           '<int name="limit">50</int><int name="start">{}</int><boolean name="skipLockedFolders">' \
                           'false</boolean><string name="topFlag">top</string><boolean name="returnTag">' \
                           'true</boolean><boolean name="returnTotal">true</boolean></object>'.format(folder.folderid,
                                                                                                      get_mail_num)
            get_mail_num += 50
            payload_url = urllib.parse.quote_plus(payload_data).replace('+', '%20')
            payload = 'var=' + payload_url
            headers = f'''
                Accept: text/javascript
                Accept-Encoding: gzip, deflate, br
                Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
                Cache-Control: no-cache
                Connection: keep-alive
                Content-type: application/x-www-form-urlencoded
                Host: mail.163.com
                Origin: https://mail.126.com
                Pragma: no-cache
                Referer: https://mail.126.com/js6/main.jsp?sid={self.sid}&df=mail126_letter
                Sec-Fetch-Dest: empty
                Sec-Fetch-Mode: cors
                Sec-Fetch-Site: same-origin
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36
            '''
            try:
                re_text = self._ha.getstring(url, req_data=payload, headers=headers, params=querystring)
                re_mailid = re.compile("'id':'(.+?)',")
                mailidall = re_mailid.findall(re_text)
                for id_one in range(len(mailidall)):
                    mail_id = mailidall[id_one]
                    eml = EML(self._clientid, self.task, self._userid, mail_id, folder, self.task.apptype)
                    eml_info = self.__download_eml(mail_id)
                    eml.io_stream = eml_info[0]
                    eml.stream_length = eml_info[1]
                    yield eml
                re_total = re.compile('\'total\':(\d+)')
                total_res = re_total.search(re_text)
                if total_res:
                    total = total_res.group(1)
                    if int(total) <= get_mail_num:
                        break
                else:
                    self._logger.error("Cant get all email, something wrong")
                    break
            except Exception:
                self._logger.error(f"Get email info error, err:{traceback.format_exc()}")

    def __download_eml(self, mail_id):
        url = "https://mail.126.com/js6/read/readdata.jsp"
        # sid = self._get_sid()
        if self.sid is None:
            self._logger.error("Invalid cookie")
        querystring = {"sid": self.sid, "mid": mail_id,
                       "mode": "download", "action": "download_eml"}
        headers = f'''
                    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                    Accept-Encoding: gzip, deflate, br
                    Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
                    Cache-Control: no-cache
                    Connection: keep-alive
                    Host: mail.126.com
                    Pragma: no-cache
                    Referer: https://mail.126.com/js6/main.jsp?sid={self.sid}&df=mail126_letter
                    Upgrade-Insecure-Requests: 1
                    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36
                '''

        # eml = self._ha.get_response_stream(url, headers=headers, params=querystring)
        # return eml
        resp = self._ha.get_response(url, headers=headers, params=querystring)
        stream_length = resp.headers.get('Content-Length', 0)
        eml = ResponseIO(resp)
        return eml, stream_length

    def __before_download(self):
        """
        设置邮箱已发送邮件的保存机制
        :return:
        """
        url = "https://mail.126.com/js6/s"
        # sid = self._get_sid()
        if self.sid is None:
            self._logger.error("Invalid cookie")
        querystring = {"sid": self.sid, "func": "user:setAttrs"}

        payload = 'var=%3C%3Fxml%20version%3D%221.0%22%3F%3E%3Cobject%3E%3Cobject%20name%3D%22' \
                  'attrs%22%3E%3Cint%20name%3D%22save_sent%22%3E1%3C%2Fint%3E%3C%2Fobject%3E%3C%2Fobject%3E'
        headers = f'''
            Accept: text/javascript
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
            Cache-Control: no-cache
            Connection: keep-alive
            Content-type: application/x-www-form-urlencoded
            Host: mail.126.com
            Origin: https://mail.126.com
            Pragma: no-cache
            Referer: https://mail.126.com/js6/main.jsp?sid={self.sid}&df=mail126_letter
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36
        '''
        try:
            # response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
            res_text = self._ha.getstring(url=url, req_data=payload, headers=headers, params=querystring)
            if 'S_OK' in res_text:
                # 设置成功
                self._logger.info("Download attachment settings are successful.")
        except Exception:
            self._logger.error(f"Before donwload setting error, err:{traceback.format_exc()}")
        finally:
            return