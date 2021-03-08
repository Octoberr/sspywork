import json
import re
import time
import traceback
from datetime import datetime
import pytz

from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import parse_js
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import HttpAccess

from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, EGender


class SpiderElong(SpiderTravelBase):
    def __init__(self, task, appcfg, clientid):
        super(SpiderElong, self).__init__(task, appcfg, clientid)
        self.userid = ""
        if self.task.cookie:
            self._ha._managedCookie.add_cookies("elong.com", self.task.cookie)

    def _cookie_login(self):

        url = "http://my.elong.com/me_getPersonalInfo"
        headers = """
Accept:*/*
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:no-cache
Connection:keep-alive
Host:my.elong.com
Pragma:no-cache
Referer:http://my.elong.com/me_personalcenter_cn
User-Agent:Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36
X-Requested-With:XMLHttpRequest"""

        # {"data": "{'gender':'','mail':'sldjlv@yeah.net','memberLevel':1,'mobile':'134****8256','sendPromotions':'\\u0000','suppressAllMailings':'1','tripFrequency':0,'tripPrice':0,'userCard':'190000000003378806','username':'艺龙会员'}","lang": "cn", "success": true}
        try:
            html = self._ha.getstring(url, headers=headers)
            jshtml = json.loads(html)
            data = parse_js(jshtml["data"])
            mail = data["mail"]
            usercard = data["userCard"]
            if not usercard == "" and usercard is not None:
                self.userid = usercard + "-elong"
            elif not mail == "" and mail is not None:
                self.userid = mail + "elong"
            else:
                return False
            return True
        except:
            return False

    def _get_orders(self):
        pageNum = 0
        total = 0
        pageSize = 100
        #     # 机票订单获取
        while True:
            pageNum += 1
            headers = """
                Accept: application/json; charset=utf-8
                Accept-Encoding: gzip, deflate
                Accept-Language: zh-CN,zh;q=0.9
                Cache-Control: no-cache
                Connection: keep-alive
                Content-Length: 46
                Content-Type: application/x-www-form-urlencoded
                Host: flight.elong.com
                Origin: http://flight.elong.com
                Pragma: no-cache
                Referer: http://flight.elong.com/flight/jorder/list/1
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
                X-Requested-With: XMLHttpRequest
            """
            url = "http://flight.elong.com/order/ly/rest/list"
            postdata = "p=%7B%22pageSize%22%3A{}%2C%22pageNo%22%3A{}%7D".format(
                pageSize, pageNum
            )
            data = self._ha.getstring(url, req_data=postdata, headers=headers)
            try:
                jsdata = json.loads(data)
                total = jsdata["totalCount"]
                if total == 0 or not total:
                    break
                orders = jsdata["orders"]
                orderids = []
                for order in orders:
                    orderid = order["orderId"]
                    orderids.append(orderid)

                if orderids:
                    for orderid in orderids:
                        isorder = re.match(r"\d+", orderid)
                        if not isorder:
                            url = "http://flight.elong.com/order/ly/rest/detail"
                            headers = """
                                    Accept: application/json; charset=utf-8
                                    Accept-Encoding: gzip, deflate
                                    Accept-Language: zh-CN,zh;q=0.9
                                    Cache-Control: no-cache
                                    Connection: keep-alive
                                    Content-Length: 72
                                    Content-Type: application/x-www-form-urlencoded
                                    Host: flight.elong.com
                                    Origin: http://flight.elong.com
                                    Pragma: no-cache
                                    Referer: http://flight.elong.com/flight/jorder/detail/0/OB8P4BCKC104WH108145
                                    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
                                    X-Requested-With: XMLHttpRequest
                                """
                            postdata = "p=%7B%22orderId%22%3A%22{}%22%2C%22orderType%22%3A0%7D".format(
                                orderid
                            )
                            html = self._ha.getstring(
                                url, headers=headers, req_data=postdata
                            )
                            html = json.loads(html)
                            res_one = ITRAVELORDER_ONE(
                                self.task, self.task.apptype, self.userid, orderid
                            )
                            try:
                                res_one.ordertime = html["orderTime"]
                            except:
                                pass
                            res_one.append_orders(html)
                            res_one.host = "www.elong.com"
                            yield res_one
                        else:
                            url = "http://flight.elong.com/flight/jorderdetail_{}_cn.html".format(
                                orderid
                            )
                            headers = """
                                    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                                    Accept-Encoding: gzip, deflate
                                    Accept-Language: zh-CN,zh;q=0.9
                                    Cache-Control: no-cache
                                    Connection: keep-alive
                                    Host: flight.elong.com
                                    Pragma: no-cache
                                    Referer: http://my.elong.com/flight/flightorder_cn.html?rnd=1543916424942
                                    Upgrade-Insecure-Requests: 1
                                    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
                                """
                            html = self._ha.getstring(url, headers=headers)

                            soup = BeautifulSoup(html, "lxml")
                            orderinfo = soup.select_one("#orderinfo").get_text(" ")
                            order = re.sub(r"\s{2,}", "", orderinfo)
                            res_one = ITRAVELORDER_ONE(
                                self.task, self.task.apptype, self.userid, orderid
                            )
                            dic = {}
                            dic["order"] = order
                            res_one.append_orders(dic)
                            res_one.ordertime = substring(order, ">(预订日期：", ")")
                            res_one.host = "www.elong.com"
                            yield res_one
            except Exception:
                self._logger.error(
                    "Got flight order fail: {}".format(traceback.format_exc())
                )
            if total <= pageSize * pageNum:
                break

        # 酒店订单
        pageNum = 0
        pagecount = 0
        while True:
            pageNum += 1
            url = "http://my.elong.com/hotel/MyHotelOrderList_cn.html"
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: my.elong.com
Pragma: no-cache
Referer: http://my.elong.com/hotel/myhotelorderdetail_cn_454498922.html
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)

            try:
                pagecount = int(substring(html, "totalPageCount:", ","))
                orderids = re.findall(r"订单号：<b>(.*?)</b>.*?预订时间：<b>(.*?)</b>", html)
                if not orderids:
                    break
                for orderid, ordertime in orderids:
                    url = "http://my.elong.com/hotel/myhotelorderdetail_cn_{}.html".format(
                        orderid
                    )
                    headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: my.elong.com
