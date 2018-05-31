"""
获取yeahnet邮箱的信息
create by swm 2018/05/29
"""
import requests

class MAIL:

    def __init__(self):
        self.cookie = 'starttime=; NTES_SESS=piyH0LD0YptBM8leUeE478YlP7T8.Vgig.MBVVoa5OYn_q13_H8IY.T_jau1Xgd13aK5m3qSOIgAXZoIvQ5woT3FPsROJ0QIeSIcFGHnqdecWJhKt57dXjBMcAe._UfATVVcxmFpPiC8JDSOTYF22vro.RoXSY7ZXU1AouztMtkGbQtnhxWNgts3zVK4ZyLQ7gr8A0K0FJ75ngNGBNtGzH3k0; S_INFO=1527558033|0|##2&70|nmsbyeahnet@yeah.net; P_INFO=nmsbyeahnet@yeah.net|1527558033|0|mailyeah|00&99|null&null&null#sic&510100#10#0#0|&0||nmsbyeahnet@yeah.net; mail_upx=c2bj.mail.yeah.net|c3bj.mail.yeah.net|c4bj.mail.yeah.net|c5bj.mail.yeah.net|c6bj.mail.yeah.net|c7bj.mail.yeah.net|c1bj.mail.yeah.net; mail_upx_nf=; mail_idc=""; Coremail=b2b7e21178053%IAAKzLnnpYMzneWhycnnReRLtzYetSUs%g1a6.mail.yeah.net; cm_last_info=dT1ubXNieWVhaG5ldCU0MHllYWgubmV0JmQ9aHR0cCUzQSUyRiUyRm1haWwueWVhaC5uZXQlMkZtJTJGbWFpbi5qc3AlM0ZzaWQlM0RJQUFLekxubnBZTXpuZVdoeWNublJlUkx0ellldFNVcyZzPUlBQUt6TG5ucFlNem5lV2h5Y25uUmVSTHR6WWV0U1VzJmg9aHR0cCUzQSUyRiUyRm1haWwueWVhaC5uZXQlMkZtJTJGbWFpbi5qc3AlM0ZzaWQlM0RJQUFLekxubnBZTXpuZVdoeWNublJlUkx0ellldFNVcyZ3PW1haWwueWVhaC5uZXQmbD0wJnQ9MTEmYXM9ZmFsc2U=; MAIL_SESS=piyH0LD0YptBM8leUeE478YlP7T8.Vgig.MBVVoa5OYn_q13_H8IY.T_jau1Xgd13aK5m3qSOIgAXZoIvQ5woT3FPsROJ0QIeSIcFGHnqdecWJhKt57dXjBMcAe._UfATVVcxmFpPiC8JDSOTYF22vro.RoXSY7ZXU1AouztMtkGbQtnhxWNgts3zVK4ZyLQ7gr8A0K0FJ75ngNGBNtGzH3k0; MAIL_SINFO=1527558033|0|##2&70|nmsbyeahnet@yeah.net; MAIL_PINFO=nmsbyeahnet@yeah.net|1527558033|0|mailyeah|00&99|null&null&null#sic&510100#10#0#0|&0||nmsbyeahnet@yeah.net; secu_info=1; mail_entry_sess=1dc3df717e7f1a97e095a96a74c01af63b2611c62f1c9abb487a17cdaa6d00b0aa3f1c3306c11a1296822eb70687c087ac64dc50b6ca8bded529139920f21396f6a671c5b998410f6c3888bb3cffefe6ac02700d06e3d9d57da6c31aecc736a882a5867cfa93ff6e3e091954d47df88e68264f3acdbac5bd768da7c6c8e63bbfbfc38060ebec9eb9c94094939410f0dfe89c6e79c3044387f02ab6461946ffe38b5217a2338f8a0290a4bf2f1f695104697b31f86a15d45f1bd44ad64f5244d3; JSESSIONID=4CD2E7ED787E17A580350265121691F2; locale='
        self.usragent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'Cookie': self.cookie,
            'User-Agent': self.usragent
        }

    def getmailist(self):
        # 登陆获取邮件列表
        url = 'http://mail.yeah.net/m/s?sid=IAAKzLnnpYMzneWhycnnReRLtzYetSUs&func=global:sequential'
        data = {
            'var': '<?xml version="1.0"?><object><array name="items"><object><string name="func">mbox:getAllFolders</string><object name="var"><boolean name="stats">true</boolean></object></object><object><string name="func">mbox:listMessages</string><object name="var"><string name="order">date</string><boolean name="desc">true</boolean><int name="start">0</int><int name="limit">20</int><int name="fid">1</int></object></object></array></object>'
        }
        data = requests.post(url, headers=self.headers, data=data)
        print(data.text)

    def getmailinfo(self):
        # 获取邮件的内容
        url = 'http://mail.yeah.net/m/s?sid=IAAKzLnnpYMzneWhycnnReRLtzYetSUs&func=mbox:readMessage&l=read&action=read'
        data = {
            "var": '<?xml version="1.0"?><object><string name="id">14:1tbiDgAMGlH7iuVvswAAbB</string><string name="mode">both</string><boolean name="autoName">true</boolean><boolean name="supportTNEF">true</boolean><boolean name="filterStylesheets">true</boolean><boolean name="returnImageInfo">true</boolean><boolean name="markRead">true</boolean></object>'
        }
        data = requests.post(url, headers=self.headers, data=data)
        print(data.text)


if __name__ == '__main__':
    MAIL().getmailinfo()