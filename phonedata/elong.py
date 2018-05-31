"""
获取艺龙的信息
create by swm
2018/05/31
"""

import requests
import json


class MAIL:

    def __init__(self):
        self.cookie = 'CookieGuid=9ecd27a8-b0d5-4c47-b018-32a15ce68cee; SessionGuid=6523f31e-e98b-436f-ac77-a636002dbde3; Esid=d64f3924-91b0-494d-904b-ba474e4564ba; com.eLong.CommonService.OrderFromCookieInfo=Status=1&Orderfromtype=1&Isusefparam=0&Pkid=50&Parentid=50000&Coefficient=0.0&Makecomefrom=0&Cookiesdays=0&Savecookies=0&Priority=8000; fv=pcweb; H5SessionId=E5128F25676C3EBB5F342A9ABF5E992D; H5Channel=ewhtml5%2CDefault; H5CookieId=e072f237-3006-4611-b732-c6c458d39b03; indate=2018-05-31; outdate=2018-06-01; _fid=e072f237-3006-4611-b732-c6c458d39b03; _RF1=175.152.119.113; _RSG=V2aw6OHlDM60w83b07c.K8; _RDG=280acd08c3f22f2aba154278c73ceb40a7; _RGUID=658dbd16-06ea-409f-853e-9870250c8e80; innerFrom=110011; ch=h5usercenter; SessionToken=7b29b206-a505-4c1d-9aa3-b05a21691177622; route=c875947fc1aa224eaa9b732cfa8b10c7; businessLine=hotel'
        self.usra = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'cookie': self.cookie,
            'user-agent': self.usra
        }

    def getorderlist(self):
        url = 'https://m.elong.com/hotel/api/gethotelorders?_rt=1527731470126&pageindex=0'
        res = requests.get(url, headers=self.headers)
        resdict = json.loads(res.text)
        print(resdict['orderList'])
        # print(res.text)


if __name__ == '__main__':
    MAIL().getorderlist()