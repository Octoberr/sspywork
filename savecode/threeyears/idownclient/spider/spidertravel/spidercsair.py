import datetime
import json
import re
import time
import traceback
import pytz

from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring
import requests

from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, EGender


class SpiderCsair(SpiderTravelBase):
    def __init__(self, task, appcfg, clientid):
        super(SpiderCsair, self).__init__(task, appcfg, clientid)
        self.userid = ""
        if self.task.cookie:
            self._ha._managedCookie.add_cookies(".csair.com", self.task.cookie)

    def _cookie_login(self):
        """
        cookie login
        """
        res = False
        url = "https://b2c.csair.com/portal/user/checkLogin"

        payload = {}
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Length": "0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": self.task.cookie,
            "Host": "b2c.csair.com",
            "Origin": "https://b2c.csair.com",
            "Pragma": "no-cache",
            "Referer": f"https://b2c.csair.com/B2C40/modules/ordernew/orderManagementFrame.html?_={int(time.time()*1000)}",
            "sec-ch-ua": '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
            "sec-ch-ua-mobile": "?0",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }
        try:
            response = requests.request("POST", url, headers=headers, data=payload)
            resstr = response.text
            jdict = json.loads(resstr)
            success = jdict.get("success")
            if success:
                res = True
                self.userid = jdict.get("data", {}).get("userId")
        except:
            self._logger.error(f"Csair login error,err:{traceback.format_exc()}")
        return res

    def _sms_login(self):
        try:
            phone = self.task.phone
            if not phone:
                return False
            self._befor_login()
            url = "http://b2c.csair.com/B2C40/modules/bookingnew/manage/login.html"
            headers = """
Host: b2c.csair.com
Proxy-Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Referer: http://www.csair.com/cn/index.shtml?WT.mc_id=sem-baidu-pbzc-title1214&WT.srch=1
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
"""
            html = self._ha.getstring(url, headers=headers)

            url = "http://b2c.csair.com/portal/smsMessage/EUserVerifyCode"
            headers = """
Accept: application/json, text/javascript, */*; q=0.01
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 18
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Host: b2c.csair.com
Origin: https://b2c.csair.com
Pragma: no-cache
Referer: https://b2c.csair.com/B2C40/modules/bookingnew/manage/login.html
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            postdata = f"mobile={phone}"
            html = self._ha.getstring(url, headers=headers, req_data=postdata)

            url = "https://b2c.csair.com/portal/user/login"
            vcode = self._get_vercode()
            postdata = "userId={}&vcode={}&loginType=12&memberType=8".format(
                phone, vcode
            )
            headers = """
Host: b2c.csair.com
Proxy-Connection: keep-alive
Content-Length: 57
Accept: application/json, text/javascript, */*; q=0.01
Origin: http://b2c.csair.com
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Referer: http://b2c.csair.com/B2C40/modules/bookingnew/manage/login.html
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
"""
            html = self._ha.getstring(
                url, headers=headers, req_data=postdata, verify=False
            )
            res = self._cookie_login()
            return res
        except Exception:
            self._logger.error("Sms login fail: {}".format(traceback.format_exc()))

    def _pwd_login(self):
        try:
            if self.task.account and self.task.account:
                account = self.task.account
                password = self.task.password
            else:
                return False
            self._befor_login()
            url = "http://b2c.csair.com/portal/user/login"
            headers = """
Host: b2c.csair.com
Proxy-Connection: keep-alive
Content-Length: 60
Accept: application/json, text/javascript, */*; q=0.01
Origin: http://b2c.csair.com
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Referer: http://b2c.csair.com/B2C40/modules/bookingnew/manage/login.html
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
"""
            postdata = f"userId={account}&passWord={password}&loginType=1&memberType=1"
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            newcookie = self._ha._managedCookie.get_cookie_for_domain(
                "http://csair.com"
            )
            self.cookie = newcookie
            res = self._cookie_login()
            return res
        except Exception:
            self._logger.error("password login fail: {}".format(traceback.format_exc()))

    def _get_profile(self):
        try:
            url = "https://skypearl.csair.com/skypearl/personal/basic"
            headers = """
