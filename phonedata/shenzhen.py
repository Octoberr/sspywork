"""
获取深圳航空的信息
createby swm
2018/05/31
"""

import requests
import json


class MAIL:

    def __init__(self):
        self.cookie = 'JSESSIONID=FBF76A8391B4BCE16F0CD66706CA8D52-n1; sajssdk_2015_cross_new_user=1; CoreSessionId=f4f2ca2b88fcbd153c6f8e8fc097c7de766ca3eaee0fc6e1; _g_sign=4af763b39f17a81243224b5957aba865; _gscu_1330024767=27733381gsidk115; _gscbrs_1330024767=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22163b4016013281-039a60ff19649b-2d604637-304500-163b40160142f6%22%2C%22%24device_id%22%3A%22163b4016013281-039a60ff19649b-2d604637-304500-163b40160142f6%22%2C%22props%22%3A%7B%22nowStatus%22%3A%22%E9%9D%9E%E4%BC%9A%E5%91%98%E7%99%BB%E5%BD%95%22%2C%22platform%22%3A%22WAP%22%2C%22loginid%22%3A%22%22%7D%7D; _gscs_1330024767=2773338129d3kv15|pv:21'
        self.usr = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'Cookie': self.cookie,
            'User-Agent': self.usr
        }

    def getorderinfo(self):
        url = 'http://m.shenzhenair.com/weixin_front/orders.do?method=queryOrdersView'
        payload = {
            'PAGE_INDEX': '0',
            'ISNOLOGINSEARCHORDERINFO': 'false',
            'SENDMESSAGE': '',
            'MOBILE': ''
        }
        res = requests.post(url, headers=self.headers, data=payload)
        resdict = json.loads(res.text)
        print(resdict['orders'])


if __name__ == '__main__':
    MAIL().getorderinfo()
