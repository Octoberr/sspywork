import json
import re
import time
import traceback
from datetime import datetime
import pytz

from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import ResponseIO

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, RESOURCES, ESign, EResourceType, EGender


class SpiderQyer(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderQyer, self).__init__(task, appcfg, clientid)
        self.cookie = self.task.cookie
        if self.cookie:
            self._ha._managedCookie.add_cookies('qyer.com', self.cookie)

    def _check_registration(self):
        """
        查询手机号是否注册了穷游
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            url = "https://passport.qyer.com/register/mobile?ref=https%3A%2F%2Fwww.qyer.com%2F"
            html = self._ha.getstring(url, headers="""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: passport.qyer.com
Pragma: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")

            headers = """
Content-Type: application/x-www-form-urlencoded;charset=UTF-8
Origin: https://passport.qyer.com
Referer: https://passport.qyer.com/register/mobile?ref=https%3A%2F%2Fwww.qyer.com%2F
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            url = 'https://passport.qyer.com/qcross/passport/register/mobile/checkmobile?ajaxID=591d04b6733e86c93db2a1b0'
            postdata = f"mobile=86-{self.task.phone}"
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            if '"error_code":510002,' in html:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)

        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return

    def _cookie_login(self):
        url = 'http://www.qyer.com/qcross/home/ajax?action=loginstatus'
        postdata = 'timer={}'.format(int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000))
        headers = """
Accept: application/json, text/javascript, */*; q=0.01
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Content-Length: 19
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Host: www.qyer.com
Origin: http://www.qyer.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://www.qyer.com/u/10552906/profile
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest"""

        try:
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            userid = substring(html, '"uid":"', '"')
            if userid:
                self.userid = userid + '-qyer'
                return True
            else:
                return False
        except Exception:
            return False

    def _get_profile(self):
        try:
            userid = self.userid.split('-')[0]
            url = 'http://www.qyer.com/u/{}/profile'.format(userid)
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Host: www.qyer.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://www.qyer.com/u/10552906/editprofile
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            soup = BeautifulSoup(html, 'lxml')
            info = soup.select('.clearfix.fontArial li')
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            res.nickname = info[0].select_one('.right').get_text().replace('\r', '').replace('\n', '')
            sex = info[1].select_one('.right').get_text()
            if sex == '男':
                res.gender = EGender.Male
            elif sex == '女':
                res.gender = EGender.Female
            else:
                res.gender = EGender.Unknown
            res.birthday = info[2].select_one('.right').get_text()
            res.address = info[3].select_one('.right').get_text()
            photourl = substring(html, '<img.png src="', '"')
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

    def _get_orders(self):
        page = 0
        while True:
            page += 1
            url = 'http://zuser.qyer.com/orderList?page={}'.format(page)
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: zuser.qyer.com
Pragma: no-cache
Referer: http://zuser.qyer.com/orderList
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""

            try:
                html = self._ha.getstring(url, headers=headers)
                ordersInfo = re.findall(r'订单编号：<a href="(.*?)" target="_blank">(.*?)</a>', html)
                for orderUrl, orderid in ordersInfo:
                    try:
                        ordertime, order = self._order_detail(orderUrl)
                        res_one = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                        res_one.append_orders(order)
                        res_one.ordertime = ordertime
                        res_one.host = 'www.qyer.com'
                        yield res_one
                    except:
                        pass

                isorder = re.findall(r"class='ui_page_item ui_page_next' title=", html)
                if not isorder:
                    break
            except:
                self._logger.error('{} has no orders: {}'.format(self.userid, traceback.format_exc()))
                break

    def _order_detail(self, orderUrl):
        orderUrl = 'http:' + orderUrl
        headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: zuser.qyer.com
Pragma: no-cache
Referer: http://zuser.qyer.com/orderList
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
        html = self._ha.getstring(orderUrl, headers=headers)
        ordertime = substring(html, '下单时间：', '<')
        data = substring(html, 'window.__INITIAL_STATE__=', ';(function(){var s')
        jsdata = json.loads(data)

        order = {}
        order['title'] = substring(data, '"p_title":"', '"').replace('\\u002F', '/')
        order['type'] = substring(data, '"p_type_name":"', '",')
        order['stutas'] = substring(data, '"st_name":"', '"')
        order['price'] = substring(data, '"total_price":"', '"')
        order['num'] = substring(data, '"num":"', '",')
        order['merchant_name'] = substring(data, '"merchant_name":"', '",')
        order['call'] = substring(data, '"call":"', '",')
        order['contactInfo'] = jsdata['renderData']['data']['contactInfo']
        order['detail'] = jsdata['renderData']['data']['lastminute']
        return ordertime, order
