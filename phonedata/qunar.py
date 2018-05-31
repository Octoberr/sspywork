"""
获取去哪网的订单信息
createby swm
2018/05/30
"""

import requests
import json


class MAIL:

    def __init__(self):
        self.cookie = 'QN99=6616; QN300=organic; QN48=tc_f86a0f44452e489d_163afc16bfb_a47b; csrfToken=fc6988c4e58e0163d9d3d1c6acc7fd43; _RF1=175.152.119.113; _RSG=5eqSdEQTLrCcU_rH_wQVN8; _RDG=28a215c07653b6202015a38b18c8303981; _RGUID=cd5575a3-a773-4a05-85df-6bafd1d7f7a6; QN66=qunar; _i=ueHdPEv-rLVXugLy4hbYopS7SpkX; QN25=2e346944-82c2-4536-846b-5c13058a0c77-9f992f90; QN1=O5cv5lsORheColXvK1x9Ag==; fid=ddeedd92-a75f-4773-a526-96f81be959fa; QN271=74f03292-23b4-45c9-b566-557185b2173b; _s=s_U3AO2LUJWHCJTL5H7RMCXCFTOU; _v=FTILl1PT2lUZlCeBUulGrsq9swEr9WNCOWYU5gsTL4gtit7b0F2Rsvy4YIGxY7066Pjdfzfcv9Nf9B6Fu-R_k5PY9-JdG0ZvtpuV5zImVbAzfxtfItgA8DwpbXNtLAYIcUAQDL2weAN6XGkNnaVHg9d73pNY9Vq-193MtDserC26; _t=25700076; _q=U.sodnvgl6020; QN43=2; QN42=rdfg5652'
        self.usr = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'cookie': self.cookie,
            'user-agent': self.usr
        }

    def getorderinfo(self):
        # 获取订单信息
        url = 'https://touch.qunar.com/api/wireless/order/query.do'
        formdata = {

            'limit': '10',
            'start': '0',
            'clientJson': {"type": "touch"},
            'businessTypes': 'flight, train, bus, directbus, hotel, hotel_sight, tese, huiyi, ticket, icar, car, travel, local, insure, qmall, shopping, pack, bnb',
            'isUserNameQuery': 'true',
            'isLocalQuery': 'false',
            'unbindQuery': 'false',
            'source': 'touchMy',
            'orderCenterStatus': 'all'
        }
        res = requests.post(url, headers=self.headers, data=formdata)
        resdict = json.loads(res.text)
        ol = resdict['data']['orderList']
        for el in ol:
            print(el)
            # print('/n')
        # print(res.text)


if __name__ == '__main__':
    MAIL().getorderinfo()