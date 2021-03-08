import datetime
import re
import time
import traceback
import pytz

from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE


class SpiderHainanAir(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderHainanAir, self).__init__(task, appcfg, clientid)
        self.userid = ''
        if self.task.cookie:
            self._ha._managedCookie.add_cookies('.hnair.com', self.task.cookie)

    def _check_registration(self):
        """
        查询手机号是否注册了海南航空
        :param account:
        :return:
        """
        t = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            url = "https://new.hnair.com/hainanair/ibe/profile/createProfile.do"
            html = self._ha.getstring(url, headers="""
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: new.hnair.com
Pragma: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")

            headers = """
Accept: */*
Referer: https://new.hnair.com/hainanair/ibe/profile/createProfile.do
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            url = f'https://new.hnair.com/hainanair/ibe/profile/checkRegisterProfileDataJSON.do?ConversationID=&check%2FmobilePhone={self.task.phone}'
            html = self._ha.getstring(url, headers=headers)
            if '"Validator" : "1024",' in html:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t, EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered', t, EBackResult.UnRegisterd)

        except Exception:
            self._logger.error('Check registration fail: {}'.format(traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed, 'Check registration fail', t, EBackResult.CheckRegisterdFail)
        return

    def _cookie_login(self):
        try:
            url = 'https://new.hnair.com/hainanair/ibe/common/loginStatus.do'
            headers = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Connection:keep-alive
Upgrade-Insecure-Requests:1"""

            html = self._ha.getstring(url, headers=headers)
            self.userid = re.findall(r"userID:'(.*?)'", html)[0] + '-hnair'
            return True
        except:
            return False

    def _get_profile(self):
        try:
            url = 'http://new.hnair.com/hainanair/ibe/common/profileLanding.do'
            headers = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:no-cache
Connection:keep-alive
Pragma:no-cache
Referer:http://www.hnair.com/
Upgrade-Insecure-Requests:1"""
            html = self._ha.getstring(url, headers=headers)

            conversationid = substring(html, "ConversationID = '", "'")
            url = 'https://new.hnair.com/hainanair/ibe/profile/editProfile.do?type=queryB2CUser&ConversationID={}'.format(
                conversationid)
            html = self._ha.getstring(url, headers=headers).replace('\n', '')
            res = self._try_get_profile(html)
            if res:
                yield res
        except Exception:
            self._logger.error('{} got profile fail: {}'.format(self.userid, traceback.format_exc()))

    def _try_get_profile(self, html) -> PROFILE:
        res: PROFILE = None
        try:
            if html is None or html == "":
                return res
            soup = BeautifulSoup(html, 'lxml')
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            try:
                res.nickname = soup.select_one('.book-manage-name').get_text()
            except Exception:
                self._logger.debug("get profile nickname failed.")

            try:
                res.account = soup.select_one('.info-dl').get_text()
            except:
                pass
            try:
                res.phone = soup.select('.info-dl')[2].get_text()
            except:
                pass
            try:
                res.email = soup.select('.info-dl')[3].get_text()
            except:
                pass
            try:
                res.bithday = soup.select_one('#userBirthDate')['value']
            except:
                pass
            try:
                res.city = soup.select_one('#mailState')['value'] + '省/市/自治区' + soup.select_one('mailCity')[
                    'value'] + '市'
            except:
                pass
            detail = {}
            try:
                detail['实名认证'] = soup.select_one('.drawer').get_text()
            except:
                pass
            try:
                detail['常旅客卡号'] = soup.select('.info-dl')[1].get_text()
            except:
                pass
            try:
                detail['证件类型'] = soup.select_one('.select-con.select-disable span').get_text()
            except:
                pass
            try:
                detail['证件号码'] = soup.select_one('#idnumber')['value']
            except:
                pass
            res.detail = detail
        except Exception:
            res = None
            self._logger.error("Get profile error: {}".format(traceback.format_exc()))
        return res

    def _get_orders(self):
        try:
            # 拿...
            url = 'http://new.hnair.com/hainanair/ibe/common/profileLanding.do'
            headers = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:no-cache
Connection:keep-alive
Pragma:no-cache
Referer:http://www.hnair.com/
Upgrade-Insecure-Requests:1"""
            html = self._ha.getstring(url, headers=headers)
            conversationid = substring(html, "ConversationID = '", "'")
            if not conversationid:
                self._logger.error("Get conversationid failed: {}".format(self.uname_str))
                return

            # 拿...
            url = 'https://new.hnair.com/hainanair/ibe/profile/myProfile.do'
            now = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))
            nowdate = now.strftime('%Y-%m-%d')
            lastdate = str(int(now.year) - 3) + '-' + now.strftime('%m-%d')
            postdata = 'bpage=1&epage=1&tpage=1&bookingSearch%2FpageNumber=&bookingSearch%2Funticketed=false&searchWay=0&bookingSearch%2FDateInformation%2FbookingDateFrom={dtfrom}&bookingSearch%2FDateInformation%2FbookingDateTo={dtNow}&bookingSearch%2FDateInformation%2FflightDateFrom=&bookingSearch%2FDateInformation%2FFlightDateTo=&bookingSearch%2FOriginDestinationInformation%2FOrigin%2Flocation=&bookingSearch%2FOriginDestinationInformation%2FOrigin%2Flocation_input=&bookingSearch%2FOriginDestinationInformation%2FDestination%2Flocation=&bookingSearch%2FOriginDestinationInformation%2FDestination%2Flocation_input=&bookingSearch%2FproductType=&bookingSearch%2FproductState=&bookingSearch%2FhotelName=&bookingSearch%2Freference='.format(
                dtfrom=lastdate, dtNow=nowdate)
            headers = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:no-cache
Connection:keep-alive
Content-Length:713
Content-Type:application/x-www-form-urlencoded
Origin:http://new.hnair.com
Pragma:no-cache
Referer:https://new.hnair.com/hainanair/ibe/profile/myProfile.do
Upgrade-Insecure-Requests:1"""
            html = self._ha.getstring(url, headers=headers, req_data=postdata)

            for o in self._try_get_orders(html, conversationid):
                if o:
                    yield o

        except Exception as ex:
            self._logger.error('{} Got ConversationId failed: {}'.format(self.userid, traceback.format_exc()))

    def _try_get_orders(self, html, conversationid) -> iter:
        try:
            soup = BeautifulSoup(html, 'lxml')
            orderList = soup.select('#orderList tr')
            for m in orderList[1:]:
                orderid = None
                try:
                    orderid = m.select_one('a').get_text()

                    if orderid is not None or orderid != '':
                        dic = {}
                        res_one = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                        dic['order'] = self._get_order_detail(conversationid, orderid)
                        res_one.append_orders(dic)
                        try:
                            ordertime = m.select('td')[4].get_text()
                            res_one.ordertime = ordertime
                        except:
                            pass
                        res_one.host = 'www.hnair.com'
                        yield res_one
                except:
                    self._logger.error("Get one order failed: orderid: {}".format(orderid))
        except Exception:
            self._logger.error('{} got order fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_order_detail(self, conversationid, orderid):
        url = 'https://new.hnair.com/hainanair/ibe/bookingManagement/home.do?ConversationID={conversationid}'.format(
            conversationid=conversationid)
        ost = 'bookingSearch%2Freference={orderid}&bookingSearch%2Femail=&isMyporfile=OK'.format(orderid=orderid)
        headers = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:no-cache
Connection:keep-alive
Content-Type:application/x-www-form-urlencoded
Origin:http://new.hnair.com
Pragma:no-cache
Referer:http://new.hnair.com/hainanair/ibe/profile/myProfile.do"""
        html, redir = self._ha.getstring_with_reurl(url, req_data=ost, headers=headers)
        url = 'https://new.hnair.com/hainanair/ibe/bookingManagement/retrieveBookingRedirect.do'
        postdata = "ConversationID=&ENCRYPTED_QUERY=&QUERY=&redirected=true"
        headers = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:no-cache
Connection:keep-alive
Content-Type:application/x-www-form-urlencoded
Origin:http://new.hnair.com
Host:new.hnair.com
Pragma:no-cache
Referer:http://new.hnair.com/hainanair/ibe/bookingManagement/retrieveBookingRedirect.do"""
        html, redir = self._ha.getstring_with_reurl(url, req_data=postdata, headers=headers)
        soup = BeautifulSoup(html, 'lxml')
        order = soup.select_one('.main').get_text()
        order = re.subn(r'\s{2,}', '', order)
        return order

    def logout(self):
        res = False
        try:
            url = 'https://new.hnair.com/hainanair/ibe/profile/signout.do'
            html = self._ha.getstring(url, headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: no-cache
            Connection: keep-alive
            Host: new.hnair.com
            Pragma: no-cache
            Referer: https://new.hnair.com/hainanair/ibe/profile/myProfile.do?telassa-id=IbeNotLogin%7E33B28C9590258B8EACC99217F5290C9B.HUIBEServer2%7Ehu-dev-PRD-0a08e42e-431738-44505&_catRootMessageId=hu-dev-PRD-0a08e42e-431738-44505&_catParentMessageId=hu-dev-PRD-0a08e42e-431738-44505&_catChildMessageId=null-0a08e42e-431738-32883
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")
            if not self._cookie_login():
                res = True
        except Exception:
            self._logger.error('log out fail: {}'.format(traceback.format_exc()))

        return res
