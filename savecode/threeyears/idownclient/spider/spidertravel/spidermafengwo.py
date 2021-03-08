import re
import time
import traceback
from datetime import datetime
import pytz

from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import HttpAccess, ResponseIO

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, RESOURCES, ESign, EResourceType, EGender


class SpiderMafengwo(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderMafengwo, self).__init__(task, appcfg, clientid)
        self.ha = HttpAccess()
        if self.task.cookie:
            self.ha._managedCookie.add_cookies('mafengwo.cn', self.task.cookie)

    def _check_registration(self):
        """
        查询手机号是否注册了马蜂窝
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            phone = self.task.phone
            url = 'https://passport.mafengwo.cn/regist.html'
            headers = """
Host: passport.mafengwo.cn
Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Referer: http://www.mafengwo.cn/?mfw_chid=3546
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
"""
            html = self.ha.getstring(url, headers=headers)
            token = substring(html, 'name="token" value="', '"')

            url = 'https://passport.mafengwo.cn/regist'
            headers = """
Host: passport.mafengwo.cn
Connection: keep-alive
Content-Length: 59
Cache-Control: max-age=0
Origin: https://passport.mafengwo.cn
Upgrade-Insecure-Requests: 1
Content-Type: application/x-www-form-urlencoded
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Referer: https://passport.mafengwo.cn/regist.html
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
"""
            data = f"token={token}&passport={phone}"
            html = self.ha.getstring(url, headers=headers, req_data=data)
            isreg = re.findall(r'<div class="alert alert-danger">', html)
            if isreg:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)

        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return

    def _cookie_login(self):
        try:
            url = 'https://passport.mafengwo.cn/setting/security/'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: passport.mafengwo.cn
Pragma: no-cache
Referer: https://passport.mafengwo.cn/setting/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self.ha.getstring(url, headers=headers)
            userid = substring(html, '"UID":', ',')
            if userid:
                self.userid = userid + '-mafengwo'
                return True
            else:
                return False
        except Exception:
            self._logger.error('Mafengwo cookie login error: {}'.format(traceback.format_exc()))
            return False

    def _get_profile(self):
        try:
            url = 'https://passport.mafengwo.cn/setting/'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: passport.mafengwo.cn
Pragma: no-cache
Referer: https://www.mafengwo.cn
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self.ha.getstring(url, headers=headers)
            soup = BeautifulSoup(html, 'lxml')
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            res.nickname = soup.select_one('[name="name"]')['value']
            # 1男0女2保密
            sex = soup.select_one('[checked="true"]')['value']
            if sex == '1':
                res.gender = EGender.Male
            elif sex == '0':
                res.gender = EGender.Female
            else:
                res.gender = EGender.Unknown
            res.city = soup.select_one('[name="city"]')['value']
            res.birthday = soup.select_one('[name="birthday"]')['value']
            detail = {}
            detail['introduce'] = soup.select_one('[name="intro"]').get_text()
            if detail['introduce']:
                res.append_details(detail)

            url = 'https://passport.mafengwo.cn/setting/security/'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: passport.mafengwo.cn
Pragma: no-cache
Referer: https://passport.mafengwo.cn/setting/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self.ha.getstring(url, headers=headers).replace('\n', '')
            html = re.sub(r'\s{2,}', '', html)
            soup = BeautifulSoup(html, 'lxml')
            userid = substring(html, '"UID":', ',')
            email = soup.select('.userpass dd')[1].get_text('-')
            res.email = email.split('-')[0]
            phone = soup.select('.userpass dd')[2].get_text('-')
            res.phone = phone.split('-')[0]

            url = 'https://pagelet.mafengwo.cn/user/apps/pagelet/pageViewHeadInfo?callback=jQuery181042165802873390845_{}&params=%7B%22type%22%3A1%7D&_={}'.format(
                int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000), int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000))
            headers = """
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: pagelet.mafengwo.cn
Pragma: no-cache
Referer: https://passport.mafengwo.cn/setting/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self.ha.getstring(url, headers=headers).replace('\\', '')
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
            self._logger.error('{} got profile fail: {}'.format(self.userid, traceback))

    def _get_orders(self):
        try:
            start = -10
            while True:
                start += 10
                url = f'https://www.mafengwo.cn/order_center/?status=0&start={start}'
                headers = """
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
referer: https://www.mafengwo.cn/order_center/?status=0&start=0
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
                html = self.ha.getstring(url, headers=headers).replace('\r', '').replace('\n', '').replace('\t', '')
                html = re.sub(r'\s{2,}', ' ', html)
                soup = BeautifulSoup(html, 'lxml')
                tables = soup.select('.order-item')
                for table in tables:
                    try:
                        order = {}
                        orderid = table.attrs.get('data-id')
                        order['orderid'] = orderid
                        ordertime = table.select_one('.time').get_text()
                        try:
                            order['supplier'] = table.select_one('.supplier').get_text()
                        except:
                            pass
                        try:
                            order['telphone'] = table.select_one('.telphone').get_text()
                        except:
                            pass
                        order['pro-detail'] = table.select_one('.pro-detail').get_text(' ')
                        order['td-date'] = table.select_one('.td-date').get_text()
                        order['price'] = table.select_one('.td-cost').get_text()
                        order['status'] = table.select_one('.td-status').get_text()

                        try:
                            orderurl = table.select_one('caption a')['href']
                            if orderurl:
                                detail = self._order_detail(orderurl)
                                order['detail'] = detail
                        except:
                            pass
                        res_one = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                        res_one.append_orders(order)
                        res_one.ordertime = ordertime.split('：', 1)[1]
                        res_one.host = "www.mafengwo.cn"
                        yield res_one
                    except Exception:
                        self._logger.error('Mafengwo one order get fail: {}'.format(traceback.format_exc()))

                if not tables:
                    break
        except Exception:
            self._logger.error('{} get order fail: {}'.format(self.userid, traceback.format_exc()))

    def _order_detail(self, orderurl):
        orderurl = 'https://www.mafengwo.cn' + orderurl
        headers = """
Host: www.mafengwo.cn
Connection: keep-alive
Pragma: no-cache
Cache-Control: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
"""
        html = self.ha.getstring(orderurl, headers=headers).replace('\r', '').replace('\n', '').replace('\t', '')
        # html = ha.get_response(orderurl, headers=headers)
        html = re.sub(r'\s{2,}', ' ', html)
        soup = BeautifulSoup(html, 'lxml')
        order = soup.select_one('.order-detail').get_text(' ')
        return order

    def logout(self):
        res = False
        try:
            url = 'https://passport.mafengwo.cn/logout.html'
            html = self._ha.getstring(url, headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: no-cache
            Host: www.mafengwo.cn
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")

            if not self._cookie_login():
                res = True
        except Exception:
            self._logger.error('log out fail: {}'.format(traceback.format_exc()))

        return res
