import json
import time
import traceback
from datetime import datetime
import pytz

from commonbaby.httpaccess.httpaccess import HttpAccess, ResponseIO

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, RESOURCES, ESign, EResourceType, EGender


class SpiderTuniu(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderTuniu, self).__init__(task, appcfg, clientid)
        self.cookie = self.task.cookie
        self.ha = HttpAccess()
        if self.cookie:
            self.ha._managedCookie.add_cookies('tuniu.com', self.cookie)

    def _check_registration(self):
        """
        查询手机号是否注册了途牛
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            url = "https://passport.tuniu.com/register"
            html = self._ha.getstring(url, headers="""
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")

            headers = """
Accept: */*
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Origin: https://passport.tuniu.com
Referer: https://passport.tuniu.com/register
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            url = 'https://passport.tuniu.com/register/isPhoneAvailable'
            postdata = f"intlCode=0086&tel={self.task.phone}"
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            if '"errno":-1,' in html:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)

        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return

    def _cookie_login(self):
        url = 'https://i.tuniu.com/usercenter/usercommonajax/japi'
        headers = """
Accept: application/json, text/javascript, */*; q=0.01
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 76
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Host: i.tuniu.com
Origin: https://i.tuniu.com
Pragma: no-cache
Referer: https://i.tuniu.com/userinfoconfirm
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest"""
        postdata = 'serviceName=MOB.MEMBERS.InnerController.getUserInfo&serviceParamsJson=%7B%7D'
        try:
            html = self.ha.getstring(url, headers=headers, req_data=postdata)
            jshtml = json.loads(html)
            userid = jshtml['data']['data']['userId']
            if userid:
                self.userid = str(userid) + '-tuniu'
                return True
            else:
                return False
        except:
            return False

    def _get_profile(self):
        try:
            url = 'https://i.tuniu.com/usercenter/usercommonajax/japi'
            headers = """
Accept: application/json, text/javascript, */*; q=0.01
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 76
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Host: i.tuniu.com
Origin: https://i.tuniu.com
Pragma: no-cache
Referer: https://i.tuniu.com/userinfoconfirm
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            postdata = 'serviceName=MOB.MEMBERS.InnerController.getUserInfo&serviceParamsJson=%7B%7D'
            html = self.ha.getstring(url, headers=headers, req_data=postdata)
            jshtml = json.loads(html)
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            userid = jshtml['data']['data']['userId']
            res.nickname = jshtml['data']['data']['nickName']
            res.phone = jshtml['data']['data']['tel']
            res.birthday = jshtml['data']['data']['birthday']
            res.email = jshtml['data']['data']['email']
            res.address = jshtml['data']['data']['additionalAddress']
            sex = jshtml['data']['data']['sex']
            if sex == 1:
                res.gender = EGender.Male
            elif sex == 0:
                res.gender = EGender.Female
            else:
                res.gender = EGender.Unknown
            detail = jshtml['data']['data']
            res.append_details(detail)
            photourl = jshtml['data']['data']['largeAvatarUrl']
            if photourl:
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
            self._logger.error('{} .got profile fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_orders(self):
        try:
            page = 0
            while True:
                page += 1
                url = 'https://i.tuniu.com/usercenter/usercommonajax/japi/getOrderList?serviceName=MOB.MEMBER.InnerOrderController.getOrderList&serviceParamsJson=%7B%22type%22%3A0%2C%22page%22%3A{}%2C%22status%22%3A0%2C%22size%22%3A5%7D&_={}'.format(
                    page, int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000))
                headers = """
Accept: application/json, text/javascript, */*; q=0.01
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: i.tuniu.com
Pragma: no-cache
Referer: https://i.tuniu.com/list/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest"""
                html = self.ha.getstring(url, headers=headers)
                jshtml = json.loads(html)
                orderList = jshtml['data']['data']['orderList']
                if orderList:
                    for order in orderList:
                        try:
                            orderid = order['orderId']
                            ordertime = order['orderTime']
                            res_one = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                            res_one.append_orders(order)
                            res_one.ordertime = ordertime
                            res_one.host = 'www.tuniu.com'
                            yield res_one
                        except:
                            pass
                totalpage = jshtml['data']['data']['totalPage']
                if totalpage <= page:
                    break
        except Exception:
            self._logger.error('{} got order fail: {}'.format(self.userid, traceback.format_exc()))
