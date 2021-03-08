# -*- coding:utf-8 -*-

import datetime
import json
import re
import time
import traceback

from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess import ResponseIO
from selenium import webdriver
from selenium.webdriver import ChromeOptions

from .spidermailbase import SpiderMailBase
from ...clientdatafeedback import CONTACT_ONE, CONTACT, EML, Folder, PROFILE


class Spider126Vip(SpiderMailBase):

    def __init__(self, task, appcfg, clientid):
        super(Spider126Vip, self).__init__(task, appcfg, clientid)
        if self.task.cookie:
            self._ha._managedCookie.add_cookies('vip.126.com', self.task.cookie)
            self.mail_uid = substring(self.task.cookie, 'NETEASE_VIP=', ';') + '@vip.126.com'
            self.sid = self._get_sid()

    def _cookie_login(self)->bool:
        try:
            url = 'http://webmail.vip.126.com/js6/main.jsp?sid={}&df=mailvip'.format(self.sid)
            html = self._ha.getstring(url, headers=f"""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Host: webmail.vip.126.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://reg.vip.126.com/enterMail.m?username={self.mail_uid}&style=-1&language=-1&enterVip=true&verifycookie=1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36""")
            userid = substring(html, "uid:'", "'")
            if userid:
                self.userid = userid + '-126vip'
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
            if '@vip.126.com' in self.task.account:
                self.task.account = self.task.account.split('@')[0]
            chrome_options = ChromeOptions()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('blink-settings=imagesEnabled=false')
            # chrome_options.add_argument('--no-sandbox')
            driver = webdriver.Chrome(chrome_options=chrome_options)
            # driver = webdriver.Chrome()
            driver.get("http://vip.126.com/")
            time.sleep(1)

            html = driver.find_element_by_xpath("//*").get_attribute("outerHTML")
            # 126iframe的id
            id = re.findall(r'"(x-URS-iframe.*?)"', html)[0]
            # 定位到iframe
            iframe = driver.find_element_by_id(id)
            # 切换到iframe
            driver.switch_to.frame(iframe)

            # 登录
            driver.find_element_by_css_selector("input[name='email']").send_keys(self.task.account)
            driver.find_element_by_css_selector("input[name='password']").send_keys(self.task.password)
            time.sleep(2)
            driver.find_element_by_id("dologin").click()

            diccookie = driver.get_cookies()
            newcookie = ''
            for cookie in diccookie:
                # cookie = json.loads(cookie)
                if cookie['domain'] == '.vip.126.com':
                    newcookie = newcookie + cookie['name'] + '=' + cookie['value'] + '; '
            if newcookie:
                self._ha._managedCookie.add_cookies('vip.126.com', newcookie)
                self.mail_uid = substring(newcookie, 'NETEASE_VIP=', ';') + '@vip.126.com'
                self.sid = self._get_sid()
            res = self._cookie_login()

        except Exception as ex:
            self._logger.error('Pwd login by selenium fail: {}'.format(traceback.format_exc()))
            self._write_log_back("账密登录失败: {}".format(ex.args))
        return res

    def _get_contacts(self):
        try:
            url = f'http://webmail.vip.126.com/contacts/call.do?uid={self.mail_uid}&sid={self.sid}&from=webmail&cmd=newapi.getContacts&vcardver=3.0&ctype=all&attachinfos=yellowpage,frequentContacts&freContLim=20&limitinfo=get'
            headers = f"""
Accept: */*
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Content-Length: 36
Content-type: application/x-www-form-urlencoded
Host: webmail.vip.126.com
Origin: http://webmail.vip.126.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://webmail.vip.126.com/js6/main.jsp?sid={self.sid}&df=mailvip
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            postdata = 'order=[{"field":"N","desc":"false"}]'
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            if 'data' not in html:
                return None
            jshtml = json.loads(html)
            # 获取分组字典
            dicgroup = {}
            try:
                if jshtml['data']['groups']:
                    for group in jshtml['data']['groups']:
                        guid = group['UID']
                        dicgroup[guid] = group['N']
            except:
                pass
            # 获取联系人
            try:
                if jshtml['data']['contacts']:
                    res = CONTACT(self._clientid, self.task, self.task.apptype)
                    for contact in jshtml['data']['contacts']:
                        contactid = contact['UID']
                        res_one = CONTACT_ONE(self.userid, contactid, self.task, self.task.apptype)
                        res_one.email = contact['EMAIL;type=INTERNET;type=pref']
                        res_one.nickname = contact['FN']
                        try:
                            res_one.phone = contact['TEL;type=CELL;type=VOICE;type=pref']
                        except:
                            pass
                        try:
                            groupid = contact['GROUPING']
                            res_one.group = dicgroup[groupid]
                        except:
                            pass
                        res.append_innerdata(res_one)
                    if res.innerdata_len > 0:
                        yield res
            except:
                return None
        except Exception:
            self._logger.error("Got contacts error, err:{}".format(traceback.format_exc()))

    def _get_folders(self):
        dic = {'1': '收件箱', '2': '草稿箱', '3': '已发送', '4': '已删除', '5': '垃圾邮件', '-2': '红旗邮件', 'defer': '待办邮件'}
        for id in dic:
            res = Folder()
            res.folderid = id
            res.name = dic[id]
            yield res

    def _get_mails(self, folder: Folder):
        try:
            folderid = folder.folderid

            num = -100
            while True:
                num += 100
                url = f'http://webmail.vip.126.com/js6/s?sid={self.sid}&func=mbox:listMessages'
                headers = f"""
