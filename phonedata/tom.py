"""
获取tom邮箱的信息
create by swm
2018/05/29
"""

import requests
import json

class MAIL:

    def __init__(self):
        self.cookie = 'JSESSIONID=mfxygg45wlgi2nm611a3wefd; Hm_lvt_089662dc0ddc20a9fadd295d90f8c982=1527579185; user_token=A6F9A8E9DB43974BAE034D87F23888E51B28CB41BFC3A675AA1BC2A8804F8FE2; SERVERID=RZ_16120_A; _pk_ref.23.b39f=%5B%22%22%2C%22%22%2C1527579281%2C%22http%3A%2F%2Fmail.tom.com%2F%22%5D; _pk_ses.23.b39f=*; at_oviwm=BQ0D2AjWB!1!1527579290!1527579290!0!; _pk_id.23.b39f=36a6994cb62bbe37.1527579281.1.1527579396.1527579281.; Hm_lpvt_089662dc0ddc20a9fadd295d90f8c982=1527579396'
        self.usragent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'Cookie': self.cookie,
            'User-Agent': self.usragent
        }

    def getmaillist(self):
        # 获取邮件列表
        url = 'http://mail1.tom.com/webmail/query/queryfolder.action'
        data = {
            "folderName": 'INBOX',
            "currentPage": '1',
            "_ts": '1527580597012'
        }
        data = requests.post(url, headers=self.headers, data=data)
        res = json.loads(data.text)
        print(res['result']['pageList'])

    def getmailinfo(self):
        # 获取邮件内容
        url = 'http://mail1.tom.com/webmail/readmail/show.action'
        data = {
            'uid': '5',
            'folderName': 'INBOX'
        }
        res = requests.post(url, headers=self.headers, data=data)
        print(res.text)


if __name__ == '__main__':
    # MAIL().getmaillist()
    MAIL().getmailinfo()