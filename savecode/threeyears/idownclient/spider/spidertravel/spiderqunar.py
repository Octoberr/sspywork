import json
import re
import time
import traceback
from datetime import datetime, timedelta
import pytz

import requests
from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import ResponseIO

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import (
    EResourceType,
    PROFILE,
    ITRAVELORDER_ONE,
    RESOURCES,
    IdownLoginLog_ONE,
    ESign,
    EGender,
)


class SpiderQunar(SpiderTravelBase):
    def __init__(self, task, appcfg, clientid):
        super(SpiderQunar, self).__init__(task, appcfg, clientid)
        self.cookie = self.task.cookie
        self.userid = ""
        self._s = requests.Session()
        self._ha._managedCookie.add_cookies("qunar.com", self.cookie)

    def _check_registration(self):
        """
        查询手机号是否注册了去哪儿
        :param account:
        :return:
        """
        t = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            headers = """
Accept: application/json, text/javascript, */*; q=0.01
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Origin: https://user.qunar.com
Referer: https://user.qunar.com/passport/register.jsp?ret=%2Fuserinfo%2Findex.jsp
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            url = "https://user.qunar.com/ajax/validator.jsp"
            postdata = f"method={self.task.phone}&prenum=86&vcode=null"
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            if '"errMsg":"用户已存在"' in html:
                self._write_task_back(
                    ECommandStatus.Succeed, "Registered", t, EBackResult.Registerd
                )
            else:
                self._write_task_back(
                    ECommandStatus.Succeed, "Not Registered", t, EBackResult.UnRegisterd
                )

        except Exception:
            self._logger.error(
                "Check registration fail: {}".format(traceback.format_exc())
            )
            self._write_task_back(
                ECommandStatus.Failed,
                "Check registration fail",
                t,
                EBackResult.CheckRegisterdFail,
            )
        return

    def _cookie_login(self):
        try:
            csrfToken = substring(self.cookie, "csrfToken=", ";")
            if csrfToken is None or csrfToken == "":
                return False
            t = str(
                int(datetime.now(pytz.timezone("Asia/Shanghai")).timestamp() * 1000)
            )
            cookieurl = (
                "http://user.qunar.com/index/basic?t={t}&csrfToken={csrfToken}".format(
                    t=t, csrfToken=csrfToken
                )
            )
            headers = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:max-age=0
Connection:keep-alive
Host:user.qunar.com
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36"""
            html = self._ha.getstring(cookieurl, headers=headers)
            jshtml = json.loads(html)
            self.userid = str(jshtml["data"]["uid"]) + "-qunar"
            return True
        except:
            return False

    def _get_loginlog(self):
        try:
            csrfToken = substring(self.cookie, "csrfToken=", ";")
            if csrfToken is None or csrfToken == "":
                return None
            t = str(
                int(datetime.now(pytz.timezone("Asia/Shanghai")).timestamp() * 1000)
            )
            url = "http://user.qunar.com/security/queryUserLoginHistoryRecords.jsp"
            postdata = "csrfToken={}&t={}".format(csrfToken, t)
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 58
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Host: user.qunar.com
Origin: http://user.qunar.com
Pragma: no-cache
Referer: http://user.qunar.com/userinfo/account.jsp
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            jshtml = json.loads(html)
            data = jshtml["data"]
            if data:
                for m in data:
                    res = IdownLoginLog_ONE(
                        self.task, self._appcfg._apptype, self.userid
                    )
                    res.platform = m["method"]
                    res.logintype = m["deviceType"]
                    res.logintime = m["dateTime"] + " " + m["hourTime"]
                    res.region = m["location"]
                    yield res
        except Exception:
            self._logger.info("Got login log fail: {}".format(traceback.format_exc()))

    def _get_profile(self):
        try:
            csrfToken = substring(self.cookie, "csrfToken=", ";")
            if csrfToken is None or csrfToken == "":
                return None
            t = str(
                int(datetime.now(pytz.timezone("Asia/Shanghai")).timestamp() * 1000)
            )
            cookieurl = (
                "http://user.qunar.com/index/basic?t={t}&csrfToken={csrfToken}".format(
                    t=t, csrfToken=csrfToken
                )
            )
            headers = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:max-age=0
Connection:keep-alive
Host:user.qunar.com
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36"""
            html = self._ha.getstring(cookieurl, headers=headers)
            jshtml = json.loads(html)

            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            data = jshtml["data"]
            res.account = data["username"]
            gender = data["gender"]
            if gender == 0:
                res.gender = EGender.Unknown
            elif gender == 1:
                res.gender = EGender.Male
            elif gender == 2:
                res.gender = EGender.Female
            res.phone = data["mobile"]
            res.email = data["email"]
            res.nickname = data["nickname"]
            encodeName = data["encodeName"]
            if not encodeName is None or encodeName == "":
                photo = {}
                photo[
                    "picurl"
                ] = "http://headshot.user.qunar.com/avatar/{}.png?l".format(encodeName)

                profilepic: RESOURCES = RESOURCES(
                    self._clientid,
                    self.task,
                    photo["picurl"],
                    EResourceType.Picture,
                    self._appcfg._apptype,
                )

                resp_stream: ResponseIO = self._ha.get_response_stream(photo["picurl"])
                profilepic.io_stream = resp_stream
                profilepic.filename = encodeName + ".png"
                profilepic.resourceid = encodeName
                profilepic.sign = ESign.PicUrl
                res.append_resource(profilepic)

                yield profilepic
            yield res
        except Exception:
            self._logger.error(
                "{} got profile fail: {}".format(self.userid, traceback.format_exc())
            )

    def _get_orders(self):
        try:
            dicCookie = {}
            # for line in self.cookie.split(';'):
            #     key, value = line.split('=', 1)
            #     dicCookie[key] = value
            # self._s.cookies.update(dicCookie)
            orderurl = "http://order.qunar.com/frontapi/getorder"
            orderheaders = """
