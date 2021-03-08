import datetime
import json
import re
import traceback
from urllib import parse
import pytz

from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import HttpAccess

from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, EGender


class SpiderCeair(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderCeair, self).__init__(task, appcfg, clientid)
        self.userid = ''
        if self.task.cookie:
            self._ha._managedCookie.add_cookies('ceair.com', self.task.cookie)

    def _cookie_login(self):
        res = False
        try:
            url = "https://easternmiles.ceair.com/mpf/auth/loginCheck_CN?locale=cn"
            headers = """
Accept: application/json, text/plain, */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 5
Content-Type: application/json;charset=UTF-8
Host: easternmiles.ceair.com
Origin: https://easternmiles.ceair.com
Pragma: no-cache
Referer: https://easternmiles.ceair.com/mpf/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
"""
            html = self._ha.getstring(url, headers=headers, req_data='')
            userid = substring(html, '"memberId":"', '"')
            if userid:
                self.userid = userid + '-ceair'
                res = True
            return res
        except Exception:
            return res

    def _get_profile(self):
        try:
            url = "https://easternmiles.ceair.com/mpf/user/userinfo?locale=cn"
            headers = """
Accept: application/json, text/plain, */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 5
Content-Type: application/json;charset=UTF-8
Host: easternmiles.ceair.com
Origin: https://easternmiles.ceair.com
Pragma: no-cache
Referer: https://easternmiles.ceair.com/mpf/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
"""
            html = self._ha.getstring(url, headers=headers, req_data='zh_CN')
            jshtml = json.loads(html)
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            res.phone = jshtml['phoneNumber']
            res.email = jshtml['email']
            res.account = jshtml['memberId']
            gender = jshtml['sex']
            if gender == 'M':
                res.gender = EGender.Male
            elif gender == 'F':
                res.gender = EGender.Female
            else:
                res.gender = EGender.Unknown
            res.birthday = jshtml['birthday']
            countrycode = jshtml['homeCountryCode']
            res.country = substring(html, '"{}","text":"'.format(countrycode), '"')
            provincecode = jshtml['homeProvinceCode']
            res.region = substring(html, 'id":"{}","text":"'.format(provincecode), '"')
            res.adress = jshtml['homeCityCode'] + jshtml['homeAdress']

            detail = {}
            detail['name'] = jshtml['firstCnName'] + jshtml['lastCnName']
            detail['idcard'] = jshtml['idCard']
            detail['homeZipCode'] = jshtml['homeZipCode']
            res.append_details(detail)
            yield res

        except Exception:
            self._logger.error('{} get profile fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_orders(self):
        dtEnd = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
        dtStart = dtEnd - datetime.timedelta(days=30)
        # 列表去重
        orderids = []
        # 默认获取3年订单
        End = dtEnd - datetime.timedelta(days=365 * 3)
        while dtStart >= End:

            try:
                page = 0
                totalPage = 1
                while page < totalPage:
                    page += 1
                    url = 'http://ecrm.ceair.com/traveller/optmember/uni-order-query!queryOrders.shtml'
                    postdata = f"""{{"orderType":"01","orderBeginDate":"{dtStart.strftime('%Y-%m-%d')}","orderEndDate":"{dtEnd.strftime('%Y-%m-%d')}","orderStatus":"","orderNo":"","tktNo":"","pnrNo":"","paxName":"","totalPageNum":"0","page":"{page}"}}"""
                    postdata = 'orderManagercond=' + parse.quote_plus(postdata)
                    headers = """
Accept: application/json, text/javascript, */*; q=0.01
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Content-Length: 310
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Host: ecrm.ceair.com
Origin: http://ecrm.ceair.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://ecrm.ceair.com/order/list.html?orderType=01
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest"""
                    html = self._ha.getstring(url, req_data=postdata, headers=headers)
                    jshtml = json.loads(html)

                    totalPage = jshtml['content']['totalPageNum']
                    orderList = jshtml['content']['uniOrderListDetailList']

                    for order in orderList:
                        try:
                            orderid = order['orderNo']
                            ordertime = order['crtDt']
                            if orderid not in orderids:
                                orderids.append(orderid)
                                order = self._get_orderDetail(orderid)
                                res_one = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                                res_one.ordertime = ordertime
                                res_one.host = 'www.ceair.com'
                                res_one.append_orders(order)
                                yield res_one
                        except:
                            pass
                dtEnd = dtStart - datetime.timedelta(days=1)
                dtStart = dtEnd - datetime.timedelta(days=30)

            except Exception:
                self._logger.error('{} got order fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_orderDetail(self, orderid):
        try:
            url = 'http://ecrm.ceair.com/traveller/optmember/order-query!queryOrderDetails.shtml'
            postdata = 'orderNo={}&orderType=AIR'.format(orderid)
            headers = f"""
Accept: application/json, text/javascript, */*; q=0.01
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 36
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Host: ecrm.ceair.com
Origin: http://ecrm.ceair.com
Pragma: no-cache
Referer: http://ecrm.ceair.com/order/detail.html?orderNo={orderid}&orderType=AIR
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            html = self._ha.getstring(url, req_data=postdata, headers=headers)
            jshtml = json.loads(html)
            order = {}
            order['orderid'] = orderid
            stuatsCode = jshtml['orderInfoDto']['orderStatus']
            order['stuats'] = self._get_orderStuats(stuatsCode)
            order['type'] = jshtml['orderInfoDto']['airOrderTypeCN']
            order['price'] = jshtml['orderInfoDto']['payAmtList'][0]['price']
            order['contactInfo'] = jshtml['orderInfoDto']['contactInfoDto']
            order['detail'] = jshtml['paxInfoDtoList'][0]
            return order

        except Exception:
            print('get order detail fail')

    def _get_orderStuats(self, stuatsCode):
        # http://ecrm.ceair.com/resource/js/orderDetail/index.js?v=zh_CN_17878
        stuats = """
10050: {tips: "等待支付",className: "waitPayB"},
10051: {tips: "支付成功",className: "waitPayG"},
10052: {tips: "交易处理中",className: "waitPayG"},
10053: {tips: "差错退款",className: "warning"},
10054: {tips: "交易成功",className: "success"},
10055: {tips: "交易异常",className: "error"},
10056: {tips: "交易取消",className: "cancel"},
10057: {tips: "等待确认",className: "waitPay"},
10058: {tips: "预定失败",className: "cancel"},
10059: {tips: "退票",className: "warning"},
10060: {tips: "候补购票中",className: "grabTickets"},
10061: {tips: "候补购票取消",className: "cancel"}"""
        stuats = stuats.replace('\n', '')
        stuats = re.sub('\s{2,}', '', stuats)
        stuatsList = re.findall(r'(\d+).*?"(.*?)",className', stuats)
        dic = {}
        for code, stuat in stuatsList:
            dic[code] = stuat

        if stuatsCode in dic.keys():
            return dic[stuatsCode]
        else:
            return None