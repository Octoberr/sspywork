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


class SpiderCaisa(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderCaisa, self).__init__(task, appcfg, clientid)
        self.cookie = self.task.cookie
        if self.cookie:
            self._ha._managedCookie.add_cookies('caissa.com.cn', self.cookie)

    def _check_registration(self):
        """
        查询手机号是否注册了凯撒旅行
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            url = "http://www.caissayl.com/trail/save?source_third=other&first_page=http://my.caissa.com.cn/SignIn/Index?redirect_uri=http://my.caissa.com.cn/Index/Index&referrer=false&expired=30&callback=jsonpCallback"
            html = self._ha.getstring(url, headers="""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Host: www.caissayl.com
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://my.caissa.com.cn/SignIn/Index?redirect_uri=http://my.caissa.com.cn/Index/Index
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")

            headers = """
Accept: */*
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Content-Length: 174
Content-Type: application/x-www-form-urlencoded
Host: my.caissa.com.cn
Origin: http://my.caissa.com.cn
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://my.caissa.com.cn/Registered/index
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            url = 'http://my.caissa.com.cn/Registered/CheckPhone'
            postdata = f"hdurl=http%3A%2F%2Fmy.caissa.com.cn%2FSignIn%2FIndex%3Fredirect_uri%3Dhttp%3A%2F%2Fmy.caissa.com.cn%2FIndex%2FIndex&hdsessionId=&phone={self.task.phone}&imgcode=&captcha=&password="
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            if '手机号已存在' in html:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)

        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return

    def _cookie_login(self):
        try:
            url = 'http://my.caissa.com.cn/ws/UserHandler.ashx?action=getinfo&charset=&callback=jQuery171017810140921028506_{}&_={}'.format(
                int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000),
                int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000))
            headers = """
Accept: text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: my.caissa.com.cn
Pragma: no-cache
X-Requested-With: XMLHttpRequest
Referer: http://my.caissa.com.cn/GetInfo/GetWebInfo?&nav=
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            userid = substring(html, '"uid":"', '"')
            if userid:
                self.userid = userid + '-caissa'
                return True
            else:
                return False

        except:
            pass
        return False


def _get_profile(self):
    try:
        url = 'http://my.caissa.com.cn/ws/UserHandler.ashx?action=getinfo&charset=&callback=jQuery171017810140921028506_{}&_={}'.format(
            int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000),
            int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000))
        headers = """
Accept: text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: my.caissa.com.cn
Pragma: no-cache
X-Requested-With: XMLHttpRequest
Referer: http://my.caissa.com.cn/GetInfo/GetWebInfo?&nav=
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
        html = self._ha.getstring(url, headers=headers)
        res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
        userid = substring(html, '"uid":"', '"')
        res.account = substring(html, '"username":"', '"')
        res.phone = substring(html, '"mobile":"', '"')
        photourl = substring(html, '"faceurl":"', '"')
        if photourl:
            profilepic: RESOURCES = RESOURCES(self._clientid, self.task, photourl, EResourceType.Picture,
                                              self._appcfg._apptype)

            resp_stream: ResponseIO = self._ha.get_response_stream(photourl)
            profilepic.io_stream = resp_stream
            profilepic.filename = photourl.rsplit('/', 1)[-1]
            profilepic.sign = ESign.PicUrl
            res.append_resource(profilepic)
            yield profilepic

        url = 'http://my.caissa.com.cn/Index?&nav='
        headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Host: my.caissa.com.cn
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://my.caissa.com.cn/GetInfo/GetWebInfo?&nav=
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
        html = self._ha.getstring(url, headers=headers)
        email = substring(html, '绑定邮箱：', ' </span>')
        if email:
            res.email = email

        url = 'http://my.caissa.com.cn/GetInfo/GetWebInfo?&nav='
        headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: my.caissa.com.cn
Pragma: no-cache
Referer: http://my.caissa.com.cn/GetInfo/GetWebInfo
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
        html = self._ha.getstring(url, headers=headers)
        soup = BeautifulSoup(html, 'lxml')
        info = soup.select('.P_I_wz01.P_I_wz02')
        detail = {}
        detail['realname'] = info[1].get_text()
        sex = info[2].get_text()
        if sex == '男':
            res.gender = EGender.Male
        elif sex == '女':
            res.gender = EGender.Female
        res.birthday = info[3].get_text()
        res.address = info[4].get_text()
        detail['zipcode'] = info[5].get_text()
        detail['intrest'] = info[6].get_text()
        detail['sign'] = info[7].get_text()
        res.append_details(detail)
        yield res
    except Exception:
        self._logger.error('{} got profile fail: {}'.format(self.userid, traceback.format_exc()))


def _get_orders(self):
    try:
        page = 0
        while True:
            page += 1
            url = 'http://search.caissa.com.cn/order/orderList?page={}'.format(page)
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Host: search.caissa.com.cn
Pragma: no-cache
Proxy-Connection: keep-alive
Referer: http://my.caissa.com.cn/order/Controls/DuJia.aspx?src=http://search.caissa.com.cn/order/orderlist
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers).replace('\r', '').replace('\n', '').replace('\t', '')
            soup = BeautifulSoup(html, 'lxml')
            ispage = soup.select_one('.pages').get_text()
            if not ispage:
                break
            orderids = soup.select('.productList')
            if orderids:
                for o in orderids:
                    try:
                        orderid = o.select_one('.info_list')['id']
                        ordertime = substring(str(o), '订单日期: <em>', '</em>')
                        order = self._order_detail(orderid)
                        res_one = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                        res_one.ordertime = ordertime
                        res_one.append_orders(order)
                        res_one.host = 'www.caissa.com.cn'
                        yield res_one
                    except:
                        pass
            isnextpage = re.findall(r'class="next" href="javascript:void', html)
            if isnextpage:
                break
    except Exception:
        self._logger.error('{} got order fail: {}'.format(self.userid, traceback.format_exc()))


def _order_detail(self, orderid):
    url = 'http://search.caissa.com.cn/order/orderDetail?orderNumber={}'.format(orderid)
    headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: search.caissa.com.cn
Pragma: no-cache
Referer: http://search.caissa.com.cn/order/orderlist
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
    html = self._ha.getstring(url, headers=headers).replace('\r', '').replace('\n', '').replace('\t', '')
    soup = BeautifulSoup(html, 'lxml')
    order = {}
    detail = soup.select_one('.rightcon').get_text()
    detail = re.sub(r'\s{2,}', ' ', detail)
    order['detail'] = detail
    return order
