"""spider mail 21cn"""

# -*- coding:utf-8 -*-

import pytz
import json
import random
import time
import traceback
import datetime
import base64

from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess import HttpAccess, ResponseIO

from .spidermailbase import SpiderMailBase
from ...clientdatafeedback import CONTACT_ONE, CONTACT, EML, Folder, PROFILE, RESOURCES, EResourceType, ESign


class Spider21CN(SpiderMailBase):

    def __init__(self, task, appcfg, clientid):
        super(Spider21CN, self).__init__(task, appcfg, clientid)
        if self.task.cookie:
            self._ha._managedCookie.add_cookies('21cn.com', self.task.cookie)

    def _cookie_login(self) -> bool:
        try:
            url = 'http://mail.21cn.com/w2/logon/signOn.do'
            headers = """
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: no-cache
            Host: mail.21cn.com
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Referer: http://mail.21cn.com/w2/template/inbox.jsp
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            if "21CN个人邮箱" in html and "退出" in html and "收信" in html:
                strAccount = substring(html, "accountName\":\"", "\"")
                if not strAccount or strAccount == "-1":
                    # self._log("Get account failed.")
                    return False
                else:
                    self.userid = strAccount + '-MAIL21cn'
                    return True
            else:
                return False
        except Exception:
            self._logger.error('Cookie login fail: {}'.format(traceback.format_exc()))
            return False

    def _pwd_login(self):
        res = False
        try:
            if not self.task.account or not self.task.password:
                return res
#             url = 'http://mail.21cn.com'
#             headers = """
# Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
# Accept-Encoding:gzip, deflate, sdch
# Accept-Language:zh-CN,zh;q=0.8
# Connection:keep-alive
# User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36"""
#             html = self._ha.getstring(url, headers=headers)
#             urlJump = substring(html, "window.location=\"", "\"")
#
#             headers = """
# Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
# Accept-Encoding:gzip, deflate, sdch
# Accept-Language:zh-CN,zh;q=0.8
# Connection:keep-alive
# Referer:http://mail.21cn.com/"""
#             html = self._ha.getstring(urlJump, headers=headers)

            # 一个验证，拿appid
            url = 'http://mail.21cn.com/w2/logon/UnifyLogin.do?t={}'.format(int(datetime.datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000))
            headers = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Accept-Encoding:gzip, deflate, sdch
Accept-Language:zh-CN,zh;q=0.9
Connection:keep-alive
Host: mail.21cn.com
Referer:https://mail.21cn.com/w2/
Sec-Fetch-Dest: iframe
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-origin
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"""
            html, redir = self._ha.getstring_with_reurl(url, headers=headers)
            appid = substring(redir, "appId=", "&")
            if not html or not appid:
                # logger.LogInformation($@"{strAccount} Get appid failed.");
                appid = "8013411507"

            # 验证账号
            url = f"http://open.e.189.cn/api/common/needcaptcha.do?appId={appid}"
            headers = f"""
