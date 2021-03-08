import json
import time
import re
import traceback
from commonbaby.helpers.helper_str import substring
from bs4 import BeautifulSoup
from commonbaby.httpaccess.httpaccess import HttpAccess
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, EGender
from .spidertravelbase import SpiderTravelBase


class SpiderSuper8(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderSuper8, self).__init__(task, appcfg, clientid)
        self.userid = ''
        if self.task.cookie:
            self._ha._managedCookie.add_cookies('super8.com.cn', self.task.cookie)

    def _cookie_login(self):
        res = False
        try:

            url = "http://www.super8.com.cn/MemInfo/MemPersonalDetail"
            headers = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:no-cache
Connection:keep-alive
Host:www.super8.com.cn
Pragma:no-cache
Referer:http://www.super8.com.cn/MemInfo/MemLogin
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            soup = BeautifulSoup(html, 'lxml')
            userid = soup.select_one('.fwSpan .data-inner.eng').get_text()
            if userid:
                self.userid = userid + '-super8'
                res = True
            return res
        except Exception:
            return res

    def _get_profile(self):
        try:
            url = "http://www.super8.com.cn/MemInfo/MemPersonalDetail"
            headers = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:no-cache
Connection:keep-alive
Host:www.super8.com.cn
Pragma:no-cache
Referer:http://www.super8.com.cn/MemInfo/MemLogin
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers)
            html = re.sub(r'\s{2,}', '', html)
            soup = BeautifulSoup(html, 'lxml')
            detail = {}
            data_inner = soup.select('.data-inner')
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            try:
                res.account = data_inner[0].get_text()
            except:
                pass
            try:
                name = data_inner[1].get_text()
                if name:
                    detail['name'] = name
            except:
                pass
            try:
                gender = data_inner[2].get_text()
                if gender == '男':
                    res.gender = EGender.Male
                elif gender == '女':
                    res.gender = EGender.Female
                else:
                    res.gender = EGender.Unknown
            except:
                pass
            try:
                idtype = data_inner[3].get_text()
                if idtype:
                    detail['idtype'] = idtype
            except:
                pass
            try:
                idnumber = data_inner[4].get_text()
                if idnumber:
                    detail['idnumber'] = idnumber
            except:
                pass
            try:
                res.phone = data_inner[5].get_text()
            except:
                pass
            try:
                email = data_inner[6].get_text()
                if email:
                    res.email = email
            except:
                pass
            res.append_details(detail)
            yield res

        except Exception:
            self._logger.error('{} get profile fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_orders(self):
        url = 'http://www.super8.com.cn/MemInfo/GetMemCusOrder'
        pagesize = 5
        pageindex = 0
        resultCount = 0
        orderCntGot = False
        while True:
            try:
                pageindex += 1
                postdata = 'PageSize={}&PageIndex={}'.format(pagesize, pageindex)
                headers = """
Accept:*/*
Accept-Encoding:gzip, deflate
Accept-Language:zh-CN,zh;q=0.9
Cache-Control:no-cache
Connection:keep-alive
Content-Type:application/x-www-form-urlencoded; charset=UTF-8
Host:www.super8.com.cn
Origin:http://www.super8.com.cn
Pragma:no-cache
Referer:http://www.super8.com.cn/MemInfo/MemCusOrder
X-Requested-With:XMLHttpRequest"""
                html = self._ha.getstring(url, headers=headers, req_data=postdata)
                if not orderCntGot:
                    # "rscount": 4, "pages": 1, "pageindex": 1}
                    strResCnt = substring(html, '"rscount":', ',')
                    if strResCnt:
                        resultCount = int(strResCnt)
                    orderCntGot = True
                jshtml = json.loads(html)
                arrdata = jshtml['data']['arrdata']
                if arrdata:
                    for order in arrdata:
                        try:
                            ordertime = order['CreateTime'] + ':00'
                            orderid = order['OrderID']
                            res_one = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                            res_one.host = 'http://www.super8.com.cn'
                            res_one.ordertime = ordertime
                            res_one.append_orders(order)
                            yield res_one
                        except:
                            pass
                if resultCount <= pagesize * pageindex:
                    break
            except Exception:
                self._logger.error('{} get order fail: {}'.format(self.userid, traceback.format_exc()))

    def logout(self):
        res = False
        try:
            url = 'http://www.super8.com.cn/Home/LogOut'
            html = self._ha.getstring(url, headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: no-cache
            Host: www.super8.com.cn
            Pragma: no-cache
            Proxy-Connection: keep-alive
            Referer: http://www.super8.com.cn/MemInfo/MemCusOrder
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")
            if not self._cookie_login():
                res = True
        except Exception:
            self._logger.error('log out fail: {}'.format(traceback.format_exc()))

        return res

