"""
验证手机号是否注册了wo邮箱
20181023
"""
import re
import time
import traceback

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidermailbase import SpiderMailBase
from lxml import etree
from urllib.parse import urlencode


class SpiderWo(SpiderMailBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderWo, self).__init__(task, appcfg, clientid)

    def _check_registration(self):
        """
        查询手机号是否注册了WO邮箱
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            url = 'https://mail.wo.cn/resetpwd_checkuser'
            headers = """
Accept: */*
Content-Type: application/x-www-form-urlencoded
Origin: https://mail.wo.cn
Referer: https://mail.wo.cn/resetPassword
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            postdata = f'actionType=CheckUser&user={self.task.phone}&domain=wo.cn'
            response = self._ha.getstring(url=url, req_data=postdata, headers=headers)
            if '{"uid":"' in response:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return

    def _cookie_login(self) -> bool:
        res = False
        try:
            self._ha._managedCookie.add_cookies('wo.cn', self.task.cookie)
            url = 'https://mail.wo.cn/welcome'
            headers = '''
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.97 Safari/537.36
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            '''
            html = self._ha.getstring(url, headers=headers)
            if not html.__contains__('退出') or not html.__contains__('个人信息'):
                return res

            html = etree.HTML(html, etree.HTMLParser())
            self._userid = html.xpath('normalize-space(//li[@id="currentUser"]/text())')
            if not self._userid:
                return res
            res = True
        except Exception:
            self._logger.error(f"Cookie login error, err:{traceback.format_exc()}")
        return res

    def _pwd_login(self) -> bool:
        res = False
        try:
            url = 'https://mail.wo.cn/coremail/index.jsp?cus=1'
            headers = '''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: max-age=0
            Connection: keep-alive
            Content-Type: application/x-www-form-urlencoded
            Host: mail.wo.cn
            Origin: https://mail.wo.cn
            Referer: https://mail.wo.cn/
            Sec-Fetch-Dest: document
            Sec-Fetch-Mode: navigate
            Sec-Fetch-Site: same-origin
            Sec-Fetch-User: ?1
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36
            '''
            uid = re.search(r'(\w+)@wo.cn', self.task.account).group(1)
            form_data = {
                'locale': 'zh_CN',
                'nodetect': 'false',
                'destURL': '',
                'supportLoginDevice': 'true',
                'accessToken': '',
                'timestamp': '',
                'signature': '',
                'nonce': '',
                'device': '{"uuid":"webmail_windows","imie":"webmail_windows","friendlyName":"chrome 85","model":"windows","os":"windows","osLanguage":"zh-CN","deviceType":"Webmail"}',
                'supportDynamicPwd': 'true',
                'supportBind2FA': 'true',
                'authorizeDevice': '',
                'loginType': '',
                'uid': uid,
                'domain': '',
                'password': self.task.password,
                'action:login': ''
            }
            self._ha.getstring(url, req_data=urlencode(form_data), headers=headers)
            res = self._cookie_login()
        except Exception as ex:
            self._logger.error("Pwd login error, err: {}".format(ex))
            self._write_log_back("账密登录失败: {}".format(ex.args))
        return res
