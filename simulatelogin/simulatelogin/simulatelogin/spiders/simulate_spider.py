# coding:utf-8

import scrapy
from scrapy.selector import Selector
class SimulateVoxer(scrapy.Spider):
    name = 'voxer'
    startUrl = 'http://www.ip138.com/yuming/'
    header = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": "www.ip138.com",
        "Upgrade-Insecure-Requests": 1,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
    }

    def start_requests(self):
        yield scrapy.Request(self.startUrl, headers=self.header, callback=self.parse)

    def parse(self, response):
        res = Selector(response)
        div = 