"""
微博：个人信息，cookie验证，好友信息，群组信息，
        好友聊天记录，群组聊天记录,账号检测是否注册,
        账密登陆，短信登陆
20181113
"""
import base64
import datetime
import json
import re
import time
import traceback
from pathlib import Path

import execjs
from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import parse_js
from commonbaby.helpers.helper_str import substring, is_none_or_empty
from commonbaby.httpaccess.httpaccess import ResponseIO

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from ..spidersocialbase import SpiderSocialBase
from ....clientdatafeedback import CONTACT_ONE, ICHATLOG_ONE, ICHATGROUP_ONE, PROFILE, RESOURCES, EResourceType, ESign, \
    EGender


class SpiderWeibo(SpiderSocialBase):
    def __init__(self, task, appcfg, clientid):
        super(SpiderWeibo, self).__init__(task, appcfg, clientid)
        self.userid = ''
        self.cookie = self.task.cookie
        self.ha = None
        self._jspath = Path(__file__)
        self.all_contacts = []

    def _check_registration(self):
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            string = self.task.account
            s = string.encode('utf-8')
            su = base64.b64encode(s).decode('utf-8')

            url = "https://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su={su}&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.19)&_=1542358466862".format(
                su=su)
            headers = """
            Referer: https://weibo.com/
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36"""

            r = self._ha.getstring(url, headers=headers)
            patislogin = re.compile(r'"smsurl":')
            islogin = patislogin.search(r)
            if islogin:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Uber check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return

    def _pwd_login(self):

        # # 获取经base64编码的用户名
        # def get_encodename(name, runntime):
        #     return runntime.call('get_name', name)
        try:
            name = self.task.account
            password = self.task.password
            if name is None or name == '' or password is None or password == '':
                self._logger.error("Account or password is invalid: {} {}".format(name, password))
                return False
            runntime = self._get_runntime(self._jspath.parent / 'sinalogin.js')
            s = name.encode('utf-8')
            su = base64.b64encode(s).decode('utf-8')

            # 获取预处理信息
            url = "http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su={su}&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.18)".format(
                su=su)
            headers = """
Referer: https://weibo.com/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36"""

            r = self._ha.getstring(url, headers=headers)
            json_pattern = r'.*?\((.*)\)'
            m = re.match(json_pattern, r)
            pre_obj = json.loads(m.group(1))
            sp = self._get_pass(password, pre_obj, runntime)
            # patsmsurl = re.compile(r'"smsurl":"(.*?)"')
            # smsurl = patsmsurl.findall(r)[0].replace('\\', '')
            # print(smsurl)

            post_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'

            post_data = """entry=weibo&gateway=1&from=&savestate=7&qrcode_flag=false&useticket=1&pagerefer=https%3A%2F%2Fweibo.com%2F522143114%2Fhome&vsnf=1&su={su}&service=miniblog&servertime={servertime}&nonce={nonce}&pwencode=rsa2&rsakv={rsakv}&sp={sp}&sr=1440*900&encoding=UTF-8&prelt=247&url=https%3A%2F%2Fweibo.com%2Fajaxlogin.php%3Fframelogin%3D1%26callback%3Dparent.sinaSSOController.feedBackUrlCallBack&returntype=META""".format(
                su=su, servertime=pre_obj['servertime'], nonce=pre_obj['nonce'], rsakv=pre_obj['rsakv'], sp=sp)
            # post_data=parse.quote_plus(parse_data)

            html = self._ha.getstring(url=post_url, req_data=post_data, encoding='gbk')

            loginurl = re.findall(r"replace\('(.*?)'\)", html)[0]
            msg, redir = self._ha.getstring(loginurl, encoding='gbk')
            # if redir is None or redir == "":
            #     raise Exception("跳转失败")
            # res, redir = self._ha.getstring_unredirect(redir, encoding='gbk')

            # 不是仅判断Msg为空，而是去页面上判断登陆成功的标记
            if is_none_or_empty(msg):  # and '欢迎您:' in msg:
                self._logger.error("Password login failed.")
                return False

            self.cookie = self._ha._managedCookie.get_cookie_for_domain('https://weibo.com')
            res = self._cookie_login()
            return res
        except Exception:
            self._logger.error('{} passworde login fail: {}'.format(self.userid, traceback.format_exc()))

    def _sms_login(self):
        result = False
        try:
            name = self.task.phone
            if name is None or name == '':
                self._logger.error("Account is invalid: {} ".format(name))
                return False
            runntime = self._get_runntime(self._jspath.parent / 'sinalogin.js')
            s = name.encode('utf-8')
            su = base64.b64encode(s).decode('utf-8')

            # 获取预处理信息
            url = "http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su={su}&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.18)".format(
                su=su)
            headers = """
Referer: https://weibo.com/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36"""

            r = self._ha.getstring(url, headers=headers)
            json_pattern = r'.*?\((.*)\)'
            m = re.match(json_pattern, r)
            pre_obj = json.loads(m.group(1))

            # 模拟发送短信
            patsmsurl = re.compile(r'"smsurl":"(.*?)"')
            smsurl = patsmsurl.findall(r)[0].replace('\\', '')
            ressms = self._ha.getstring(smsurl)

            verification_code = self._get_vercode()

            sp = self._get_pass(verification_code, pre_obj, runntime)
            post_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'
            post_data = """entry=weibo&gateway=1&from=&savestate=7&qrcode_flag=false&useticket=1&pagerefer=https%3A%2F%2Fweibo.com%2Fp%2F1005055774635121%2Fmanage%3Ffrom%3Dpage_100505%26mod%3DTAB&cfrom=1&vsnf=1&su={su}&service=miniblog&servertime={servertime}&nonce={nonce}&pwencode=rsa2&rsakv={rsakv}&sp={sp}&sr=1440*900&encoding=UTF-8&prelt=156&url=https%3A%2F%2Fweibo.com%2Fajaxlogin.php%3Fframelogin%3D1%26callback%3Dparent.sinaSSOController.feedBackUrlCallBack&returntype=META""".format(
                su=su, servertime=pre_obj['servertime'], nonce=pre_obj['nonce'], rsakv=pre_obj['rsakv'], sp=sp)
            # post_data=parse.quote_plus(parse_data)
            headers = """
Host: login.sina.com.cn
Connection: keep-alive
Content-Length: 631
Cache-Control: max-age=0
Origin: https://weibo.com
Upgrade-Insecure-Requests: 1
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Referer: https://weibo.com/
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9"""
            html = self._ha.getstring(url=post_url, req_data=post_data, headers=headers)
            loginurl = substring(html, "location.replace('", "')")
            if is_none_or_empty(loginurl):
                self._logger.error("Get location url failed: {}".format(html))
                return result

            # re.findall(r"replace\('(.*?)'\)", html)[0]
            msg = self._ha.getstring(loginurl, encoding='gbk', headers="""
Referer: {}
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36""".format(
                loginurl))
            if is_none_or_empty(msg):
                self._logger.error("Sms login failed..'xxx' not found in page..")
                return False
            # if redir is None or redir == "":
            #     raise Exception("跳转失败")
            # res, redir = self._ha.getstring_unredirect(redir, encoding='gbk')
            self.cookie = self._ha._managedCookie.get_cookie_for_domain('https://weibo.com')
            result = self._cookie_login()
        except Exception:
            self._logger.error("{} Sms login error: {}".format(self.userid, traceback.format_exc()))

        return result

    def _cookie_login(self):
        try:
            self._ha._managedCookie.add_cookies('weibo.com', self.cookie)
            homeurl = 'https://weibo.com/home'
            home = self._ha.getstring(homeurl)
            self.userid = re.findall(r"CONFIG\['uid']='(.*?)'", home)[0]
            return True
        except Exception:
            self._logger.error("Cookie login error: {}".format(traceback.format_exc()))
            return False

    def _get_profile(self):
        try:
            url = 'https://account.weibo.com/set/iframe?skin=skin048'
            self._ha._managedCookie.add_cookies('weibo.com', self.cookie)
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: account.weibo.com
Pragma: no-cache
Referer: https://weibo.com
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36"""
            r = self._ha.getstring(url, headers=headers)
            soup = BeautifulSoup(r, 'lxml')
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)

            straccount = soup.select_one('.con')
            res.account = substring(str(straccount), '>', ' <a')
            try:
                res.account = re.findall(r'un=(.*?);', self.cookie)[0]
            except:
                pass
            res.phone = res.account
            res.nickname = soup.select_one('[node-type="nickname_view"]').get_text()
            # userid = nickname + '-weibo'

            res.region = soup.select_one('[node-type="city_view"]').get_text()
            res.birthday = soup.select_one('[node-type="birth_view"]').get_text()
            sex = soup.select_one('[node-type="sex_view"]').get_text()
            if sex == '男':
                res.gender = EGender.Male
            elif sex == '女':
                res.gender = EGender.Female
            email = soup.select_one('[node-type="email_view"]').get_text()
            if '@' in email:
                res.email = email
            detail = {}
            try:
                detail['真实姓名'] = soup.select_one('[node-type="realname_view"]').get_text()
            except:
                pass
            try:
                detail['性取向'] = soup.select_one('[node-type="sextrend_view"]').get_text()
            except:
                pass
            try:
                detail['感情状况'] = str(soup.select_one('[node-type="love_view"]').get_text()).replace('\t', '').replace(
                    '\n', '').replace(' ', '')
            except:
                pass
            try:
                detail['血型'] = soup.select_one('[node-type="blood_view"]').get_text()
            except:
                pass
            try:
                detail['博客地址'] = soup.select_one('[node-type="blog_view"]').get_text()
            except:
                pass
            try:
                detail['个性域名'] = soup.select_one('.con [target="_top"]').get_text()
            except:
                pass
            try:
                detail['简介'] = soup.select_one('[node-type="desc_view"]').get_text()
            except:
                pass
            try:
                detail['注册时间'] = soup.select('[node-type="desc_view"]')[1].get_text()
            except:
                pass
            try:
                detail['QQ'] = soup.select_one('[node-type="qq_view"] p').get_text()
            except:
                pass
            try:
                detail['MSN'] = soup.select_one('[node-type="msn_view"] p').get_text()
            except:
                pass
            try:
                detail['公司'] = soup.select_one('[node-type="joblist_item"]').get_text().replace('\t', '').replace('\n',
                                                                                                                  '').replace(
                    ' ', '')
            except:
                pass

            res.detail = detail

            getphotourl = 'https://weibo.com/messages'
            headers0 = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: weibo.com
Pragma: no-cache
Referer: https://weibo.com/message/history
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
"""
            html = self._ha.getstring(getphotourl, headers=headers0)
            photourl = re.findall(r"'avatar_large']='(.*?)';", html)[0]
            if photourl:
                photourl = 'https:' + photourl
                profilepic: RESOURCES = RESOURCES(self._clientid, self.task, photourl, EResourceType.Picture,
                                                  self._appcfg._apptype)

                resp_stream: ResponseIO = self._ha.get_response_stream(photourl)
                profilepic.io_stream = resp_stream
                profilepic.filename = photourl.rsplit('/', 1)[-1]
                profilepic.sign = ESign.PicUrl
                res.append_resource(profilepic)
                yield profilepic
            yield res
        except Exception:
            self._logger.error('{} got profile fail {}'.format(self.userid, traceback.format_exc()))

    def _get_group_chatlogs(self, grp):
        try:
            self._ha._managedCookie.add_cookies('weibo.com', self.cookie)
            max_mid = '0'
            last_read_mid = ''

            while max_mid != last_read_mid:
                #                 url = 'https://api.weibo.com/webim/groupchat/query_messages.json?source=209678993&callback=angular.callbacks._7&convert_emoji=1&count=200&id={gid}&max_mid={max_mid}&query_sender=1'.format(
                #                     gid=grp._groupid, max_mid=max_mid)
                #                 headers = """
                # Accept: */*
                # Accept-Encoding: gzip, deflate, br
                # Accept-Language: zh-CN,zh;q=0.9
                # Cache-Control: no-cache
                # Connection: keep-alive
                # Host: api.weibo.com
                # Pragma: no-cache
                # Referer: https://api.weibo.com/chat/
                # User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36"""
                #                 html = self._ha.getstring(url, headers=headers)
                #                 patismessages = re.compile(r'"messages":\[]')
                #                 ismessages = patismessages.search(html)
                #                 if ismessages:
                #                     url = 'https://api.weibo.com/webim/groupchat/query_messages.json?source=209678993&callback=angular.callbacks._7&convert_emoji=1&count=200&id={gid}&max_mid={max_mid}&query_sender=1'.format(
                #                         gid=grp._groupid, max_mid=max_mid)
                #                     headers = """
                # Accept: */*
                # Accept-Encoding: gzip, deflate, br
                # Accept-Language: zh-CN,zh;q=0.9
                # Cache-Control: no-cache
                # Connection: keep-alive
                # Host: api.weibo.com
                # Pragma: no-cache
                # Referer: https://api.weibo.com/chat/
                # User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36"""
                #                     html = self._ha.getstring(url, headers=headers)
                #                     patismessages = re.compile(r'"messages":\[]')
                #                     ismessages = patismessages.search(html)
                #                     if ismessages:
                #                         break
                #                 pat = re.compile(r'"data":(.*?)}\)')
                #                 datajs = pat.findall(html)[0]
                res, data = self._is_group_chatlog(grp._groupid, max_mid)
                if not res:
                    break
                data = parse_js(data)
                last_read_mid = data['last_read_mid']
                i = 0
                for msg in data['messages']:
                    if i == 0:
                        max_mid = msg['id']

                    sessionid = grp._groupid
                    messageid = str(msg['id'])
                    messagetype = 4
                    chattype = 1
                    senderid = msg['from_uid']
                    content = msg['content']
                    # 获取时间戳转date
                    timeStamp = msg['time']
                    timeArray = time.localtime(timeStamp)
                    sendtime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
                    sendername = msg['from_user']['screen_name']
                    ishttp = re.findall(r'http', msg['content'])
                    if ishttp != []:
                        messagetype = 3
                    resources = []
                    try:
                        for resourceid in msg['fids']:
                            url = 'https://upload.api.weibo.com/2/mss/meta_query.json?source=209678993&callback=angular.callbacks._2d&fid={}'.format(
                                resourceid)
                            html = self._ha.getstring(url)
                            extension = substring(html, 'extension":"', '"')
                            filename = substring(html, '"filename":"', '"')
                            if extension == 'jpg' or extension == 'png' or extension == 'gif' or extension == 'bmp' or extension == 'webp':
                                messagetype = 0
                                resourceurl = 'https://upload.api.weibo.com/2/mss/msget_thumbnail?fid={}&high=240&width=240&size=240,150&source=209678993'.format(
                                    resourceid)

                                resource: RESOURCES = RESOURCES(self._clientid, self.task, resourceurl,
                                                                EResourceType.Picture,
                                                                self._appcfg._apptype)

                                resp_stream: ResponseIO = self._ha.get_response_stream(resourceurl)
                                if not resp_stream:
                                    continue
                                resource.io_stream = resp_stream
                                if not isinstance(resourceid, str):
                                    resourceid = str(resourceid)
                                resource.resourceid = resourceid
                                resource.filename = filename
                                yield resource
                                resources.append(resource)

                            elif extension in ['mp4', 'mkv', 'avi', 'rmvb', 'mov', 'mpg', 'mlv', 'mpe', 'dat']:
                                messagetype = 1
                                resourceurl = 'https://upload.api.weibo.com/2/mss/msget?source=209678993&fid={}'.format(
                                    resourceid)

                                resource: RESOURCES = RESOURCES(self._clientid, self.task, resourceurl,
                                                                EResourceType.Video,
                                                                self._appcfg._apptype)

                                resp_stream: ResponseIO = self._ha.get_response_stream(resourceurl)
                                if not resp_stream:
                                    continue
                                resource.io_stream = resp_stream
                                if not isinstance(resourceid, str):
                                    resourceid = str(resourceid)
                                resource.resourceid = resourceid
                                resource.filename = filename
                                yield resource
                                resources.append(resource)

                            elif extension in ['mp3', 'wma', 'rm', 'wav', 'midi', 'ape', 'flac']:
                                messagetype = 2
                                resourceurl = 'https://upload.api.weibo.com/2/mss/msget?source=209678993&fid={}'.format(
                                    resourceid)

                                resource: RESOURCES = RESOURCES(self._clientid, self.task, resourceurl,
                                                                EResourceType.Audio,
                                                                self._appcfg._apptype)

                                resp_stream: ResponseIO = self._ha.get_response_stream(resourceurl)
                                if not resp_stream:
                                    continue
                                resource.io_stream = resp_stream
                                if not isinstance(resourceid, str):
                                    resourceid = str(resourceid)
                                resource.resourceid = resourceid
                                resource.filename = filename
                                yield resource
                                resources.append(resource)

                            else:
                                resourceurl = 'https://upload.api.weibo.com/2/mss/msget?source=209678993&fid={}'.format(
                                    resourceid)

                                resource: RESOURCES = RESOURCES(self._clientid, self.task, resourceurl,
                                                                EResourceType.Other_Text,
                                                                self._appcfg._apptype)

                                resp_stream: ResponseIO = self._ha.get_response_stream(resourceurl)
                                if not resp_stream:
                                    continue
                                resource.io_stream = resp_stream
                                if not isinstance(resourceid, str):
                                    resourceid = str(resourceid)
                                resource.resourceid = resourceid
                                resource.filename = filename
                                yield resource
                                resources.append(resource)

                    except:
                        pass

                    res_one = ICHATLOG_ONE(self.task, self._appcfg._apptype, self.userid, messagetype, sessionid,
                                           chattype,
                                           messageid, senderid, sendtime)
                    res_one.content = content
                    res_one.sendername = sendername
                    if resources:
                        for resource in resources:
                            res_one.append_resource(resource)
                    yield res_one
                    i += 1
        except Exception:
            self._logger.error('{} got group chatlog fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_contact_chatlogs(self, ct):
        try:
            max_id = '0'
            ischatlog = False
            while not ischatlog:
                self._ha._managedCookie.add_cookies('weibo.com', self.cookie)
                res, data = self._is_contact_chatlog(max_id, ct._contactid)
                if not res:
                    break
                data = parse_js(data)
                for msg in data['direct_messages']:
                    max_id = str(int(msg['id']) - 1)

                    sessionid = ct._contactid
                    messageid = str(msg['id'])
                    messagetype = 4
                    chattype = 0
                    senderid = msg['sender_id']

                    # UTC时间格式转换
                    newTime = msg['created_at']
                    GMT_FORMAT = '%a %b %d %H:%M:%S +0800 %Y'
                    newTimes = datetime.datetime.strptime(newTime, GMT_FORMAT)
                    sendtime = str(newTimes)
                    sendername = msg['sender_screen_name']
                    content = msg['text']
                    ishttp = re.findall(r'http', msg['text'])
                    if ishttp != []:
                        messagetype = 3
                    resources = []
                    try:
                        for resourceid in msg['att_ids']:
                            url = 'https://upload.api.weibo.com/2/mss/meta_query.json?source=209678993&callback=angular.callbacks._2d&fid={}'.format(
                                resourceid)
                            html = self._ha.getstring(url)
                            extension = substring(html, 'extension":"', '"')
                            filename = substring(html, '"filename":"', '"')
                            if extension == 'jpg' or extension == 'png' or extension == 'gif' or extension == 'bmp' or extension == 'webp':
                                messagetype = 0
                                resourceurl = 'https://upload.api.weibo.com/2/mss/msget_thumbnail?fid={}&high=240&width=240&size=240,150&source=209678993'.format(
                                    resourceid)

                                resource: RESOURCES = RESOURCES(self._clientid, self.task, resourceurl,
                                                                EResourceType.Picture,
                                                                self._appcfg._apptype)

                                resp_stream: ResponseIO = self._ha.get_response_stream(resourceurl)
                                if not resp_stream:
                                    continue
                                resource.io_stream = resp_stream
                                if not isinstance(resourceid, str):
                                    resourceid = str(resourceid)
                                resource.resourceid = resourceid
                                resource.filename = filename
                                yield resource
                                resources.append(resource)

                            elif extension in ['mp4', 'mkv', 'avi', 'rmvb', 'mov', 'mpg', 'mlv', 'mpe', 'dat']:
                                messagetype = 1
                                resourceurl = 'https://upload.api.weibo.com/2/mss/msget?source=209678993&fid={}'.format(
                                    resourceid)

                                resource: RESOURCES = RESOURCES(self._clientid, self.task, resourceurl,
                                                                EResourceType.Video,
                                                                self._appcfg._apptype)

                                resp_stream: ResponseIO = self._ha.get_response_stream(resourceurl)
                                if not resp_stream:
                                    continue
                                resource.io_stream = resp_stream
                                if not isinstance(resourceid, str):
                                    resourceid = str(resourceid)
                                resource.resourceid = resourceid
                                resource.filename = filename
                                yield resource
                                resources.append(resource)

                            elif extension in ['mp3', 'wma', 'rm', 'wav', 'midi', 'ape', 'flac']:
                                messagetype = 2
                                resourceurl = 'https://upload.api.weibo.com/2/mss/msget?source=209678993&fid={}'.format(
                                    resourceid)

                                resource: RESOURCES = RESOURCES(self._clientid, self.task, resourceurl,
                                                                EResourceType.Audio,
                                                                self._appcfg._apptype)

                                resp_stream: ResponseIO = self._ha.get_response_stream(resourceurl)
                                if not resp_stream:
                                    continue
                                resource.io_stream = resp_stream
                                if not isinstance(resourceid, str):
                                    resourceid = str(resourceid)
                                resource.resourceid = resourceid
                                resource.filename = filename
                                yield resource
                                resources.append(resource)

                            else:
                                resourceurl = 'https://upload.api.weibo.com/2/mss/msget?source=209678993&fid={}'.format(
                                    resourceid)

                                resource: RESOURCES = RESOURCES(self._clientid, self.task, resourceurl,
                                                                EResourceType.Other_Text,
                                                                self._appcfg._apptype)

                                resp_stream: ResponseIO = self._ha.get_response_stream(resourceurl)
                                if not resp_stream:
                                    continue
                                resource.io_stream = resp_stream
                                if not isinstance(resourceid, str):
                                    resourceid = str(resourceid)
                                resource.resourceid = resourceid
                                resource.filename = filename
                                yield resource
                                resources.append(resource)
                    except:
                        pass

                    res_one = ICHATLOG_ONE(self.task, self._appcfg._apptype, self.userid, messagetype, sessionid,
                                           chattype,
                                           messageid, senderid, sendtime)
                    res_one.content = content
                    res_one.sendername = sendername
                    if resources:
                        for resource in resources:
                            res_one.append_resource(resource)
                    yield res_one
        except Exception:
            self._logger.error('{} got contact chatlog fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_contacts(self):
        try:
            self._ha._managedCookie.add_cookies('weibo.com', self.cookie)
            # 获取分组id
            url = 'https://weibo.com/messages'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: weibo.com
Pragma: no-cache
Referer: https://weibo.com/message/history
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
"""
            html = self._ha.getstring(url, headers=headers)
            patgid = re.compile(r'gid=\\"(.*?)\\"')
            gidlist = patgid.findall(html)

            # 遍历联系人分组，从中获取联系人列表
            for gid in gidlist:
                contacturl = 'https://weibo.com/aj/relation/groupmembers?gid={gid}'.format(gid=gid)
                headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Type: application/x-www-form-urlencoded
Host: weibo.com
Pragma: no-cache
Referer: https://weibo.com/messages
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
X-Requested-With: XMLHttpRequest"""
                html = self._ha.getstring(contacturl, headers=headers)
                jshtml = parse_js(html)
                if jshtml['data'] == {}:
                    continue
                for contact in jshtml['data']['users']:
                    try:
                        dic = {}
                        dic['contactid'] = contact['idstr']
                        dic['nickname'] = contact['screen_name']
                        dic['picurl'] = 'https:' + contact['profile_image_url'].replace('\\', '')
                        gender = contact['gender']
                        if gender == 'm':
                            dic['gender'] = EGender.Male
                        elif gender == 'f':
                            dic['gender'] = EGender.Female
                        else:
                            dic['gender'] = EGender.Unknown
                        dic['group'] = contact['group']['gname']
                        dic['contact_type'] = 1
                        detail = {}
                        detail['location'] = contact['location']
                        detail['description'] = contact['description']
                        detail['verified_reason'] = contact['verified_reason']
                        dic['detail'] = detail
                        if not self.all_contacts.__contains__(dic['contactid']):
                            self.all_contacts.append(dic['contactid'])
                            res_one = CONTACT_ONE(self.userid, dic['contactid'], self.task, self._appcfg._apptype)
                            res_one.detail = detail
                            res_one.nickname = dic['nickname']
                            res_one.gender = dic['gender']
                            res_one.group = dic['group']
                            res_one.contact_type = dic['contact_type']

                            if dic['picurl']:
                                res_one.picurl = dic['picurl']

                                contactpic: RESOURCES = RESOURCES(self._clientid, self.task, res_one.picurl,
                                                                  EResourceType.Picture,
                                                                  self._appcfg._apptype)
                                resp_stream: ResponseIO = self._ha.get_response_stream(res_one.picurl)
                                if not resp_stream:
                                    continue
                                contactpic.io_stream = resp_stream
                                rid = contact['profile_url']
                                if not isinstance(rid, str):
                                    rid = str(rid)
                                contactpic.resourceid = rid
                                contactpic.filename = dic['picurl'].rsplit('/', 1)[-1]
                                contactpic.sign = ESign.PicUrl
                                res_one.append_resource(contactpic)
                                yield contactpic

                            yield res_one

                    except Exception:
                        self._logger.error("Parse one contact error: {}".format(traceback.format_exc()))

            # 聊天记录页获取联系人（陌生人）
            # for page in range(1, 1000):
            page = 0
            while True:
                page += 1
                url = 'https://weibo.com/messages?page={page}'.format(page=page)
                headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: weibo.com
Pragma: no-cache
Referer: https://weibo.com/message/history
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
"""
                html = self._ha.getstring(url, headers=headers)
                r = html.replace('\\n', '').replace('\\t', '').replace('\\', '')
                r1 = re.findall(r'"html":"(.*?)"}\)</script>', r)[4]
                soup = BeautifulSoup(r1, 'lxml')
                body = soup.select('.private_body')[0]
                # private_body = re.findall(r'(<div class="private_body">.*?下一页</a></div></div>)', r, re.S)[0]
                # body = BeautifulSoup(private_body, 'lxml')
                private_list = body.select('.private_list.SW_fun_bg.S_line2.clearfix')
                for contacts in private_list:
                    try:

                        dic = {}
                        isgid = re.findall(r'gid=', str(contacts))
                        if isgid != []:
                            continue
                        dic['contactid'] = contacts.attrs.get('uid')
                        dic['nickname'] = contacts.select_one('.W_face_radius')['alt']
                        dic['picurl'] = 'https:' + contacts.select_one('.W_face_radius')['src']
                        dic['contact_type'] = 0
                        # dic['contact_type']
                        detail = {}
                        detail['最近联系时间'] = contacts.select_one('.data.W_fl.S_txt2').get_text()
                        try:
                            detail['微博类型'] = contacts.select_one('[suda-data="key=pc_apply_entry&value=feed_icon"] i')[
                                'title']
                        except:
                            pass
                        dic['detail'] = detail

                        if not self.all_contacts.__contains__(dic['contactid']):
                            res_one = CONTACT_ONE(self.userid, dic['contactid'], self.task, self._appcfg._apptype)
                            res_one.detail = detail
                            res_one.isfriend = 0
                            res_one.bothfriend = 0
                            res_one.nickname = dic['nickname']

                            if dic['picurl']:
                                res_one.picurl = dic['picurl']
                                contactpic: RESOURCES = RESOURCES(self._clientid, self.task, res_one.picurl,
                                                                  EResourceType.Picture,
                                                                  self._appcfg._apptype)

                                resp_stream: ResponseIO = self._ha.get_response_stream(res_one.picurl)
                                contactpic.io_stream = resp_stream
                                contactpic.filename = dic['picurl'].rsplit('/', 1)[-1]
                                contactpic.sign = ESign.PicUrl
                                res_one.append_resource(contactpic)
                                yield contactpic
                            yield res_one
                    except Exception:
                        self._logger.error("Parse one stranger error: {}".format(traceback.format_exc()))

                patnextpage = re.compile('下一页')
                nextpage = patnextpage.search(r)
                if not nextpage:
                    break
                patispage = re.compile(r'href="javascript:void\(0\);" class="page_dis page next S_txt1 S_line1">下一页')
                ispage = patispage.search(r)
                if ispage:
                    break
        except Exception:
            self._logger.error('{} got contacts fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_groups(self):
        try:
            all_groups = {}
            self._ha._managedCookie.add_cookies('weibo.com', self.cookie)

            # 获取群组列表中的群id（自己创建）
            url = 'https://weibo.com/aj/message/getjoingroups'
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Type: application/x-www-form-urlencoded
Host: weibo.com
Pragma: no-cache
Referer: https://weibo.com/message/history
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            html = self._ha.getstring(url, headers=headers)
            try:
                jshtml = parse_js(html)

                for group in jshtml['data']['join_groups']:
                    dic = {}
                    dic['groupid'] = str(group['id'])
                    if not all_groups.__contains__(dic['groupid']):
                        all_groups[dic['groupid']] = dic

                # 聊天记录页获取群id（非自己创建）
                page = 0
                while True:
                    page += 1
                    url = 'https://weibo.com/messages?page={page}'.format(page=page)
                    headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: weibo.com
Pragma: no-cache
Referer: https://weibo.com/message/history
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
"""
                    html = self._ha.getstring(url, headers=headers)
                    r = html.replace('\\n', '').replace('\\t', '').replace('\\', '')
                    r1 = re.findall(r'"html":"(.*?)"}\)</script>', r)[4]
                    soup = BeautifulSoup(r1, 'lxml')
                    body = soup.select('.private_body')[0]
                    # private_body = re.findall(r'(<div class="private_body">.*?下一页</a></div></div>)', r, re.S)[0]
                    # body = BeautifulSoup(private_body, 'lxml')
                    private_list = body.select('.private_list.SW_fun_bg.S_line2.clearfix')
                    for groups in private_list:
                        isgid = re.findall(r'uid=', str(groups))
                        if isgid != []:
                            continue
                        dic0 = {}
                        dic0['groupid'] = groups.attrs.get('gid')
                        if not all_groups.__contains__(dic0['groupid']):
                            all_groups[dic0['groupid']] = dic0
                    patnextpage = re.compile('下一页')
                    nextpage = patnextpage.search(r)
                    if not nextpage:
                        break
                    patispage = re.compile(
                        r'href="javascript:void\(0\);" class="page_dis page next S_txt1 S_line1">下一页')
                    ispage = patispage.search(r)
                    if ispage:
                        break
            except Exception:
                self._logger.error("Got one groupid error: {}".format(traceback.format_exc()))

            # 遍历群id获取群组信息

            for groupid in all_groups:
                try:
                    url = 'https://api.weibo.com/webim/query_group.json?source=209678993&callback=angular.callbacks._8&id={gid}&is_pc=1&query_member=1&query_member_count=100&sort_by_jp=1'.format(
                        gid=groupid)
                    headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: api.weibo.com
Pragma: no-cache
Referer: https://api.weibo.com/chat/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36"""
                    html = self._ha.getstring(url, headers=headers)
                    data = re.findall(r'"data":(.*?)}\);}', html)[0]
                    jsdata = parse_js(data)
                    # self.member_infos = jsdata['member_infos']

                    participants = list(jsdata['members'])
                    groupname = jsdata['name']
                    grouppicurl = jsdata['round_avatar']

                    res_one = ICHATGROUP_ONE(self.task, self._appcfg._apptype, self.userid, groupid)
                    res_one.append_participants(*participants)
                    res_one.groupname = groupname
                    if grouppicurl:
                        grouppic: RESOURCES = RESOURCES(self._clientid, self.task, grouppicurl, EResourceType.Picture,
                                                        self._appcfg._apptype)
                        resp_stream: ResponseIO = self._ha.get_response_stream(grouppicurl)
                        grouppic.io_stream = resp_stream
                        grouppic.filename = grouppicurl.rsplit('/', 1)[-1]
                        grouppic.sign = ESign.PicUrl
                        res_one.append_resource(grouppic)
                        yield grouppic
                    yield res_one
                except Exception:
                    self._logger.error("{} Got one group error: {}".format(self.userid, traceback.format_exc()))
        except Exception:
            self._logger.error("{} Got groups error: {}".format(self.userid, traceback.format_exc()))

    def _get_group_contacts(self, grp):
        try:
            url = 'https://api.weibo.com/webim/query_group.json?source=209678993&callback=angular.callbacks._8&id={gid}&is_pc=1&query_member=1&query_member_count=100&sort_by_jp=1'.format(
                gid=grp._groupid)
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: api.weibo.com
Referer: http://api.weibo.com/chat/
Pragma: no-cache
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            data = re.findall(r'"data":(.*?)}\);}', html)[0]
            jsdata = parse_js(data)
            member_infos = jsdata['member_infos']

            for member_info in member_infos:
                res_one = CONTACT_ONE(self.userid, member_info['uid'], self.task, self._appcfg._apptype)
                if member_info['uid'] not in self.all_contacts:
                    res_one.isfriend = 0
                    res_one.bothfriend = 0
                res_one.nickname = member_info['screen_name']
                contactpicurl = member_info['profile_image_url']
                if contactpicurl:
                    contactpic: RESOURCES = RESOURCES(self._clientid, self.task, contactpicurl,
                                                      EResourceType.Picture,
                                                      self._appcfg._apptype)
                    resp_stream: ResponseIO = self._ha.get_response_stream(contactpicurl)
                    contactpic.io_stream = resp_stream
                    contactpic.filename = contactpicurl.rsplit('/', 1)[-1]
                    contactpic.sign = ESign.PicUrl
                    res_one.append_resource(contactpic)
                    yield contactpic
                yield res_one
        except Exception:
            self._logger.error('{} got group contacts fail: {}'.format(self.userid, traceback.format_exc()))

    # 编译js环境
    def _get_runntime(self, path):
        """
        :param path: 加密js的路径,注意js中不要使用中文！估计是pyexecjs处理中文还有一些问题
        :return: 编译后的js环境
        """
        phantom = execjs.get('PhantomJS')  # 这里必须为phantomjs设置环境变量，否则可以写phantomjs的具体路径
        with open(path, 'r') as f:
            source = f.read()
        return phantom.compile(source)

    # 获取加密后的密码
    def _get_pass(self, password, pre_obj, runntime):
        """
        :param password: 登陆密码
        :param pre_obj: 返回的预登陆信息
        :param runntime: 运行时环境
        :return: 加密后的密码
        """
        nonce = pre_obj['nonce']
        pubkey = pre_obj['pubkey']
        servertime = pre_obj['servertime']
        return runntime.call('get_pass', password, nonce, servertime, pubkey)

    # 循环获取联系人200条聊天记录.防止访问到一半访问频繁
    def _is_contact_chatlog(self, max_id, uid):
        try:
            res = True
            failed_count = 0
            while True:
                url = 'https://api.weibo.com/webim/2/direct_messages/conversation.json?source=209678993&callback=angular.callbacks._a&convert_emoji=1&count=200&is_include_group=0&max_id={max_id}&uid={uid}'.format(
                    max_id=max_id, uid=uid)
                headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: api.weibo.com
Pragma: no-cache
Referer: https://api.weibo.com/chat/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36"""
                html = self._ha.getstring(url, headers=headers)
                patchatlog = re.compile(r'"direct_messages":\[]')
                ischatlog = patchatlog.search(html)

                # while not ischatlog:
                #     res = False
                #     html = ha.getstring(url, headers=headers)
                #     patchatlog = re.compile(r'"direct_messages":\[]')
                #     ischatlog = patchatlog.search(html)

                if ischatlog:
                    failed_count += 1
                    if failed_count >= 3:
                        res = False
                        break
                else:
                    break

            if res:
                data = re.findall(r'"data":(.*?)}\)', html)[0]

            else:
                data = ''
            return res, data
        except Exception:
            self._logger.error('{} is contact chatlog fail: {}'.format(self.userid, traceback.format_exc()))

    # 循环获取群组200条聊天记录.防止访问到一半访问频繁
    def _is_group_chatlog(self, gid, max_mid):
        try:
            res = True
            failed_count = 0
            while True:
                url = 'https://api.weibo.com/webim/groupchat/query_messages.json?source=209678993&callback=angular.callbacks._7&convert_emoji=1&count=20&id={gid}&max_mid={max_mid}&query_sender=1'.format(
                    gid=gid, max_mid=max_mid)
                headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: api.weibo.com
Pragma: no-cache
Referer: https://api.weibo.com/chat/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36"""
                html = self._ha.getstring(url, headers=headers)
                patismessages = re.compile(r'"messages":\[]')
                ismessages = patismessages.search(html)

                if ismessages:
                    failed_count += 1
                    if failed_count >= 3:
                        res = False
                        break
                else:
                    break

            if res:
                pat = re.compile(r'"data":(.*?)}\)')
                data = pat.findall(html)[0]

            else:
                data = ''
            return res, data
        except Exception:
            self._logger.error('{} is group chatlog fail: {}'.format(self.userid, traceback.format_exc()))

    def _logout(self):
        res = False
        try:
            url = 'https://passport.weibo.com/wbsso/logout?r=https%3A%2F%2Fweibo.com&returntype=1'
            html = self._ha.getstring(url, headers="""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: passport.weibo.com
Pragma: no-cache
Referer: https://login.sina.com.cn/crossdomain2.php?action=logout&r=https%3A%2F%2Fpassport.weibo.com%2Fwbsso%2Flogout%3Fr%3Dhttps%253A%252F%252Fweibo.com%26returntype%3D1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")
            res = self._cookie_login()
            if not res:
                res = True
        except Exception:
            self._logger.error('login out fail:{}'.format(traceback.format_exc()))
        return res