Accept:application/json, text/javascript, */*; q=0.01
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.8
Connection:keep-alive
Content-Type:application/x-www-form-urlencoded; charset=UTF-8
Origin:http://open.e.189.cn
Referer:{redir}
X-Requested-With:XMLHttpRequest"""
            strAccount = self.task.account
            password = self.task.password
            postdata = f"userName={strAccount}&apptype=web"
            html = self._ha.getstring(url, headers=headers, req_data=postdata)

            # //登陆
            try:
                lsid = self._ha.cookies.get_dict()["LSID"]
            except:
                # logger.LogInformation($@"{strAccount} Get LSID failed.");
                return res
            url = 'https://open.e.189.cn/api/common/loginSubmit.do'
            postData = f"clientType=&accountType=02&appId={appid}&returnUrl=http%3A%2F%2Fmail.21cn.com%2Fw2%2Flogon%2FunifyPlatformLogonReturn.do%3FLSID%3D{lsid}&captchaToken=&ValidateCode=&userName={strAccount}&password={password}"
            headers = f"""
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding:gzip, deflate, br
Accept-Language:zh-CN,zh;q=0.8
Connection:keep-alive
Content-Type:application/x-www-form-urlencoded
Origin:http://open.e.189.cn
Referer:{redir}
Upgrade-Insecure-Requests:1"""
            html = self._ha.getstring(url, headers=headers, req_data=postData)
            msg = substring(html, "\"msg\":\"", "\"").lower()
            toUrl = substring(html, "\"toUrl\":\"", "\"")
            if not html or not msg == "success" or not toUrl:
                # logger.LogInformation($@"{strAccount} Login failed: {msg}");
                return res

            # //第一次跳转
            headers = f"""
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding:gzip, deflate, sdch
Accept-Language:zh-CN,zh;q=0.8
Connection:keep-alive
Referer:{redir}
Upgrade-Insecure-Requests:1"""
            html, forwardLogin = self._ha.getstring_with_reurl(toUrl, headers=headers)
            homePageUrl = substring(html, "window.parent.location.href=\"", "\"")
            if not html or not homePageUrl:
                # 'logger.LogInformation($@"{strAccount} Get login url failed.");
                return res
            if "http://" not in homePageUrl:
                homePageUrl = f"http://mail.21cn.com/{homePageUrl.lstrip('/')}"

            # 访问主页
            headers = f"""
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding:gzip, deflate, sdch
Accept-Language:zh-CN,zh;q=0.8
Connection:keep-alive
Referer:{forwardLogin}
Upgrade-Insecure-Requests:1"""
            html = self._ha.getstring(homePageUrl, headers=headers)
            if not html or strAccount not in html:
                # 'logger.LogInformation($@"{strAccount} Access homePage failed.");
                return res
            newcookie = self._ha._managedCookie.get_cookie_for_domain('http://21cn.com')

            res = self._cookie_login()
            return res

        except Exception as ex:
            self._logger.error('Password login fail: {}'.format(traceback.format_exc()))
            self._write_log_back("账密登录失败: {}".format(ex.args))
            return False

    def _get_contacts(self):
        try:
            res = None
            pageNum = 0
            nextPage = True
            host = 'mail.21cn.com'
            while nextPage:
                pageNum += 1
                url = f"http://mail.21cn.com/w2/contact/showManList.do?pageNum={pageNum}&desc=0&orderName=0&keyword=&sKey=&groupUuid=&noCache={random.random()}"
                html = self._ha.getstring(url, headers=f"""
Accept:*/*
Accept-Encoding:gzip, deflate, sdch
Accept-Language:zh-CN,zh;q=0.8
Connection:keep-alive
Referer:http://{host}/w2/logon/signOn.do
User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36
X-Requested-With:XMLHttpRequest""")
                if not html or "\"code\":0" not in html:
                    # 'logger.LogInformation($@"{strAccount}  Get contacts failed: {html}");
                    return res
                js = json.loads(html)
                pageNum = js['pageNum']
                pageSize = js['pageSize']
                totalSize = js['totalSize']
                nextPage = totalSize > (pageNum * pageSize)

                contactList = js['contactList']
                if contactList:
                    res = CONTACT(self._clientid, self.task, self.task.apptype)
                    for contact in contactList:
                        try:
                            contactid = contact['linkManUuid']
                            res_one = CONTACT_ONE(self.userid, contactid, self.task, self.task.apptype)
                            res_one.email = contact['mailAddress']
                            res_one.nickname = contact['linkManName']
                            res_one.phone = contact['phoneNum']
                            groupname: str = contact['groupInfoList'][0]['groupName']
                            res_one.group = '=?utf-8?b?' + str(base64.b64encode(groupname.encode('utf-8')), 'utf-8')
                            res.append_innerdata(res_one)
                        except:
                            pass
                    if res.innerdata_len > 0:
                        yield res
        except Exception:
            self._logger.error("Got contacts error, err:{}".format(traceback.format_exc()))

    def _get_folders(self):
        dic = {'1': '收件箱', '2': '草稿箱', '3': '发件箱', '4': '垃圾箱', '5': '回收箱', '6': '定时邮件夹', '7': '广告邮箱',
               '8': '安全邮件夹', '104': '星标邮箱'}
        for id in dic:
            res = Folder()
            res.folderid = id
            res.name = dic[id]
            yield res

    def _get_mails(self, folder: Folder):
        try:
            pageNum = 0
            next = True
            while next:
                pageNum += 1
                url = f'http://mail.21cn.com/w2/mail/listMail.do?labelId={folder.folderid}&pageNum={pageNum}&excludeFlag=&mailFlag=&noCache={random.random()}'
                html = self._ha.getstring(url, headers=f"""
