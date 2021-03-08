"""
验证手机号是否注册了蘑菇街
验证cookie登陆
获取订单，个人信息
20181102
"""
import json
import re
import time
import traceback

from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import ResponseIO

from .spidershoppingbase import SpiderShoppingBase
from ...clientdatafeedback import ISHOPPING_ONE
from ...clientdatafeedback import PROFILE
from ...clientdatafeedback import RESOURCES, EResourceType, ESign, EGender


class SpiderMogujie(SpiderShoppingBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderMogujie, self).__init__(task, appcfg, clientid)
        self.userid = ''
        if self.task.cookie:
            self._ha._managedCookie.add_cookies('mogujie.com', self.task.cookie)

    def _cookie_login(self):
        url = 'https://www.mogujie.com/api/profile/userinfo/getBaseUserInfo'
        headers = """
Accept: application/json, text/javascript, */*; q=0.01
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 0
Host: www.mogujie.com
Origin: https://www.mogujie.com
Pragma: no-cache
Referer: https://www.mogujie.com/settings/personal?ptp=1.SmeXub._head.0.1DKf28xy
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
X-Requested-With: XMLHttpRequest
"""
        try:
            r = self._ha.getstring(url, headers=headers, req_data='')
            jsr = json.loads(r)
            result = jsr['result']
            uid = result.get('uid')
            if uid:
                self.userid = uid + '-mogujie'
                return True
            else:
                return False
        except:
            return False

    def _get_orders(self):
        try:
            pattoken = re.compile(r'nekot=(.*?);')
            token = pattoken.findall(self.task.cookie)
            if token:
                token = token[0]
                page = 0
                while True:
                    page += 1
                    url = 'https://order.mogujie.com/jsonp/buyerOrderListJsonp/1?token={token}&data=%7B%22buyerUserId%22%3A%22%22%2C%22marketType%22%3A%22market_mogujie%22%2C%22page%22%3A%22{page}%22%2C%22pageSize%22%3A10%2C%22status%22%3A%22all%22%2C%22orderPlatformCode%22%3A%22PC%22%2C%22orderVisibleStatusCode%22%3A%22%22%7D&callback=httpCb154104424217163&_=1541044242171'.format(
                        token=token, page=page)
                    headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: order.mogujie.com
Pragma: no-cache
Referer: https://order.mogujie.com/order/list4buyer?ptp=1.n5T00._head.0.3soDVWhc
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
"""
                    r = self._ha.getstring(url, headers=headers)
                    data = r.encode('utf-8').decode('unicode-escape')
                    patpayorder = re.compile(r'"payOrder":(.*?)"extraInfo"')
                    payorder = patpayorder.findall(data)
                    if payorder:
                        for order in payorder:
                            # print(order)
                            dic1 = {}
                            patorderidesc = re.compile(r'"payOrderIdEsc":"(.*?)",')
                            dic1['orderidesc'] = patorderidesc.findall(order)[0]
                            patfinalprice = re.compile(r'"buyerFinalPrice":(.*?),')
                            finalprice = float(patfinalprice.findall(order)[0]) / 100
                            dic1['finalprice'] = '%.2f' % finalprice
                            patorderid = re.compile(r'"payOrderId":(.*?),')
                            orderid = patorderid.findall(order)[0]
                            patorderstatus = re.compile(r'"orderStatus":"(.*?)",')
                            dic1['orderstatus'] = patorderstatus.findall(order)[0]
                            patcommoditys = re.compile(r'{"itemOrderOperations":(.*?)"delayRisk":')
                            commoditys = patcommoditys.findall(order)
                            dic = []

                            for commodity in commoditys:
                                # print(commodity)
                                dic0 = {}
                                pattitle = re.compile(r'"title":"(.*?)"')
                                dic0['title'] = pattitle.findall(commodity)[0]
                                patprice = re.compile(r'"nowPrice":(.*?),')
                                price = float(patprice.findall(commodity)[0]) / 100
                                dic0['nowPrice'] = '%.2f' % price
                                patnumber = re.compile(r'"number":(.*?),')
                                dic0['number'] = patnumber.findall(commodity)[0]
                                patskuAttributes = re.compile(r'"skuAttributes":\[(.*?)]')
                                dic0['skuAttributes'] = patskuAttributes.findall(commodity)[0]
                                dic.append(dic0)
                            dic1['commodity'] = dic
                            res_one = ISHOPPING_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                            timeStamp = substring(order, '"created":', ',')
                            if timeStamp:
                                timeArray = time.localtime(int(timeStamp))
                                res_one.ordertime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
                            res_one.append_orders(dic1)
                            res_one.host = 'www.mogujei.com'
                            yield res_one
                    else:
                        break
            else:
                yield None
        except Exception:
            self._logger.error('{} got order fail:{}'.format(self.userid, traceback.format_exc()))

    def _get_profile(self):
        try:
            url = 'https://www.mogujie.com/api/profile/userinfo/getBaseUserInfo'
            headers = """
Accept: application/json, text/javascript, */*; q=0.01
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 0
Host: www.mogujie.com
Origin: https://www.mogujie.com
Pragma: no-cache
Referer: https://www.mogujie.com/settings/personal?ptp=1.SmeXub._head.0.1DKf28xy
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
X-Requested-With: XMLHttpRequest
"""
            r = self._ha.getstring(url, headers=headers, req_data='')
            jsr = json.loads(r)
            result = jsr['result']
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            res.birthday = result.get('birthday')
            res.account = result.get('uname')
            gender = result.get('gender')
            if gender == 1:
                res.gender = EGender.Male
            elif gender == 0:
                res.gender = EGender.Female
            else:
                res.gender = EGender.Unknown
            res.phone = result.get('mobile')
            res.region = result.get('province')
            res.address = result.get('city')
            res.email = result.get('email')
            detail = {}
            detail['uid'] = result.get('uid')
            detail['profession'] = result.get('profession')
            detail['introduce'] = result.get('introduce')
            res.detail = json.dumps(detail)
            photourl = result.get('avatar')
            if photourl:
                profilepic: RESOURCES = RESOURCES(self._clientid, self.task, photourl, EResourceType.Picture,
                                                  self._appcfg._apptype)

                resp_stream: ResponseIO = self._ha.get_response_stream(photourl)
                profilepic.io_stream = resp_stream
                profilepic.filename = photourl.rsplit('/', 1)[-1]
                profilepic.sign = ESign.PicUrl
                res.append_resource(profilepic)
                yield profilepic
            yield res
        except Exception:
            self._logger.error('{} got profile fail: {}'.format(self.userid, traceback.format_exc()))

    def _logout(self):
        res = False
        try:
            url = 'https://www.mogujie.com/logout?ptp=1.OzLLi._head.74.R2dK2wJ2'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: www.mogujie.com
Pragma: no-cache
Referer: https://order.mogujie.com/order/list4buyer?ptp=1.n5T00._head.0.YzvJFr4t
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            if '您没有登录' in html:
                res = True
        except Exception:
            self._logger.error('login out fail:{}'.format(traceback.format_exc()))
        return res
