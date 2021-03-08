"""
163vip的爬虫
by judy 2019/01/11

update by judy 2019/03/06
统一使用ha
"""

import json
import re
import traceback
import urllib.parse

import requests
from commonbaby.httpaccess import ResponseIO

from idownclient.clientdatafeedback import CONTACT_ONE, CONTACT, EML, Folder, PROFILE
from .spidermailbase import SpiderMailBase


class Spider163vip(SpiderMailBase):

    def __init__(self, task, appcfg, clientid):
        super(Spider163vip, self).__init__(task, appcfg, clientid)
        self._html = None

    def _get_sid(self):
        re_sid1 = re.compile("%(.+?)%")
        re_sid2 = re.compile("Coremail.sid=(.+?);")
        sid1 = re_sid1.search(self.task.cookie)
        if sid1:
            return sid1.group(1)
        sid2 = re_sid2.search(self.task.cookie)
        if sid2:
            return sid2.group(1)
        else:
            return None

    def _cookie_login(self) -> bool:
        res = False
        sid = self._get_sid()
        if sid is None:
            self._logger.error("Invalid cookie")
            return res
        url = f"http://webmail.vip.163.com/js6/main.jsp?sid={sid}&df=mailvip"
        headers = {
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Cookie': self.task.cookie.encode('utf-8'),
            'Host': "webmail.vip.163.com",
            'Pragma': "no-cache",
            'Proxy-Connection': "keep-alive",
            'Referer': "http://webmail.vip.163.com/js6/main.jsp?sid=BAsnkgKKqetoFpUtUVKKteyfONhRRwgX&df=mailvip",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        }

        try:
            response = requests.get(url, headers=headers)

            res_text = response.text
            if "已发送" in res_text:
                self._html = res_text
                res = True
                # 增加cookie到ha, encode是因为cookie中可能出现中文，也是醉了
                self._ha._managedCookie.add_cookies('vip.163.com', self.task.cookie.encode('utf-8'))
        except Exception:
            self._logger.error(f"Cookie login error, err:{traceback.format_exc()}")
        finally:
            return res

    def _get_profile(self) -> iter:
        self.__before_download()
        if self._html is None:
            sid = self._get_sid()
            if sid is None:
                self._logger.error("Invalid cookie")
            url = f"http://webmail.vip.163.com/js6/main.jsp?sid={sid}&df=mailvip"
            headers = {
                'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                'Accept-Encoding': "gzip, deflate",
                'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
                'Cache-Control': "no-cache",
                'Cookie': self.task.cookie.encode('utf-8'),
                'Host': "webmail.vip.163.com",
                'Pragma': "no-cache",
                'Proxy-Connection': "keep-alive",
                'Referer': "http://webmail.vip.163.com/js6/main.jsp?sid=BAsnkgKKqetoFpUtUVKKteyfONhRRwgX&df=mailvip",
                'Upgrade-Insecure-Requests': "1",
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            res_text = response.text
            if "已发送" in res_text:
                self._html = res_text
        try:
            re_uid = re.compile('uid:\'(.+?)\',suid')
            uid = re_uid.search(self._html)
            self._userid = uid.group(1)
            re_username = re.compile("'true_name':'(.+?)'")
            u_name = re_username.search(self._html)
            p_data = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
            p_data.nickname = u_name.group(1)
            if self.task.account is None:
                self.task.account = self._userid  # 目前在去重的这个方法里，account是不能为空的
            yield p_data
        except Exception:
            self._logger.error(f"Get profile info error, err:{traceback.format_exc()}")

    def _get_contacts(self) -> iter:
        sid = self._get_sid()
        if sid is None:
            self._logger.error("Invalid cookie")
        url = "http://webmail.vip.163.com/contacts/call.do"

        querystring = {"uid": self._userid, "sid": sid, "from": "webmail",
                       "cmd": "newapi.getContacts", "vcardver": "3.0", "ctype": "all",
                       "attachinfos": "yellowpage,frequentContacts", "freContLim": "20", "limitinfo": "get"}

        payload = {
            'order': [{'field': 'N', 'desc': 'false'}]
        }
        headers = {
            'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
            'Accept': "*/*",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Content-Length': "36",
            'Content-type': "application/x-www-form-urlencoded",
            'Cookie': self.task.cookie.encode('utf-8'),
            'Host': "webmail.vip.163.com",
            'Origin': "http://webmail.vip.163.com",
            'Pragma': "no-cache",
            'Proxy-Connection': "keep-alive",
            'Referer': "http://webmail.vip.163.com/js6/main.jsp?sid={}&df=mailvip".format(sid),
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        }

        try:
            response = requests.request("POST", url, data=payload, headers=headers, params=querystring)

            res_text_json = json.loads(response.text)
            if res_text_json.get('code') != 200:
                self._logger.error(f"Get contacts error, err:{traceback.format_exc()}")
                return
            con_list = res_text_json.get('data').get('contacts')
            if con_list is None or len(con_list) == 0:
                return
            con_all = CONTACT(self._clientid, self.task, self.task.apptype)
            for one in con_list:
                name = one.get('FN')
                mail = one.get('EMAIL;type=INTERNET;type=pref')
                con_one = CONTACT_ONE(self._userid, mail, self.task, self.task.apptype)
                con_one.email = mail
                con_one.nickname = name
                if one.get('TEL;type=CELL;type=VOICE;type=pref') is not None:
                    con_one.phone = one.get('TEL;type=CELL;type=VOICE;type=pref')
                con_all.append_innerdata(con_one)
            if con_all.innerdata_len > 0:
                yield con_all
        except Exception:
            self._logger.error(f"Get contact error, err:{traceback.format_exc()}")

    def _get_folders(self) -> iter:
        try:
            if self._html is None:
                sid = self._get_sid()
                if sid is None:
                    self._logger.error("Invalid cookie")
                url = f"http://webmail.vip.163.com/js6/main.jsp?sid={sid}&df=mailvip"
                headers = {
                    'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    'Accept-Encoding': "gzip, deflate",
                    'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
                    'Cache-Control': "no-cache",
                    'Cookie': self.task.cookie.encode('utf-8'),
                    'Host': "webmail.vip.163.com",
                    'Pragma': "no-cache",
                    'Proxy-Connection': "keep-alive",
                    'Referer': "http://webmail.vip.163.com/js6/main.jsp?sid=BAsnkgKKqetoFpUtUVKKteyfONhRRwgX&df=mailvip",
                    'Upgrade-Insecure-Requests': "1",
                    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
                }
                response = requests.get(url, headers=headers)
                res_text = response.text
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
        sid = self._get_sid()
        if sid is None:
            self._logger.error("Invalid cookie")
        get_mail_num = 0
        url = "http://webmail.vip.163.com/js6/s"

        querystring = {"sid": sid, "func": "mbox:listMessages",
                       "LeftNavfolder1Click": "1", "mbox_folder_enter": folder.folderid}
        while True:
            payload_data = '<?xml version="1.0"?><object><int name="fid">{}</int>' \
                           '<string name="order">date</string><boolean name="desc">true</boolean>' \
                           '<int name="limit">50</int><int name="start">{}</int><boolean name="skipLockedFolders">false' \
                           '</boolean><string name="topFlag">top</string><boolean name="returnTag">true</boolean>' \
                           '<boolean name="returnTotal">true</boolean></object>'.format(folder.folderid, get_mail_num)
            get_mail_num += 50
            payload_url = urllib.parse.quote_plus(payload_data).replace('+', '%20')
            payload = 'var=' + payload_url
            headers = {
                'Accept': "text/javascript",
                'Accept-Encoding': "gzip, deflate",
                'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
                'Cache-Control': "no-cache",
                'Content-Length': "539",
                'Content-type': "application/x-www-form-urlencoded",
                'Cookie': self.task.cookie.encode('utf-8'),
                'Host': "webmail.vip.163.com",
                'Origin': "http://webmail.vip.163.com",
                'Pragma': "no-cache",
                'Proxy-Connection': "keep-alive",
                'Referer': "http://webmail.vip.163.com/js6/main.jsp?sid={}&df=mailvip".format(sid),
                'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
            }
            try:
                response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
                re_text = response.text
                re_mailid = re.compile("'id':'(.+?)',")
                mailidall = re_mailid.findall(re_text)
                # re_subject = re.compile("'subject':'(.+?)',")
                # subject_all = re_subject.findall(re_text)
                for id_one in range(len(mailidall)):
                    mail_id = mailidall[id_one]
                    # mail_subject = subject_all[id_one]
                    eml = EML(self._clientid, self.task, self._userid, mail_id, folder, self.task.apptype)
                    # eml.subject = mail_subject
                    # eml.io_stream = self.__download_eml(mail_id)
                    eml_info = self.__download_eml(mail_id)
                    eml.io_stream = eml_info[0]
                    eml.stream_length = eml_info[1]
                    yield eml
                re_total = re.compile('\'total\':(\d+)')
                total = re_total.search(re_text).group(1)
                if int(total) <= get_mail_num:
                    break
            except Exception:
                self._logger.error(f"Get email info error, err:{traceback.format_exc()}")

    def __download_eml(self, mail_id):
        sid = self._get_sid()
        if sid is None:
            self._logger.error("Invalid cookie")
        url = "http://webmail.vip.163.com/js6/read/readdata.jsp"

        querystring = {"sid": sid, "mid": mail_id,
                       "mode": "download", "action": "download_eml"}
        headers = f'''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
            Cache-Control: no-cache
            Host: webmail.vip.163.com
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Referer: http://webmail.vip.163.com/js6/main.jsp?sid={sid}&df=mailvip
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
        sid = self._get_sid()
        if sid is None:
            self._logger.error("Invalid cookie")
        url = "http://webmail.vip.163.com/js6/s"

        querystring = {"sid": sid, "func": "user:setAttrs"}

        payload = "var=%3C%3Fxml%20version%3D%221.0%22%3F%3E%3Cobject%3E%3Cobject%20name%3D%22attrs%22%3E%3Cint" \
                  "%20name%3D%22save_sent%22%3E1%3C%2Fint%3E%3C%2Fobject%3E%3C%2Fobject%3E"
        headers = {
            'Accept': "text/javascript",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
            'Cache-Control': "no-cache",
            'Content-Length': "163",
            'Content-type': "application/x-www-form-urlencoded",
            'Cookie': self.task.cookie.encode('utf-8'),
            'Host': "webmail.vip.163.com",
            'Origin': "http://webmail.vip.163.com",
            'Pragma': "no-cache",
            'Proxy-Connection': "keep-alive",
            'Referer': "http://webmail.vip.163.com/js6/main.jsp?sid={}&df=mailvip".format(sid),
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        }

        try:
            response = requests.request("POST", url, data=payload, headers=headers, params=querystring)
            if 'S_OK' in response.text:
                # 设置成功
                self._logger.info("Download attachment settings are successful.")
        except Exception:
            self._logger.error(f"Before donwload setting error, err:{traceback.format_exc()}")
        finally:
            return
