"""
获取189邮箱信息
createby swm 2018/05/29
"""

import requests
import json


class MAIL:

    def __init__(self):
        self.cookie = 'JSESSIONID=arLBuM6X2MUfTERXPo; 189LOGINFLAG=newwebmail; LSID=arLBuM6X2MUfTERXPo; 189SESSION_ID=189-USERINFO-183810952821527562326; 189ACCOUNT=18381095282@189.cn; advertId=af858643f56431d8e3838690dee2032dd8baf8fe56d0f9f7; 189ALIAS=; 189LTID=1aff1be271145dcd4d1642b20b0d57dc'
        self.usragent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            "Cookie": self.cookie,
            "User-Agent": self.usragent
        }

    def getmaillist(self):
        # 获取邮件列表
        url = 'https://wap.189.cn/wap2/mail/listMail.do?labelId=1&pageNum=1&sortWay=68&sortField=0&excludeFlag=&mailFlag=&noCache=0.7695235649129788'
        res = requests.get(url, headers=self.headers)
        dictres = json.loads(res.text)
        print(dictres['mailMap'])

    def getmailcont(self):
        url = 'https://wap.189.cn/wap2/mail/readMail.do?messageId=100.10.64.12.22.15196235237930gmadver.18381095282%40100&msId=153'
        res = requests.get(url, headers=self.headers)
        dictres = json.loads(res.text)
        print(dictres['subject'])


if __name__ == '__main__':
    MAIL().getmailcont()