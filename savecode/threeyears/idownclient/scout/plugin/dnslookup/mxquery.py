"""
查询邮服地址
根据mx记录来查询
然后根据ping来找ip地址(命令要分windows和linux)
create by judy 2019/09/03
"""
import re
import traceback
from subprocess import Popen, PIPE
from sys import platform

from datacontract.iscoutdataset import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import MailServer
from ..scoutplugbase import ScoutPlugBase


class MXQuery(ScoutPlugBase):

    def __init__(self, task):
        ScoutPlugBase.__init__(self)
        # 默认程序在docker里，但是调试或者本地的时候有可能会在windows
        # 以防万一还是写一个windows的版本，方便本地调试
        self.task: IscoutTask = task

        self.pf = 'linux'
        if platform == 'linux' or platform == 'linux2':
            self.pf = 'linux'
        elif platform == 'win32':
            self.pf = 'windows'

    def __ping_domain(self, mail_domian):
        """
        根据mx查询到的domain，去ping一下获取到当前的ip
        根据操作系统的不同，使用不同的正则去提取
        :param mail_domian:
        :return:
        """
        re_ip = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
        res = None
        if self.pf == 'linux':
            try:
                proc = Popen(f'ping -c 2 {mail_domian}', stdout=PIPE, shell=True)
                outs, errs = proc.communicate(timeout=15)
                res = outs.decode('utf-8')
            except:
                print(f"Linux ping result error, err:{traceback.format_exc()}")
                res = None
        elif self.pf == 'windows':
            try:
                proc = Popen(f'ping {mail_domian}', stdout=PIPE, shell=True)
                outs, errs = proc.communicate(timeout=15)
                res = outs.decode('gbk')
            except:
                print(f"Windows ping result error, err:{traceback.format_exc()}")
                res = None

        if res is not None:
            ips: list = re_ip.findall(res)
            if len(ips) > 0:
                return ips[0]
        else:
            return res

    def get_mail_server(self, level, email):
        """
        外部接口，获取mail server
        :param level:
        :param email:
        :return:
        """
        # 正则
        re_mailserver = re.compile('mail exchanger = (.+)')
        # --------获取邮箱账号的后缀
        mail_suffix = email
        if '@' in email:
            mail_suffix = email.split('@')[-1]

        proc = Popen(f'nslookup -q=mx {mail_suffix}', stdout=PIPE, shell=True)
        outs, errs = proc.communicate(timeout=15)
        # 根据不同的操作系统用不同的编码解析
        res = outs
        if self.pf == 'linux':
            res = outs.decode('utf-8')
        elif self.pf == 'windows':
            res = outs.decode('gbk')
        # 提取所有的mailserver,然后根据操作系统不同来解析
        # windows 就是当前的
        ms_list: list = re_mailserver.findall(res)
        # linux qq.com	mail exchanger = 30 mx1.qq.com.
        if self.pf == 'linux' and len(ms_list) > 0:
            ms_list = [el.strip().split(' ')[-1].strip('.') for el in ms_list]

        # res = outs.decode('utf-8')
        for md in ms_list:
            ms = MailServer(self.task, level, md.strip(), 'SMTP')
            ip = self.__ping_domain(md.strip())
            if ip is not None:
                ms.set_ip(ip)
            yield ms
