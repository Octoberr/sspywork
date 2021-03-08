"""
唯品会cookie登陆
订单，个人信息下载
20181030
"""
import requests
import traceback
from .spidershoppingbase import SpiderShoppingBase
import re
import pytz
import time
import datetime
import json
from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import HttpAccess, ResponseIO
from ...clientdatafeedback import (
    PROFILE,
    RESOURCES,
    EResourceType,
    ISHOPPING_ONE,
    EGender,
    ESign,
)


class SpiderWeiPinhui(SpiderShoppingBase):
    def __init__(self, task, appcfg, clientid):
        super(SpiderWeiPinhui, self).__init__(task, appcfg, clientid)
        self.cookie = self.task.cookie
        self.userid = ""
        self.time = datetime.datetime.now(pytz.timezone("Asia/Shanghai")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    def _cookie_login(self):
        url = "http://myi.vip.com/api/account/base_info"
        self._ha._managedCookie.add_cookies(".vip.com", self.cookie)
        headers = """
accept: application/json, text/javascript, */*; q=0.01
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
referer: https://myi.vip.com/basicinfo.html?ff=103|2|2|9
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
x-requested-with: XMLHttpRequest
"""
        try:
            r = self._ha.getstring(url, headers=headers)
            jsdata = json.loads(r)
            phone = jsdata["data"]["mobile"]
            if phone:
                self.userid = phone + "-weipinhui"
                return True
            else:
                return False
        except:
            return False

    def _get_orders(self):
        try:
            orderurl = "http://order.vip.com/order/getOrderListTab?tabChannel=all&status=0&searchKey=&pageNo=1"
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Cookie: {cookie}
Host: order.vip.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://order.vip.com/order/orderlist?tabChannel=all&status=0&searchKey=&pageNo=1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
X-Requested-With: XMLHttpRequest
""".format(
                cookie=self.cookie
            )
            r = self._ha.getstring(orderurl, headers=headers)
            patpage = re.compile(r"共(.*?)页")
            ispagenum = patpage.search(r)
            if ispagenum:
                pagenum = int(patpage.findall(r)[0]) + 1
                for page in range(1, pagenum):
                    url = "http://order.vip.com/order/getOrderListTab?tabChannel=all&status=0&searchKey=&pageNo={page}".format(
                        page=page
                    )
                    headers = """
Accept: */*
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Cookie: {cookie}
Host: order.vip.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://order.vip.com/order/orderlist?tabChannel=all&status=0&searchKey=&pageNo=1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
X-Requested-With: XMLHttpRequest
""".format(
                        cookie=self.cookie
                    )
                    r = self._ha.getstring(url, headers=headers)
                    soup = BeautifulSoup(r, "lxml")
                    orderlist = soup.select(".m-table tbody")
                    for order in orderlist[1:]:
                        dicorder = dict()
                        dicorder["mobile"] = order.attrs.get("data-mobile")
                        dicorder["money"] = order.attrs.get("data-money")
                        orderid = order.attrs.get("data-ordersn")
                        dicorder["receiver"] = order.attrs.get("data-receiver")
                        dicorder["sizeamount"] = order.attrs.get("data-sizeamount")
                        ordertime = order.select_one(".num.order-gen-date").get_text()
                        dicorder["status"] = order.select_one(".purple span").get_text()
                        list = order.select(".order-bd")

                        commodity = []
                        for commoditys in list:
                            diccommodity = dict()
                            diccommodity["name"] = commoditys.select_one(
                                ".name"
                            ).get_text()
                            diccommodity["size"] = commoditys.select_one(
                                ".size"
                            ).get_text()
                            commodity.append(diccommodity)

                        dicorder["commodity"] = commodity

                        res_one = ISHOPPING_ONE(
                            self.task, self._appcfg._apptype, self.userid, orderid
                        )
                        res_one.ordertime = ordertime
                        res_one.append_orders(dicorder)
                        res_one.host = "www.vip.com"
                        yield res_one
            else:
                yield None
        except Exception:
            self._logger.error(
                "{} got order fail: {}".format(self.userid, traceback.format_exc())
            )

    def _get_profile(self):
        try:
            url = "http://myi.vip.com/api/account/base_info"
            self._ha._managedCookie.add_cookies(".vip.com", self.cookie)
            headers = """
accept: application/json, text/javascript, */*; q=0.01
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
referer: https://myi.vip.com/basicinfo.html?ff=103|2|2|9
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
x-requested-with: XMLHttpRequest
"""
            r = self._ha.getstring(url, headers=headers)
            jsdata = json.loads(r)
            data = jsdata["data"]
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            res.phone = data.get("mobile")
            res.email = data.get("email")
            res.account = data.get("userName")
            res.nickname = data.get("nickname")
            gender = data.get("gender")
            if gender == 1:
                res.gender = EGender.Male
            elif gender == 0:
                res.gender = EGender.Female
            else:
                res.gender = EGender.Unknown
            res.birthday = data.get("birthday")
            res.address = data.get("address")
            countryId = data.get("countryId")
            detail = {}
            detail["areaCode"] = data.get("areaCode")
            detail["telephone"] = data.get("telephone")
            detail["cityId"] = data.get("cityId")
            detail["countryId"] = countryId
            res.detail = json.dumps(detail)
            #             headers1 = """
            # accept: application/json, text/javascript, */*; q=0.01
            # accept-encoding: gzip, deflate, br
            # accept-language: zh-CN,zh;q=0.9
            # cache-control: no-cache
            # pragma: no-cache
            # referer: https://myi.vip.com/basicinfo.html?ff=103|2|2|9
            # user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
            # x-requested-with: XMLHttpRequest
            # """
            #             response = self._ha.getstring(
            #                 "https://myi.vip.com/api/account/extra_info", headers=headers1
            #             )
            #             jsresponse = json.loads(response)
            #             if jsresponse["data"]["image_url"]:
            #                 photourl = "https:" + jsresponse["data"]["image_url"]

            #                 profilepic: RESOURCES = RESOURCES(
            #                     self._clientid,
            #                     self.task,
            #                     photourl,
            #                     EResourceType.Picture,
            #                     self._appcfg._apptype,
            #                 )

            #                 resp_stream: ResponseIO = self._ha.get_response_stream(photourl)
            #                 profilepic.io_stream = resp_stream
            #                 profilepic.filename = photourl.rsplit("/", 1)[-1]
            #                 profilepic.sign = ESign.PicUrl
            #                 res.append_resource(profilepic)
            #                 yield profilepic
            yield res
        except Exception:
            self._logger.error(
                "{} got profile fail: {}".format(self.userid, traceback.format_exc())
            )

    def _logout(self):
        res = False
        try:
            url = "https://passport.vip.com/logout?src=https%3A%2F%2Fwww.vip.com%2F"
            html = self._ha.getstring(
                url,
                headers="""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: passport.vip.com
Pragma: no-cache
Referer: https://www.vip.com/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""",
            )
            res = self._cookie_login()
            if not res:
                res = True
        except Exception:
            self._logger.error("login out fail:{}".format(traceback.format_exc()))
        return res