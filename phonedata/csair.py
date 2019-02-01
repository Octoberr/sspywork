"""
中国南方航空的信息收集
create by swm
2018/05/30
"""
import requests
import json


class MAIL:

    def __init__(self):
        self.cookie = 'JSESSIONID=D882130978F2F7629FC07C6AFBB9113C; WM_TID=tvLz7AbpwWANzRcmyhpAe7g%2BOYLZbo2l; WT-FPC=id=175.152.119.113-3333738160.30668790:lv=1527671799110:ss=1527671747349:fs=1527671747349:pn=3:vn=1; TOKEN=b8e804fa50ba44aab8b6df95fe1522db; cs1246643sso=b8e804fa50ba44aab8b6df95fe1522db; csmbpdeviceid=hafqDRjI8LaA1jJacI4lJSaNkToDNSaS; csmbplogintype=1'
        self.usra = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'cookie': self.cookie,
            'user-agent': self.usra,
            'content-length': '151'
        }

    def getinlist(self):
        url = 'https://m.csair.com/touch/com.csair.mbp.index/index.html#com.csair.mbp.mytrip_new/orderList'
        payload = {
            "aid": "",
            "userId": "480005130044",
            "depTime": "",
            "arrTime": "",
            "bookTimeFrom": "2018-04-30",
            "bookTimeTo": "2018-05-31",
            "status": "",
            "orderno": "",
            "period": 30
        }
        # res = requests.post(url, headers=self.headers, data=payload)
        res = requests.get(url, headers=self.headers)
        print(res.text)


if __name__ == '__main__':
    MAIL().getinlist()
