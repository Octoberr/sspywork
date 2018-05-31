"""
新浪邮箱信息获取
create by swm
2018/05/29
"""

import requests
import json

class MAIL:

    def __init__(self):
        self.cookie = 'SCF=AjQxr_Zh4IYQSEoMMLcFVd8i4Yf6E-BeL4bHM9j0bNqmXoL5Od7nLH6oJY5b_VhRgXBV4dlSjcu66acVeWogDhE.; SUB=_2A252CIxDDeRhGeBN61UR-SnEwz-IHXVV8hQLrDV9PUJbktBeLW7ckW1NRLc6_zBX2rLr9ZAlBeXj0C2UQgAZ0V1N; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFB9TA-lBRnpnXgskMV7Gix5JpX5K2hUgL.Foq0ehM71KMR1he2dJLoIp7LxKML1KBLBKnLxKqL1hnLBoMce05Neh.N1hn0; SWEBAPPSESSID=20a06c020ca992f66dd5c84aa52c739a3'
        self.usragrnt = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'Cookie': self.cookie,
            'User-Agent': self.usragrnt
        }

    def getmaillist(self):
        # 获取邮件的列表
        url = 'http://m0.mail.sina.cn/wa.php?a=list_mail'
        formdata = {
            'fid': 'new',
            'order': 'htime',
            'sorttype': 'desc',
            'start': '0',
            'length': '20'
        }
            # 'fid=new&order=htime&sorttype=desc&start=0&length=20'
        res = requests.post(url, headers=self.headers, data=formdata)
        dicres = json.loads(res.text)
        # print(dicres)
        maillist = dicres['data']['maillist']
        print(maillist)
        print(len(maillist))

    def getmailinfo(self):
        # 获取邮件内容
        url='http://m0.mail.sina.cn/wa.php?a=readmail'
        data = {
            'mid': '04CF8E7F6230F85CC6B9677C09E81D130C00000000000001',
            'fid': 'new'
        }
        res = requests.post(url, headers=self.headers, data=data)
        resdic = json.loads(res.text)
        print(resdic['data'])


if __name__ == '__main__':
    # MAIL().getmaillist()
    MAIL().getmailinfo()