Pragma: no-cache
Referer: http://my.elong.com/hotel/MyHotelOrderList_cn.html
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36"""
                    html = self._ha.getstring(url, headers=headers)
                    soup = BeautifulSoup(html, "lxml")
                    ordertop = soup.select_one(".detailTop").get_text()
                    order = (
                        ordertop + " " + soup.select_one(".detailCon.clx").get_text()
                    )
                    order = order.replace("\n", "").replace("\r", "").replace("\r", "")
                    order = re.sub(r"\s{2,}", "", order)
                    res_one = ITRAVELORDER_ONE(
                        self.task, self.task.apptype, self.userid, orderid
                    )
                    dic = {}
                    dic["order"] = order
                    res_one.append_orders(dic)
                    res_one.ordertime = ordertime
                    res_one.host = "www.elong.com"
                    yield res_one
            except Exception:
                self._logger.error(
                    "Got hotel order fail: {}".format(traceback.format_exc())
                )

            if pageNum >= pagecount:
                break

        # 国际酒店订单获取
        pageNum = 0
        total = 0
        while True:
            pageNum += 1
            time1 = int(datetime.now(pytz.timezone("Asia/Shanghai")).timestamp() * 1000)
            time2 = int(datetime.now(pytz.timezone("Asia/Shanghai")).timestamp() * 1000)
            url = "http://ihotel.elong.com/order/list?callback=jsonp{}&_={}&pageNo={}&pageSize=100".format(
                time1, time2, pageNum
            )
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: ihotel.elong.com
Pragma: no-cache
Referer: http://my.elong.com/ihotel/orderlist_cn.html?rnd=1543982045782
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            try:
                html = substring(html, "(", ")")
                jshtml = json.loads(html)
                total = jshtml["data"]["pageInfo"]["totalCount"]
                orders = jshtml["data"]["orderList"]
                if orders:
                    for order in orders:
                        orderid = order["orderId"]
                        ordertime = order["orderTime"]
                        arr = time.localtime(ordertime)
                        ordertime = time.strftime("%Y-%m-%d %H:%M:%S", arr)
                        res_one = ITRAVELORDER_ONE(
                            self.task, self.task.apptype, self.userid, orderid
                        )
                        res_one.append_orders(order)
                        res_one.ordertime = ordertime
                        res_one.host = "www.elong.com"
                        yield res_one

            except Exception:
                self._logger.error(
                    "Got international hotel order fail: {}".format(
                        traceback.format_exc()
                    )
                )
            if total <= pageNum * pageSize:
                break

    def _get_profile(self):
        url = "http://my.elong.com/me_getPersonalInfo"
        headers = """
Accept:*/*
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:no-cache
Connection:keep-alive
Host:my.elong.com
Pragma:no-cache
Referer:http://my.elong.com/me_personalcenter_cn
User-Agent:Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36
X-Requested-With:XMLHttpRequest"""
        html = self._ha.getstring(url, headers=headers)
        # {"data": "{'gender':'','mail':'sldjlv@yeah.net','memberLevel':1,'mobile':'134****8256','sendPromotions':'\\u0000','suppressAllMailings':'1','tripFrequency':0,'tripPrice':0,'userCard':'190000000003378806','username':'艺龙会员'}","lang": "cn", "success": true}
        try:
            jshtml = json.loads(html)
            data = parse_js(jshtml["data"])
            res = PROFILE(self._clientid, self.task, self.task.apptype, self.userid)
            try:
                res.account = data["userCard"]
            except:
                pass
            try:
                res.mail = data["mail"]
            except:
                pass
            try:
                res.nickname = data["username"]
            except:
                pass
            try:
                res.phone = data["mobile"]
            except:
                pass
            try:
                gender = data["gender"]
                if gender == "male":
                    res.gender = EGender.Male
                elif gender == "female":
                    res.gender = EGender.Female
                else:
                    res.gender = EGender.Unknown
            except:
                pass
            try:
                res.address = data["city"]
            except:
                pass
            yield res
        except Exception as ex:
            self._logger.error("%s get profile fail: %s" % (self.userid, ex))
