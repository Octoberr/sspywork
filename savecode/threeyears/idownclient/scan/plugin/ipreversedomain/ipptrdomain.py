"""
使用nslookup
查询ip的ptr记录
create by judy 2020/06/18
nslookup -q=ptr 117.123.235.6 8.8.8.8

意思是指定查询ip117.123.235.6 在8.8.8.8的ptr记录
"""
import re
import os
import psutil
import signal
from subprocess import Popen, PIPE, TimeoutExpired


class IpPtrDomain(object):
    def __init__(self):
        pass

    @classmethod
    def get_ip_reverse_domain(cls, ip):
        """
        外部接口，根据ip去获取mx记录
        新的接口便于独立话，所以写了冗余的代码
        :param ip:
        :return:
        """
        # 正则
        re_name = re.compile("name = (.+)")
        # --------获取邮箱账号的后缀
        # mail_suffix = email
        # if '@' in email:
        #     mail_suffix = email.split('@')[-1]
        res = None
        proc = Popen(f"nslookup -q=ptr {ip} 8.8.8.8", stdout=PIPE, shell=True)
        outs, errs = proc.communicate(timeout=15)
        # 根据不同的操作系统用不同的编码解析
        # 无论是1.0还是2.0都直接在docker容器内运行
        dnstext = outs.decode("utf-8")
        name_res = re_name.search(dnstext)
        if name_res:
            res = name_res.group(1).strip().strip(".")
            # return res
        if proc is not None:
            try:
                pid = proc.pid
                parent = psutil.Process(pid)
                children = parent.children(recursive=True)
                children[-1].send_signal(signal.SIGTERM)
            except:
                pass
            finally:
                proc.kill()

        return res
