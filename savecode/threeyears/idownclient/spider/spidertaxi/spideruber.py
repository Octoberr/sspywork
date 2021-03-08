import json
import re
import time
import traceback

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidertaxibase import SpiderTaxiBase


class SpiderUber(SpiderTaxiBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderUber, self).__init__(task, appcfg, clientid)
        if not self.task.globaltelcode:
            self.globaltelcode = '86'
        else:
            self.globaltelcode = self.task.globaltelcode.replace('+', '')

    def _check_registration(self):
        """
        查询手机号是否注册了uber
        # 中国的手机号需要加上+86
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            ua = "https://auth.uber.com/login"
            url = "https://auth.uber.com/login/handleanswer"
            data = {'answer': {'type': "VERIFY_INPUT_MOBILE", 'userIdentifier': {
                'mobile': {'countryCode': "{code}".format(code=self.globaltelcode),
                           'phoneNumber': "{account}".format(account=self.task.account)}}}, 'init': 'true'}
            # data = '{"answer":{"type":"VERIFY_INPUT_MOBILE","userIdentifier":{"mobile":{"countryCode":"{code}","phoneNumber":"{phone}"}}},"init":true}'.format(code=self.globaltelcode, phone=self.task.phone)
            data = json.dumps(data)
            r = self._ha.getstring(ua)
            pattern = re.compile(r'window.csrfToken = \'(.*?)\';')
            csrftoken = pattern.findall(r)[0]
            headers = f"""
Accept: application/json
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 130
content-type: application/json
Host: auth.uber.com
Origin: https://auth.uber.com
Pragma: no-cache
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
x-csrf-token: {csrftoken}"""
            response = self._ha.getstring(url=url, req_data=data, headers=headers)
            if '"PUSH_LOGIN"' in response or 'RECAPTCHA' in response:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Uber check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return
