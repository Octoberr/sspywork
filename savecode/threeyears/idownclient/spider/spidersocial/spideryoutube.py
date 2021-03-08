import time
import traceback

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidersocialbase import SpiderSocialBase


class SpiderYoutube(SpiderSocialBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderYoutube, self).__init__(task, appcfg, clientid)
        self.account = self.task.globaltelcode.replace('+', '') + self.task.account

    def _check_registration(self):
        """
        查询手机号是否注册了youtube
        # 中国的手机号需要加上+86
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            url = "https://accounts.google.com"
            html = self._ha.getstring(url)
            headers = """
accept: */*
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
content-length: 2339
content-type: application/x-www-form-urlencoded;charset=UTF-8
google-accounts-xsrf: 1
origin: https://accounts.google.com
pragma: no-cache
referer: https://accounts.google.com/signin/v2/identifier?passive=true&service=youtube&uilel=3&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Fnext%3D%252F%26hl%3Dzh-CN%26app%3Ddesktop%26action_handle_signin%3Dtrue&hl=zh-CN&flowName=GlifWebSignIn&flowEntry=ServiceLogin
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
x-same-domain: 1"""
            url = 'https://accounts.google.com/_/signin/sl/lookup?hl=zh-CN&_reqid=36094&rt=j'
            postdata = f"continue=https%3A%2F%2Fwww.youtube.com%2Fsignin%3Fnext%3D%252F%26hl%3Dzh-CN%26app%3Ddesktop%26action_handle_signin%3Dtrue&service=youtube&hl=zh-CN&f.req=%5B%22%2BP{self.account}%22%2C%22AEThLlxjm9Eg70EneKSN_Y2YPrbr8pbHpZmuqklPctAcpfw9aaLAOXCEpkSqxouF9EskebhXdHrNR6dCl6tFMFaR9P75pmUDMGv52EhQH3APBX05qtcLVLq5BU-6QiKDETt7tvMkDx0pMSZveSfn2nLv5nHapU1qt3gVDWosokpaB-bl8IFYjSYnrSps7iUKqfC3VOLYA3LJru0cnxjEzQEz1SlY1ih8oA%22%2C%5B%5D%2Cnull%2C%22KR%22%2Cnull%2Cnull%2C2%2Cfalse%2Ctrue%2C%5Bnull%2Cnull%2C%5B2%2C1%2Cnull%2C1%2C%22https%3A%2F%2Faccounts.google.com%2FServiceLogin%3Fpassive%3Dtrue%26service%3Dyoutube%26uilel%3D3%26continue%3Dhttps%253A%252F%252Fwww.youtube.com%252Fsignin%253Fnext%253D%25252F%2526hl%253Dzh-CN%2526app%253Ddesktop%2526action_handle_signin%253Dtrue%26hl%3Dzh-CN%22%2Cnull%2C%5B%5D%2C4%2C%5B%5D%2C%22GlifWebSignIn%22%5D%2C1%2C%5Bnull%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2C%5B%5D%2C%5B%5D%5D%2Cnull%2Cnull%2Cnull%2Ctrue%5D%2C%22%2B8618123003156%22%5D&bgRequest=%5B%22identifier%22%2C%22!lZallrdCBwoVB145V7VE3PcRNJjxWEsCAAAASFIAAAAomQHDt1boul0D8iUdSI3NX0TCPQxGXA7lBin4_OUJ1ft6xs8yQxp2A-Ozkgm2JVpRyxjSUTbeBFHEugHIrFENJcxVHKjTf7qi6U2TnqamoZKpkxGPPf2xhVuMyGojBcnHtA2wT7rkAlTiyfeQzB2RWrakbUg5sub-2PqKdaF3TzJoN68Zgzp0M4_9GpOBA8tZFX30wVU_G8nxRwQYdczkTKoLs-_gEATnyos7jFGPeAOh0O6nFbcaaZuPun0F7ou8KiO5hDlDkzsBtI5zSz9x72N2-K_TX-pt5HiKAErEsDhTzVsHTJUdAVTpxkXSc1GSpjZZRR_iRmkLHxBVJ7KlVy0bUXbhxZyC9azCyWD9Zcwvrk-FpNBfeVS1dWUGzzssHVfshaSfmjEWmsrW519aWByGFUgkXM-GSp7z7NY58jRvVkAHR1M2UkyHNEkMA_SyVwpou-SUTYCIrOROljsibHK1MizhKgf0M3g-tlkZzG0g7N33zAkS3XSyNEQUqFNtf-ALtBYR2szDES9b26K0nr6m3N2vjCLWAl19WdbsB97xzopeZ0emR1adL0Kz-dwEHsW-bsUupIGjTgEHgoLeRJxk8oUdYg%22%5D&azt=AFoagUVLtJNKCHfcfxo2U3mceDwYINM5eA%3A1552295306037&cookiesDisabled=false&deviceinfo=%5Bnull%2Cnull%2Cnull%2C%5B%5D%2Cnull%2C%22KR%22%2Cnull%2Cnull%2C%5B%5D%2C%22GlifWebSignIn%22%2Cnull%2C%5Bnull%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2C%5B%5D%2C%5B%5D%5D%5D&gmscoreversion=undefined&checkConnection=youtube%3A594%3A1&checkedDomains=youtube&pstMsg=1&"
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            if '",null,null,null,2]' in html:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)

        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return
