import time
import traceback

from commonbaby.helpers.helper_str import substring

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidersocialbase import SpiderSocialBase


class SpiderSkype(SpiderSocialBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderSkype, self).__init__(task, appcfg, clientid)
        self.account = self.task.globaltelcode + self.task.phone

    def _init_page(self):
        pass

    def _check_registration(self):
        """
        查询手机号是否注册了skype
        # 中国的手机号需要加上+86
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            url = 'https://login.live.com/login.srf'
            headers = f"""
        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
        Accept-Encoding: gzip, deflate, br
        Accept-Language: zh-CN,zh;q=0.9
        Cache-Control: no-cache
        Connection: keep-alive
        Host: login.live.com
        Pragma: no-cache
        Upgrade-Insecure-Requests: 1
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"""
            response = self._ha.getstring(url, headers=headers)
            uaid = substring(response, 'uaid=', '"')
            flowToken = substring(response, 'id="i0327" value="', '"')

            url = f'https://login.live.com/GetCredentialType.srf?vv=1600&mkt=ZH-CN&lc=2052&uaid={uaid}'
            headers = f"""
        Accept: application/json
        client-request-id: {uaid}
        Content-type: application/json; charset=UTF-8
        hpgact: 0
        hpgid: 33
        Origin: https://login.live.com
        Referer: https://login.live.com/login.srf
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"""

            postdata = '{"username":"' + self.account + '","uaid":"' + uaid + '","isOtherIdpSupported":false,"checkPhones":true,"isRemoteNGCSupported":true,"isCookieBannerShown":false,"isFidoSupported":false,"forceotclogin":false,"otclogindisallowed":true,"flowToken":"' + flowToken + '"}'
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            if '"IfExistsResult":0,' in html:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return