Accept: text/javascript
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Content-Length: 539
Content-type: application/x-www-form-urlencoded
Host: webmail.vip.126.com
Origin: http://webmail.vip.126.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://webmail.vip.126.com/js6/main.jsp?sid={self.sid}&df=mailvip
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
                # 收件箱 草稿 已发送
                if folderid in ['1', '2', '3']:
                    postdata = f'var=%3C%3Fxml%20version%3D%221.0%22%3F%3E%3Cobject%3E%3Cint%20name%3D%22fid%22%3E{folderid}%3C%2Fint%3E%3Cstring%20name%3D%22order%22%3Edate%3C%2Fstring%3E%3Cboolean%20name%3D%22desc%22%3Etrue%3C%2Fboolean%3E%3Cint%20name%3D%22limit%22%3E{100}%3C%2Fint%3E%3Cint%20name%3D%22start%22%3E{num}%3C%2Fint%3E%3Cboolean%20name%3D%22skipLockedFolders%22%3Efalse%3C%2Fboolean%3E%3Cstring%20name%3D%22topFlag%22%3Etop%3C%2Fstring%3E%3Cboolean%20name%3D%22returnTag%22%3Etrue%3C%2Fboolean%3E%3Cboolean%20name%3D%22returnTotal%22%3Etrue%3C%2Fboolean%3E%3C%2Fobject%3E'
                # 已删除 垃圾邮件
                elif folderid in ['4', '5']:
                    postdata = f'var=%3C%3Fxml%20version%3D%221.0%22%3F%3E%3Cobject%3E%3Cint%20name%3D%22fid%22%3E{folderid}%3C%2Fint%3E%3Cstring%20name%3D%22order%22%3Edate%3C%2Fstring%3E%3Cboolean%20name%3D%22desc%22%3Etrue%3C%2Fboolean%3E%3Cint%20name%3D%22limit%22%3E{100}%3C%2Fint%3E%3Cint%20name%3D%22start%22%3E{num}%3C%2Fint%3E%3Cboolean%20name%3D%22skipLockedFolders%22%3Efalse%3C%2Fboolean%3E%3Cboolean%20name%3D%22returnTag%22%3Etrue%3C%2Fboolean%3E%3Cboolean%20name%3D%22returnTotal%22%3Etrue%3C%2Fboolean%3E%3C%2Fobject%3E'
                # 红旗邮件
                elif folderid == '-2':
                    postdata = f'var=%3C%3Fxml%20version%3D%221.0%22%3F%3E%3Cobject%3E%3Cobject%20name%3D%22filter%22%3E%3Cint%20name%3D%22label0%22%3E1%3C%2Fint%3E%3C%2Fobject%3E%3Cstring%20name%3D%22order%22%3Edate%3C%2Fstring%3E%3Cboolean%20name%3D%22desc%22%3Etrue%3C%2Fboolean%3E%3Carray%20name%3D%22fids%22%3E%3Cint%3E1%3C%2Fint%3E%3Cint%3E3%3C%2Fint%3E%3C%2Farray%3E%3Cint%20name%3D%22limit%22%3E{100}%3C%2Fint%3E%3Cint%20name%3D%22start%22%3E{num}%3C%2Fint%3E%3Cboolean%20name%3D%22skipLockedFolders%22%3Etrue%3C%2Fboolean%3E%3Cboolean%20name%3D%22returnTag%22%3Etrue%3C%2Fboolean%3E%3Cboolean%20name%3D%22returnTotal%22%3Etrue%3C%2Fboolean%3E%3C%2Fobject%3E'
                # 待办邮件
                else:
                    postdata = f'var=%3C%3Fxml%20version%3D%221.0%22%3F%3E%3Cobject%3E%3Carray%20name%3D%22fids%22%3E%3Cint%3E1%3C%2Fint%3E%3Cint%3E2%3C%2Fint%3E%3Cint%3E3%3C%2Fint%3E%3Cint%3E4%3C%2Fint%3E%3Cint%3E5%3C%2Fint%3E%3C%2Farray%3E%3Cstring%20name%3D%22order%22%3EdeferredDate%3C%2Fstring%3E%3Cboolean%20name%3D%22desc%22%3Efalse%3C%2Fboolean%3E%3Cobject%20name%3D%22filter%22%3E%3Cstring%20name%3D%22defer%22%3E19700101%3A%3C%2Fstring%3E%3C%2Fobject%3E%3Cint%20name%3D%22limit%22%3E{100}%3C%2Fint%3E%3Cint%20name%3D%22start%22%3E{num}%3C%2Fint%3E%3Cboolean%20name%3D%22skipLockedFolders%22%3Etrue%3C%2Fboolean%3E%3Cboolean%20name%3D%22returnTag%22%3Etrue%3C%2Fboolean%3E%3Cboolean%20name%3D%22returnTotal%22%3Etrue%3C%2Fboolean%3E%3C%2Fobject%3E'
                html = self._ha.getstring(url, headers=headers, req_data=postdata).replace('\n', '')
                res = self._mail_detai(html, folder)
                for res_one in res:
                    yield res_one
                try:
                    total = int(substring(html, "'total':", "}"))
                    if total <= num:
                        break
                except:
                    break
        except Exception:
            self._logger.error('{} Got mails fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_profile(self):
        try:
            url = 'http://webmail.vip.126.com/js6/main.jsp?sid={}&df=mailvip'.format(self.sid)
            html = self._ha.getstring(url, headers=f"""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Host: webmail.vip.126.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://reg.vip.126.com/enterMail.m?username={self.mail_uid}&style=-1&language=-1&enterVip=true&verifycookie=1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36""")
            res = PROFILE(self._clientid, self.task, self.task.apptype, self.userid)
            res.account = substring(html, "uid:'", "'")
            yield res
        except Exception:
            self._logger.error('{} got profile fail: {}'.format(self.userid, traceback.format_exc()))

    def _mail_detai(self, html, folder):
        if 'var' not in html:
            return None
        jshtml = re.findall(r"('id'.*?)'hmid'", html)
        if jshtml:
            for mail in jshtml:
                mailid = substring(mail, "'id':'", "'")
                res_one = EML(self._clientid, self.task, self.userid, mailid, folder, self.task.apptype)
                res_one.provider = substring(mail, "'from':'", "'")
                res_one.subject = substring(mail, "'subject':'", "'")
                sendtime = substring(mail, "'sentDate':new Date(", "),")
                if "'read':true" in mail:
                    res_one.state = 1
                else:
                    res_one.state = 0
                j = 1
                a = []
                for i in sendtime.split(','):
                    if j == 2:
                        i = str(int(i) + 1)
                    if len(i) == 1:
                        i = '0' + i
                    a.append(i)
                    j += 1
                sendtime = f'{a[0]}-{a[1]}-{a[2]} {a[3]}:{a[4]}:{a[5]}'
                res_one.sendtime = datetime.datetime.strptime(sendtime, "%Y-%m-%d %H:%M:%S")


                # 下载邮件
                url = f'http://webmail.vip.126.com/js6/read/readdata.jsp?sid={self.sid}&mid={mailid}&mode=download&l=read&action=download_eml'
                headers = f"""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: webmail.vip.126.com
Pragma: no-cache
Referer: http://webmail.vip.126.com/js6/main.jsp?sid={self.sid}&df=mailvip
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
                # response = self._ha.get_response_stream(url, headers=headers)
                resp = self._ha.get_response(url, headers=headers)
                res_one.stream_length = resp.headers.get('Content-Length', 0)
                res_one.io_stream = ResponseIO(resp)
                # res_one.io_stream = response
                yield res_one

    def _get_sid(self):
        try:
            url = 'http://entry.vip.126.com/entry/door?style=-1&language=-1&destip=&verifycookie=1&lightweight=0&product=mailvip&module='
            headers = """
Host: entry.vip.126.com
Proxy-Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Referer: http://reg.vip.126.com/enterMail.m
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
"""
            html, redir = self._ha.getstring_unredirect(url, headers=headers)
            sid = substring(redir, 'sid=', '&')
            return sid
        except:
            return None