Accept:*/*
Accept-Encoding:gzip, deflate, sdch
Accept-Language:zh-CN,zh;q=0.8
Cache-Control:no-cache
Connection:keep-alive
Pragma:no-cache
Referer:ttp://mail.21cn.com/w2/logon/signOn.do
X-Requested-With:XMLHttpRequest""")
                if not html or "\"code\":0" not in html:
                    # 'logger.LogInformation($@"{strAccount} Get mail list failed: {html}");
                    break
                jshtml = json.loads(html)
                mailCount = jshtml['mailCount']
                pageNumTmp = jshtml['pageNum']
                pageSize = jshtml['pageSize']
                mailList = jshtml['mailList']
                next = mailCount > (pageNumTmp * pageSize)
                if mailList:
                    for mail in mailList:
                        messageId = mail['messageId']
                        res_one = EML(self._clientid, self.task, self.userid, messageId, folder, self.task.apptype)
                        res_one.provider = json.dumps(mail['sendersAddress'])
                        res_one.owner = json.dumps(mail['toAddress'])
                        res_one.subject = mail['subject']
                        sendDate = mail['sendDate']
                        t = time.localtime(int(sendDate) / 1000)
                        sendtime = time.strftime('%Y-%m-%d %H:%M:%S', t)
                        res_one.sendtime = datetime.datetime.strptime(sendtime, "%Y-%m-%d %H:%M:%S")
                        newMail = mail['newMail']
                        if not newMail:
                            res_one.state = 1
                        else:
                            res_one.state = 0
                        messageId = mail['messageId']
                        msId = mail['msId']
                        downloadUrl = f'http://mail.21cn.com/w2/downLoadAttachNormal.do?messageid={messageId}&msid={msId}&partid=9999'
                        downHeaders = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Encoding:gzip, deflate, sdch
Accept-Language:zh-CN,zh;q=0.8
Cache-Control:no-cache
Connection:keep-alive
Pragma:no-cache
Referer:http://mail.21cn.com/w2/logon/signOn.do
Upgrade-Insecure-Requests:1"""
                        # res_one.io_stream = self._ha.get_response_stream(downloadUrl, headers=downHeaders)
                        resp = self._ha.get_response(downloadUrl, headers=downHeaders)
                        if resp.status_code == 200:
                            res_one.stream_length = resp.headers.get('Content-Length', 0)
                            res_one.io_stream = ResponseIO(resp)
                            yield res_one
        except Exception:
            self._logger.error('{} Got mails fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_profile(self):
        try:
            url = 'http://mail.21cn.com/w2/logon/signOn.do'
            html = self._ha.getstring(url, headers="""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Host: mail.21cn.com
Pragma: no-cache
Proxy-Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36""")
            detail = {}
            detail['userid'] = substring(html, '"uuserId":"', '"')
            res = PROFILE(self._clientid, self.task, self.task.apptype, self.userid)
            res.nickname = substring(html, '"userName":"', '"')
            res.account = substring(html, 'accountName":"', '"')
            photourl = substring(html, 'src="..', '"')
            if photourl:
                photourl = 'http://mail.21cn.com/w2' + photourl
                profilepic: RESOURCES = RESOURCES(self._clientid, self.task, photourl, EResourceType.Picture,
                                                  self.task.apptype)

                resp_stream: ResponseIO = self._ha.get_response_stream(photourl)
                profilepic.io_stream = resp_stream
                profilepic.filename = photourl.rsplit('/', 1)[-1]
                profilepic.sign = ESign.PicUrl
                res.append_resource(profilepic)
                yield profilepic
            yield res
        except Exception:
            self._logger.error('{} got profile fail: {}'.format(self.userid, traceback.format_exc()))
