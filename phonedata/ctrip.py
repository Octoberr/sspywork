"""
爬取携程网的信息
createby swm
2018/05/30
"""
import requests
import json


class MAIL:

    def __init__(self):
        self.cookie = 'abtest_userid=dad75d61-e406-4b77-8a7e-12c6ea954d3b; MKT_Pagesource=H5; _ga=GA1.2.624166291.1527669104; _gid=GA1.2.1264386226.1527669104; ASP.NET_SessionSvc=MTAuMTQuMy41Mnw5MDkwfG91eWFuZ3xkZWZhdWx0fDE1MjU4MzIxNjY0ODM; _RF1=175.152.119.113; _RSG=V2aw6OHlDM60w83b07c.K8; _RDG=280acd08c3f22f2aba154278c73ceb40a7; _RGUID=658dbd16-06ea-409f-853e-9870250c8e80; _fpacid=09031067210419915485; GUID=09031067210419915485; _jzqco=%7C%7C%7C%7C1527669104165%7C1.202191417.1527669103788.1527669103789.1527669115090.1527669103789.1527669115090.0.0.0.2.2; login_uid=C2034F4CB67B5D3B36887DE154643AB5303261B2071D42007ACD0A030A766A99; login_type=0; cticket=D4297B693DFFD85E54249FB5592801293E6EEDFDFA6A202FB49C4707E50BB478; ticket_ctrip=bJ9RlCHVwlu1ZjyusRi+ypZ7X2r4+yojlOMkLbYro8jXHLSmQL0goBGYa+VZrumJ4Cx/iujSyNWqErS9GdRI4Hi6dWjqvT4HmGNpjuG3GUHXiKEhke8zYxbE5+esEdPd76JZraLQkMI8jblDlfJrMYh+Tja1JqWRc8fBny4iXhuyt0CbBgk8YF6Q5xUMGQtOFYlYtDq2/cBmTlgDLGTiE6J8JA/47asiJOUkhhr7XE70ENiV2I+pb4/IgNpT9ExoYYnx7IIT/a0r41fVLGYq40AKRkB4BKRawCwvTzcEcGE=; AHeadUserInfo=VipGrade=0&UserName=&NoReadMessageCount=0; DUID=u=C535DC0521C931FF4EE5A603C0F96BA2&v=0; IsNonUser=F; _bfa=1.1527669103180.10cmxod.1.1527669103180.1527669201121.1.5.600003395'
        self.usra = 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        self.headers = {
            'cookie': self.cookie,
            'user-agent': self.usra,
            'content - type': 'application / json',
            'x - ctrip - pageid': '600001411',
            'x - requested -with': 'XMLHttpRequest'
        }

    def gettriplist(self):
        # 获取个人订单的列表信息
        url = 'https://m.ctrip.com/restapi/soa2/10098/GetOrdersSearch.json?_fxpcqlniredt=09031067210419915485'
        formdata = {
            "ClientVersion": "7.13",
            "Channel": "H5",
            "PageSize": '15',
            "BizTypes": "Flight,PreSale,FlightX",
            "OrderStatusClassify": "All",
            "FilterValidOrder": 'false',
            "PageIndex": '1',
            "sequence": "ccdacaeb-edeb-eb8e-79e8-152a5af01626",
            "head": {"cid": "09031067210419915485", "ctok": "", "cver": "1.0", "lang": "01", "sid": "8888",
                     "syscode": "09", "auth": 'null',
                     "extension": [{"name": "sequence", "value": "ccdacaeb-edeb-eb8e-79e8-152a5af01626"},
                                   {"name": "protocal", "value": "https"}]},
            "contentType": "json"
        }
        res = requests.post(url, headers=self.headers, data=formdata)
        resdict = json.loads(res.text)
        print(resdict)
        # print(res.text)


if __name__ == '__main__':
    MAIL().gettriplist()
