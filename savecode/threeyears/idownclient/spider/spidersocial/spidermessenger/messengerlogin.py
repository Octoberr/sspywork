"""messenger login"""

# -*- coding:utf-8 -*-

import re
import traceback
from urllib import parse
from lxml import etree
import base64
import json
import websocket
import random

from commonbaby.helpers import helper_str, helper_time

from datacontract.idowndataset import Task
from .messengerbase import MessengerBase


class MessengerLogin(MessengerBase):
    """messenger login"""

    # 最外层是__d("LSGraphqlInitialSyncQuery.graphql"
    # params: {
    #     id: "3325130330947119",
    #     metadata: {},
    #     name: "LSGraphqlInitialSyncQuery",
    #     operationKind: "query",
    #     text: null
    # }
    _re_docid_LSGraphqlInitialSyncQuery = re.compile(
        r'__d\("LSGraphqlInitialSyncQuery.graphql".*?params:\s*?(.*?name:\s*?"LSGraphqlInitialSyncQuery".*?\s*?})',
        re.S)

    def __init__(self, task: Task, appcfg, clientid):
        MessengerBase.__init__(self, task, appcfg, clientid)

    def _sms_login_(self) -> bool:
        res: bool = False
        try:
            res = self.__sms_login()

            if res and not (isinstance(self._username, str)
                            or self._username == ""):
                res, msg = self._access_profile()

            if not isinstance(self._host, str) or self._host == "":
                self._host = 'facebook.com'
        except Exception:
            self._logger.error("Sms login error:%s" % traceback.format_exc())

        return res

    def _cookie_login_(self) -> bool:
        """用cookie登陆尝试"""
        res: bool = False
        try:
            # self._ha._managedCookie.add_cookies(".facebook.com",
            #                                     self.task.cookie)

            res, msg = self._refresh_neccessary_fields()
            if not res:
                self._logger.error("Cookie login failed: {}".format(msg))
                return res

            res, msg = self._access_profile()
            if not res:
                self._logger.error("Cookie login failed: {}".format(msg))
                return res

            if not isinstance(self._host, str) or self._host == "":
                self._host = 'facebook.com'

            msg = "登录成功"
            res = True
        except Exception:
            self._logger.error(
                "Cookie login error:%s" % traceback.format_exc())
        return res

    def __sms_login(self) -> bool:
        """拿手机号去登陆，看能不能拿到验证码？"""
        res: bool = False
        try:
            if not isinstance(self.phone, str) or self.phone == "":
                self._logger.error("Phone number '%s' is invalid" % self.phone)
                return res

            phone = self.phone

            # 登陆首页拿参数
            url = "https://www.messenger.com/login.php"
            html = self._ha.getstring(
                url,
                headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                cache-control: no-cache
                pragma: no-cache
                upgrade-insecure-requests: 1
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36
            """)

            # "_js_datr","egJxW0NbHZJOq9uB6i8b165T"
            # 加cookie
            succ, _js_datr = helper_str.substringif(html, '"_js_datr","', '"')
            if not succ:
                raise Exception("_js_datr not found.")
            self._ha._managedCookie.add_cookies("messenger.com",
                                                "_js_datr=%s" % _js_datr)
            self._ha._managedCookie.add_cookies("facebook.com",
                                                "datr=%s" % _js_datr)

            # "identifier":"f348eeb7776c1fa9c07e9e74ba25bece"
            # post data
            succ, identifier = helper_str.substringif(html, '"identifier":"',
                                                      '"')
            if not succ:
                raise Exception("identifier not found.")
            # //"initialRequestID":"ASkMH7-Nr9L8BiOCVp8Uvsk"
            # //post data
            succ, initial_requestid = helper_str.substringif(
                html, '"initialRequestID":"', '"')
            if not succ:
                raise Exception("initial_requestid not found.")

            # //"pkg_cohort":"PHASED:messengerdotcom_pkg"
            # //post data
            succ, self._pc = helper_str.substringif(html, 'pkg_cohort":"', '"')
            if not succ:
                raise Exception("__pc not found.")

            # //{"server_revision":4201737,
            # //post data
            succ, self._rev = helper_str.substringif(html, 'server_revision":',
                                                     ',')
            if not succ:
                raise Exception("__rev not found.")

            # //<input type="hidden" name="lsd" value="AVoa4_T_" autocomplete="off" />
            # //post data
            succ, self.lsd = helper_str.substringif(html, 'name="lsd" value="',
                                                    '"')
            if not succ:
                raise Exception("lsd not found.")

            # 这个请求里设置了cookie
            pnl_data2 = helper_str.base64str(
                '{"a":"all_pagelets_displayed","c":"XMessengerDotComLoginPageController","b":false,"d":"/login/identify","e":["primer_no_pagetrans"]}'
            )
            self._ha._managedCookie.add_cookies("messenger.com",
                                                "pnl_data2=%s" % pnl_data2)
            url = "https://www.messenger.com/ajax/bz"
            postdata = (
                    '__a=1&__be=-1&__pc=' + parse.quote_plus(self._pc) + '&__req='
                    + parse.quote_plus(self._req.get_next()) + '&__rev=' +
                    parse.quote_plus(
                        self._rev) + '&__user=0&lsd=' + parse.quote_plus(self.lsd)
                    + '&ph=C3&q=%5B%7B%22user%22%3A%220%22%2C%22page_id'
                      '%22%3A%22bkhrdy%22%2C%22posts%22%3A%5B%5B%22clic'
                      'k_ref_logger%22%2C%5B%220ZDU%22%2C1534132912147%'
                      '2C%22act%22%2C1534132912145%2C0%2C%22https%3A%2F'
                      '%2Fwww.facebook.com%2Flogin%2Fidentify%3Fctx%3Dr'
                      'ecover%22%2C%22click%22%2C%22click%22%2C%22-%22%'
                      '2C%22r%22%2C%22%2Flogin%2F%22%2C%7B%22ft%22%3A%7'
                      'B%7D%2C%22gt%22%3A%7B%7D%7D%2C0%2C0%2C0%2C0%2C%2'
                      '2bkhrdy%22%2C%22XMessengerDotComLoginPageControl'
                      'ler%22%5D%2C1534132912145.8%2C0%5D%5D%2C%22trigg'
                      'er%22%3A%22click_ref_logger%22%2C%22send_method%'
                      '22%3A%22ajax%22%7D%5D&ts=' + str(helper_time.ts_since_1970()))
            # &__dyn=5V8WXBzamaUmgDxKS5k2m3miWGey8jrWo466EeAq2i5U4e2CEaUgxebkwy6UnGiidz9XDG4XzEa8iyA14zorx64oKjG2e5UC4bz8gxO1iyECUd8hxG1awxwxgeEtxK1fwLhob876u4rGUpCwCGm8xC784a3mbwExuazoK13x3yUWfxu8CwKwCzUR1zAz8bAu9xm3edBAyEOfBK6o-6UG6EO1pGFUaUvxucy8KV8zwEwFypUKUbUgzVU
            html = self._ha.getstring(
                url,
                req_data=postdata,
                headers="""
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                cache-control: no-cache
                content-type: application/x-www-form-urlencoded
                origin: https://www.messenger.com
                referer: https://www.messenger.com/login/""")

            # 忘记密码页面，设置cookie  sb=rwJxWwQgofG3h1HEQAuVRhAN;
            url = "https://www.facebook.com/login/identify?ctx=recover"
            self._ha._managedCookie.add_cookies(
                "messenger.com", "fr=00UVPcWMVc9W2tUi2..BbcQJ8...1.0.BbcQJ8.")
            html = self._ha.getstring(
                url,
                headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                cache-control: no-cache
                referer: https://www.messenger.com/
                upgrade-insecure-requests: 1""")

            # <input type="hidden" name="lsd" value="AVoa4_T_" autocomplete="off" />
            # post data
            succ, self.lsd = helper_str.substringif(html, 'name="lsd" value="',
                                                    '"')
            if not succ:
                raise Exception("lsd not found.")
            # {"server_revision":4201737,
            # post data
            succ, self._rev = helper_str.substringif(html,
                                                     '"server_revision":', ',')
            if not succ:
                raise Exception("__rev not found.")
            # "pkg_cohort":"PHASED:messengerdotcom_pkg"
            # post data
            succ, self._pc = helper_str.substringif(html, 'pkg_cohort":"', '"')
            if not succ:
                raise Exception("__pc not found.")

            # 点击搜索后，有个自动发送的，设置了很多cookie的
            url = "https://www.facebook.com/cookie/consent/?dpr=1"
            self._ha._managedCookie.add_cookies(
                "facebook.com",
                "_js_reg_ext_ref=https%3A%2F%2Fwww.messenger.com%2F;")
            self._ha._managedCookie.add_cookies(
                "facebook.com",
                r"_js_reg_fb_ref=https%3A%2F%2Fwww.facebook.com%2Flogin%2Fidentify%3Fctx%3Drecover;"
            )
            self._ha._managedCookie.add_cookies(
                "facebook.com",
                r"_js_reg_fb_gate=https%3A%2F%2Fwww.facebook.com%2Flogin%2Fidentify%3Fctx%3Drecover;"
            )
            html = self._ha.getstring(
                url,
                headers="""
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                cache-control: no-cache
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                referer: https://www.facebook.com/login/identify?ctx=recover"""
            )

            # 检查账号是否存在
            url = "https://www.facebook.com/ajax/login/help/identify.php?ctx=recover&dpr=1"
            did_submit = "搜索"
            postdata = (
                    r'lsd=' + parse.quote_plus(self.lsd) + r'&email=' +
                    parse.quote_plus(phone) + r'&did_submit=' +
                    parse.quote_plus(did_submit) + r'&__user=0&__a=1&__req=' +
                    self._req.get_next() + r'&__be=-1&__pc=' + parse.quote_plus(
                self._pc) + r'&__rev=' + parse.quote_plus(self._rev))
            html = self._ha.getstring(
                url,
                req_data=postdata,
                headers="""
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                cache-control: no-cache
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                pragma: no-cache
                referer: https://www.facebook.com/login/identify?ctx=recover"""
            )

            if html is None or html == "":
                raise Exception("Check if account registered failed.")
            accExists = False
            # 你的搜索没有返回任何结果。请换用其他信息再试一次。
            if r'\u4f60\u7684\u641c\u7d22\u6ca1\u6709\u8fd4\u56de\u4efb\u4f55\u7ed3\u679c\u3002\u8bf7\u6362\u7528\u5176\u4ed6\u4fe1\u606f\u518d\u8bd5\u4e00\u6b21\u3002\u003' in html:
                # raise Exception("Account not exists: %s" % phone)
                self._logger.info('%s %s 你的搜索没有返回任何结果。请换用其他信息再试一次' %
                                  (self.task.taskid, self._username))
            # 识别您的账户
            elif r'\u8bc6\u522b\u60a8\u7684\u5e10\u6237\u003C' in html:
                # raise Exception("Account not unique, need to select one: %s" % phone)
                self._logger.info('%s %s 结果不止一个，请识别您的账户' % (self.task.taskid,
                                                            self._username))
            else:
                accExists = True
            if not accExists:
                return res

            # "onload": [
            #   "window.location.href=\"\\\/recover\\\/initiate\\\/?ldata=AWfsYMWVOOUqIwhHc2GGQ9EwqHBZdawTEWgiu-s7AvwlvB-KV5HUau4AOMQ_vIT46Ug1aicvq_Q_ZbvGWckaey0lRPHIPI1hGV_qf0TkrS2lqS9Nqh4KNXHuWd9iyLwN1x1iTmnMibf_cS9UvVrK5Y7EQUMt6iX9x5vFllbXdjTYexBNzcvDIPwctWcxB5Z-uv84i8tM3WjxLITX8T6aV0aax4x_Yzj-2dF6Al_wEjDqMXxKmk_Alekb1fOD-78VqIg\""
            # ],
            succ, tmp = helper_str.substringif(html, 'onload":[', ']')
            if not succ or tmp is None or tmp == '':
                raise Exception(
                    "get check account registration redirection failed.")
            tmp = tmp.replace(r'\\"', '"').replace('\\', '').replace(
                '\\/', '/')
            succ, reUrl = helper_str.substringif(tmp, 'window.location.href="',
                                                 '"')
            if not succ or reUrl is None or reUrl == '':
                raise Exception(
                    "get check account registration redirection failed.")
            redir = "https://www.facebook.com/%s" % reUrl.strip('/')

            # 检查账号成功的请求会设置cookie "sfiu"，后面postdata好像会用到
            if not self._ha._managedCookie.contains_cookie('sfiu'):
                raise Exception("sfui not found.")
            sfiu = self._ha._managedCookie.get_cookie_value("sfiu")
            if sfiu is None or sfiu == None:
                raise Exception("sfui not found.")

            # 检查账号后 跳转链接
            htmlSms = self._ha.getstring(
                redir,
                headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                cache-control: no-cache
                referer: https://www.facebook.com/login/identify?ctx=recover
                upgrade-insecure-requests: 1""")
            if not 'class="inputtext"' in htmlSms:
                raise Exception("Select sms verify type failed.")

            # 有个值后面要POST用，也可能不用，而是验证码直接已经发送了，不用选择验证方式。
            # <input type="radio" id="send_sms:AYiYdwu_ywchlQTBjq_uGE-rtBcz
            # 8gUVGgwXsH8CDsB8Zpp16qGxIJ-MaL3cfEsaGZg" name="recover_metho
            # d" value="send_sms:AYiYdwu_ywchlQTBjq_uGE-rtBcz8gUVGgwXsH8CD
            # sB8Zpp16qGxIJ-MaL3cfEsaGZg" checked="1" class="uiInputLabelI
            # nput uiInputLabelRadio" />
            clickToSend = True
            succ, recover_method = helper_str.substringif(
                htmlSms, 'type="radio" id="', '"')
            if not succ or recover_method is None or recover_method == '':
                self._logger.debug("recover_method not found.")
                clickToSend = False

            hash_ = ""
            if clickToSend:
                # 点击 是我，继续  发送验证码
                url = "https://www.facebook.com/ajax/recover/initiate/?dpr=1"
                postdata = (
                        r'lsd=' + parse.quote_plus(self.lsd) +
                        r'&openid_provider_id=&openid_provider_name=&' +
                        r'recover_method=' + parse.quote_plus(recover_method) +
                        r'&reset_action=1&__user=0&__a=1&' + r'__req=' +
                        parse.quote_plus(self._req.get_next()) + r'&__be=-1&__pc='
                        + parse.quote_plus(
                    self._pc) + r'&__rev=' + parse.quote_plus(self._rev))
                html = self._ha.getstring(
                    url,
                    req_data=postdata,
                    headers="""
                    accept: */*
                    accept-encoding: gzip, deflate
                    accept-language: zh-CN,zh;q=0.9
                    content-type: application/x-www-form-urlencoded
                    origin: https://www.facebook.com
                    referer: %s""" % redir)

                # 有个跳转链接，不知道是搞啥的
                # "redirectPageTo",[],["https:\/\/www.facebook.com\/recover\/code\/?ce=1625022&rm=send_sms&hash=AUbXIrQtnKwFxe_P",false,false
                succ, reDirPageTo = helper_str.substringif(
                    html, 'redirectPageTo",[],["', '"')
                if not succ or reDirPageTo is None or reDirPageTo == "":
                    raise Exception("redirect page to failed.")
                reDirPageTo = reDirPageTo.replace('\\', '')
                # 有个hash
                succ, hash_ = helper_str.substringif(html, 'hash=', '"')
                if not succ or hash_ is None or hash_ == "":
                    raise Exception("hash not found.")

            # 搞验证码
            smscode: str = self._get_vercode()

            # 进入验证码页面准备输入验证码
            urlSendSms = 'https://www.facebook.com/recover/code/?ph[0]=%s&rm=send_sms&hash=%s' % (
                parse.quote_plus(phone), hash_)
            html = self._ha.getstring(
                urlSendSms,
                headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                referer: %s
                upgrade-insecure-requests: 1""" % redir)
            if not 'class="inputtext"' in html:
                raise Exception("Send sms failed.")

            # 点击继续，进入改密页面
            url = "https://www.facebook.com/recover/code?ph[0]=%s&recover_method=send_email&wsr=0" % (
                parse.quote_plus(phone))
            postdata = 'lsd=' + parse.quote_plus(
                self.lsd) + '&n=' + parse.quote_plus(
                smscode) + '&reset_action=1'
            html, reDirModifyPwd = self._ha.getstring_unredirect(
                url,
                req_data=postdata,
                headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                referer: %s
                upgrade-insecure-requests: 1""" % urlSendSms)
            if reDirModifyPwd is None or reDirModifyPwd == "":
                raise Exception("Jump to password modify page1 failed.")
            # 跳转链接里的u= 就是用户id
            # https://www.facebook.com/recover/password/?u=xxx&n=599428&fl=default_recover&sih=0
            succ, userid = helper_str.substringif(reDirModifyPwd, 'u=', '&')
            if not succ or userid is None or userid == '':
                raise Exception("Userid not found.")
            self._userid = userid

            # 继续跳转
            html = self._ha.getstring(
                reDirModifyPwd,
                headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                referer: %s
                upgrade-insecure-requests: 1""" % urlSendSms)
            if 'id="password_new"' not in html:
                raise Exception("Jump to password modify page2 failed.")

            # 点击跳过改密，直接登录，这个请求会有很多setcookie跳转到facebook
            url = "https://www.facebook.com/recover/password/?u=%s&n=%s&by&bm&bd&fl=default_recover" % (
                userid, smscode)
            postdata = 'lsd=%s&password_new=&btn_skip=1' % self.lsd
            html, reDirHome = self._ha.getstring_unredirect(
                url,
                req_data=postdata,
                headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                referer: %s
                upgrade-insecure-requests: 1""" % reDirModifyPwd)
            if reDirHome is None or reDirHome == "" or not "www.facebook.com" in reDirHome:
                raise Exception("Jump to home page failed.")

            succ, msg = self._refresh_neccessary_fields()
            if not succ:
                self._logger.info(msg)
                return succ

            succ = self._access_profile()

            res = succ

        except Exception:
            self._logger.error("Sms login error:\ntaskid:%s\nerror:%s" %
                               (self.task.taskid, traceback.format_exc()))
        return res

    def _refresh_neccessary_fields(self) -> (bool, str):
        """refresh neccessary fields from homepage"""
        succ: bool = False
        msg: str = None
        try:
            # facebook
            url = "https://www.facebook.com/"
            homepage = self._ha.getstring(
                url,
                headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9
                cache-control: no-cache
                content-type: application/x-www-form-urlencoded
                pragma: no-cache
                sec-fetch-mode: cors
                sec-fetch-site: same-origin
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36""")
            if homepage is None or homepage == "":
                raise Exception("Get userid failed.")
            self.homepage = homepage

            # {"USER_ID":"100027859862248","ACCOUNT_ID":"100027859862248","NAME":"San Zhang","SHORT_NAME":"San Zhang","IS_MESSENGER_ONLY_USER":false,"IS_DEACTIVATED_ALLOWED_ON_MESSENGER":false}
            succ, self._userid = helper_str.substringif(
                homepage, 'USER_ID":"', '"')
            if not succ or self._userid is None or self._userid == "":
                raise Exception("Get userid failed")
            if self._username is None or self._username == "":
                succ, username = helper_str.substringif(
                    homepage, 'NAME":"', '')
                if succ and not self._username is None and not self._username == "":
                    self._username = username
            # "async_get_token":"Adz9YM4ErUVi1H0azTmDnBX6Md_LsWwifZoVLsZMMIUakA:Adw2zeZ-U8JV7IoOmqmOkppLJGU_FOCjIicjrtSGkHuS-g"}
            succ, self.fb_dtsg_ag = helper_str.substringif(
                homepage, 'async_get_token":"', '"')
            if not succ or self.fb_dtsg_ag is None or self.fb_dtsg_ag == "":
                raise Exception("fb_dtsg_ag not found")
            # "__spin_r":4206568,
            succ, self._spin_r = helper_str.substringif(
                homepage, '__spin_r":', ',')
            if not succ or self._spin_r is None or self._spin_r == "":
                raise Exception("__spin_r not found. account may be locked")
            # "__spin_r":4206568,"__spin_b":"trunk","__spin_t":1534242344,
            succ, self._spin_t = helper_str.substringif(
                homepage, '__spin_t":', ',')
            if not succ or self._spin_t is None or self._spin_t == "":
                raise Exception("__spin_t not found")
            succ, self._spin_b = helper_str.substringif(
                homepage, '__spin_b":', ',')
            if not succ or self._spin_b is None or self._spin_b == "":
                raise Exception("__spin_b not found")
            self._spin_b = self._spin_b.strip().strip('"')
            # "hsi":"6746747510353494316-0"
            succ, self.hsi = helper_str.substringif(homepage, '"hsi":"', '"')
            if not succ or self.hsi is None or self.hsi == "":
                raise Exception("hsi not found")

            # {"name":"fb_dtsg","value":"AQHRzELKyYTl:AQFKH4XWkHlv"}
            succ, self.fb_dtsg = helper_str.substringif(homepage, '"name":"fb_dtsg","value":"', '"')
            if not succ or self.fb_dtsg is None or self.fb_dtsg == "":
                raise Exception("fb_dtsg not found")
            # {"name":"jazoest","value":"22097"}
            succ, self.jazoest = helper_str.substringif(
                homepage, '"name":"jazoest","value":"', '"')
            if not succ or self.jazoest is None or self.jazoest == "":
                raise Exception("jazoest not found")
            # 没有QuicklingConfig
            # ,"pkg_cohort":"EXP2:comet_pkg","
            succ, self._pc = helper_str.substringif(
                homepage, '"pkg_cohort":"', '"')
            if not succ or self._pc is None or self._pc == "":
                raise Exception("_pc not found")
            # "client_revision":1003006555,
            succ, self._rev = helper_str.substringif(
                homepage, '"client_revision":', ',')
            if not succ or self._rev is None or self._rev == "":
                raise Exception("_rev not found")
            # 获取个人主页地址
            html, redir = self._ha.getstring_unredirect('https://www.facebook.com/me',
                                                        headers="""
                                        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                                        accept-encoding: gzip, deflate
                                        accept-language: en-US,en;q=0.9
                                        sec-fetch-dest: document
                                        sec-fetch-mode: navigate
                                        sec-fetch-site: none
                                        sec-fetch-user: ?1
                                        upgrade-insecure-requests: 1
                                        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36"""
                                                        )
            if redir is None or redir == "":
                raise Exception("进入个人主页失败")
            self._host = redir

            # 进入messenger页面(通过facebook的cookie进入，如果不是，url需要改)

            # "deviceId":"39f79811-b3a7-447e-8483-7d2f59e35915","schemaVersion":"3696807697038235",
            re_params = re.compile(r'"deviceId":"(.*?)","schemaVersion":"(.*?)",')
            # {"epochId":"6754309714097997511"},5634]
            re_epochid = re.compile(r'"epochId":"(.*?)"}')
            # "fbid":"100054477585089","appID":219994525426954,
            re_aid = re.compile(r'"fbid":".*?","appID":(.*?),')
            # {"app_id":"772021112871879"}
            re_appid = re.compile(r'\{"app_id":"(\d+)"\}')

            url = 'https://www.facebook.com/messages'
            html = self._ha.getstring(url, headers='''
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6
                sec-fetch-dest: document
                sec-fetch-mode: navigate
                sec-fetch-site: none
                sec-fetch-user: ?1
                upgrade-insecure-requests: 1
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36
            ''')
            m = re.search(re_params, html)
            if m is None:
                raise Exception("进入messenger页面失败")
            self.device_id = m.group(1)
            self.schema_version = m.group(2)
            # epoch_id
            m = re.search(re_epochid, html)
            if m is None:
                raise Exception("epoch id not found")
            self.epoch_id = m.group(1)
            # aid
            m = re.search(re_aid, html)
            if m is None:
                raise Exception('aid not found')
            self.aid = m.group(1)
            # app_id
            m = re.search(re_appid, html)
            if m is None:
                raise Exception("app id not found")
            self.appid = m.group(1)

            # if 'lightspeed_web_initial_sync_v2' in html:
            #     re_respnse_js = re.compile(r'"lightspeed_web_initial_sync_v2":\{.*?"response":\[("function.*?),\s*"function.*?\]\}\}\}')
            #     m = re_respnse_js.search(html)
            #     if m is None:
            #         raise Exception("Get js function fail")
            #     js_func = m.group(1)
            #     if js_func is None or js_func == '':
            #         raise Exception("Get js function fail")
            #     res = self._parse_init_js(js_func)
            #     if not res:
            #         raise Exception("处理初始消息js失败")

            succ = True
            msg = "Refresh neccessary fields succeed."
        except Exception:
            self._logger.error(
                "Refresh neccessary fields from homepage error, taskid:%s\nphone:%s\nex:%s"
                % (self.task.taskid, self.phone, traceback.format_exc()))
            succ = False
            msg = "Refresh neccessary fields failed."
        return (succ, msg)

    def _access_profile(self) -> (bool, str):
        """access simple profile"""
        try:
            url = "https://www.facebook.com/"
            html = self._ha.getstring(
                url,
                headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9
                cache-control: no-cache
                content-type: application/x-www-form-urlencoded
                pragma: no-cache
                sec-fetch-mode: cors
                sec-fetch-site: same-origin
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"""
            )
            if html is None or html == "":
                raise Exception("Get profile page failed.")
            # {"USER_ID":"100027859862248","ACCOUNT_ID":"100027859862248",
            # "NAME":"San Zhang","SHORT_NAME":"San Zhang","IS_MESSENGER_ON
            # LY_USER":false,"IS_DEACTIVATED_ALLOWED_ON_MESSENGER":false}
            succ, self._userid = helper_str.substringif(
                html, 'USER_ID":"', '"')
            if not succ or self._userid is None or self._userid == "":
                succ, self._userid = helper_str.substringif(
                    html, 'user_id:"', '"')
                if not succ or self._username is None or self._username == "":
                    msg = "访问个人信息失败"
                    return (succ, msg)
            succ, self._username = helper_str.substringif(html, 'NAME":"', '"')
            if not succ or self._username is None or self._username == "":
                succ, self._username = helper_str.substringif(
                    html, 'name:"', '"')
                if not succ or self._username is None or self._username == "":
                    msg = "访问个人信息失败"
                    return (succ, msg)
            succ, self.is_messenger_only_user = helper_str.substringif(
                html, 'IS_MESSENGER_ONLY_USER":', ',')
            if succ and not self.is_messenger_only_user is None:
                if self.is_messenger_only_user == "false":
                    self.is_messenger_only_user = False
                else:
                    self.is_messenger_only_user = True
            succ, self.is_deactived_allowed_on_messenger = helper_str.substringif(
                html, 'IS_DEACTIVATED_ALLOWED_ON_MESSENGER":', ',')
            if succ and not self.is_deactived_allowed_on_messenger is None:
                if self.is_deactived_allowed_on_messenger == "false":
                    self.is_deactived_allowed_on_messenger = False
                else:
                    self.is_deactived_allowed_on_messenger = True

            succ = True
            msg = "访问个人信息成功"

        except Exception:
            self._logger.error(
                "Access profile error:%s" % traceback.format_exc())
            succ = False
            msg = "访问个人信息失败"
        return (succ, msg)

    def _get_js_resources(self) -> iter:
        """下载并迭代返回所有页面里的js资源，用于查找各种docid..."""
        try:
            with self._jspages_locker:
                if self._jspages_listpage is None:
                    # 拿资源列表页面
                    url = (
                            'https://www.facebook.com/ajax/bootloader-endpoint/?' +
                            'modules=NotificationList.react%2CNotificationJewelL' +
                            'ist.react%2CNotificationAsyncWrapper%2CNotification' +
                            'Store%2CNotificationJewelController%2CMercuryJewel%' +
                            '2CMercuryThreadInformer%2CMessengerState.bs%2CMesse' +
                            'ngerGraphQLThreadlistFetcher.bs%2CMercuryServerRequ' +
                            'ests%2CMercuryJewelUnreadCount.bs&' + '__user=' +
                            parse.quote_plus(self._userid) + '&__a=1&' + '__req=' +
                            self._req.get_next() + '&__be=1&' +
                            '__pc=PHASED%3Aufi_home_page_pkg&dpr=1&' + '__rev=' +
                            parse.quote_plus(self._rev) + '&fb_dtsg_ag=' +
                            parse.quote_plus(self.fb_dtsg_ag) + '&jazoest=' +
                            self.jazoest + '&__spin_r=' + parse.quote_plus(
                        self._spin_r) + '&__spin_b=' + parse.quote_plus(
                        self._spin_b) + '&__spin_t=' +
                            parse.quote_plus(self._spin_t))

                    html = self._ha.getstring(
                        url,
                        headers="""
                            accept: */*
                            accept-encoding: gzip, deflate
                            accept-language: zh-CN,zh;q=0.9
                            referer: https://www.facebook.com/""")

                    if not isinstance(html, str) or html == "":
                        self._logger.error("Get docid js pages failed.")
                        return

                    self._jspages_listpage = html

                if len(self._jspages_itemurls) < 1:
                    # 解析资源列表页面
                    matches = MessengerLogin.re_js_resoures.findall(html)
                    if matches is None or not any(matches):
                        raise Exception("Get js resources failed.")
                    for m in matches:
                        try:
                            if len(m) != 2:
                                continue
                            n = m[0]
                            u = m[1]
                            u = u.replace('\\', '')
                            if not self._jspages_itemurls.__contains__(n):
                                self._jspages_itemurls[n] = u
                        except Exception:
                            self._logger.trace(
                                "Get docid for contact parse item url error: {} {}"
                                    .format(m, traceback.format_exc()))
                    self._logger.info(
                        "Got js resources list, {} count={}".format(
                            self.uname_str, len(self._jspages_itemurls)))

                # fbcookie = self._ha._managedCookie.get_cookie_for_domain(
                #     "https://www.facebook.com/")
                # self._ha._managedCookie.add_cookies(uridocid.netloc, fbcookie)
                for jsurl in self._jspages_itemurls.items():
                    try:
                        if self._jspages.__contains__(jsurl[0]):
                            yield self._jspages[jsurl[0]]
                        else:
                            jspage = self._ha.getstring(
                                jsurl[1],
                                headers="""
                                    Origin: https://www.facebook.com
                                    Referer: https://www.facebook.com/""")

                            self._jspages[jsurl[0]] = (jsurl[1], jspage)
                            self._logger.debug("Got js resource: {} {}".format(
                                self.uname_str, jsurl[1]))
                            yield self._jspages[jsurl[0]]
                    except Exception:
                        self._logger.error(
                            "Download js resources error: {} {}".format(
                                self.uname_str, traceback.format_exc()))

        except Exception:
            self._logger.error("Get js resources error: {} {}".format(
                self.uname_str, traceback.format_exc()))

    #######################################
    def _get_js_v1(self) -> iter:
        try:
            html = self._ha.getstring('https://www.facebook.com',
                                      headers="""
                        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
                        accept-encoding: gzip, deflate
                        accept-language: en-US,en;q=0.9
                        cache-control: no-cache
                        content-type: application/x-www-form-urlencoded
                        pragma: no-cache
                        sec-fetch-mode: cors
                        sec-fetch-site: same-origin
                        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"""
                                      )
            # 先取script src直接能拿到部分
            ehtml = etree.HTML(html)
            src_list = ehtml.xpath('//script/@src')
            self._logger.info(
                "Got js resources list count={}".format(len(src_list)))
            for jsurl in src_list:
                if jsurl.startswith('https://'):
                    js = self._ha.getstring(jsurl, headers='''
                                Origin: https://www.facebook.com
                                Referer: https://www.facebook.com/
                                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36''')
                    yield js
        except Exception:
            self._logger.error(
                "Get js src error: {}".format(traceback.format_exc()))

    def _get_docid_init(self) -> bool:
        """"""
        if self.docid_init is not None:
            return True
        res: bool = False
        try:
            # LSGraphqlInitialSyncQuery
            for js in self._get_js_v1():
                try:
                    if helper_str.is_none_or_empty(js) or 'LSGraphqlInitialSyncQuery' not in js:
                        continue
                    m = MessengerLogin._re_docid_LSGraphqlInitialSyncQuery.search(js)
                    if m is not None:
                        m_docid = re.search(r'id:\s*?"(\d+)"', m.group(1))
                        if m_docid is not None:
                            self.docid_init = m_docid.group(1)
                            res = True
                            break

                except Exception:
                    self._logger.debug(
                        "Parse init message docid error: {}".format(traceback.format_exc()))

        except Exception:
            self._logger.error(
                "Get docid for init message error: {} {}".format(
                    self.uname_str, traceback.format_exc()))
        return res

    def _parse_init_js(self, js_func) -> iter:
        """处理初始消息js， 包含联系人、第一条发送消息等信息"""
        res = False
        try:
            re_js_seq = re.search(r'return LS.seq\(\[(.*?)\]\)\}', js_func)
            if re_js_seq is None:
                self._logger.error('处理js代码失败')
            req_js = re_js_seq.group(1)
            re_js_sp = re.compile(r'_=>LS.sp\((.*?)\)')
            m = re_js_sp.findall(req_js)
            if m is None:
                self._logger.error('处理js代码失败')
            for js_one in m:
                param_list = self._parse_js_one_v1(js_one)
                dict_one = dict()
                if param_list[0] == '"396"':
                    self.last_applied_cursor = param_list[4][1:-1]
                # LSMailboxDeleteThenInsertThreadStoredProcedure
                # 聊天通道
                elif param_list[0] == '"130"':
                    dict_one['type'] = 'threads'
                    dict_one['thread_id'] = self.J(self._parse_n(param_list[8]))
                    self.messenger_thread_id.append(dict_one['thread_id'])
                    #  function c(a) {
                    #         if (b("bs_caml_int64").eq(a, b("MessagingThreadType.bs").group) || b("bs_caml_int64").eq(a, b("MessagingThreadType.bs").tincanGroupDisappearing))
                    #             return !0;
                    #         else
                    #             return !1
                    #     }
                    is_group = self._parse_n(param_list[10])
                    if is_group == [0, 2] or is_group == [0, 8]:
                        dict_one['is_group'] = 1
                    else:
                        dict_one['is_group'] = 0
                    dict_one['group_name'] = param_list[4][1:-1] if param_list[4] != 'undefined' else 'undefined'
                    # 头像
                    dict_one['pic_url'] = param_list[5][1:-1].replace('\\', '') if param_list[5] != 'undefined' else 'undefined'
                # LSMailboxAddParticipantIdToGroupThreadStoredProcedure
                # 成员
                elif param_list[0] == '"40"':
                    dict_one['type'] = 'participants'
                    dict_one['thread_id'] = self.J(self._parse_n(param_list[1]))
                    dict_one['member_id'] = self.J(self._parse_n(param_list[2]))
                # 联系人会话翻页，94和135都可以，但是参数和参数位置有变化
                elif param_list[0] == '"94"':
                    if param_list[2] == 'n`2`' or param_list[3] == 'undefined':
                        self.threads_ranges_time = 0
                        self.threads_ranges_id = 0
                    else:
                        self.threads_ranges_time = self.J(self._parse_n(param_list[2]))
                        self.threads_ranges_id = self.J(self._parse_n(param_list[3]))
                # LSMailboxUpsertMessageStoredProcedure
                # 消息
                elif param_list[0] == '"123"':
                    dict_one['type'] = 'messages'
                    thread_id = self._parse_n(param_list[4])
                    dict_one['thread_id'] = self.J(thread_id)
                    dict_one['time'] = self.J(self._parse_n(param_list[6]))  # 6 or 7，还没找出差别
                    dict_one['content'] = param_list[1][1:-1]
                    dict_one['msg_id'] = param_list[9][1:-1]  # mid.$cAAAAAJQIzuh9Ih48hV28Nj1p8EeN
                    dict_one['member_id'] = self.J(self._parse_n(param_list[11]))  # 发送者的thread_id
                    dict_one['unknow'] = param_list[10][1:-1]  # 6754333178547160973不知道有用没,和请求的epoch_id有点像
                    dict_one['from_sys'] = param_list[13]  # 是否是系统消息
                # LSMailboxInsertAttachmentStoredProcedure
                elif param_list[0] == '"138"':
                    dict_one['type'] = 'attachments'
                    thread_id = self._parse_n(param_list[35])
                    dict_one['thread_id'] = self.J(thread_id)
                    dict_one['msg_id'] = param_list[38][1:-1]
                    # 如果是视频的话，第二个url是缩略图，如果是gif的话，第一个url是mp4，第二个url是gif
                    dict_one['atta_url1'] = param_list[8][1:-1].replace('\\', '') if param_list[8] != 'undefined' else 'undefined'
                    dict_one['rsc_type1'] = param_list[11][1:-1].replace('\\', '') if param_list[11] != 'undefined' else 'undefined'
                    dict_one['atta_url2'] = param_list[13][1:-1].replace('\\', '') if param_list[13] != 'undefined' else 'undefined'
                    dict_one['rsc_type2'] = param_list[16][1:-1].replace('\\', '') if param_list[16] != 'undefined' else 'undefined'
                # LSContactVerifyContactRowExistsStoredProcedure
                # 联系人或群员
                elif param_list[0] == '"533"':
                    dict_one['type'] = 'contacts'
                    thread_id = self._parse_n(param_list[1])
                    dict_one['thread_id'] = self.J(thread_id)
                    # 头像
                    dict_one['pic_url'] = param_list[3][1:-1].replace('\\', '') if param_list[3] != 'undefined' else 'undefined'
                    # 名称或备注 4 or 9 ?
                    dict_one['nick_name'] = param_list[4][1:-1]
                    # 用来提取entity_id
                    # dict_one['url'] = param_list[6]
                    # dict_one['entity_id'] = helper_str.substring(dict_one['url'], 'entity_id=', '&')
                if dict_one != {}:
                    self.js_res.append(dict_one)
            res = True
        except Exception:
            self._logger.error("Parse contacts error: {}".format(
                traceback.format_exc()))
        return res

    def _get_init_js_res(self):
        succ = False
        try:
            # 拿联系人的资源docid
            if not self._get_docid_init():
                self._logger.error(
                    "Get docid for init messages failed: {}".format(
                        self.uname_str))
                return succ
            url = 'https://www.facebook.com/api/graphql/'
            # 先抓15个联系人
            variables = '{' + f'"deviceId":"{self.device_id}","schemaVersion":"{self.schema_version}","numThreads":15,"epochId":"{self.epoch_id}"' + '}'
            postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=LSGraphqlInitialSyncQuery&variables=' + parse.quote(
                variables) + f'&doc_id={self.docid_init}'
            html = self._ha.getstring(url, postdata,
                                      headers="""
                                    accept: */*
                                    accept-encoding: gzip, deflate
                                    accept-language: en-US,en;q=0.9,zh;q=0.8
                                    content-length: {}
                                    content-type: application/x-www-form-urlencoded
                                    origin: https://www.facebook.com
                                    sec-fetch-dest: empty
                                    sec-fetch-mode: cors
                                    sec-fetch-site: same-origin
                                    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                                    """.format(len(postdata)))
            res = json.loads(html)
            if 'data' not in res or \
                    'viewer' not in res['data'] or \
                    'lightspeed_web_initial_sync_v2' not in res['data']['viewer']:
                self._logger.error("Get js function fail: {}".format(
                    self.uname_str))
                return succ
            js_func = res['data']['viewer']['lightspeed_web_initial_sync_v2']['response'][0]
            if js_func is None or js_func == '':
                self._logger.error("Get js function fail: {}".format(
                    self.uname_str))
                return succ
            res = self._parse_init_js(js_func)
            if not res:
                self._logger.error("处理初始消息js失败")
                return succ
            succ = True
        except Exception:
            self._logger.error("Get init js result failed: {}".format(
                traceback.format_exc()))
        return succ

    def _get_wss_obj(self):
        """获取一个wss实例"""
        try:
            if self.ws is not None:
                try:
                    # 收发一次消息判断连接是否断开
                    self.ws.send_binary('\xc0\x00')
                    self.ws.recv()
                    return self.ws
                except:
                    pass
            self.message_identifier = 1  # 一个递增的数字，每发送一次加1
            self.request_id = 2  # ls_rep请求的递增id，从2开始
            sid = random.randint(1000000000000000, 9999999999999999)
            wss_uri = 'wss://edge-chat.facebook.com/chat?region=prn&sid={}&cid={}'.format(
                sid, self.device_id
            )
            ws = websocket.create_connection(wss_uri,
                                             timeout=10,
                                             host='edge-chat.facebook.com',
                                             origin='https://www.facebook.com',
                                             # http_proxy_host='192.168.90.45',
                                             # http_proxy_port=10809,
                                             cookie=self.task.cookie)
            # fst = f'\x10\x90\x02\x00\x06MQIsdp\x03\x82\x00\x0a\x00\x0cmqttwsclient\x00\xf4{{"u":"{self._userid}","s":{sid},"cp":3,"ecp":10,"chat_on":true,"fg":true,"d":"{self.device_id}","ct":"websocket","mqtt_sid":"","aid":{self.aid},"st":[],"pm":[],"dc":"","no_auto_fg":true,"gas":null,"pack":[]}}'
            payload = f'{{"u":"{self._userid}","s":{sid},"cp":3,"ecp":10,"chat_on":true,"fg":true,"d":"{self.device_id}","ct":"websocket","mqtt_sid":"","aid":{self.aid},"st":[],"pm":[],"dc":"","no_auto_fg":true,"gas":null,"pack":[]}}'
            msg1 = self._build_connect_request(payload)
            ws.send_binary(msg1)
            res = ws.recv()
            if res != b' \x02\x00\x00':
                self._logger.error('websocket connect failed!')
                return
            # 这个请求可以写死
            ws.send_binary('\x82\r\x00\t\x00\x08/ls_resp\x00')
            # 试了下随机数也可以，先写个大概范围内
            epoch_id = random.randint(6753201641581840000, 6755042416160449999)
            # ws.send_binary(
            #     f'2\xfb\x01\x00\x07/ls_req\x00\x10{{"request_id":8,"type":2,"payload":"{{\\"database\\":1,\\"version\\":{self.schema_version},\\"epoch_id\\":{epoch_id},\\"last_applied_cursor\\":\\"{self.last_applied_cursor}\\",\\"failure_count\\":null,\\"sync_params\\":null}}","app_id":"{self.appid}"}}')
            payload = f'{{"request_id":{self.request_id},"type":2,"payload":"{{\\"database\\":1,\\"version\\":{self.schema_version},\\"epoch_id\\":{epoch_id},\\"last_applied_cursor\\":\\"{self.last_applied_cursor}\\",\\"failure_count\\":null,\\"sync_params\\":null}}","app_id":"{self.appid}"}}'
            msg2 = self._build_ls_req_request(payload)
            ws.send_binary(msg2)
            # 返回的数据有对应的"request_id"才算成功，不然之后请求返回的不全
            succ = False
            while True:
                try:
                    res = ws.recv()
                    # self._logger.debug(res)
                    if f'"request_id":{self.request_id}' in res.decode('latin1'):
                        succ = True
                except:
                    break
            if succ:
                self.message_identifier += 1
                self.request_id += 1
                re_js_sp = re.compile(r'LS.seq\(\[_=>LS.sp\((\\"396\\",.*?)\)')
                m = re_js_sp.search(res.decode('latin1'))
                # wss断开重连可能没有396标识的方法
                if m is not None:
                    param_list = [i.strip() for i in m.group(1).split(',')]
                    self.last_applied_cursor = param_list[4].replace('\\"', '')
                self.ws = ws
                return self.ws
        except:
            self._logger.error(f'websocket connect failed: {self._username}')
        return None

    def _build_connect_request(self, payload):
        """构建wss建立连接后的第一条请求"""
        # c.encode = function() {
        #             var a = (this.messageType & 15) << 4   messageType是1，枚举值
        #               , b = q.length + 3;
        #             b += g(this.clientId) + 2;
        #             b += g(this.connectOptions.userName) + 2;
        #             var c = k(b);
        #             b = new ArrayBuffer(1 + c.length + b);
        #             var d = new Uint8Array(b);
        #             d[0] = a;
        #             a = 1;
        #             d.set(c, 1);
        #             a += c.length;
        #             d.set(q, a);
        #             a += q.length;
        #             c = 2 | 128;
        #             d[a++] = c;
        #             a = n(this.connectOptions.keepAliveInterval, d, a);
        #             a = m(this.clientId, g(this.clientId), d, a);
        #             a = m(this.connectOptions.userName, g(this.connectOptions.userName), d, a);
        #             return b
        #         }
        def k(a):
            b = []
            for _ in range(4):
                d = a % 128
                a = a // 128
                if a > 0:
                    b.append(d | 128)
                else:
                    b.append(d)
                    break
            return b
        # 固定字段
        q = [0, 6, 77, 81, 73, 115, 100, 112, 3]
        a = 16
        b = len(q) + 3
        b += len('mqttwsclient') + 2
        b += len(payload) + 2
        c = k(b)
        d = [a]
        d.extend(c)
        d.extend(q)
        c = 2 | 128
        d.append(c)
        d.append(10 >> 8)
        d.append(10 % 256)
        d.append(len('mqttwsclient') >> 8)
        d.append(len('mqttwsclient') % 256)
        for i in 'mqttwsclient':
            d.append(ord(i))
        d.append(len(payload) >> 8)
        d.append(len(payload) % 256)
        res = ''
        for i in d:
            res += chr(i)
        res += payload
        return res

    def _build_ls_req_request(self, payload):
        """构造ls_req请求"""
        # c.encode = function() {
        #     var a = (this.messageType & 15) << 4;
        #     this.duplicate && (a |= 8);
        #     a = a |= this.qos << 1;
        #     this.retained && a != 1;
        #     var b = g(this.topic)
        #       , c = b + 2
        #       , d = this.qos === 0 ? 0 : 2;
        #     c += d;
        #     d = this.payloadMessage.bytes();
        #     c += d.byteLength;
        #     var e = k(c);
        #     c = new ArrayBuffer(1 + e.length + c);
        #     var f = new Uint8Array(c);
        #     f[0] = a;
        #     f.set(e, 1);
        #     a = 1 + e.length;
        #     a = m(this.topic, b, f, a);
        #     this.qos !== 0 && this.messageIdentifier != null && (a = n(this.messageIdentifier, f, a));
        #     f.set(d, a);
        #     return c
        # }
        def k(a):
            b = []
            for _ in range(4):
                d = a % 128
                a = a // 128
                if a > 0:
                    b.append(d | 128)
                else:
                    b.append(d)
                    break
            return b
        # CONNACK: 2 CONNECT: 1 DISCONNECT: 14 PINGREQ: 12 PINGRESP: 13 PUBACK: 4 PUBLISH: 3 SUBACK: 9 SUBSCRIBE: 8 UNSUBACK: 11 UNSUBSCRIBE: 10
        messagetype = 3
        a = (messagetype & 15) << 4
        a = a | 2
        b = len('/ls_req')
        c = b + 2
        d = 2
        c += d
        c += len(payload)
        e = k(c)
        f = [a]
        f.extend(e)
        f.append(len('/ls_req') >> 8)
        f.append(len('/ls_req') % 256)
        for i in '/ls_req':
            f.append(ord(i))
        f.append(self.message_identifier >> 8)
        f.append(self.message_identifier % 256)
        res = ''
        for i in f:
            res += chr(i)
        res += payload
        return res
