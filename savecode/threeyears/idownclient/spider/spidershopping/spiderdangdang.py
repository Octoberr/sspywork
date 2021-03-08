"""
vpdn当当网爬虫
验证cookie登陆
获取订单，个人信息
20210113
"""
import requests
import json
import re
import time
import traceback
from bs4 import BeautifulSoup

from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import ResponseIO

from .spidershoppingbase import SpiderShoppingBase
from ...clientdatafeedback import ISHOPPING_ONE
from ...clientdatafeedback import PROFILE
from ...clientdatafeedback import RESOURCES, EResourceType, ESign, EGender


class SpiderDangDang(SpiderShoppingBase):
    def __init__(self, task, appcfg, clientid):
        super(SpiderDangDang, self).__init__(task, appcfg, clientid)
        self.userid = ""
        if self.task.cookie:
            self._ha._managedCookie.add_cookies("dangdang.com", self.task.cookie)

    def _cookie_login(self):
        res = False
        url = "http://myhome.dangdang.com/"
        headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Host: myhome.dangdang.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://www.dangdang.com/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36
        """
        try:
            res = self._ha.getstring(url, headers=headers, encoding="GBK", timeout=10)
            soup = BeautifulSoup(res, "html.parser")
            tilte = soup.title.text
            if tilte == "我的当当":
                re_name = re.compile("uname=(.+?)&")
                name = re_name.search(self.task.cookie)
                if name:
                    self.userid = name.group(1)
                res = True
            else:
                res = False
        except:
            self._logger.error(
                f"Connect to dangdang error, err:{traceback.format_exc()}"
            )
        return res

    def _get_orders(self):
        """
        获取当当网的订单，目前来说只要是订单都能获取到
        """
        # 起始页
        page = 1
        while True:
            try:
                url = f"http://myhome.dangdang.com/myOrder/list?searchType=1&statusCondition=0&timeCondition=0&page_current={page}"
                headers = """
                    Accept: */*
                    Accept-Encoding: gzip, deflate
                    Accept-Language: zh-CN,zh;q=0.9
                    Cache-Control: no-cache
                    Connection: keep-alive
                    Host: myhome.dangdang.com
                    Pragma: no-cache
                    Referer: http://myhome.dangdang.com/myOrder
                    User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36
                    X-Requested-With: XMLHttpRequest
                """
                text = self._ha.getstring(
                    url, headers=headers, encoding="GBK", timeout=10
                )
                if text is None or text == "":
                    break
                re_info = re.compile("var info=eval\((\{.+?\})\);")
                info_res = re_info.search(text)
                if info_res:
                    orderjson = info_res.group(1)
                    order_dict = json.loads(orderjson)
                    order_list = order_dict.get("orderList")
                    for orderinfo in order_list:
                        orderid = orderinfo.get("order").get("orderId")
                        orderctime = orderinfo.get("order").get("orderCreationDate")
                        res_one = ISHOPPING_ONE(
                            self.task, self._appcfg._apptype, self.userid, orderid
                        )
                        res_one.ordertime = orderctime
                        res_one.append_orders(orderinfo)
                        res_one.host = "www.dangdang.com"
                        yield res_one
                    # 最后判断下是否要继续
                    pageinfo = order_dict.get("pageInfo")
                    pindex = pageinfo.get("pageIndex")
                    pcount = pageinfo.get("pageCount")
                    if pindex < pcount:
                        page += 1
                    else:
                        break

            except:
                self._logger.error(
                    f"Get dangdang orders error, err:{traceback.format_exc()}"
                )
                break

    def _get_profile(self):
        """
        拿取个人信息
        """
        # 1、尝试在cookie里面直接拿
        name = None
        if self.userid == "":
            re_phone = re.compile("uname=(.+?)&")
            rphone = re_phone.search(self.task.cookie)
            if rphone:
                phone = rphone.group(1)
                self.userid = phone
        re_name = re.compile("MDD_username=(.+?);")
        rname = re_name.search(self.task.cookie)
        if rname:
            name = rname.group(1)
        if self.userid != "":
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            if name is not None:
                res.nickname = name
            yield res
        else:
            url = "http://info.safe.dangdang.com/Myarchives.php"
            headers = """
                Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                Accept-Encoding: gzip, deflate
                Accept-Language: zh-CN,zh;q=0.9
                Cache-Control: no-cache
                Connection: keep-alive
                Host: info.safe.dangdang.com
                Pragma: no-cache
                Referer: http://myhome.dangdang.com/
                Upgrade-Insecure-Requests: 1
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36
            """
            try:
                text = self._ha.getstring(
                    url, headers=headers, encoding="GBK", timeout=10
                )
                soup = BeautifulSoup(text, "html.parser")
                p_div = soup.find(
                    "div", attrs={"class": "account_right", "id": "your_position"}
                )
                # 唯一的昵称
                nameinfo_div = p_div.find("div", attrs={"class": "edit_message1"})
                name_div = nameinfo_div.find("input", attrs={"name": "Txt_petname"})
                name = name_div.get("value")
                self.userid = name
                res = PROFILE(
                    self._clientid, self.task, self._appcfg._apptype, self.userid
                )
                yield res
            except:
                self._logger.error(f"Get profile error, err:{traceback.format_exc()}")
            # 居住地
            # loc_info_div = p_div.find('div', attrs={'id':"area_div", 'class':"mesage_list"})

    def _logout(self):
        ...
