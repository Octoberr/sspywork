"""
获取海南航空的信息
createby swm
2018/05/30
"""

import requests
import json


class MAIL:

    def __init__(self):
        self.usra = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers ={
            'User-Agent': self.usra
        }

    def getorderlist(self):
        url = 'https://app.hnair.com/mapp/webservice/v1/user/tmsExchange/orderList?token=dfaffdc7f59972b93c58d7bced54bdf2_bf72ab157460ca9c7581c05c8ea09319&hnairSign=B32021D662E88AB3E9750C34EDDC9A3AB622EA1D'
        formdata = {"common":{"sname":"Win32","sver":"5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1","schannel":"HTML5","slang":"zh-CN","did":"defualt_web_did","stime":1527670440588,"szone":-480,"aname":"com.hnair.spa.web.standard","aver":"6.11.1","akey":"9E4BBDDEC6C8416EA380E418161A7CD3","abuild":"10099","atarget":"standard","slat":"slat","slng":"slng","gtcid":"defualt_web_gtcid"},"data":{"pageSize":10,"page":1,"refresh":'true',"orderFlag":"0","beginDate":"20180430","endDate":"20180531"}}
        res = requests.post(url, headers=self.headers, data=formdata)
        print(res.text)


if __name__ == '__main__':
    MAIL().getorderlist()