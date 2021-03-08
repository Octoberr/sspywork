import json
import re
import time
import traceback
from datetime import datetime
from bs4 import BeautifulSoup
import pytz
from commonbaby.httpaccess.httpaccess import HttpAccess
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, EGender
from .spidertravelbase import SpiderTravelBase


class SpiderCtrip(SpiderTravelBase):
    def __init__(self, task, appcfg, clientid):
        super(SpiderCtrip, self).__init__(task, appcfg, clientid)
        self.userid = ""
        if self.task.cookie:
            self._ha._managedCookie.add_cookies(".ctrip.com", self.task.cookie)

    def _cookie_login(self):
        res = False
        url = "https://my.ctrip.com/myinfo/home"
        headers = """
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
referer: https://sinfo.ctrip.com/
sec-ch-ua: "Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"
sec-ch-ua-mobile: ?0
sec-fetch-dest: document
sec-fetch-mode: navigate
sec-fetch-site: same-site
sec-fetch-user: ?1
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"""
        try:
            html = self._ha.getstring(url, headers=headers, timeout=10)
            soup = BeautifulSoup(html, "html.parser")
            title = soup.title.text
            if "我的携程" in title:
                res = True
        except:
            self._logger.error(f"Ctrip login error, err:{traceback.format_exc()}")
        return res

    def _get_profile(self):
        try:
            url = "https://m.ctrip.com/restapi/soa2/11838/getUserInfo"
            postdata = """{"parameterList":[{"key":"BizType","value":"BASE"}],"queryConditionList":[{"key":"Self","value":"1"},{"key":"NeedBindInfo","value":"1"}]}"""
            headers = """
accept: */*
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
content-length: 137
content-type: application/json; charset=UTF-8
origin: https://sinfo.ctrip.com
pragma: no-cache
referer: https://sinfo.ctrip.com/
sec-ch-ua: "Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"
sec-ch-ua-mobile: ?0
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-site
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36
"""
            html = self._ha.getstring(url, req_data=postdata, headers=headers)
            jshtml = json.loads(html)
            this_userinfo = jshtml.get("thisUserInfo")
            userid = jshtml.get("uID")
            if userid is None or userid == "":
                raise Exception("Ctrip cannot get userid")
            self.userid = userid
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            res.email = this_userinfo.get("email")
            res.nickname = this_userinfo.get("username")
            gender = this_userinfo.get("gender")
            if gender == "F":
                res.gender = EGender.Female
            elif gender == "M":
                res.gender = EGender.Male
            else:
                res.gender = EGender.Unknown
            detail = this_userinfo
            res.detail = detail
            yield res
        except Exception:
            self._logger.error(
                "{} got profile fail: {}".format(self.userid, traceback.format_exc())
            )

    def _get_orders(self):
        url = "https://my.ctrip.com/myinfo/all"
        headers = """
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            accept-encoding: gzip, deflate, br
            accept-language: zh-CN,zh;q=0.9
            cache-control: no-cache
            pragma: no-cache
            referer: https://my.ctrip.com/myinfo/all
            sec-ch-ua: "Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"
            sec-ch-ua-mobile: ?0
            sec-fetch-dest: document
            sec-fetch-mode: navigate
            sec-fetch-site: same-origin
            sec-fetch-user: ?1
            upgrade-insecure-requests: 1
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36
        """
        try:
            html = self._ha.getstring(url, headers=headers, timeout=10)
            re_orderinfo = re.compile(
                "<script>window.__PRELOAD_STATE__ = (.+?)</script>"
            )
            sorinfo = re_orderinfo.search(html)
            if sorinfo:
                order_info = sorinfo.group(1)
                d_orderinfo = json.loads(order_info)
                order_list = (
                    d_orderinfo.get("order", {})
                    .get("download", {})
                    .get("originOrderList")
                )
                if order_list is None or len(order_list) == 0:
                    self._logger.info(f"There is no order in Ctrip")
                    return
                for order in order_list:
                    orderid = order.get("OrderID")
                    res_one = ITRAVELORDER_ONE(
                        self.task, self._appcfg._apptype, self.userid, orderid
                    )
                    ortime = order.get("BookingDate")
                    if ortime is not None and ortime != "":
                        re_ortime = re.compile("\/Date\((.+?)\+0800\)\/")
                        g_ortime = re_ortime.search(ortime)
                        if g_ortime:
                            ordertimr_str = g_ortime.group(1)
                            time_str = datetime.fromtimestamp(
                                int(ordertimr_str[:-3])
                            ).strftime("%Y-%m-%d %H:%M:%S")
                            res_one.ordertime = time_str
                    res_one.host = "ctrip.com"
                    res_one.append_orders(order)
                    yield res_one

        except:
            self._logger.error(f"Ctrip get order error, err:{traceback.format_exc()}")

    def logout(self, parameter_list):
        """
        docstring
        """
        pass