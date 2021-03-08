
import re
import json
import time
import traceback
from datetime import datetime
import pytz

import requests
from bs4 import BeautifulSoup
from commonbaby.helpers.helper_str import substring
from commonbaby.httpaccess.httpaccess import HttpAccess, ResponseIO

from .spidertravelbase import SpiderTravelBase
from ...clientdatafeedback import PROFILE, ITRAVELORDER_ONE, RESOURCES, ESign, EResourceType, EGender



class SpiderTujia(SpiderTravelBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderTujia, self).__init__(task, appcfg, clientid)
        if self.task.cookie:
            self._ha._managedCookie.add_cookies('tujia.com', self.task.cookie)

    def _cookie_login(self):
        try:
            url = 'https://vip.tujia.com/WebParts/Portal/UserInfo?isShowCreateNewStore=False&callback=jQuery17109690176311480858_{}&_={}'.format(
                int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000), int(datetime.now(pytz.timezone('Asia/Shanghai')).timestamp() * 1000))
            headers = """
Accept: text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: vip.tujia.com
Pragma: no-cache
Referer: https://vip.tujia.com/UserInfo/Info/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
X-Requested-With: XMLHttpRequest"""
            html = self._ha.getstring(url, headers=headers).replace('\r', '').replace('\n', '').replace('\t', '')
            userid = substring(html, "userId: '", "'")
            if userid:
                self.userid = userid + '-tujia'
                return True
            else:
                return False
        except:
            return False

    def _get_profile(self):
        try:
            url = 'https://vip.tujia.com/UserInfo/Info/'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: vip.tujia.com
Pragma: no-cache
Referer: https://vip.tujia.com/UserInfo/UpdateInfo/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            html = self._ha.getstring(url, headers=headers).replace('\r', '').replace('\n', '').replace('\t', '')
            html = re.sub(r'\s{2,}', ' ', html)
            soup = BeautifulSoup(html, 'lxml')
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)

            detail = {}
            try:
                res.account = soup.select('.emphasize-text')[0].get_text()
            except:
                pass
            try:
                res.email = soup.select('.emphasize-text')[1].get_text()
            except:
                pass
            try:
                res.phone = soup.select('.emphasize-text')[2].get_text()
                res.nickname = res.phone
            except:
                pass
            try:
                detail['registerTime'] = soup.select('.emphasize-text')[3].get_text()
            except:
                pass
            try:
                detail['realname'] = soup.select_one('#Name')['value']
            except:
                pass
            try:
                text = substring(html, 'for="SexMale"', 'checked')
                sexnum = re.findall(r'name="Sex"', text)
                if len(sexnum) == 1:
                    res.gender = EGender.Male
                elif len(sexnum) == 2:
                    res.gender = EGender.Female
            except:
                pass
            try:
                birth = soup.select('.control-group.deta-group select')
                res.birthday = birth[0].select_one('[selected="selected"]').get_text() + '-' + birth[1].select_one(
                    '[selected="selected"]').get_text() + '-' + birth[2].select_one('[selected="selected"]').get_text()
            except:
                pass
            try:
                detail['constellation'] = soup.select_one('.age-info').get_text()
            except:
                pass
            try:
                detail['Education'] = soup.select_one('#Education [selected="selected"]').get_text()
            except:
                pass
            try:
                detail['Job'] = soup.select_one('#Job [selected="selected"]').get_text()
            except:
                pass
            res.append_details(detail)
            photourl = soup.select_one('.user-cont #usp-bg')['src']
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
            page = 0
            while True:
                page += 1
                url = 'https://vip.tujia.com/UserInfo/OrderList/{}/'.format(page)
                headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: vip.tujia.com
Pragma: no-cache
Referer: https://vip.tujia.com/UserInfo/OrderList/1/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
                html = self._ha.getstring(url, headers=headers)
                soup = BeautifulSoup(html, 'lxml')
                tables = soup.select('table')
                if not tables:
                    break
                for table in tables:
                    try:
                        orderid = table.select_one('.order-number').get_text()

                        order = self._order_detail(orderid)
                        res_one = ITRAVELORDER_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                        res_one.append_orders(order)
                        res_one.host = 'www.tujia.com'
                        yield res_one
                    except:
                        pass
                nextpage = re.findall(r'disabled="disabled">下一页', html)
                if nextpage:
                    break
        except Exception:
            self._logger.error('{} get order fail: {}'.format(self.userid, traceback.format_exc()))

    def _order_detail(self, orderid):
        orderurl = 'https://vip.tujia.com/UserInfo/OrderInfoTNS/{}/'.format(orderid)
        headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: vip.tujia.com
Pragma: no-cache
Referer: https://vip.tujia.com/UserInfo/OrderList/1/
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
        html = self._ha.getstring(orderurl, headers=headers).replace('\n', '').replace('\t', '').replace('\r', '')
        html = re.sub(r'\s{2,}', ' ', html)
        soup = BeautifulSoup(html, 'lxml')
        dic = {}
        dic['order'] = soup.select_one('tbody').get_text('')
        dic['orderDetails'] = soup.select_one('.orderDetails').get_text('')
        return dic

    def logout(self):
        res = False
        try:
            url = 'https://passport.tujia.com/PortalSite/Logout'
            html = self._ha.getstring(url, headers="""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: no-cache
            Connection: keep-alive
            Host: passport.tujia.com
            Pragma: no-cache
            Referer: https://vip.tujia.com/UserInfo/OrderList/
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36""")
            if not self._cookie_login():
                res = True
        except Exception:
            self._logger.error('log out fail: {}'.format(traceback.format_exc()))

        return res