accept: */*
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
content-length: 91
content-type: application/x-www-form-urlencoded; charset=UTF-8
origin: https://order.qunar.com
pragma: no-cache
referer: https://order.qunar.com/
sec-ch-ua: "Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"
sec-ch-ua-mobile: ?0
sec-fetch-dest: empty
sec-fetch-mode: cors
sec-fetch-site: same-origin
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36
x-requested-with: XMLHttpRequest
"""
            pagesize = 20
            start = 0
            totalcount = 0
            # 只能查询一年的
            time_now = datetime.now()
            time_now_str = time_now.strftime("%Y-%m-%d")
            last_year = time_now - timedelta(days=365)
            last_year_str = last_year.strftime("%Y-%m-%d")
            while True:
                orderdata = f"category=&range=12&businessType=&start={start}&orderType=&startDate={last_year_str}&endDate={time_now_str}"
                html = self._ha.getstring(
                    orderurl, req_data=orderdata, headers=orderheaders
                )
                try:
                    pagesize = int(substring(html, 'data-pagesize=\\"', '\\"'))
                except:
                    self._logger.info("Got pagesize fail")

                try:
                    totalcount = int(substring(html, 'data-totalcount=\\"', '\\"'))
                except:
                    self._logger.info("Got totalcount fail")
                datahtml = (
                    html.replace("link", "")
                    .replace("appDown", "")
                    .replace("\\n", "")
                    .replace("\\", "")
                )
                soup = BeautifulSoup(datahtml, "html.parser")
                order_divs = soup.find_all(
                    "div", attrs={"class": "mainorder order-pay"}
                )
                if len(order_divs) == 0:
                    self._logger.info(
                        "Cannot find any orders info, please check the html rules"
                    )
                for od in order_divs:
                    try:
                        order_dict = {}
                        data_orderno = od.get("data-orderno")
                        res_one = ITRAVELORDER_ONE(
                            self.task, self._appcfg._apptype, self.userid, data_orderno
                        )
                        order_dict["订单号"] = data_orderno
                        data_type = od.get("data-type")
                        order_dict["订单类型"] = data_type
                        # 下单时间
                        time_span = od.find("span", attrs={"class": "first"})
                        if time_span:
                            order_time = time_span.text.split("|")[-1].strip()
                            res_one.ordertime = order_time
                            order_dict["下单时间"] = order_time
                        info_table = od.find("table", attrs={"class": "order-bd"})
                        if data_type == "hotel":
                            order_dict["酒店名字"] = info_table.a.text
                            order_time_info = info_table.find_all("dd")
                            order_dict["入住时间"] = order_time_info[0].text
                            order_dict["离开时间"] = order_time_info[1].text
                            # 价格和数量
                            price = info_table.find(
                                "td", attrs={"class": "qunatity"}
                            ).text.strip()
                            order_dict["订单价格"] = price
                            # 状态
                            state = info_table.find(
                                "td", attrs={"class": "state"}
                            ).text.strip()
                            order_dict["订单状态"] = state
                        elif data_type == "flight":
                            # 行程
                            order_dict["行程"] = info_table.find("h3").text.strip()
                            # 航空名字
                            order_dict["航空公司"] = info_table.find(
                                "div", attrs={"class": "clearfix"}
                            ).img.get("title")
                            # 具体起飞机场
                            start_flight = info_table.find_all(
                                "div", attrs={"class": "name-main clearfix"}
                            )
                            order_dict["起飞机场"] = start_flight[0].div.text.strip()
                            order_dict["起飞时间"] = start_flight[0].p.text
                            # 落地信息
                            order_dict["落地机场"] = start_flight[1].div.text.strip()
                            order_dict["落地时间"] = start_flight[1].p.text
                            # 价格和数量
                            price = info_table.find(
                                "td", attrs={"class": "qunatity"}
                            ).text.strip()
                            order_dict["订单价格"] = price
                            # 状态
                            state = info_table.find(
                                "td", attrs={"class": "state"}
                            ).text.strip()
                            order_dict["订单状态"] = state
                        res_one.host = "qunar.com"
                        res_one.append_orders(order_dict)
                        yield res_one
                    except:
                        self._logger.error(
                            f"Parse order info error, err:{traceback.format_exc()}"
                        )
                        continue

                start += pagesize
                if start > totalcount:
                    break

        except Exception:
            self._logger.error(
                "{} got order fail: {}".format(self.userid, traceback.format_exc())
            )
