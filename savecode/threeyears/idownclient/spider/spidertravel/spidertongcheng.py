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


class SpiderTongCheng(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderTongCheng, self).__init__(task, appcfg, clientid)
        self.cookie = self.task.cookie
        self.ha = HttpAccess()
        if self.cookie:
            self.ha._managedCookie.add_cookies('ly.com', self.cookie)

    def _cookie_login(self):
        url = 'https://member.ly.com/information'
        headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: member.ly.com
Pragma: no-cache
Referer: https://member.ly.com/order
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
        html = self.ha.getstring(url, headers=headers).replace('\r', '').replace('\n', '').replace('\t', '')
        html = re.sub(r'\s{2,}', '', html)
        soup = BeautifulSoup(html, 'lxml')
        try:
            phone = soup.select_one("#tel").get_text('-')
            phone = phone.split('-')[1]
            userid = substring(self.cookie, 'userid=', '&')
            if userid:
                self.userid = userid + '-tongcheng'
                return True
            elif phone:
                self.userid = phone + '-tongcheng'
                return True
            else:
                return False
        except:
            return False

    def _get_profile(self):
        try:
            url = 'https://member.ly.com/information'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: member.ly.com
Pragma: no-cache
Referer: https://member.ly.com/order
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self.ha.getstring(url, headers=headers).replace('\r', '').replace('\n', '').replace('\t', '')
            html = re.sub(r'\s{2,}', '', html)
            soup = BeautifulSoup(html, 'lxml')
            detail = {}
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            try:
                res.nickname = soup.select_one('#txtsmallName')['value']
            except:
                pass
            try:
                detail['realname'] = soup.select_one('#txtName')['value']
            except:
                pass
            try:
                email = soup.select_one("#email").get_text('-')
                res.emali = email.split('-')[1]
            except:
                pass
            try:
                phone = soup.select_one("#tel").get_text('-')
                res.phone = phone.split('-')[1]
            except:
                pass
            try:
                text = substring(html, 'class="sex1"', 'checked=&quot;checked&quot;')
                sexnum = re.findall(r'name="sex"', text)
                if len(sexnum) == 1:
                    res.gender = EGender.Male
                elif len(sexnum) == 2:
                    res.gender = EGender.Female
            except:
                pass
            try:
                detail['profession'] = soup.select_one('#ddlZhiye').get_text()
            except:
                pass
            try:
                res.bithday = soup.select_one('#hfYear')['value'] + '-' + soup.select_one('#hfMonth')['value'] + '-' + \
                          soup.select_one('#hfDay')['value']
            except:
                pass
            try:
                detail['QQ'] = soup.select_one('#txtQQ')['value']
            except:
                pass

            res.append_details(detail)
            photourl = soup.select_one('#contentHead img.png')['src']
            if photourl:
                photourl = 'https:' + photourl
                profilepic: RESOURCES = RESOURCES(self._clientid, self.task, photourl, EResourceType.Picture,
                                                  self._appcfg._apptype)

                resp_stream: ResponseIO = self.ha.get_response_stream(photourl)
                profilepic.io_stream = resp_stream
                profilepic.filename = photourl.rsplit('/', 1)[-1]
                profilepic.sign = ESign.PicUrl
                res.append_resource(profilepic)
                yield profilepic
            yield res
        except Exception:
            self._logger.error('{} got profile fail {}'.format(self.userid, traceback.format_exc()))

    def _get_orders(self):
        try:
            page = 0
            while True:
                page += 1
                url = 'https://member.ly.com/orderajax/default?OrderFilter=0&DateType=0&PageIndex={}'.format(page)
                headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: member.ly.com
Pragma: no-cache
Referer: https://member.ly.com/order
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest"""
                html = self.ha.getstring(url, headers=headers)
                jshtml = json.loads(html)
                OrderDetailList = jshtml['ReturnValue']['OrderDetailList']
                if OrderDetailList:
                    for OrderDetail in OrderDetailList:
                        try:
                            orderid = OrderDetail['OrderId']
                            order = {}
                            order['title'] = OrderDetail['ProductName']
                            order['FirstDesc'] = OrderDetail['FirstDesc']
                            order['price'] = OrderDetail['ProductPrice']
                            order['status'] = OrderDetail['ChieseOrderStatus']
                            order['SerialId'] = OrderDetail['SerialId']
                            order['ExtendData'] = OrderDetail['ExtendData']
                            OrderDetailUrl = OrderDetail['OrderDetailUrl']
                            ordertime, detail = self._order_detail(OrderDetailUrl)
                            if detail:
                                order['detail'] = detail
                            res_one = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                            res_one.append_orders(order)
                            res_one.ordertime = ordertime
                            res_one.host = 'www.ly.com'
                            yield res_one
                        except:
                            pass
                OrderListCount = jshtml['ReturnValue']['OrderListCount']
                if OrderListCount <= 10 * page:
                    break
        except Exception:
            self._logger.error('{} got order fail: {}'.format(self.userid, traceback.format_exc()))

    def _order_detail(self, orderurl):
        orderurl = 'https:' + orderurl
        headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: member.ly.com
Pragma: no-cache
Referer: https://member.ly.com/order
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
        html = self.ha.getstring(orderurl, headers=headers).replace('\n', '').replace('\t', '')
        soup = BeautifulSoup(html, 'lxml')
        # 火车票全部js加密了暂时未获取

        # 景点
        dic = {}
        ordertime = ''
        if re.findall(r'Scenery', orderurl):
            ordertime = substring(html, '创建时间：', ' <')
            dic['Contacts'] = soup.select_one('.infor_box table').get_text(' ')

        # 机票
        elif re.findall(r'Flight', orderurl):
            ordertime = soup.select_one('.orderTime span').get_text('')
            dic['Passenger'] = soup.select_one('.no_bottom.infoLine').get_text(' ')
            dic['Contacts'] = soup.select_one('.contactPerson').get_text(' ')

        # 酒店
        elif re.findall(r'hotel', orderurl):
            ordertime = soup.select_one('.time-point').get_text(' ')
            dic['checkinPerson'] = soup.select_one('.checkin-info.part').get_text(' ')

        return ordertime, dic
