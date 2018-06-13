"""
tom邮箱的爬虫
啊！终于到js拼接啥的了，just do it!
create by swm 2018/06/01
"""
from bs4 import BeautifulSoup
import requests
import json
import time
import random
import email
import datetime
import uuid
import base64

from .conf import config
# 导入同级别的文件夹的方法
import sys
sys.path.append('..')
from tools.writelog import WRITELOG


class MAIL:

    def __init__(self):
        # 保存本次会话
        self.usr = ['Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
                    'Mozilla/5.0 (Linux; U; Android 4.0; en-us; GT-I9300 Build/IMM76D) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30',
                    'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
                    'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Mobile Safari/537.36']
        self.host = 'mail1.tom.com'
        self.headers = {
            # 'Cookie': self.cookie,
            'User-Agent': random.choice(self.usr)
        }
        self.mailfloder = config['emlfloder']
        self.contactsfloder = config['contactsfloder']

    def cookielogin(self, cookies):
        # 使用旧版cookie构造headers
        self.headers['Cookie'] = cookies
        self.headers['X-Forwarded-For'] = '%s.%s.%s.%s' % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        # 邮件首页
        url = 'http://mail1.tom.com/webmail/main/index.action'
        s = requests.session()
        try:
            res = s.get(url, headers=self.headers)
        except Exception as err:
            # 访问网络出错
            WRITELOG().writelog('line 38 cookie login err:{}'.format(err))
            return False
        if 'Set-Cookie' in res.headers and 'JSESSIONID=' in res.headers['Set-Cookie']:
            # cookie登陆失败
            return False
        else:
            # cookie登陆成功
            cookiedict = res.cookies.get_dict()
            # 如果有新增加的cookies那么就增加到cookies字符串
            if cookiedict:
                cookie_string = ';'.join([str(x) + '=' + str(y) for x, y in cookiedict.items()])
                cookies += cookie_string
            return cookies

    def readmail(self, mail):
        """
        获取mail的html格式的邮件，已弃用
        create by swm 2018/06/06
        :param mail:
        :return:
        """
        # 根据标题读取邮件获取的结果为html格式
        url = 'http://mail1.tom.com/webmail/readmail/show.action'
        formdata = {
            'uid': mail['uid'],
            'coremail':'',
            'folderName': mail['folderName'],
            'nextUid':'',
            'preUid':'',
            'nextSubject':'',
            'preSubject':''
        }

        res = requests.post(url, headers=self.headers, data=formdata)
        return res.text

    def getthemail(self, cookies):
        """
        获取所有的邮件类表并，获取eml格式的邮件并保存为文件在本地
        """
        self.headers['Cookie'] = cookies
        self.headers['X-Forwarded-For'] = '%s.%s.%s.%s' % (
        random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        url = 'http://mail1.tom.com/webmail/query/queryfolder.action'
        formdata = {
            'folderName': 'INBOX',
            'currentPage': '1'
        }
        try:
            res = requests.post(url, headers=self.headers, data=formdata)
        except Exception as err:
            WRITELOG().writelog('line 85 get eml file error:{}'.format(err))
            return False
        cookiedict = res.cookies.get_dict()
        try:
            resdict = json.loads(res.text)
            totalpage = resdict['result']['totalPage']
        except Exception as err:
            WRITELOG().writelog('cookie is failure, err:{}'.format(err))
            return False
        if cookiedict:
            cookie_string = ';'.join([str(x) + '=' + str(y) for x, y in cookiedict.items()])
            cookies += cookie_string
            self.headers['Cookie'] = cookies
        for i in range(int(totalpage)):
            formdata['currentPage'] = i+1
            data = requests.post(url, headers=self.headers, data=formdata)
            dictres = json.loads(data.text)
            pagelist = dictres['result']['pageList']
            for mail in pagelist:
                self.getemlfile(mail, cookies)
        return cookies

    def storageeml(self, eml):
        file = str(uuid.uuid1())+'.eml'
        filename = self.mailfloder/file
        with open(filename, 'w') as fp:
            fp.write(eml)
        fp.close()
        return

    def getemlfile(self, mail, cookies):
        # 获取eml格式的邮件
        url = 'http://mail1.tom.com/webmail/readmail/rawcontent.action'
        formdata = {
        'filename': mail['subject'],
        'uid': mail['uid'],
        'uuid':'',
        'folderName': mail['folderName'],
        'partId':'',
        'suffix':'',
        'subject':'',
        'coremail': 'newmail',
        }
        try:
            res = requests.post(url, headers=self.headers, data=formdata)
        except Exception as err:
            WRITELOG().writelog('line 130 network err: {}'.format(err))
            return
        eml = res.text
        if eml:
            # 寻找增加的cookie
            cookiedict = res.cookies.get_dict()
            if cookiedict:
                cookie_string = ';'.join([str(x) + '=' + str(y) for x, y in cookiedict.items()])
                cookies += cookie_string
                self.headers['Cookie'] = cookies
            # 拼接eml字符串
            mailtext = 'download:1\n'
            msg = email.message_from_string(eml)
            to = email.utils.parseaddr(msg.get("to"))[1]
            now = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
            mailtext += 'time:{}\n'.format(now)+'owner:{}\n'.format(to)
            mailtext += eml
            self.storageeml(mailtext)
            return

    def strtobsstr(self, strdata):
        """
        bs64加密
        :param strdata:
        :return:
        """
        bytedata = str.encode(strdata)
        bsdata = base64.b64encode(bytedata)
        strbsdata = config['bshead'] + bsdata.decode()
        return strbsdata

    def storagecontacts(self, accountinfo):
        file = str(uuid.uuid1())+'.an_ct'
        filename = config['contactsfloder']/file
        with open(filename, 'w') as fp:
            fp.write(accountinfo)
        fp.close()
        return

    def getcontacts(self, cookies):
        accountinfo = ''
        # 获取联系人
        self.headers['Cookie'] = cookies
        t = int(time.time()*1000)
        url = 'http://mail1.tom.com/webmail/contact/index.action?_ts={}'.format(t)
        try:
            res = requests.get(url, headers=self.headers)
        except Exception as err:
            WRITELOG().writelog('line 185 network err: {}'.format(err))
            return False
        try:
            soup = BeautifulSoup(res.text, 'lxml')
            # 寻找来源账号
            input = soup.find('input', type="hidden")
            account = input['value']
            header = 'account:{}\n'.format(account)
        except Exception as err:
            WRITELOG().writelog('cookie is failure, err: {}'.format(err))
            return False
        try:
            # 寻找联系人
            div = soup.find('div', class_="main-conatainer")
            table = div.find('table')
            tbody = table.find('tbody')
            alltr = tbody.find_all('tr')
            for tr in alltr:
                tmpc = ''
                now = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
                tmpc += 'time:{}\n'.format(now)
                alltd = tr.find_all('td')
                friendemail = alltd[3].get_text()
                tmpc += 'contact:{}\n'.format(friendemail)
                friendname = alltd[1].get_text()
                detail = ''
                if friendname:
                    detail += 'name:{};'.format(friendname)
                friendnickname = alltd[2].get_text()
                if friendnickname:
                    detail += 'nickname:{};'.format(friendnickname)
                if detail:
                    tmpc += 'detail:{}\n'.format(self.strtobsstr(detail))
                tmpc += '\n'
                accountinfo += header+tmpc
            self.storagecontacts(accountinfo)
            return cookies
        except Exception as err:
            WRITELOG().writelog('No contacts, err:{}'.format(err))
            return False

    def accountlogin(self, account, pwd):
        """
        账号密码登陆
        createby swm 2018/06/07
        :param account:
        :param pwd:
        :return:
        """
        loginurl = 'http://mail1.tom.com/webmail/login/loginService.action'
        unixtime = int(time.time())
        reqcookie = 'Hm_lvt_089662dc0ddc20a9fadd295d90f8c982={}; Hm_lpvt_089662dc0ddc20a9fadd295d90f8c982={}'.format(unixtime, unixtime)
        headers = {
            # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            # 'Accept-Encoding': 'gzip, deflate',
            # 'Accept-Language': 'zh-CN,zh;q=0.9',
            # 'Cache-Control': 'max-age=0',
            # 'Content - Length': '109',
            # 'Content-Type': 'application/x-www-form-urlencoded',
            # 'Host': 'mail1.tom.com',
            # 'Origin': 'http://mail.tom.com',
            # 'Referer': 'http://mail.tom.com/',
            # 'Upgrade-Insecure-Requests': '1',
            'Cookie': reqcookie,
            'User-Agent': random.choice(self.usr),
            # 'Connection': 'keep - alive',
            'X-Forwarded-For': '%s.%s.%s.%s' % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
        }
        formdata = {
            'username': account,
            'password': pwd,
            'from_domain': 'web.mail.tom.com',
            'fromSource': 'mail.tom.com',
            'tab': '0',
            'jump': '1'
        }
        s = requests.session()
        try:
            res = s.post(loginurl, headers=headers, data=formdata, allow_redirects=False)
        except Exception as err:
            WRITELOG().writelog('line 273 network err:{}'.format(err))
            return False
        if 'Location' in res.headers:
            cookiedict = res.cookies.get_dict()
            cookie_string = ';'.join([str(x) + '=' + str(y) for x, y in cookiedict.items()])
            # 成功后返回cookies
            return cookie_string
        else:
            # print('default')
            # 登陆失败返回False
            return False


# if __name__ == '__main__':
    # m = MAIL()
    # cookie = m.accountlogin('nmsbtom@tom.com', 'nmsbtom')
    # print(cookie)
    # 登陆获取的cookies
    # cookies = 'SERVERID=RZ_16110_A;user_token=8BA7C33C47A09284E32A34ECDAB9064C1B28CB41BFC3A675AA1BC2A8804F8FE2;JSESSIONID=1l1hblkp9h9fyzeergzvhq4a6;tom_mail_locale=zh_CN;tom_user=nmsbtom'
    # cookies = 'swm'
    # e = m.cookielogin(cookies)
    # t = m.getthemail(cookies)
    # m.getcontacts(cookies)
    # print(a)
