import re
from .spidersocialbase import SpiderSocialBase
import requests


class SpiderFaceBook(SpiderSocialBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderFaceBook, self).__init__(task, appcfg, clientid)
        self.account = '+' + self.task.globaltelcode + self.task.account

    def _check_registration(self):
        """
        查询手机号是否注册了facebook
        # 中国的手机号需要加上+86
        :param account:
        :return:
        """
        url = "https://www.facebook.com/login.php?login_attempt=1&lwv=100"
        res = False
        data = {
            'email': self.account,
            'pass': '18123',
        }

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            # 'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'max-age=0',
            'content-length': '527',
            'content-type': 'application/x-www-form-urlencoded',
            'cookie': 'sb=ICySW8nqss2f2dTN1S3lZJnO; datr=ICySW5CdCZmWYS_DP10Fq6xZ; reg_fb_gate=https%3A%2F%2Fwww.facebook.com%2Flogin.php%3Flogin_attempt%3D1%26lwv%3D110; locale=zh_CN; reg_fb_ref=https%3A%2F%2Fwww.facebook.com%2Flogin.php%3Flogin_attempt%3D1%26lwv%3D100; fr=1jCnLhnNdWh3ktlLA..Bbkiwg.wC.AAA.0.0.BbkjBE.AWX4-ntc; _js_datr=ICySW5CdCZmWYS_DP10Fq6xZ; _js_reg_fb_ref=https%3A%2F%2Fwww.facebook.com%2Flogin.php%3Flogin_attempt%3D1%26lwv%3D110; wd=304x627; act=1536307287893%2F4',
            'origin': 'https://www.facebook.com',
            'referer': 'https://www.facebook.com/login.php?login_attempt=1&lwv=110',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36'
        }

        response = requests.post(url, data=data, headers=headers)
        islongin = re.compile(r'www.facebook.com\\/recover\\/', re.S)
        signup = islongin.search(response.text)
        if signup:
            res = True
        return res

