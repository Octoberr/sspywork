"""
nslookup可以通过 p去查询域名
nslookup -qt=ptr 8.8.8.8
create by judy 2019/10/17
"""

import re
import traceback
from subprocess import Popen, PIPE
from sys import platform

from datacontract.iscoutdataset import IscoutTask
from ..scoutplugbase import ScoutPlugBase


class IpMxDomain(ScoutPlugBase):

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

    def get_ip_reverse_domain(self, level, ip, reason=None):
        """
        外部接口，根据ip去获取mx记录
        新的接口便于独立话，所以写了冗余的代码
        :param level:
        :param ip:
        :param reason:
        :return:
        """
        # 正则
        re_name = re.compile('name = (.+)')
        # --------获取邮箱账号的后缀
        # mail_suffix = email
        # if '@' in email:
        #     mail_suffix = email.split('@')[-1]
        res = None
        try:
            proc = Popen(f'nslookup -q=ptr {ip} 8.8.8.8', stdout=PIPE, shell=True)
            outs, errs = proc.communicate(timeout=15)
            # 根据不同的操作系统用不同的编码解析
            dnstext = outs
            if self.pf == 'linux':
                dnstext = outs.decode('utf-8')
            elif self.pf == 'windows':
                dnstext = outs.decode('gbk')
            name_res = re_name.search(dnstext)
            if name_res:
                res = name_res.group(1).strip().strip('.')
                # return res
        except:
            self._logger.error(f"Nslookup ip error,err:{traceback.format_exc()}")
        finally:
            return res
