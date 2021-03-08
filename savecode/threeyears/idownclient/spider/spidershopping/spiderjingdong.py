"""
京东cookie登陆
订单，个人信息下载
20181026
"""
import requests
from .spidershoppingbase import SpiderShoppingBase
import re
import time
from commonbaby.helpers.helper_str import substring
import json
import traceback
import datetime
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from ...clientdatafeedback import ISHOPPING_ONE
from ...clientdatafeedback import RESOURCES, EResourceType, PROFILE, ESign, EGender
from commonbaby.httpaccess.httpaccess import HttpAccess, ResponseIO


class SpiderJingDong(SpiderShoppingBase):

    def __init__(self, task, appcfg, clientid):
        # SpiderMeiTuan.__init__(self,tst:Task, 'meituan', '1000')
        super(SpiderJingDong, self).__init__(task, appcfg, clientid)
        self.userid = ''
        if self.task.cookie:
            self._ha._managedCookie.add_cookies('jd.com', self.task.cookie)

    def _cookie_login(self):
        url = 'https://i.jd.com/user/info'
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Host': 'i.jd.com',
            'Referer': 'https://order.jd.com/center/list.action',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36'
        }
        try:
            headerx = ''
            for key, value in headers.items():
                headerx = headerx + key + ':' + value + '\n'
            r = self._ha.getstring(url, headers=headerx)
            soup = BeautifulSoup(r, 'lxml')
            userid = soup.select_one('#aliasBefore strong').get_text()
            if userid:
                self.userid = userid + '-jingdong'
                return True
            else:
                return False
        except:
            return False


    def _get_orders(self):
        try:
            for year in [3, 2014, 2015, 2016, 2017, 2018, 2]:
                page = 0
                while True:
                    page += 1
                    url = 'https://order.jd.com/center/list.action?d={}&s=4096&page={}'.format(year, page)
                    headers = {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                        'Connection': 'keep-alive',
                        'Host': 'order.jd.com',
                        'Referer': 'https://order.jd.com/center/list.action',
                        'Upgrade-Insecure-Requests': '1',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36'
                    }
                    headerx = ''
                    for key, value in headers.items():
                        headerx = headerx + key + ':' + value + '\n'
                    r = self._ha.getstring(url, headers=headerx)

                    soup = BeautifulSoup(r, 'html.parser')
                    tbody = soup.select('table tbody')
                    if not tbody:
                        break
                    commodity = self._commodity_name(r, headers)
                    for item in tbody:
                        # print(item)
                        pattbodyid = re.compile(r'<tbody id="parent-')
                        tbodyid = pattbodyid.search(str(item))
                        if not tbodyid:
                            dic0 = {}
                            ordertime = item.select_one('.dealtime')['title']
                            dic0['orderid'] = item.select_one("[name='orderIdLinks']").get_text()
                            goods = []
                            good = item.select('[class="tr-bd"]')
                            for g in good:
                                d = {}
                                commodityid = substring(str(g), 'goods-item p-', '"')
                                for dic in commodity:
                                    if dic['productId'] == int(commodityid):
                                        d['commodity'] = dic['name']
                                        break
                                d['number'] = item.select_one('.goods-number').get_text().strip()
                                goods.append(d)
                            dic0['goods'] = goods
                            shopId = item.select_one('.order-shop a')['class'][1]
                            if shopId == 'btn-im-jd':
                                dic0['shop'] = '京东'
                            else:
                                shopnames = self._shop_name(r, url)
                                shopId = re.findall(r'\d+', shopId)[0]
                                dic0['shop'] = shopnames[shopId]['venderName']
                            dic0['recipients'] = item.select_one('.consignee.tooltip .txt').get_text()
                            dic0['address'] = item.select_one('.pc p').get_text()
                            dic0['phone'] = item.select('.pc p')[1].get_text()
                            dic0['amount'] = item.select_one('.amount span').get_text()
                            dic0['payment'] = item.select_one('.amount .ftx-13').get_text()
                            dic0['status'] = item.select_one('.order-status').get_text().strip()
                            res_one = ISHOPPING_ONE(self.task, self._appcfg._apptype, self.userid, dic0['orderid'])
                            res_one.append_orders(dic0)

                            res_one.order = json.dumps(dic0)
                            res_one.ordertime = ordertime
                            res_one.host = 'www.jd.com'
                            res_one.orderid = dic0['orderid']
                            yield res_one
        except Exception:
            self._logger.error('{} got order fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_profile(self):
        try:
            url = 'https://i.jd.com/user/info'
            headers = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Host: i.jd.com
Pragma: no-cache
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36"""
            r = self._ha.getstring(url, headers=headers)
            soup = BeautifulSoup(r, 'lxml')
            userid = soup.select_one('#aliasBefore strong').get_text()
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            res.account = userid
            res.nickname = soup.select_one('#nickName')['value']
            patbirthday = re.compile(r"originalBirthday='(.*?)'")
            res.birthday = patbirthday.findall(str(soup))[0]
            patsex = re.compile(r'if\((.*?)==0\){')
            sex = patsex.findall(str(soup))[0]
            if sex == '0':
                res.gender = EGender.Male
            elif sex == '1':
                res.gender = EGender.Female

            res.email = soup.select_one('[clstag="homepage|keycount|home2013|infomail"] strong').get_text().strip()
            detail = dict()
            detail['京享值'] = soup.select_one('.rank.jxz a')['title']
            detail['小白信用'] = soup.select_one('[href="//credit.jd.com"]').get_text()
            patvip = re.compile(r'<div>会员类型：(.*?)</div>')
            detail['会员类型'] = patvip.findall(str(soup))[0]
            res.append_details(detail)
            photourl = soup.select_one('.u-pic img.png')['src']
            if photourl:
                photourl = 'https:' + photourl
                # res.resoures = photo
                # profilepic: RESOURCES = RESOURCES(self.task, photo['picurl'], EResourceType.Picture,
                #                                   self._appcfg._apptype)
                #
                # resp_stream: ResponseIO = self._ha.get_response_stream(photo['picurl'])
                # profilepic.io_stream = resp_stream
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

    def _commodity_name(self, html, headers):
        data = substring(html, "$ORDER_CONFIG['toolbarOdoSwitch']=", "$ORDER_CONFIG['orderRemindIds']")
        value = re.findall(r"='(.+?)'", data)
        if len(value) == 6:
            dic = {}
            dic['orderWareIds'] = value[0]
            dic['orderWareTypes'] = value[1]
            dic['orderIds'] = value[2]
            dic['orderTypes'] = value[3]
            dic['orderSiteIds'] = value[4]
            dic['sendPays'] = value[5]
        else:
            return None
        url = 'https://order.jd.com/lazy/getOrderProductInfo.action'
        r = requests.post(url, headers=headers, data=dic)
        return r.json()

    def _shop_name(self, html, ul):
        data = substring(html, "['popVenderIds']='", "'")
        url = 'https://order.jd.com/lazy/getPopTelInfo.action'
        postdata = 'popVenderIds=' + quote_plus(data)
        headers = f"""
accept: application/json, text/javascript, */*; q=0.01
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
content-length: 143
content-type: application/x-www-form-urlencoded
origin: https://order.jd.com
pragma: no-cache
referer: {ul}
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36
x-requested-with: XMLHttpRequest"""
        r = self._ha.getstring(url, headers=headers, req_data=postdata)
        return json.loads(r)
    
    def _logout(self):
        res = False
        try:
            url = 'https://passport.jd.com/uc/login?ltype=logout&ReturnUrl=https://order.jd.com/center/list.action'
            headers = """
Host: passport.jd.com
Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Referer: https://order.jd.com/center/list.action
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
"""
            html = self._ha.get_response(url, headers=headers).content.decode('gbk')
            if '京东-欢迎登录' in html:
                res = True
        except Exception:
            self._logger.error('log out fail: {}'.format(traceback.format_exc()))
        
        return res