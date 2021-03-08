"""Ofo"""

# -*- coding:utf-8 -*-

import json
import operator as op
import traceback

from datacontract.idowndataset import Task
from .spidertaxibase import SpiderTaxiBase
from ..appcfg import AppCfg
from ...clientdatafeedback import PROFILE, ITRIP_ONE


class SpiderOfo(SpiderTaxiBase):
    """Ofo"""

    def __init__(self, task: Task, appcfg: AppCfg, clientid):
        super(SpiderOfo, self).__init__(task, appcfg, clientid)
        self.task: Task = self.task
        self.phone = self.task.phone
        self._token = None

        self._profile: PROFILE = None
        self._orderlist: dict = {}

        # web required fields
        self.json1 = None

    def _cookie_login(self) -> bool:
        res: bool = False
        try:
            self._token = self.task.cookie
            self._profile = self._get_profile_()
            if self._profile is None:
                return res

            res = True
        except Exception:
            self._logger.error(
                "Login error: {}".format(traceback.format_exc()))
        return res

    def _sms_login(self) -> bool:
        res: bool = False
        try:

            self._logger.info("Get sms verify code: %s" % self.phone)
            playload = {"tel": self.phone}
            playload = self._add_public_playloads(playload, False)
            data = "".join("%s=%s&" % (i[0], i[1])
                           for i in playload.items()).rstrip('&')
            url = 'https://base.api.ofo.com/ofo/Api/v5/getVerifyCode'
            html = self._ha.getstring(url, req_data=data)
            if html is None or html == "":
                self._logger.error(
                    "Access profile failed: %s %s" % (self.phone, html))
            json1 = None
            try:
                json1 = json.loads(html)
            except Exception:
                self._logger.error(
                    "Access profile error: {}".format(traceback.format_exc()))
                return res
            # json1 = json.loads(html)
            smscode: str = None
            if json1["errorCode"] == 200:
                smscode = self._get_vercode()
                if not isinstance(smscode, str) or smscode == "":
                    self._logger.error("Sms verify code is empty")
                    return res
            elif json1["errorCode"] == 50004:
                self._logger.info(
                    "Too many requests for sms verify code: %s %s" % (self.phone, html))
                return res
            else:
                self._logger.info(
                    "Request sms verify code failed: %s %s" % (self.phone, html))
                return res

            playload = {
                "tel": self.phone,
                "code": smscode,
                "unionid": "",
                "idfa": "local",
                "imei": "863254010301561",
                "androidid": "309c236f08016990",
            }
            playload = self._add_public_playloads(playload)
            data = "".join("%s=%s&" % (i[0], i[1])
                           for i in playload.items()).rstrip('&')
            url = "https://user.api.ofo.com/ofo/Api/login"
            html = self._ha.getstring(url, req_data=data)
            if html is None or html == "":
                self._logger.error("Login failed: %s %s" % (self.phone, html))
            sjlogin = None
            try:
                sjlogin = json.loads(html)
            except Exception:
                self._logger.error(
                    "Login failed: {}".format(traceback.format_exc()))
                return res
            if sjlogin["errorCode"] == 20004:
                self._logger.info(
                    "Sms verifycode is incorrect: %s %s" % (self.phone, html))
                return res
            if sjlogin["errorCode"] == 200:
                self._token = sjlogin["values"]["token"]
                self.task.cookie = self._token
                res = True

        except Exception:
            self._logger.error(
                "Login error: {}".format(traceback.format_exc()))
        return res

    def _get_profile(self) -> iter:
        """获取个人信息和头像（如果有），不要把异常抛出来"""
        try:
            if self._profile is None:
                self._profile = self._get_profile_()

            if not self._profile is None:
                yield self._profile

        except Exception as ex:
            self._logger.error("Fetch userinfo failed: %s" % ex)

    def _get_profile_(self) -> PROFILE:
        res: PROFILE = None
        try:
            playload = {}
            playload = self._add_public_playloads(playload)
            data = "".join("%s=%s&" % (i[0], i[1])
                           for i in playload.items()).rstrip('&')

            # payload[ "token"] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJle
            # HAiOjE1MzcyMzM4OTAsImEiOjEzMzM5NDY5NDYsImIiOjI2MTg0OTQzNzYxNjQy
            # ODIxMjYsImMiOjI1NjEyMTYyNjcxMDMwNjM4MjJ9.sj7IBYhF56ckR5XwetSfxq
            # a3GWLICRalLe9HPPj16LI'
            url = "https://user.api.ofo.com/ofo/Api/v4/info/user"
            html = self._ha.getstring(url, req_data=data)
            sj = None
            try:
                sj = json.loads(html)
            except Exception:
                self._logger.error(
                    "Get profile error: {}".format(traceback.format_exc()))
                return res

            if sj["msg"] == "个人信息获取成功":
                pass
            else:
                self._logger.error(sj['msg'])
                return res

            res: PROFILE = PROFILE(
                self.task, self._appcfg._apptype, self._phone)
            detail: str = ""
            if (op.eq(sj["values"]["info"]["name"], '') == 0):
                res.nickname = sj["values"]["info"]["name"]
            if (op.eq(sj["values"]["info"]["cityIndex"], '') == 0):
                detail = detail + "cityindex:" + \
                         str(sj["values"]["info"]["cityIndex"]).replace(
                             ',', " ").replace(':', ' ') + ","
            if (op.eq(sj["values"]["info"]["cityName"], '') == 0):
                res.address = "cityname:" + \
                              str(sj["values"]["info"]["cityName"]).replace(
                                  ',', " ").replace(':', ' ') + ","
            if (op.eq(sj["values"]["info"]["creditTotal"], '') == 0):
                detail = detail + "credittotal:" + \
                         str(sj["values"]["info"]["creditTotal"]).replace(
                             ',', " ").replace(':', ' ') + ","
            if (op.eq(sj["values"]["info"]["creditDate"], '') == 0):
                detail = detail + "creditdate:" + \
                         str(sj["values"]["info"]["creditDate"]).replace(
                             ',', " ").replace(':', ' ') + ","
            if (op.eq(sj["values"]["info"]["isAutoPay"], '') == 0):
                detail = detail + "creditdate:" + \
                         str(sj["values"]["info"]["creditDate"]).replace(
                             ',', " ").replace(':', ' ') + ","
            if (op.eq(sj["values"]["info"]["isVIP"], '') == 0):
                detail = detail + "isvip:" + \
                         str(sj["values"]["info"]["isVIP"]).replace(
                             ',', " ").replace(':', ' ') + ","
            if (op.eq(sj["values"]["info"]["hasTimes"], 0) == 0):
                detail = detail + "hastimes:" + \
                         str(sj["values"]["info"]["hasTimes"]).replace(
                             ',', " ").replace(':', ' ') + ","
            if (op.eq(sj["values"]["info"]["freeTimes"], 0) == 0):
                detail = detail + "freetimes:" + \
                         str(sj["values"]["info"]["freeTimes"]).replace(
                             ',', " ").replace(':', ' ') + ","
            if (op.eq(sj["values"]["info"]["qqNickName"], '') == 0):
                detail = detail + "qqNickname:" + \
                         str(sj["values"]["info"]["qqNickName"]).replace(
                             ',', " ").replace(':', ' ') + ","
            if (op.eq(sj["values"]["info"]["wechatNickName"], '') == 0):
                detail = detail + "wechatnickname:" + \
                         str(sj["values"]["info"]["wechatNickName"]).replace(
                             ',', " ").replace(':', ' ') + ","
            if (op.eq(sj["values"]["info"]["isEnterpriseUser"], 0) == 0):
                detail = detail + "isenterpriseuser:" + \
                         str(sj["values"]["info"]["isEnterpriseUser"]).replace(
                             ',', " ").replace(':', ' ') + ","
            if (op.eq(sj["values"]["info"]["foreignOauthType"], '') == 0):
                detail = detail + "foreignoauthtype:" + \
                         str(sj["values"]["info"]["foreignOauthType"]).replace(
                             ',', " ").replace(':', ' ')

            res.detail = detail
            res.phone = self.phone

        except Exception as ex:
            res = None
            self._logger.error("Get profile failed: %s" % ex)

        return res

    def _get_orders(self) -> iter:
        """获取所有行程记录"""
        succ: bool = False
        msg: str = None
        try:

            for orderid in self._get_order_list():
                order = self._get_order_details(orderid)
                if order is None:
                    continue
                yield order

        except Exception as ex:
            self._logger.error("Fetch records failed: %s" % ex)
            succ = False
            msg = "获取行程记录失败"
        return (succ, msg)

    def _get_order_list(self) -> iter:
        try:
            playload = {"classify": 0, "page": 1}
            playload = self._add_public_playloads(playload)
            playload["token"] = self._token
            data = "".join("%s=%s&" % (i[0], i[1])
                           for i in playload.items()).rstrip('&')
            url = "https://user.api.ofo.com/ofo/Api/v3/detail"
            html = self._ha.getstring(url, req_data=data)
            if html is None or html == "":
                self._logger.error(
                    "Get ride record failed: %s" % self.uname_str)
                return

            orderlist = json.loads(html)
            if op.eq(orderlist["msg"], "操作成功") == 1:
                n = orderlist["values"]["info"]
                length = len(n)
                if length == 0:
                    self._logger.info(
                        "No record list in 3 months: %s" % self.uname_str)
                else:
                    for i in orderlist["values"]["info"]:
                        if not self._orderlist.__contains__(i["ordernum"]):
                            self._orderlist[i["ordernum"]] = None
                            yield i["ordernum"]
            else:
                self._logger.info("Get record list failed: %s" %
                                  self.uname_str)

        except Exception:
            self._logger.error(
                "Fetch record list error: {}".format(traceback.format_exc()))

    def _get_order_details(self, orderid) -> ITRIP_ONE:
        """"""
        res: ITRIP_ONE = None
        try:
            if not isinstance(orderid, str) or orderid == "":
                self._logger.error("Param orderid is empty.")
                return res

            res: ITRIP_ONE = self._get_order_detail(orderid)
            if res is None:
                return res
            coordinate = self._get_coordinate(orderid)
            if not isinstance(coordinate, list) or len(coordinate) < 1:
                return res

            # 坐标点太多，只保留5个坐标点：第一个，最后一个，中间三个
            if len(coordinate) > 5:
                # 先保留第一个
                restore_coor: list = []
                restore_coor.append(coordinate[0])
                # 再中间选3个
                # 先将列表平分为4段，则可以取到5个点，排除已经取了的首尾两点，
                # 再取前三段的每段末尾的点即可
                #      ↓     ↓     ↓
                # --------------------------
                seglen = round(len(coordinate) / 4)
                curr_cooridx = 0
                for i in range(1, 4):
                    curr_cooridx = seglen * i - 1
                    while len(coordinate) < curr_cooridx:
                        curr_cooridx = curr_cooridx - 1
                    restore_coor.append(coordinate[curr_cooridx])
                coordinate = restore_coor
                # 保留最后一个
                restore_coor.append(coordinate[len(coordinate) - 1])

            res.coordinate = coordinate
            self._orderlist[orderid] = res

        except Exception:
            res = None
            self._logger.error("Get record list failed:\nordernum:{}\nerror:{}".format(
                orderid, traceback.format_exc()))
        return res

    def _get_order_detail(self, orderid: str) -> ITRIP_ONE:
        """"""
        res: ITRIP_ONE = None
        try:
            playload = {"ordernum": orderid}
            playload = self._add_public_playloads(playload)
            data = "".join("%s=%s&" % (i[0], i[1])
                           for i in playload.items()).rstrip('&')

            url = "https://order.api.ofo.com/ofo/Api/v4/orderInfo"
            html = self._ha.getstring(url, req_data=data)
            orderinfo = json.loads(html)
            if op.eq(orderinfo["values"], "") == 1:
                self._logger.info("Get record detail failed: %s %s" %
                                  (self.phone, orderid))
                return res

            od = ITRIP_ONE(self.task, self._appcfg._apptype,
                           self.phone, orderid)

            if (op.eq(orderinfo['values']['info']['totalCost'], '') == 0):
                od.totalcost = str(orderinfo['values']['info']['totalCost'])
            if (op.eq(orderinfo['values']['info']['actualCost'], '') == 0):
                od.actualcost = str(orderinfo['values']['info']['actualCost'])
            if (op.eq(orderinfo['values']['info']['carno'], '') == 0):
                od.carno = str(orderinfo['values']['info']['carno'])
            if (op.eq(orderinfo['values']['info']['createAt'], '') == 0):
                od.createat = orderinfo['values']['info']['createAt']
            if (op.eq(orderinfo['values']['info']['isTimeOut'], '') == 0):
                od.istimeout = orderinfo['values']['info']['isTimeOut']
            if (op.eq(orderinfo['values']['info']['endAt'], '') == 0):
                od.endat = orderinfo['values']['info']['endAt']
            if (op.eq(orderinfo['values']['info']['costTime'], 0) == 0):
                od.costtime = str(orderinfo['values']['info']['costTime'])
            if (op.eq(orderinfo['values']['info']['distance'], 0) == 0):
                od.distance = str(
                    round(orderinfo['values']['info']['distance']))
            if (op.eq(orderinfo['values']['info']['redPacketAmount'], 0) == 0):
                od.redpacketamount = str(
                    orderinfo['values']['info']['redPacketAmount'])
            if (op.eq(orderinfo['values']['info']['userComment'], "") == 0):
                od.usercomment = str(
                    orderinfo['values']['info']['userComment'])
            res = od
        except Exception as ex:
            self._logger.error("Fetch record list failed: %s" % ex)
        return res

    def _get_coordinate(self, orderid: str) -> str:
        """"""
        res: str = None
        try:
            playload = {"ordernum": orderid}
            playload = self._add_public_playloads(playload)
            data = "".join("%s=%s&" % (i[0], i[1])
                           for i in playload.items()).rstrip('&')

            url = "https://path.api.ofo.com/ofo/Api/journeyPath"
            html = self._ha.getstring(url, req_data=data)
            journeypath = json.loads(html)
            if op.eq(journeypath["values"], "") == 1:
                self._logger.info("Get order coordinate failed: %s %s" %
                                  (self.phone, orderid))
                return res

            res = journeypath['values']['info']
        except Exception as ex:
            res = None
            self._logger.error("Fetch record list failed: %s" % ex)
        return res

    def _add_public_playloads(self, playload: dict, addtoken: bool = True) -> dict:
        """public bodys for playload"""
        if playload is None:
            playload = {}
        playload["source-system"] = "4.4.2"
        playload["cuid"] = "e86c260b8443080c00a0f7b7aac58fb7"
        playload["source-locale"] = "zh_CN"
        playload["source"] = "2"
        # payload["location"] = "%5B32.99908447265625%2C106.56749725341797%2C0%2C1535637548000%2C0%2C1%2C0%2C1%5D"
        playload["appVersion"] = "3.6.0"
        playload["sourceVersion"] = "17049"
        playload["source-model"] = "SM-G955F"
        playload["source-version"] = "17049"
        if addtoken and not self._token is None and not self._token == "" and not playload.__contains__("token"):
            playload["token"] = self._token
        return playload

    def _restore_resources(self):
        """Ofo专用令牌维护..."""
        if isinstance(self._token, str) and not self._token == "":
            self.task.cookie = self._token

        self.task.account = self.uname_str
        if not isinstance(self.task.account, str) or self.task.account == "":
            raise Exception("Account must be set after login succeed")
        if isinstance(self._host, str) and not self._host == "":
            self.task.host = self._host
        if isinstance(self._url, str) and not self._url == "":
            self.task.url = self._url
