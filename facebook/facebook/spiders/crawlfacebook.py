"""
爬取facebook的内容
"""
import scrapy
import scrapy_splash
from scrapy import http
from scrapy.selector import Selector
from scrapy_splash import SplashRequest

import json
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
    "cookie":"sb=oHADW-ZcKeEjonBqTB8aej77; datr=oHADW5gHZ9Z03CBY-QhlJXq5; locale=zh_CN; c_user=100026301698530; xs=11%3AMlHEwT9fLhrHrQ%3A2%3A1526952876%3A-1%3A-1; pl=n; ; fr=0ZI8S8W5dSa7utuLH.AWXzJTM5QlSvb195FCkjALtPzzA.Ba77es.qj.AAA.0.0.BbBQ4D.AWW4O79X; act=1527058935570%2F86; presence=EDvF3EtimeF1527058937EuserFA21B26301698530A2EstateFDt3F_5bDiFA2user_3a1B26063503367A2ErF1EoF4EfF10CAcDiFA2user_3a1B26B242731A2ErF1EoF6EfF9C_5dEutc3F1527058431371G527058937646CEchFDp_5f1B26301698530F137CC; wd=594x769"
}


class FACEBOOK(scrapy.Spider):

    name = 'facebook'
    url = 'https://www.facebook.com/CWTheFlash/'
    # anotest = 'http://www.dytt8.net/'

    def start_requests(self):
        yield SplashRequest(url=self.url, headers=headers, callback=self.parse_page,
                            args={
                                'wait': 1
                            }
                            )
          # yield http.Request(url=self.anotest, callback=self.parse_page)

    def parse_page(self, response):
        print("resbody:", response.body)
        html = Selector(response)
        data = html.xpath('//*[@id="u_hl_7"]/div[3]/div[1]/div[2]/div[2]/div/p').extract()
        print('data:', data)
        # div = html.xpath('//*[@id="u_0_l"]')
        # div1 = div.xpath('//*[@id="globalContainer"]')
        # div2 = div1.xpath('//*[@id="u_0_1l"]/div/div[3]/div[3]').extract()
        # print('div1:', div2)
        # print('length', len(div2))
        # data = response.body.decode("utf-8")
        # print("data:", data)
        # html =data['items_html']
        # print(html)
        # respon = response.body.decode("utf-8")
        # text = response.selector.xpath('//*[@id="u_0_1l"]/div').extract()
        # print("data:", text)


