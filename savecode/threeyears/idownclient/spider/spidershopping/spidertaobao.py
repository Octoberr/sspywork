"""
淘宝cookie登陆，账密登陆待完善（密码是加密后的）
订单，个人信息下载
20181023
"""
import datetime
import json
import re
import time
import traceback
import pytz

from bs4 import BeautifulSoup
from commonbaby.httpaccess.httpaccess import HttpAccess, ResponseIO

from .spidershoppingbase import SpiderShoppingBase
from ...clientdatafeedback import ISHOPPING_ONE
from ...clientdatafeedback import PROFILE
from ...clientdatafeedback import RESOURCES, EResourceType, EGender, ESign


class SpiderTaoBao(SpiderShoppingBase):

    def __init__(self, task, appcfg, clientid):
        super(SpiderTaoBao, self).__init__(task, appcfg, clientid)
        self.time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        self._ha = HttpAccess()
        self.userid = ''
        self.cookie = self.task.cookie

    def _cookie_login(self):
        self._ha._managedCookie.add_cookies("taobao.com", self.cookie)

        try:
            resopnse = self._ha.getstring('https://member1.taobao.com/member/fresh/account_security.htm')
            soup1 = BeautifulSoup(resopnse, 'html.parser')
            account = soup1.find_all("span", {"class": "default grid-msg "})[0].get_text()
            if account:
                self.userid = account + '-taobao'
                return True
            else:
                return False
        except:
            return False

    # def _needcode(self):
    #     # 判断是否需要验证码，一般都不需要。若需要就不再执行之后的代码，验证码待解决
    #     r = self._ha.getstring('https://login.taobao.com/member/request_nick_check.do?_input_charset=utf-8')
    #     pat = re.compile(r'"needcode":false')
    #     isneed = pat.findall(r)
    #     if isneed:
    #         res = True
    #     else:
    #         res = False
    #     return res
    #
    #
    #     def pwd_login(self):
    #         if self._needcode():
    #             # 手动登陆一次获取账号，和加密后的256位密码。um_token,ua 可以持续使用
    #             try:
    #                 # 获取um
    #                 url = 'https://ynuf.alipay.com/service/um.json'
    #                 data = '''data=ENCODE~~V01~~eyJ4diI6IjMuMy43IiwieHQiOiJDMTUzOTc1ODg3MzI3OTkwODY1NDAzMjI5MTUzOTc1ODg3MzI3OTI5NSIsImV0ZiI6InUiLCJ4YSI6InRhb2Jhb19sb2dpbiIsInNpdGVJZCI6IiIsInVpZCI6IiIsImVtbCI6IkFBIiwiZXRpZCI6IiIsImVzaWQiOiIiLCJ0eXBlIjoicGMiLCJuY2UiOnRydWUsInBsYXQiOiJXaW4zMiIsIm5hY24iOiJNb3ppbGxhIiwibmFuIjoiTmV0c2NhcGUiLCJubGciOiJ6aC1DTiIsInN3IjoxNDQwLCJzaCI6OTAwLCJzYXciOjE0NDAsInNhaCI6ODYwLCJic3ciOjE0MTUsImJzaCI6OTE5LCJlbG9jIjoiaHR0cHMlM0ElMkYlMkZsb2dpbi50YW9iYW8uY29tJTJGbWVtYmVyJTJGbG9naW4uamh0bWwiLCJldHoiOjQ4MCwiZXR0IjoxNTM5NzU4ODczNDYxLCJlY24iOiJiNmUzNGRlZDBhMGQxMWFkOWJhM2Q5MjI0MmIyZWExZThhMmU5MTYxIiwiZWNhIjoiRk1sTkZHUkJ2alVDQVdYTWU5ZGN6QU5CIiwiZXJkIjoiZGVmYXVsdCxjb21tdW5pY2F0aW9ucyxhOTY4MWU4MTYwMzk5ZGVmMjkwN2IzM2JlMDFjZDU1ZDVmY2Q0NTUyYWE0MmNjZGYxZDc0MzljNmNlM2VkNDVkIiwiY2FjaGVpZCI6ImE2MTU1OGRkMDk0ZGJjNDciLCJ4aCI6IiIsImlwcyI6IjE5Mi4xNjguNDAuMjciLCJlcGwiOjMsImVwIjoiMmZiZjRhMGQzNDIxNGQ0ZmRlNmNjOGEyMjg5N2QxMTVhNzY2NzgxMSIsImVwbHMiOiJDMzcwYzMwN2Y0YWNhNzg1ODQ5M2RmZTMyMjI1NGU1Y2I0MzhiZTk0NCxOMGZjZDZlMThmZjZkZjc0Zjk4YTY5OGI3ZjZiNmQ4MzhhNmMxMWU2OSIsImVzbCI6ZmFsc2V9'''
    #                 r0 = self._ha.getstring(url, req_data=data)
    #                 patum = re.compile(r'{"tn":"(.*?)"')
    #                 um = patum.findall(r0)[0]
    #
    #                 url = 'https://login.taobao.com/member/login.jhtml?redirectURL=http%3A%2F%2Fuland.taobao.com%2Fsem%2Ftbsearch%3Fkeyword%3D%25E7%25BD%2591%25E6%25B7%2598%25E5%25AE%259D%26refpid%3Dmm_26632258_3504122_32538762%26clk1%3D96c17d51a8de3455444def907818d976%26upsid%3D96c17d51a8de3455444def907818d976'
    #                 data = """TPL_username={account}&TPL_password=&ncoSig=&ncoSessionid=&ncoToken=8374672d18e483bd0f6f39b0638cf4f717e652a3&slideCodeShow=false&useMobile=false&lang=zh_CN&loginsite=0&newlogin=0&TPL_redirect_url=https%3A%2F%2Fi.taobao.com%2Fmy_taobao.htm%3Fspm%3Da2e15.8261149.1997525045.1.513d29b4SpO5fP&from=tbTop&fc=default&style=&css_style=&keyLogin=false&qrLogin=true&newMini=false&newMini2=false&tid=&loginType=3&minititle=&minipara=&pstrong=&sign=&need_sign=&isIgnore=&full_redirect=&sub_jump=&popid=&callback=&guf=&not_duplite_str=&need_user_id=&poy=&gvfdcname=10&gvfdcre=68747470733A2F2F756C616E642E74616F62616F2E636F6D2F73656D2F74627365617263683F7265667069643D6D6D5F32363633323235385F333530343132325F3332353338373632266B6579776F72643D26636C6B313D37333763303966343036323835646335356337353734373936303632366633362675707369643D3733376330396634303632383564633535633735373437393630363236663336&from_encoding=&sub=true&TPL_password_2={password}&loginASR=1&loginASRSuc=1&allp=&oslanguage=zh-CN&sr=1440*900&osVer=&naviVer=chrome%7C70.035284&osACN=Mozilla&osAV=5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F70.0.3528.4+Safari%2F537.36&osPF=Win32&miserHardInfo=&appkey=00000000&nickLoginLink=&mobileLoginLink=https%3A%2F%2Flogin.taobao.com%2Fmember%2Flogin.jhtml%3Ffrom%3Dtaobaoindex%26f%3Dtop%26style%3D%26sub%3Dtrue%26redirect_url%3Dhttps%3A%2F%2Fi.taobao.com%2Fmy_taobao.htm%3Fspm%3Da2e15.8261149.1997525045.1.513d29b4SpO5fP%26useMobile%3Dtrue&showAssistantLink=&um_token={um}&ua=112%23y7ZAac4WDEN%2B4mHzkW7CXzLl83YWtnWIfYqlxuD9pkxezGSBy82xHdU1%2Bz9HuXkMfR26HWpFZNWOI4DAmypKUNAFwuPH73TKN9emJlAiVVAQ1PxFlwKtsUH2e1JUVzTAlhrXT3HKWgp97V6117sF07h%2B80F1DbfQOC9S%2BcI0LOuAZ9EhTbhtawmxPLUgc7ub3BPq6XoCuCKcHPW2ab%2Fm07lh4UXqZAHrs4SsVffYA8usbPYVhkr9qNcciJ7oQ9tKSydH16TUwGpoLupH6oZ73pNyazmIkh6ngIefwMzYow%2Fw1%2FrQuUvVNxvF2%2BBd0ZxNkGGL8smu0EuIN4tVkqotEe6vLvwlyfhtDBLx6w3r%2Bn1GcfNVfVcDcCfNryZRhVyJceksSl%2Bz3yuxMuvikeUYKCqr9nN%2B5R5VHeVf83cA7e6XP5ApLtdMNhMdPdk8crONeCpmo1F9F6695Sajqz0KXIfDZbh5vnjvfIU4bvMPZt48%2BSN8boo9M%2BPfJX1%2B%2Bpy4edvCrktGxHvLBLyg1d3pH1t7qFSxN6VmvpggiSOD1EOchJl1ayWIOIi9i4OGEPZY12XkWZM%2F0U0ZCTPuV8oeoD1FAeyNaDWtDO7pBs0ZZtW7lKC5wQx9vfV68F%2B0cgH24SToFWlHCsBX5WF9l0SsozHR%2F7xqN2xOZ%2FwDc62bh9LzmIXop7l%2Bsi5lpcR5u2nOzroru4xSgyH5pDQ2AcIumWGEuTyF4V808dkWo0ng9QApgco8KtNUfLQzZpCGh%2BZWtnON1vPOb3SexR5fLREAb1mM%2Fc7Uc9FDpP%2F17MMZpnL5krOZA4l%2B7fysXJ4KiqEDhPnz7cMZrqCw%2F%2FMxiR3sKfm%2F%2Fc7%2BTAv4Yy3g5WX5QcXcYm5qvRKPMl1VpYetEoIcx%2FK9v26IgW3PWh5u0%2F3mN87FlXNOw%2Bw09BTeD67nz4NITOPlhlYPH6XyGIfxnzwsJKzViMWPvgxfwlTCEUiGlafbi8Oy%2FDLyFEL3kj06%2FB%2B4WLdskNlinhO5TfulxWaZbCjcDR%2FSVMovkXl7B6rT4O1GeOq6qSN1gI%2Bi5fv0U4Qo9xz%2BcQg9A95Go0XwHaFUo7f5QkeeP%2F3hdd%2Bu5aj5IhBnl1D7lZzlUt1QQC2Fz%2B8uHk3X%2Beduq37gWATJBAU07MhWd%2Fq0Ou7lz9KjiVbarWJb0vQqyM40SJlsF6OWjaQ%2FVyRNMwi5afotZrV99yuInrrSVoeZ%2BawQxsj7eLZ%2F1fySG%2BhBgmGcsUeMEIbgw8PsUGnu9vopAfDD2S8Zsxo5FiFV318D3%2BefR8EXItfuDcy0VpymDa9PKOiZxL3CN%2F4Ih66elaec61KGI9kzeFJQvHxJo3%2BE31wxDjqvGGfWzSKpiP8LJI9L2OrH%2FnCpPtb1O0nFRxXO0y0cf%2BKAXLybh88M9sRc%2BFoSjzP0UpDzAMGWwnPmCNuGNeBGmA47O%2BjSpQvPQZoHyARO1ck2pZgFN%2FUIK9dbB64vBoOambxtKL%2BSPX7b%2B4Uqkgn%2BS71UarxKI9Z9%2F%2Flz0szGzOK2O9BR1JRo0vqMI9pOOwC8U%2FVmfZ5SqC1VgduP983JSiEhof7LYnnlBhcIcyuuqqJ%2F4iUVzTXb%2BwDFs%2F2e%2BPjDf%2FQM%2Bq%2F6cclZYrZjuxqjI1e0FKcaPRuFBVcL%2BVx4Pf4GQ4u2JXluJv2jdihrAevHxu3Zx1HIFPuqOCIYBoDF4zqcKgBWiymhrN%2FsRpe%2B""".format(account=self.account, password=self.password, um=um)
    #                 headers = """
    # accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
    # accept-encoding: gzip, deflate
    # accept-language: zh-CN,zh;q=0.9
    # Origin: https://login.taobao.com
    # Upgrade-Insecure-Requests: 1
    # Content-Type: application/x-www-form-urlencoded
    # Connection: keep-alive
    # Host: login.taobao.com
    # Referer: https://login.taobao.com/member/login.jhtml?spm=a2e15.8261149.754894437.1.118f29b4TQ4p9O&f=top&redirectURL=http%3A%2F%2Fuland.taobao.com%2Fsem%2Ftbsearch%3Fkeyword%3D%25E7%25BD%2591%25E6%25B7%2598%25E5%25AE%259D%26refpid%3Dmm_26632258_3504122_32538762%26clk1%3D96c17d51a8de3455444def907818d976%26upsid%3D96c17d51a8de3455444def907818d976
    # User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
    # """
    #                 r = self._ha.getstring(url, req_data=data, headers=headers, encoding='gb2312')
    #                 pattoken = re.compile(r'token=(.*?)&')
    #                 token = pattoken.findall(r)[0]
    #
    #                 # 通过token获取st
    #                 url1 = 'https://passport.alibaba.com/mini_apply_st.js?site=0&token={token}&callback=callback'.format(token=token)
    #                 headers1 = """
    # Accept: */*
    # Accept-Encoding: gzip, deflate, br
    # Accept-Language: zh-CN,zh;q=0.9
    # User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
    # Referer: https://login.taobao.com/member/login.jhtml?redirectURL=http%3A%2F%2Fuland.taobao.com%2Fsem%2Ftbsearch%3Fkeyword%3D%25E7%25BD%2591%25E6%25B7%2598%25E5%25AE%259D%26refpid%3Dmm_26632258_3504122_32538762%26clk1%3D96c17d51a8de3455444def907818d976%26upsid%3D96c17d51a8de3455444def907818d976
    # Host: passport.alibaba.com
    # Connection: keep-alive
    # """
    #                 r1 = self._ha.getstring(url1, headers=headers1)
    #                 patst = re.compile(r'st":"(.*?)"')
    #                 st = patst.findall(r1)[0]
    #
    #                 # 通过st模拟登陆
    #                 url2 = 'https://login.taobao.com/member/vst.htm?st={st}&TPL_username={account}'.format(st=st, account=self.account)
    #                 headers2 = """
    # accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
    # accept-encoding: gzip, deflate, br
    # accept-language: zh-CN,zh;q=0.9
    # User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
    # Upgrade-Insecure-Requests: 1
    # Connection: keep-alive
    # Host: login.taobao.com
    # """
    #                 r2 = self._ha.getstring(url2, headers=headers2)
    #             except Exception as ex:
    #                 self._logger.error("Download error: %s" % ex)
    #                 return False
    #             newcookie = self._ha._managedCookie.get_cookie_for_domain('https://www.taobao.com')
    #             # print(newcookie)
    #             self.cookie = newcookie
    #             self.task.cookie = newcookie
    #             return True

    def _get_profile(self):
        # 个人信息
        try:
            url = 'https://i.taobao.com/user/baseInfoSet.htm'
            headers = """
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cookie: {cookie}
upgrade-insecure-requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
""".format(cookie=self.cookie)
            r = self._ha.getstring(url, headers=headers)
            # print(r)
            soup = BeautifulSoup(r, 'html.parser')
            res = PROFILE(self._clientid, self.task, self._appcfg._apptype, self.userid)
            detail = {}

            photourl = soup.select_one('.pf-avatar img.png')['src']
            try:
                res.nickname = soup.select_one('#J_uniqueName')['value']
            except:
                pass
            try:
                detail['fullname'] = soup.select_one('#J_realname')['value']
            except:
                pass
            try:
                gender = soup.select_one('.except [checked="checked"]')['value']
                if gender == '0':
                    res.gender = EGender.Male
                elif gender == '1':
                    res.gender = EGender.Female
                else:
                    res.gender = EGender.Unknown
            except:
                pass
            try:
                year = soup.select_one('#J_Year [selected="selected"]')['value']
                month = soup.select_one('#J_Month [selected="selected"]')['value']
                data = soup.select_one('#J_Date [selected="selected"]')['value']
                res.birthday = year + '-' + month + '-' + data
            except:
                pass

            resopnse = self._ha.getstring('https://member1.taobao.com/member/fresh/account_security.htm')
            soup1 = BeautifulSoup(resopnse, 'html.parser')
            try:
                res.account = soup1.find_all("span", {"class": "default grid-msg "})[0].get_text()
            except:
                pass
            try:
                res.email = soup1.find_all("span", {"class": "default grid-msg "})[1].get_text()
            except:
                pass
            try:
                res.phone = soup1.find("span", {"class": "default grid-msg"}).get_text().strip()
            except:
                pass

            # 获取从地区表中获取住址

            try:
                liveDivisionCode = soup.select_one('input#liveDivisionCode')['value']
                if liveDivisionCode:
                    detail['hometown'] = self._get_address(liveDivisionCode)
            except:
                pass

            try:
                divisionCode = soup.select_one('input#divisionCode')['value']
                if divisionCode:
                    res.address = self._get_address(divisionCode)
                res.detail = json.dumps(detail)
            except:
                pass
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
            self._ha._managedCookie.add_cookies("taobao.com", self.cookie)
            url = 'https://buyertrade.taobao.com/trade/itemlist/asyncBought.htm?action=itemlist/BoughtQueryAction&event_submit_do_query=1&_input_charset=utf8'
            i = 0
            while True:
                i += 1
                formdata = """dateBegin=0&dateEnd=0&options=0&pageNum={i}&pageSize=15&queryOrder=desc&prePageNo={j}""".format(
                    i=i, j=i - 1)
                headers = """
accept: application/json, text/javascript, */*; q=0.01
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
content-type: application/x-www-form-urlencoded; charset=UTF-8
origin: https://buyertrade.taobao.com
pragma: no-cache
referer: https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm?spm=a1z02.1.a2109.d1000368.1c2d782dHeADbf&nekot=1470211439694
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3528.4 Safari/537.36
x-requested-with: XMLHttpRequest
"""
                # cookie: {cookie}
                response = self._ha.getstring(url, headers=headers, req_data=formdata)
                html = json.loads(response)
                mainorders = html.get('mainOrders')
                if mainorders:
                    # print("抓取第{0:d}页。".format(i))

                    for order in mainorders:
                        try:
                            dic = {}
                            orderid = order.get('id')
                            dic['id'] = order.get('id')
                            dic['shopname'] = order.get('seller').get('shopName')

                            ordertime = order.get('orderInfo').get('createTime')
                            dic['actualFee'] = order.get('payInfo').get('actualFee')
                            dic['status'] = order.get('statusInfo').get('text')
                            goods = []
                            for item in order['subOrders']:
                                di = {}
                                try:
                                    di['title'] = item.get('itemInfo').get('title')
                                except:
                                    pass
                                try:
                                    di['quantity'] = item['quantity']
                                except:
                                    pass
                                try:
                                    di['skuText'] = item['itemInfo']['skuText']
                                except:
                                    pass
                                try:
                                    di['priceInfo'] = item['priceInfo']
                                except:
                                    pass
                                goods.append(di)
                            dic['goods'] = goods
                            res_one = ISHOPPING_ONE(self.task, self._appcfg._apptype, self.userid, orderid)
                            res_one.ordertime = ordertime
                            res_one.append_orders(dic)
                            res_one.host = 'www.taobao.com'
                            yield res_one
                        except:
                            pass
                    time.sleep(1)
                else:
                    break
        except Exception:
            self._logger.error('{} got order fail: {}'.format(self.userid, traceback.format_exc()))

    def _get_address(self, adressid):
        table = self._ha.getstring('https://www.taobao.com/home/js/sys/districtselector.js?t=20140318.js')
        patdz = re.compile(r'TB.form.DistrictSelector._tb_ds_data=(.*?);TB.form.Di')
        dzdata = patdz.findall(table)[0]
        jsdata = json.loads(dzdata)
        res = []
        if adressid is not None and adressid != '1':
            dz1 = jsdata[adressid]
            res = dz1[0]
            if dz1[1] != '1':
                dz2 = jsdata[dz1[1]]
                res = dz2[0] + res
                if dz2[1] != '1':
                    dz3 = jsdata[dz2[1]]
                    res = dz3[0] + res
        return res

    def _logout(self):
        res = False
        try:
            url = 'https://login.taobao.com/member/logout.jhtml?spm=a1z02.1.754894437.7.7016782dPtkeCQ&f=top&out=true&redirectURL=https%3A%2F%2Fi.taobao.com%2Fmy_taobao.htm%3Fspm%3Da2e15.8261149.754894437.3.555929b48sljpe%26ad_id%3D%26am_id%3D%26cm_id%3D%26pm_id%3D1501036000a02c5c3739%26nekot%3DdGI4NTgzMzYzXzAw1553481160507'
            html = self._ha.getstring(url, headers="""
Host: login.taobao.com
Connection: keep-alive
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Referer: https://i.taobao.com/my_taobao.htm?spm=a2e15.8261149.754894437.3.555929b48sljpe&ad_id=&am_id=&cm_id=&pm_id=1501036000a02c5c3739&nekot=dGI4NTgzMzYzXzAw1553481160507
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
""")
            res = self._cookie_login()
            if not res:
                res = True
        except Exception:
            self._logger.error('login out fail:{}'.format(traceback.format_exc()))
        return res
