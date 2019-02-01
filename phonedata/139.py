"""
获取139邮箱的信息
create by swm 2018/05/29
"""
import requests


class MAIL:

    def __init__(self):
        self.cookie = 'Login_UserNumber=18381095282;Os_SSo_Sid=00U0MzIxNTQyODAwMDA4MTg000188EF5000001;RMKEY=5da51b4ea217f42f;SkinPath26089=;UserData=%7BssoSid%3A%2700U0MzIxNTQyODAwMDA4MTg000188EF5000001%27%2CuidList%3A%5B%221545518214%22%5D%2CprovCode%3A26%2CserviceItem%3A%270015%27%2ClastLoginDate%3A%272018-11-26+14%3A54%3A45%27%2CuserNumber%3A%278618381095282%27%2Cloginname%3A%2718381095282%27%2C%22out_qanotify%22%3Afalse%7D;a_l=1558767428000|5871728271;a_l2=1558767428000|12|MTgzODEwOTUyODJ8MjAxOS0wNS0yNSAxNDo1NzowOHx2Nm0wOWNDV1o2bDU3OE9SMmZtaWpuNWhFSllBS0x6ZVBHREZBMG1wV1ZyR2JxQW1ITHRuSW1KKzdBK2xlYkJNRW5IR0ZNTEJQUlI0SVN2MDFkUm5yUT09fDAzYWViODE3ZTc1NTVkMzQ4Zjk2YTlkMmU3MWFhZDc1;areaCode6089=2603;cookiepartid=12;cookiepartid6089=12;provCode6089=26;rmUin6089=1883607579;JSESSIONID=C3B10A007081C15854BB8F3FD222429C'

        self.usragent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604' \
                        '.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'Cookie': self.cookie,
            'User-Agent': self.usragent
        }

    def getmaillist(self):
        # 获取邮箱列表
        url = 'http://html5.mail.10086.cn/s?func=mbox:listMessages&sid=00' \
              'UyNzU1OTE3NjAwMTk4NDM4046330AD000001&fid=1&behaviorData=107088_12|107088_14|30127_60' \
              '&rnd=0.011963272201972908&cguid=1031299951914&k=6089&comefrom=2066'
        data = {"fid": 1, "order": "receiveDate", "desc": 1, "start": 1, "total": 20, "topFlag": "top",
                "sessionEnable": 2}
        res = requests.post(url, headers=self.headers, data=data)
        print(res.text)


if __name__ == '__main__':
    MAIL().getmaillist()
