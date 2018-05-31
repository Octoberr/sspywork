"""
获取139邮箱的信息
create by swm 2018/05/29
"""
import requests


class MAIL:

    def __init__(self):
        self.cookie = 'fromhtml5=1; agentid=d110f6e2-f3cb-40f4-a139-0ac671d639ba; a_l=1543111176000|3055657609; a_l2=1543111176000|12|MTgzODEwOTUyODJ8MjAxOC0xMS0yNSAwOTo1OTozNnx2Nm0wOWNDV1o2bDU3OE9SMmZtaWpuNWhFSllBS0x6ZVBHREZBMG1wV1ZyR2JxQW1ITHRuSW1KKzdBK2xlYkJNRW5IR0ZNTEJQUlI0SVN2MDFkUm5yUT09fDdhM2MxYTE4ZjI1YzJhYzY5YzEzMGY2ZmY4ZTZjMzkw; RMKEY=7045921b5b0cb408; Os_SSo_Sid=00UyNzU1OTE3NjAwMTk4NDM4046330AD000001; cookiepartid6089=12; cookiepartid=12; Login_UserNumber=18381095282; html5SkinPath6089=; provCode6089=26; areaCode6089=2603'
        self.usragent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'Cookie': self.cookie,
            'User-Agent': self.usragent
        }

    def getmaillist(self):
        # 获取邮箱列表
        url = 'http://html5.mail.10086.cn/s?func=mbox:listMessages&sid=00UyNzU1OTE3NjAwMTk4NDM4046330AD000001&fid=1&behaviorData=107088_12|107088_14|30127_60&rnd=0.011963272201972908&cguid=1031299951914&k=6089&comefrom=2066'
        data = {"fid":1,"order":"receiveDate","desc":1,"start":1,"total":20,"topFlag":"top","sessionEnable":2}
        res = requests.post(url, headers=self.headers, data=data)
        print(res.text)


if __name__ == '__main__':
    MAIL().getmaillist()


