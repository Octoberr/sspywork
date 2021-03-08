"""
验证手机号是否注册了苏宁易购
验证cookie登陆
获取订单，个人信息
20181023
"""
import datetime
import json
import re
import time
import traceback
import pytz

import requests
from bs4 import BeautifulSoup
from commonbaby.httpaccess.httpaccess import HttpAccess

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidershoppingbase import SpiderShoppingBase
from ...clientdatafeedback import ISHOPPING_ONE
from ...clientdatafeedback import PROFILE
from ...clientdatafeedback import RESOURCES, EResourceType, EGender, ESign


class SpiderSuning(SpiderShoppingBase):
    def __init__(self, task, appcfg, clientid):
        super(SpiderSuning, self).__init__(task, appcfg, clientid)
        self._ha = HttpAccess()
        self.userid = ""
        self.time = datetime.datetime.now(pytz.timezone("Asia/Shanghai")).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        if self.task.cookie:
            self._ha._managedCookie.add_cookies("suning.com", self.task.cookie)

    def _cookie_login(self):
        """
        cookie登陆测试
        """
        res = False
        url = "http://my.suning.com/person.do"
        headers = """
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Host: my.suning.com
            Proxy-Connection: keep-alive
            Referer: http://my.suning.com/person.do
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
        """
        try:
            r = self._ha.getstring(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r, "lxml")
            patuserid = re.compile(r"您的会员编号为：(.*?)，", re.S)
            userid = patuserid.findall(str(soup))[0]
            if userid:
                self.userid = userid + "-suning"
                res = True
        except:
            self._logger.error(f"Cookie login error, err:{traceback.format_exc()}")
        return res

    def _check_registration(self):
        """
        查询手机号是否注册了suning
        :param account:
        :return:
        """
        t = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            headers = """
                Accept: application/json, text/javascript, */*; q=0.01
                Content-Type: application/x-www-form-urlencoded; charset=UTF-8
                Origin: http://passport.suning.com
                Referer: http://passport.suning.com/ids/login
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
                X-Requested-With: XMLHttpRequest
            """
            url = "http://passport.suning.com/ids/login"
            postdata = f"jsonViewType=true&username={self.task.phone}&password=&password2=Ujsa1wIs9Jnzn%2Fc%2BqT%2FyQldPMMWVrWviEorr1ku8VnnZGydpUB55QyQZso%2B1%2BZYP97u1MIlXMoBbCTkKRMURME7dMO%2BGIuA6RwVOmFCawDE%2FMYMtuO1PmhgwRlxurrcKF8uBep9Sf8D4dgTv7w%2F8rYqrI3cxUTWmpedBArbxQ6Y%3D&loginTheme=defaultTheme&service=&rememberMe=true&client=app&sceneId=logonImg&detect=mmds_3nZnnnuzF3MnnnuzT3Znnniz83Znnn3zP3MnnnnzL3nZnnnnzS3ZnnnnzN3Znnnvz13Mnnn0zq3Ynnn9zE3nZnnnYzR3Znnn-z43mnnnrzr3YnnnczU3u3nncz-3nvinnczU3MnnnczU3bCnnczr3Mnnnfz43Znnnhz433ZnnnEz43MnnnXzf3Znnn.zf3Znnn1zO3Ynnnkzh3nmnnnVzB3YnnnPzB3ZnnnJzB3MnnnbzB3MnnnbzB3nq3nnFzh3ZnnnFzO3YnnnKzR3mnnnpzf3Znnnlzf3nQnnnlzt3fnnnlz43n3nnpz43Kinnpzc3znnnKzc3nMnnnFzr3YnnnTz-3o3nnJz-3CnnnLz_3MnnnNzY3nZnnnCzY3Mnnn1GY3ZnnnuGY3ZnnnA7Y3Mnnn67Y3iYnnnO7Y3VnnnO7Y3FnnnO7Z3CnnnR7M3Ynnnt753nZnnn-7o3Mnnn_7I3-nnnY7I35nnn97I3Mnnno7I3nXpnno7I3MnnnY7Z3Znnnt7U3Znnn67t3Mnnnw7R3nZnnn17h3YnnnA7h393nns7h3znnnW7h3Mnnnw7h3nMnnn.7B3QnnnA7B3mnnnT763ZnnnoGX3Ynnn1Gs33Mnnnizk3MnnnZzd3Ynnntza3Mnnnhzj3LAnnuCni3Ynnn7C3imnnnGCiiPnnnzC7i9nnneCCiMnnn5Coi3Znnn5CMiYnnn5CZiynnn5CYiCnnn5C_i5nnn5CUinmnnneCfiZnnnCCBiMnnnzCEi_3nnzC6iT3nnzCgi36nnnzCgiMnnnzCXiYnnnzCqiJCnnGCqiMnnnuCdinMnnn~zQiYYnngzLiMnnn2zViMnnn2zViZnnn2zSinl3nnXzaiennnXzaiMnnnqzdiZnnnqzNiMnnnqzNinxYa2E~~j2tjE7R.fE2EjY.Pj7Y2PRPYf.EaYaz~zf6~Eju7.xa2jPxRttxDYYR~auzz~ajx8Pnn~C_36enniCuinXoncCviZ23nk0UiMgnn4C3iMjnnk0viQConMCnirMnn4zgiMG3nwztifINnyzMi853npz43353nhzj3cY3nqzNixa22txaEEjPERP2EPutxxn3iuv7GzC0xjxtxa22tx~utxaxtxGBI3.uZinnn1znn.u9innnTvnn.uz3nnnnnnn.usinnnC5nn.uc3nnn6inn.uW3nnnnvnn.uminnnT7nn.uJnnnnnnnn.usinnn67nn.uT3nnnx2jPxs7mnnnnnvnnniu3nnnnnSgnndnnnnnnnh2nni5nnnnnn4nnnEqnnnnnnJqnnfHInnnnnUMnnAI3nnnnni7nnunnnnnnninnnKt7nnnnnlt7niz1nnnnne53nxPERxMTOnyyxLK03GCniMnnnGCiiMnnnGCGiZnnnvCCiZnnniC0i3Mnnn3CeiYnnn3CIiZnnnnCoimnnnyz5iZnnnyz9inYnnnyzMibCnnTzMi9nnnNzMiYnnntzMiZnnnPGmi3ZnnnmG5iZnnnQ75iMnnnB75iZnnnY75iMnnn97oingnnn97IiMnnn970iYnnn970iMnnn97Ci.3nn57CinZnnni70imnnnTvIiZnnnSv9iZnnnkvMiMnnnsvYi3ZnnnWvYi83nnWv_ikvnnWv_iN4nnzGUiEnnnGGUiio3nn7GUiYnnnvGUifnnnuGriCnnnvGci6nnnzGti3ZnnnoGfimnnnYGfiYnnnRGRiMnnn2GRiZnnn1Gti3ZnnnVG-iMnnnPGMiYnnnKGIiZnnnyGziZnnnizii3mnnnvzniZnnn7zl3Znnn7zp3Qnnn7zK3Mnnnvt~EzLzt~u2zF_._796d0c53-7e52-42b9-a978-a8944ba6c172_._&dfpToken=THP7fd1696fcef06aX5E3e4d3&terminal=PC&loginChannel=208000103001"
            response = self._ha.getstring(url, headers=headers, req_data=postdata)
            if '"errorCode":"badPassword.msg1"' in response:
                self._write_task_back(
                    ECommandStatus.Succeed, "Registered", t, EBackResult.Registerd
                )
            elif '"errorCode":"needVerifyCode"' in response:
                self._write_task_back(
                    ECommandStatus.Failed,
                    "Need VerifyCode!",
                    t,
                    EBackResult.CheckRegisterdFail,
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

    def _get_orders(self):
        """
        获取订单信息
        """
        headers = """
            Accept: text/html, */*; q=0.01
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: no-cache
            Connection: keep-alive
            Host: order.suning.com
            Pragma: no-cache
            sec-ch-ua: "Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"
            sec-ch-ua-mobile: ?0
            Sec-Fetch-Dest: empty
            Sec-Fetch-Mode: cors
            Sec-Fetch-Site: same-origin
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36
            X-Requested-With: XMLHttpRequest
        """
        thistime = time.strftime("%Y-%m-%d")
        patorderlist = re.compile(r'<div class="table-list">')
        page = 1
        while True:
            try:
                url = f"https://order.suning.com/order/queryOrderList.do?transStatus=&pageNumber={page}&condition=&startDate=2009-01-01&endDate={thistime}&orderType="
                html = self._ha.getstring(url, headers=headers, timeout=10)
                orderlist = patorderlist.search(html)
                if orderlist:
                    soup = BeautifulSoup(html, "lxml")
                    orders = soup.select(".table-list .table-box")
                    for order in orders:
                        try:
                            dic1 = {}
                            patid = re.compile(r'id="table_box_(.*?)"', re.S)
                            orderid = patid.findall(str(order))[0]
                            ordertime = (
                                order.select_one(".item span").get_text()
                                + " "
                                + "00:00:00"
                            )
                            dic1["shop"] = order.select(".item span")[1].get_text()
                            dic1["rowspan"] = order.select_one(".total-price").get(
                                "rowspan"
                            )
                            dic1["price"] = order.select_one(
                                ".total-price span"
                            ).get_text()
                            dic1["含运费"] = order.select_one(".total-price em").get_text()
                            dic1["status"] = order.select_one(
                                ".state .opt-item"
                            ).get_text()
                            dic1["contact"] = (
                                order.select_one(".tax-tip")
                                .get_text(" ")
                                .replace("\n", "")
                                .replace("\r", "")
                            )
                            dic = []
                            o = order.select("table .order-info")
                            for item in o:
                                di = {}
                                di["title"] = item.select_one('[name="pname_"]')[
                                    "title"
                                ]
                                di["price"] = item.select_one(".price span").get_text()
                                di["amount"] = (
                                    item.select_one(".amount").get_text().strip()
                                )
                                dic.append(di)
                                dic1["goods"] = dic

                            res_one = ISHOPPING_ONE(
                                self.task, self._appcfg._apptype, self.userid, orderid
                            )
                            res_one.ordertime = ordertime
                            res_one.append_orders(dic1)
                            res_one.host = "www.suning.com"

                            yield res_one
                        except:
                            self._logger.error(
                                f"Parser order error\nerr:\n{traceback.format_exc()}"
                            )
                            continue
                    time.sleep(1)
                    page += 1
                else:
                    break
            except Exception:
                self._logger.error(
                    "{} got order fail: {}".format(self.userid, traceback.format_exc())
                )

    def _get_profile(self):
        try:
            url = "http://my.suning.com/msi2pc/memberInfo.do"
            headers = """
            Accept: application/json, text/javascript, */*; q=0.01
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: no-cache
            Connection: keep-alive
            Host: my.suning.com
            Pragma: no-cache
            Referer: http://my.suning.com/
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36
            X-Requested-With: XMLHttpRequest
            """
            r = self._ha.getstring(url, headers=headers, timeout=10)
            rd = json.loads(r)
            nickname = rd.get("nickName")
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            res.nickname = nickname
            yield res
        except Exception:
            self._logger.error(
                "{} got profile fail: {}".format(self.userid, traceback.format_exc())
            )
