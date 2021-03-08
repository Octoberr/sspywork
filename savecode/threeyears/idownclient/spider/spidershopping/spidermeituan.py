"""
美团cookie登陆，短信登陆
订单，个人信息下载
20181023
"""
import datetime
import json
import re
import time
import traceback
import pytz

from .spidershoppingbase import SpiderShoppingBase
from ...clientdatafeedback import ISHOPPING_ONE
from ...clientdatafeedback import PROFILE
from ...clientdatafeedback import RESOURCES, EResourceType, ESign


class SpiderMeiTuan(SpiderShoppingBase):

    def __init__(self, task, appcfg, clientid):
        # SpiderMeiTuan.__init__(self,tst:Task, 'meituan', '1000')
        super(SpiderMeiTuan, self).__init__(task, appcfg, clientid)
        self.time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        self.userid = ''
        self.account = self.task.account
        self.csrf = ''
        self.cookie = self.task.cookie

    def _cookie_login(self):
        # if self._task.host is None or self._task.cookie is None or self._task.cookie=="":
        #     return False
        res = False
        try:
            headers0 = {
                # 'Cookie': cookie,
                'Cookie': self.cookie,
                'Referer': 'https://www.meituan.com/account/userinfo/',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36',
            }
            headerx = ''
            for key, value in headers0.items():
                headerx = headerx + key + ':' + value + '\n'
            html = self._ha.getstring(
                'https://www.meituan.com/account/settings', headers=headerx)
            pattoken = re.compile(r'csrf":{"token":"(.*?)"')
            token = pattoken.findall(html)[0]
            pattime = re.compile(r'"timestamp":(.*?)}')
            timestamp = pattime.findall(html)[0]

            url = 'http://www.meituan.com/ptapi/settings/userinfo'
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
                'Cookie': self.cookie,
                'Host': 'www.meituan.com',
                'Pragma': 'no-cache',
                'Proxy-Connection': 'keep-alive',
                'Referer': 'http://www.meituan.com/account/settings',
                'timestamp': timestamp,
                'token': token,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36'
            }
            headerx = ''
            for key, value in headers.items():
                headerx = headerx + key + ':' + value + '\n'
            r = self._ha.getstring(url, headers=headerx)
            # print(r.text)
            r = json.loads(r)
            userid = r['id']
            if userid:
                self.userid = userid + '-meituan'
                res = True
        except:
            return False
        return res

    def pwd_login(self):
        pass

    def _sms_login(self):
        # if self._task.phone is None:
        #     return False
        # 获取csrf

        headers1 = """
Host: passport.meituan.com
Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Referer: http://cd.meituan.com/
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
"""
        r1 = self._ha.getstring(
            'https://passport.meituan.com/account/unitivelogin?service=www&continue=https%3A%2F%2Fwww.meituan.com%2Faccount%2Fsettoken%3Fcontinue%3Dhttps%253A%252F%252Fwww.meituan.com%252F',
            headers=headers1)
        # uuid = substring(r1, '"form-uuid" style="display:none">', '</i>')
        pattern = re.compile(r'name="csrf" value="(.*?)" />', re.S)
        try:
            self.csrf = pattern.findall(r1)[0]
        except:
            return False

        count = 0
        while True:
            # 模拟发送短信验证码
            url = "https://passport.meituan.com/account/mobilelogincode?uuid=a5ec7ebc725b40babe1e.1537513653.1.0.0"
            headers = """
POST /account/mobilelogincode?uuid=252ce49f82bd402aabfb.1545615028.1.0.0 HTTP/1.1
Host: passport.meituan.com
Connection: keep-alive
Content-Length: 18
Origin: https://passport.meituan.com
X-CSRF-Token: {}
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Accept: */*
X-Requested-With: XMLHttpRequest
X-Client: javascript
Referer: https://passport.meituan.com/account/unitivelogin?service=www&continue=https%3A%2F%2Fwww.meituan.com%2Faccount%2Fsettoken%3Fcontinue%3Dhttp%253A%252F%252Fcd.meituan.com%252F
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
""".format(self.csrf)
            # data = "mobile=18123008018"
            data = "mobile={phone}".format(phone=self.task.phone)
            # resp = self._ha.get_response(url, req_data=data, headers=headers)
            # return resp.status
            # resp.close()
            r = self._ha.getstring(url, req_data=data, headers=headers)
            patissuc = re.compile(r'"success":0')
            issuc = patissuc.search(r)

            if not issuc:
                count += 1
                if count == 3:
                    self._logger.info('Need Vetify Code! Login fail')
                    return False
                continue
            else:
                break

        verification_code = self._get_vercode()

        url1 = 'https://passport.meituan.com/account/unitivemobilelogin?risk_partner=0&uuid=6d2f2cc432e94488b5bd.1537516461.1.0.0&service=www&continue=http%3A%2F%2Fwww.meituan.com%2Faccount%2Fsettoken%3Fcontinue%3Dhttps%253A%252F%252Fwww.meituan.com%252Ferror%252F403'
        # 输入短信验证码模拟登陆
        headers1 = """
Host: passport.meituan.com
Connection: keep-alive
Content-Length: 4966
Origin: https://passport.meituan.com
X-CSRF-Token: {}
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Accept: */*
X-Requested-With: XMLHttpRequest
X-Client: javascript
Referer: https://passport.meituan.com/account/unitivelogin?service=www&continue=https%3A%2F%2Fwww.meituan.com%2Faccount%2Fsettoken%3Fcontinue%3Dhttp%253A%252F%252Fcd.meituan.com%252F
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
""".format(self.csrf)
        # code = input('输入短信验证码：')
        data1 = "mobile={account}&login-captcha=n5yg&origin=account-login&fingerprint=0-13-1-5ui|ont|5k|7b|2t|1o|6w|4n|7k|81|33|gx|47nb|12w|gw|12o|8w|8w|73x5|3b|8i|47|1j|18x&csrf={csrf}&code={code}".format(
            account=self.task.phone, csrf=self.csrf, code=verification_code)
        r = self._ha.getstring(url1, req_data=data1, headers=headers1)

        newcookie = self._ha._managedCookie.get_cookie_for_domain('https://meituan.com')
        self.task.cookie = newcookie
        self.cookie = newcookie
        res = self._cookie_login()
        return res

    def _get_profile(self):
        try:
            headers0 = {
                # 'Cookie': cookie,
                'Cookie': self.cookie,
                'Referer': 'https://www.meituan.com/account/userinfo/',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36',
            }
            headerx = ''
            for key, value in headers0.items():
                headerx = headerx + key + ':' + value + '\n'
            html = self._ha.getstring(
                'https://www.meituan.com/account/settings', headers=headerx)
            pattoken = re.compile(r'csrf":{"token":"(.*?)"')
            token = pattoken.findall(html)[0]
            pattime = re.compile(r'"timestamp":(.*?)}')
            timestamp = pattime.findall(html)[0]

            url = 'http://www.meituan.com/ptapi/settings/userinfo'
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
                'Cookie': self.cookie,
                'Host': 'www.meituan.com',
                'Pragma': 'no-cache',
                'Proxy-Connection': 'keep-alive',
                'Referer': 'http://www.meituan.com/account/settings',
                'timestamp': timestamp,
                'token': token,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36'
            }
            headerx = ''
            for key, value in headers.items():
                headerx = headerx + key + ':' + value + '\n'
            r = self._ha.getstring(url, headers=headerx)
            r = json.loads(r)
            detail = {}
            photourl = r['avatarUrl']
            detail["passwordLevel"] = r["passwordLevel"]
            detail["safetyLevel"] = r["safetyLevel"]
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            res.account = r['username']
            res.phone = r['mobile']
            res.birthday = r['birthday']
            res.append_details(detail)
            if photourl:
                profilepic: RESOURCES = RESOURCES(self._clientid, self.task, photourl, EResourceType.Picture,
                                                  self._appcfg._apptype)

                resp_stream = self._ha.get_response_stream(photourl)
                # response = requests.request("GET", photourl, headers=headers, stream=True)
                profilepic.io_stream = resp_stream
                profilepic.filename = photourl.rsplit('/', 1)[-1]
                profilepic.sign = ESign.PicUrl
                res.append_resource(profilepic)
                yield profilepic
            yield res
        except Exception:
            self._logger.error('{} sms login fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_orders(self):
        try:
            count = -20
            while True:
                count += 20
                url = 'http://www.meituan.com/ptapi/orders/orderlist?statusFilter=0&offset={}'.format(count)
                headers = {
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Cache-Control': 'no-cache',
                    'Content-Type': 'application/json',
                    'Cookie': self.cookie,
                    'Host': 'www.meituan.com',
                    'Pragma': 'no-cache',
                    'Proxy-Connection': 'keep-alive',
                    'Referer': 'http://www.meituan.com/orders/',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36'
                }
                headerx = ''
                for key, value in headers.items():
                    headerx = headerx + key + ':' + value + '\n'
                r = self._ha.getstring(url, headers=headerx)
                dic_r = json.loads(r)
                list = dic_r['data']['orders']
                if list:
                    for item in list:
                        dic = {}
                        orderid = item['orderid']
                        dic['orderid'] = item['orderid']
                        dic['title'] = item['title']
                        ordertime = item['ordertime']
                        timeArray = time.localtime(int(ordertime))
                        # dic['ordertime'] = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
                        dic['catename'] = item['catename']
                        dic['orderinfo'] = item['orderinfo']
                        dic['showstatus'] = item['showstatus']
                        res_one = ISHOPPING_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                        res_one.append_orders(dic)
                        res_one.orderid = orderid
                        res_one.ordertime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
                        res_one.host = 'http://www.meituan.com'
                        yield res_one
                else:
                    break
        except Exception:
            self._logger.error('{} got order fail:{}'.format(self.userid, traceback.format_exc()))

    def _logout(self):
        res = False
        try:
            url = 'https://passport.meituan.com/account/signout'
            html = self._ha.getstring(url, headers="""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: passport.meituan.com
Pragma: no-cache
Referer: https://www.meituan.com/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")
            res = self._cookie_login()
            if not res:
                res = True
        except Exception:
            self._logger.error('login out fail:{}'.format(traceback.format_exc()))
        return res
