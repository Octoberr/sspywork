import re
import json
import time
import traceback

import requests
from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import HttpAccess, ResponseIO

from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, RESOURCES, ESign, EResourceType, EGender


class SpiderChair(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderChair, self).__init__(task, appcfg, clientid)
        self.cookie = self.task.cookie
        if self.cookie:
            self._ha._managedCookie.add_cookies('ch.com', self.cookie)

    def _cookie_login(self):
        try:
            url = 'https://account.ch.com/LoginedUserRelevant?lang=zh-cn&_={}'.format(int(time.time() * 1000))
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: account.ch.com
Pragma: no-cache
Referer: https://account.ch.com/memberinfomanagement
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            html = self._ha.getstring(url, headers=headers)
            userid = substring(html, '"aseUserId":"', '"')
            if userid:
                self.userid = userid + '-ch'
                return True
            else:
                return False
        except:
            return False

    def _get_profile(self):
        try:
            url = 'https://account.ch.com/cn/AccountInfo/GetAccountData?_={}'.format(int(time.time() * 1000))
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: account.ch.com
Pragma: no-cache
Referer: https://account.ch.com/memberinfomanagement
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            html = self._ha.getstring(url, headers=headers)
            jshtml = json.loads(html)
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            res.email = jshtml['Data']['UserModel']['Email']
            res.phone = jshtml['Data']['UserModel']['CellPhoneNo']
            res.birthday = jshtml['Data']['UserModel']['Birthday']
            sex = jshtml['Data']['UserModel']['Sex']
            if sex == '1':
                res.gender = EGender.Male
            elif sex == '0':
                res.gender = EGender.Female
            else:
                res.gender = EGender.Unknown
            res.country = jshtml['Data']['UserModel']['Country']

            url = 'https://account.ch.com/default'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: account.ch.com
Pragma: no-cache
Referer: https://account.ch.com/memberinfomanagement
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            photourl = substring(html, "this.src = '", "'")
            if photourl:
                photourl = 'https:' + photourl
                profilepic: RESOURCES = RESOURCES(self._clientid, self.task, photourl, EResourceType.Picture,
                                                  self._appcfg._apptype)

                resp_stream: ResponseIO = self._ha.get_response_stream(photourl)
                profilepic.io_stream = resp_stream
                profilepic.filename = photourl.rsplit('/', 1)[-1]
                profilepic.sign = ESign.PicUrl
                res.append_resource(profilepic)
                yield profilepic
            yield res
        except Exception:
            self._logger.error('{} got profile fail: {}'.format(self.userid, traceback.format_exc()))


    def _get_orders(self):
        # 机票，机票+酒店
        try:
            for hoteltype in (0, 1):
                page = 0
                while True:
                    page += 1
                    url = f'https://account.ch.com/order/flights/?PageNO={page}&HotelType={hoteltype}&DateRange=0&OrderNoFlightNoName='
                    header = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: account.ch.com
Pragma: no-cache
Referer: https://account.ch.com/order/flights?HotelType=0&t_id=3&m_id=1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
                    html = self._ha.getstring(url, headers=header)
                    soup = BeautifulSoup(html, 'lxml')
                    orderList = soup.select('.active.J-order.return')
                    if orderList:
                        for orderinfo in orderList:
                            orderid = orderinfo.select_one('.order').get_text()
                            orderUrl = orderinfo.select_one('a')['href']
                            ordertime, order = self._order_detail(orderUrl)
                            res_one = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                            res_one.append_orders(order)
                            res_one.ordertime = ordertime
                            res_one.host = 'www.ch.com'
                            yield res_one
                    else:
                        break
        except Exception:
            self._logger.error('{} got profile fail: {}'.format(self.userid, traceback.format_exc()))

    def _order_detail(self, orderUrl):
        headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: account.ch.com
Pragma: no-cache
Referer: https://account.ch.com/order/flights/?PageNO=2&HotelType=1&DateRange=0&OrderNoFlightNoName=
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
        html = self._ha.getstring(orderUrl, headers=headers)
        html = re.sub(r'\s{2,}', '', html)
        soup = BeautifulSoup(html, 'lxml')
        ordertime = substring(html, '下单时间</td><td>', '</td>')
        order = soup.select_one('.p-content').get_text(' ').replace('\t', '').replace('\r', '').replace('\n', '')
        order = re.sub(r'\s{2,}', ' ', order)
        res = {}
        res['detail'] = order
        return ordertime, res

