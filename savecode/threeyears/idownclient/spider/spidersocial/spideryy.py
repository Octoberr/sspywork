import time
import traceback

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidersocialbase import SpiderSocialBase


class SpiderYy(SpiderSocialBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderYy, self).__init__(task, appcfg, clientid)

    def _check_registration(self):
        """
        查询手机号是否注册了yy
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            url = 'https://zc.yy.com/reg/udb/reg4udb.do?appid=5719&action=3&type=Mobile&mode=udb&fromadv=yy_0.cpuid_0.channel_0&busiurl=http%3A%2F%2Fwww.yy.com%2F3rdLogin%2Freg-login.html'
            response = self._ha.getstring(url)
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 42
Content-Type: application/x-www-form-urlencoded
Host: zc.yy.com
Origin: https://zc.yy.com
Pragma: no-cache
Referer: https://zc.yy.com/reg/udb/reg4udb.do?appid=5719&action=3&type=Mobile&mode=udb&fromadv=yy_0.cpuid_0.channel_0&busiurl=http%3A%2F%2Fwww.yy.com%2F3rdLogin%2Freg-login.html
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
X-Requested-With: XMLHttpRequest"""

            postdata = f"passport={self.task.phone}&mobilefix=&appid=5719"
            html = self._ha.getstring('https://zc.yy.com/reg/pc/chk.do', req_data=postdata, headers=headers)
            if '"msg":"该帐号已注册"' in html:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return
