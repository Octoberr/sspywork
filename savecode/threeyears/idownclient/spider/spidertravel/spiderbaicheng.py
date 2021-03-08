import re
import time
import traceback

from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import ResponseIO

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, RESOURCES, ESign, EResourceType, EGender


class SpiderBaicheng(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderBaicheng, self).__init__(task, appcfg, clientid)
        self.cookie = self.task.cookie
        if self.cookie:
            self.ha._managedCookie.add_cookies('baicheng.com', self.cookie)

    def _check_registration(self):
        """
        查询手机号是否注册了百程旅行
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            url = "https://passport.baicheng.com/userlogin"
            html = self._ha.getstring(url, headers="""
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")

            headers = """
accept: application/json, text/javascript, */*; q=0.01
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
content-length: 20
content-type: application/x-www-form-urlencoded; charset=UTF-8
origin: https://passport.baicheng.com
pragma: no-cache
referer: https://passport.baicheng.com/userreg
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
x-requested-with: XMLHttpRequest"""
            url = 'https://passport.baicheng.com/usercommon/userisbeing'
            postdata = f"username={self.task.phone}"
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            if '"value":true,' in html:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)

        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return

    def _cookie_login(self):
        try:
            url = "https://passport.baicheng.com/member/showprofile"
            headers = """
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
referer: https://passport.baicheng.com/member/showprofile
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers).replace('\r', '').replace('\n', '').replace('\t', '')
            soup = BeautifulSoup(html, 'lxml')
            userid = soup.select_one('.telnum').get_text()
            if userid:
                self.userid = userid + '-baicheng'
                return True
            else:
                return False
        except:
            return False

    def _get_profile(self):
        try:
            url = "https://passport.baicheng.com/member/showprofile"
            headers = """
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
referer: https://passport.baicheng.com/member/showprofile
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers).replace('\r', '').replace('\n', '').replace('\t', '')
            soup = BeautifulSoup(html, 'lxml')
            userid = soup.select_one('.telnum').get_text()
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)

            res.phone = soup.select_one('.fr.user_shez a').get_text()
            res.email = soup.select('.fr.user_shez a')[1].get_text()
            forms = soup.select('[class="forms"] dd')
            detail = {}
            if forms:
                nickname = forms[0].get_text()
                if nickname:
                    res.nickname = nickname

                realname = forms[1].get_text()
                if realname:
                    detail['relname'] = realname

                sex = forms[2].get_text()
                if sex == '男':
                    res.gender = EGender.Male
                elif sex == '女':
                    res.gender = EGender.Female
                else:
                    res.gender = EGender.Unknown

                birthday = forms[3].get_text()
                if birthday:
                    res.birthday = birthday

                bloodType = forms[4].get_text()
                if bloodType:
                    detail['bloodType'] = bloodType

                marriage = forms[4].get_text()
                if marriage:
                    detail['marriage'] = marriage

                if detail:
                    res.append_details(detail)

                photourl = soup.select_one('.fl.user_headimg img.png')['src']
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
            self._logger.error('{} got profile fail: {}'.format(self.userid, traceback))

    def _get_orders(self):
        try:
            page = 0
            while True:
                page += 1
                url = 'https://passport.baicheng.com/order/list?keyword=&orderState=0&page={}'.format(page)
                headers = """
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
referer: https://www.baicheng.com/
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
                html = self._ha.getstring(url, headers=headers).replace('\n', '').replace('\t', '').replace('\r', '')
                html = re.sub(r'\s{2,}', ' ', html)
                num = substring(html, '<span class="info">共', '页')
                if not num:
                    break
                soup = BeautifulSoup(html, 'lxml')
                orderList = soup.select('.user_orderlistcon')

                if orderList:
                    for o in orderList:
                        try:
                            orderid = substring(str(o), '订单号：', '<')
                            res_one = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)

                            ordertime = substring(html, '下单时间：', ' <')
                            res_one.ordertime = ordertime
                            order_sn = re.findall(r'order_sn="(.*?)"', str(o))
                            dic = {}
                            info = []
                            if order_sn:
                                for sn in order_sn:
                                    order = self._order_detail(sn)
                                    info.append(order)
                                dic['order'] = info
                                res_one.append_orders(dic)
                            yield res_one
                        except:
                            pass
                if int(num) <= page:
                    break
        except Exception:
            self._logger.error('{} get order fail: {}'.format(self.userid, traceback.format_exc()))

    def _order_detail(self, orderid):
        url = 'https://www.baicheng.com/visa/order/detail/{}'.format(orderid)
        headers = """
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
        html = self._ha.getstring(url, headers=headers).replace('\r', '').replace('\n', '').replace('\t', '')
        order = {}
        soup = BeautifulSoup(html, 'lxml')
        order['orderinfo'] = soup.select_one('.fl.visa_orderinfoL').get_text()
        order['visainfo'] = soup.select_one('.visa_allinfo').get_text()
        return order
