import re
import time
import traceback
import uuid
from datetime import datetime
import pytz

import execjs
from bs4 import BeautifulSoup
from commonbaby.helpers import helper_crypto
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import ResponseIO

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, RESOURCES, ESign, EResourceType


class SpiderBaidu(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderBaidu, self).__init__(task, appcfg, clientid)
        self.cookie = self.task.cookie
        if self.cookie:
            self._ha._managedCookie.add_cookies('baidu.com', self.cookie)

    def _check_registration(self):
        """
        查询手机号是否注册了百度旅游
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        ti = int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)
        try:
            html = self._ha.getstring('https://passport.baidu.com/v2/?reg&tpl=tb&u=//tieba.baidu.com', headers="""
        Host: passport.baidu.com
        Connection: keep-alive
        Pragma: no-cache
        Cache-Control: no-cache
        Upgrade-Insecure-Requests: 1
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
        Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
        Accept-Encoding: gzip, deflate, br
        Accept-Language: zh-CN,zh;q=0.9
        """, encoding='utf-8')
            html.encoding = 'utf-8'
            # print(html.text)
            gid = 'DD9D1FD-752B-4AC4-9BE0-CB699316505D'
            gid = str(uuid.uuid1()).upper()[1:]
            gid = gid[:13] + '4' + gid[14:]
            js = """
                    getUniqueId = function(e) {
                        return e + Math.floor(2147483648 * Math.random()).toString(36)
                    }"""
            ctx = execjs.compile(js)
            callback = ctx.call('getUniqueId', 'bd__cbs__')
            html = self._ha.getstring(
                f'https://passport.baidu.com/v2/api/?getapi&tpl=tb&apiver=v3&tt={ti}&class=regPhone&gid={gid}&app=&traceid=&callback={callback}',
                headers="""
        Host: passport.baidu.com
        Connection: keep-alive
        Pragma: no-cache
        Cache-Control: no-cache
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
        Accept: */*
        Referer: https://passport.baidu.com/v2/?reg&tpl=tb&u=//tieba.baidu.com
        Accept-Encoding: gzip, deflate, br
        Accept-Language: zh-CN,zh;q=0.9
        """)
            token = substring(html, '"token" : "', '"')
            #
            # js = """
            # function hex_md5(s) {
            #     return binl2hex(core_md5(str2binl(s), s.length * chrsz))
            # }
            # function get_moonshad(phone) {
            #     n = hex_md5(phone + "Moonshadow");
            #     n = n.replace(/o/, "ow").replace(/d/, "do").replace(/a/, "ad"),
            #     n = n.replace(/h/, "ha").replace(/s/, "sh").replace(/n/, "ns").replace(/m/, "mo"),
            #     return n
            # }
            # """
            # moon = execjs.compile(js)
            # moonshad = moon.call('get_moonshad', self.task.phone)
            moonshad = helper_crypto.get_md5_from_str(self.task.phone + "Moonshadow")
            moonshad = re.sub(r'o', 'o~', moonshad, 1)
            moonshad = re.sub(r'd', 'd!', moonshad, 1)
            moonshad = re.sub(r'a', 'a@', moonshad, 1)
            moonshad = re.sub(r'h', 'h#', moonshad, 1)
            moonshad = re.sub(r's', 's$', moonshad, 1)
            moonshad = re.sub(r'n', 'n%', moonshad, 1)
            moonshad = re.sub(r'm', 'm^', moonshad, 1)
            moonshad = moonshad.replace('~', 'w').replace('!', 'o').replace('@', 'd').replace('#', 'a').replace('$',
                                                                                                                'h').replace(
                '%', 's').replace('^', 'n')
            callback = ctx.call('getUniqueId', 'bd__cbs__')
            url = f"https://passport.baidu.com/v2/?regphonecheck&token={token}&tpl=tb&apiver=v3&tt={ti}&phone={self.task.phone}&moonshad={moonshad}&countrycode=&gid={gid}&exchange=0&isexchangeable=1&action=reg&traceid=&callback={callback}"
            headers = """
        Host: passport.baidu.com
        Connection: keep-alive
        Pragma: no-cache
        Cache-Control: no-cache
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
        Accept: */*
        Referer: https://passport.baidu.com/v2/?reg&tpl=tb&u=//tieba.baidu.com
        Accept-Encoding: gzip, deflate, br
        Accept-Language: zh-CN,zh;q=0.9
        """
            response = self._ha.get_response(url, headers=headers)
            response.encoding = 'utf-8'
            # print(response.text)
            if '"400001"' in response.text:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Uber check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return

    def _cookie_login(self):
        url = 'https://lvyou.baidu.com/user/edit/info'
        headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: lvyou.baidu.com
Pragma: no-cache
Referer: https://lvyou.baidu.com/user/order/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""

        try:
            data: bytes = self._ha.get_response_data(url, headers=headers)
            html = data.decode('utf-8')
            userid = substring(html, 'J_nav-channel-user-center user-center">', '<')
            if userid:
                self.userid = userid + '-baidutravel'
                return True
            else:
                return False
        except:
            return False

    def _get_profile(self):
        try:
            url = 'https://lvyou.baidu.com/user/edit/info'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: lvyou.baidu.com
Pragma: no-cache
Referer: https://lvyou.baidu.com/user/order/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            data: bytes = self._ha.get_response_data(url, headers=headers)
            html = data.decode('utf-8')
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            res.nickname = substring(html, 'J_nav-channel-user-center user-center">', '<')
            photourl = substring(html, 'class="" src="', '"')
            if photourl:
                photourl = 'https:' + photourl
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
        try:
            url = 'https://lvyou.baidu.com/user/order/'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: text
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: lvyou.baidu.com
Pragma: no-cache
Referer: https://lvyou.baidu.com/huangshan/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            data: bytes = self._ha.get_response_data(url, headers=headers)
            html = data.decode('utf-8')
            soup = BeautifulSoup(html, 'lxml')
            try:
                tbody = soup.select('tbody tr')
            except:
                self._logger.info('{} have no order'.format(self.userid))
                return None
            for body in tbody:
                detailUrl = body.select_one('.ticket-name')['data-href']
                if detailUrl:
                    orderid = substring(detailUrl, 'order_id=', '&')
                    detailUrl = 'https://lvyou.baidu.com' + detailUrl.replace('amp;', '')
                    ordertime, order = self.order_Detail(detailUrl)
                    res = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                    res.append_orders(order)
                    res.ordertime = ordertime
                    res.host = 'lvyou.baidu.com'
                    yield res
        except Exception:
            self._logger.error('{} got order fail: {}'.format(self.userid, traceback.format_exc()))

    def order_Detail(self, detailUrl):
        headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: text
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: lvyou.baidu.com
Pragma: no-cache
Referer: https://lvyou.baidu.com/user/order/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
        data: bytes = self._ha.get_response_data(detailUrl, headers=headers)
        html = data.decode('utf-8')
        order = {}
        ordertime = substring(html, '>下单日期：', '<') + ' ' + '00:00:00'
        soup = BeautifulSoup(html, 'lxml')
        orderid = substring(html, "order_id: '", "'")
        ord = soup.select_one('.order-body').get_text(' ').replace('\t', '').replace('\r', '').replace('\n', '')

        order['detail'] = ord
        return ordertime, order

    def _logout(self):
        res = False
        try:
            url = 'https://passport.baidu.com/?logout&bdstoken=&u=http://lvyou.baidu.com/'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: passport.baidu.com
Pragma: no-cache
Referer: https://lvyou.baidu.com/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            if not self._cookie_login():
                res = True
        except Exception:
            self._logger.error('log out fail: {}'.format(traceback.format_exc()))

        return res

    def _sms_login(self):
        try:
            url = 'https://lvyou.baidu.com/'
            html = self._ha.getstring(url, headers="""
            Host: lvyou.baidu.com
            Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """)

            gid = str(uuid.uuid1()).upper()[1:]
            gid = gid[:13] + '4' + gid[14:]
            ti = int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)
            html = self._ha.getstring(f'https://passport.baidu.com/v2/api/?getapi&tpl=lv&apiver=v3&tt={ti}&class=login&gid={gid}&logintype=dialogLogin&traceid=&callback={self.__get_callback()}',
                headers="""
            Host: passport.baidu.com
            Connection: keep-alive
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
            Accept: */*
            Referer: https://lvyou.baidu.com/
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9""")
            token = substring(html, '"token" : "', '"')

            time_now = datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
            html = self._ha.getstring(
                f'https://passport.baidu.com/v2/api/?loginhistory&token={token}&tpl=lv&apiver=v3&'
                f'tt={int(time_now * 1000)}&gid={gid}&traceid=&callback={self.__get_callback()}',
                headers="""
            Host: passport.baidu.com
            Connection: keep-alive
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
            Accept: */*
            Referer: https://lvyou.baidu.com/
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9""")

            html = self._ha.getstring(
                f'https://passport.baidu.com/viewlog?ak=1e3f2dd1c81f2075171a547893391274&callback=jsonpCallbacka2627&v=7513',
                headers="""
            Host: passport.baidu.com
            Connection: keep-alive
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
            Accept: */*
            Referer: https://lvyou.baidu.com/
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """)

            # 发送短信
            phone = self.task.phone
            url = f'https://passport.baidu.com/v2/api/senddpass?gid={gid}&username={phone}&countrycode=&bdstoken={token}&tpl=lv&flag_code=0&client=&dv=tk0.75529222491874481554792308342%40eeIdAkqY6trnCl7hF6TNEr84I~vlIlT~pI84B5TfDHza8kEaNq__kI0RvnkvUAkvb01zd8StwAozanFGY8k0~Ak2ank0Y6trnCl7hF6TNEr84I~vlIlT~pI8FJL7XBICi~vvBBvFUTkg2hFIh0HzxAk2xyIrJ5YzAS2l8Fvw0Svx8k3dnk2U8kQd8FEU8~3x0~q-0~4xhIdBoCU2o0sAxTYJcOKJHw1GLO3JHwSpbUKAo6fD56MBLwODq__HId0mzzAktU0S0Y0~0U81zd8k4zAk3z0mzd8k4zAktU8kqYnkGz&apiver=v3&tt={int(time_now * 1000)} & traceid = & callback = {self.__get_callback()}'
            html = self._ha.getstring(url, headers="""
            Host: passport.baidu.com
            Connection: keep-alive
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
            Accept: */*
            Referer: https://lvyou.baidu.com/
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """)
            if '"errno":0,"msg":"' not in html:
                print('发送失败')
            else:
                print('发送成功')
            code = self._get_vercode()
            # post
            url = 'https://passport.baidu.com/v2/api/?login'
            callback = self.__get_callback().split('__')[-1]
            callback = 'parent.bd__pcbs__' + callback
            traceid = self.__get_traceid()
            tt = int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000)

            data = f'staticpage=https%3A%2F%2Flvyou.baidu.com%2Fstatic%2Fcommon%2Fhtml%2Fv3Jump.html&charset=UTF-8&token={token}&tpl=lv&subpro=&apiver=v3&tt={tt}&u=https%3A%2F%2Flvyou.baidu.com%2F&idc=&isdpass=1&gid={gid}&switchuname=&smscodestring=&smsvcodesign=&smsvcodestr=&is_voice_sms=0&voice_sms_flag=0&username={phone}&password={code}&fp_uid=&fp_info=&client=&isupsms=&channelid=&countrycode=&dv=tk0.75529222491874481554792308342%40eeI0j%7EAkqY6trnCl7hF6TNEr84I%7EvlIlT%7EpI84B5TfDHza8kEaNkt-AkqY6trnCl7hF6TNEr84I%7EvlIlT%7EpI8EBLlO21zd0F2d0czx0S3Y0mdE4EwoE3r8IlT4ElhN0S6NIa8X2lDO2MOMRE8KD5EY0%7Etl8kJi0SvwAkqY6trnCl7hF6TNEr84I%7EvlIlT%7EpI8LDI7PDcOkpbCOAk0x0FQUNkvxnHzzArChF3JH4ElNIlhFErix86TN2bl%7E6M6xBLDw4bT3DHz%7E0S4x8oz_kI0iknkvUAkvb01zd8StwAozanFGY8k0%7EAk2ank0Y6trnCl7hF6TNEr84I%7EvlIlT%7EpI8FJL7XBICinktzAkvl81zw0FGbAoza0F0Y0%7E4wAk0U8kQUArChF3JH4ElNIlhFErix86TN2bl%7ECMTxpIza8SEY8k4-Ak4d0FtzArChF3JH4ElNIlhFErix86TN2bl%7EEa61pLOUNq__%7EvvBBvFUTkg2hFIh0HzxAk2xyIrJ5YzAS2l8Fvw0Svx8k3dnk2U8kQd8FEU8%7E3x0%7Eq-0%7E4xhIdBoCU2o0sAxTYJcOKJHw1GLO3JHwSpbUKAo6fD56MBLwODq__HId0mzzAktU0S0Y0%7E0U81zd8k4zAk3z0mzd8k4zAktU8kqYnkGz&traceid={traceid}&callback={callback}'
            html = self._ha.getstring(url, req_data=data, headers="""
            Host: passport.baidu.com
            Connection: keep-alive
            Content-Length: 1230
            Cache-Control: max-age=0
            Origin: https://lvyou.baidu.com
            Upgrade-Insecure-Requests: 1
            Content-Type: application/x-www-form-urlencoded
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Referer: https://lvyou.baidu.com/
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """)
            cookie = self._ha._managedCookie.get_cookie_for_domain('http://baidu.com')
            p_cookie = self._ha._managedCookie.get_cookie_for_domain('http://passport.baidu.com')
            try:
                ptoken = ''
                for i in p_cookie.replace(' ', '').split(';'):
                    key = i.split('=')[0]
                    value = i.split('=')[1]
                    if key == 'PTOKEN':
                        ptoken = 'PTOKEN=' + value
                        break
                self._ha._managedCookie.add_one_cookie('.baidu.com', ptoken)
            except Exception:
                self._logger.error('Got ptoken fail: {}'.format(traceback.format_exc()))
            res = self._cookie_login()
            return res

        except Exception:
            self._logger.error('Baidu travel sms login fail: {}'.format(traceback.format_exc()))


def __get_callback(self):
    try:
        js = """
                        getUniqueId = function(e) {
                            return e + Math.floor(2147483648 * Math.random()).toString(36)
                        }"""
        ctx = execjs.compile(js)
        callback = ctx.call('getUniqueId', 'bd__cbs__')
        return callback
    except Exception:
        self._logger.error('Baidu travel __get_callback fail: {}'.format(traceback.format_exc()))


def __get_traceid(self):
    try:
        js = """
                createHeadID=function() {
                          var a = parseInt(90 * Math.random() + 10, 10).toString()
                              , t = (new Date).getTime() + a
                              , n = Number(t).toString(16)
                              , i = n.length
                              , s = n.slice(i - 6, i).toUpperCase();
                          return s
                              }"""
        ctx = execjs.compile(js)
        traceid = ctx.call('createHeadID') + '01'
        return traceid
    except Exception:
        self._logger.error('Baidu travel __get_traceid fail: {}'.format(traceback.format_exc()))
