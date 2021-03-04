"""
当当网爬虫
"""

import requests


class SpiderSuNing(object):
    def __init__(self) -> None:
        super().__init__()

    def get_order(self):
        """
        docstring
        """
        ha = requests.session()

        url = "https://order.suning.com/order/queryOrderList.do?transStatus=&pageNumber=1&condition=&startDate=2020-10-15&endDate=2021-01-15&orderType="
        headers = {
            "Accept": "text/html, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Cookie": 'JSESSIONID=ncsNTekeNRDiiLVQDeYchthM.ofsprdapp379; SN_SESSION_ID=9f7a20b7-4d6d-4bb2-a88d-c51fb863777c; _snsr=direct%7Cdirect%7C%7C%7C; streetCode=0280199; cityCode=028; districtId=12132; cityId=9265; hm_guid=e471af0e-549f-4373-a702-012e395dc67f; totalProdQty=0; _df_ud=7a6cd5a1-7cb2-4925-b69e-b1e60027b8ec; _device_session_id=p_3ea7bfca-a664-433d-8332-b4a2bf52bbf4; iar_sncd=0; tradeMA=181; custLevel=161000000100; custno=7053520565; ecologyLevel=ML100100; idsLoginUserIdLastTime=; logonStatus=2; sncnstr=SC8extImk41s7CXj%2FUlYoA%3D%3D; route=ff2e78b889bb530f32eb8c3d7d7592f2; _snzwt=THQrU717703c302a8lYks900f; nick2=181******32; nick=linmeng123456; _snmc=1; authId=siggvc10RkPbI8CnSn6P17SmNT2Bgh4IRk; secureToken=919F835F6AC8C8DC8CF65E6E8CAC92F4; _snadtp=3; _snadid=1717134520210115; _snvd=1610680073429RyZiCgVaPr0; SN_CITY=230_028_1000268_9265_01_12132_1_1_99_0280199; _memberStInfo=success%7C7053520565%7Cperson%7CE102%7CA9200020%7CA1000050%2CA9200020%2Cundefined%2Cundefined%7CA1000100%2CA9200020%2Cundefined%2Cundefined; smidV2=202101151108323d0742251a10b2c3726207dd5c6f6fc80006998e505c69be0; smhst=12123450528|0000000000a12122946298|0000000000; _snma=1%7C161061134794489909%7C1610611347943%7C1610680151394%7C1610681253744%7C26%7C3; _snmp=161068125320226848; _snmb=161068007324230842%7C1610681253766%7C1610681253752%7C12; token=317d9fab-4611-4c9a-9238-b4c274326d97; _twitter_sess=BAh7CiIKZmxhc2hJQzonQWN0aW9uQ29udHJvbGxlcjo6Rmxhc2g6OkZsYXNo%250ASGFzaHsABjoKQHVzZWR7ADoPY3JlYXRlZF9hdGwrCGsaIKtrAToMY3NyZl9p%250AZCIlNzIyZDlhODdlMTVjYjU3MTRkYTBlY2Y4NGQ5MDQzMjQ6B2lkIiVjZTgw%250ANDQ0ZmIyOTAyY2U0MjQ0NjI4ZTFmNjU0MjgwOToJdXNlcmwrCQHglUis2NwN--8ae08c231e9599f1c5868e6518664b987d936c79; personalization_id="v1_DWS0pDCpXtGGNYQxXPYQXQ=="; guest_id=v1%3A156620567551494069',
            "Host": "order.suning.com",
            "Pragma": "no-cache",
            # "Referer": "https://order.suning.com/order/orderList.do?safp=d488778a.homepagev8.Ygnh.1&safpn=10001",
            "sec-ch-ua": '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
            "sec-ch-ua-mobile": "?0",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        response = ha.get(url, headers=headers)
        print(response.status_code)


if __name__ == "__main__":
    ssn = SpiderSuNing()
    ssn.get_order()