Accept: application/json
Accept-Encoding: gzip, deflate, br
accept-language: zh
Connection: keep-alive
Host: skypearl.csair.com
Origin: https://skypearl.csair.com
Referer: https://skypearl.csair.com/skypearl/personal.html?lang=zh
Sec-Fetch-Dest: empty
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            html = self._ha.getstring(url, req_data="null", headers=headers)
            profile = PROFILE(
                self._clientid, self.task, self._appcfg._apptype, self.userid
            )
            if html == "" or html is None:
                self._logger.error(
                    "{} got profile fail: html is empty".format(self.userid)
                )
            res = json.loads(html)
            data = res["data"]
            if "memberNo" in data:
                profile.account = data["memberNo"]
            if "birthday" in data:
                profile.birthday = data["birthday"]
            if "cnFullName" in data:
                profile.nickname = data["cnFullName"]
            if "title" in data:
                if data["title"] == "先生":
                    profile.gender = EGender.Male
                elif data["title"] == "女士":
                    profile.gender = EGender.Female
                else:
                    profile.gender = EGender.Unknown
            yield profile
        except Exception:
            self._logger.error(
                "{} got profile fail: {}".format(self.userid, traceback.format_exc())
            )

    def _get_orders(self):
        try:
            now = datetime.datetime.now(pytz.timezone("Asia/Shanghai"))
            # 取3年订单
            predate = str(int(now.year) - 3) + "-" + now.strftime("%m-%d")
            url = "http://b2c.csair.com/portal/ordermanage/planeOrder/queryPlaneOrders"
            pageNum = 0
            while 1:
                pageNum += 1
                postdata = "groupflag=0&bookTimeFrom={predate}&status=&all=&page={pageNum}".format(
                    predate=predate, pageNum=pageNum
                )
                headers = """
Accept:application/json, text/javascript, */*; q=0.01
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:no-cache
Connection:keep-alive
Content-Type:application/x-www-form-urlencoded
Host:b2c.csair.com
Origin:http://b2c.csair.com
Pragma:no-cache
Referer:http://b2c.csair.com/B2C40/modules/ordernew/orderList.jsp"""
                html = self._ha.getstring(url, req_data=postdata, headers=headers)
                try:
                    jshtml = json.loads(html)
                except:
                    break
                # start = jshtml['start']
                end = jshtml["end"]
                total = jshtml["total"]
                orderList = jshtml["order"]
                if orderList:
                    for m in orderList:
                        orderid = m["orderno"]
                        ordertime = m["createdate"]
                        if m["status"] == "A":
                            m["status"] = "待支付"
                        elif m["status"] == "B":
                            m["status"] = "待出票"
                        elif m["status"] == "C":
                            m["status"] = "已出票"
                        elif m["status"] == "D":
                            m["status"] = "已取消"
                        res_one = ITRAVELORDER_ONE(
                            self.task, self._appcfg._apptype, self.userid, orderid
                        )
                        res_one.append_orders(m)
                        res_one.ordertime = ordertime
                        res_one.host = "www.csair.com"
                        yield res_one
                if total <= end:
                    break
        except Exception:
            self._logger.error(
                "{} got order fail: {}".format(self.userid, traceback.format_exc())
            )

    def _befor_login(self):
        try:
            t = int(
                datetime.datetime.now(pytz.timezone("Asia/Shanghai")).timestamp() * 1000
            )
            url = f"http://b2c.csair.com/B2C40/user/createSid.ao?callback=jQuery11020537106827026615_{t}&_={t+1}"
            headers = """
Host: b2c.csair.com
Proxy-Connection: keep-alive
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Accept: */*
Referer: http://www.csair.com/cn/index.shtml?WT.mc_id=sem-baidu-pbzc-title1214&WT.srch=1
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cookie: language=zh_CN
"""
            html1 = self._ha.getstring(url, headers=headers)

            url = "http://b2c.csair.com/portal/user/verify/isShowVCode"
            headers = """
Host: b2c.csair.com
Proxy-Connection: keep-alive
Content-Length: 2
Accept: application/json, text/javascript, */*; q=0.01
Origin: http://b2c.csair.com
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Content-Type: application/json
Referer: http://b2c.csair.com/B2C40/modules/bookingnew/manage/login.html
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
"""
            html3 = self._ha.getstring(url, headers=headers, req_data="")
            now_time = datetime.datetime.now(pytz.timezone("Asia/Shanghai")).timestamp()
            url = f"http://b2c.csair.com/portal/user/verify/challenge?_={int(now_time*1000)}"
            headers = """
Host: b2c.csair.com
Proxy-Connection: keep-alive
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Accept: image/webp,image/apng,image/*,*/*;q=0.8
Referer: http://b2c.csair.com/B2C40/modules/bookingnew/manage/login.html
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
"""
            html4 = self._ha.getstring(url, headers=headers)

        except Exception:
            self._logger.error("befor login error: {}".format(traceback.format_exc()))

    def _logout(self):
        res = False
        try:
            try:
                token = self._ha._managedCookie.get_cookie_value("cs1246643sso").value
            except:
                token = ""
            try:
                user = self._ha._managedCookie.get_cookie_value("userId").value
            except:
                user = ""
            t = int(
                datetime.datetime.now(pytz.timezone("Asia/Shanghai")).timestamp() * 1000
            )
            url = f"https://b2c.csair.com/portal/user/logout?time={t}&token={token}&userId={user}"
            html = self._ha.getstring(
                url,
                headers="""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: b2c.csair.com
Pragma: no-cache
Referer: https://b2c.csair.com/B2C40/modules/ordernew/orderManagementFrame.html?_=1553152870663
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""",
            )
            res = self._cookie_login()
            if not res:
                res = True
        except Exception:
            self._logger.error("login out fail:{}".format(traceback.format_exc()))
        return res