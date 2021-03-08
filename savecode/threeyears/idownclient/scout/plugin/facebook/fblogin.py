"""facebook login"""

# -*- coding:utf-8 -*-

import os
import re
import threading
import time
import traceback
from sys import platform
from typing import Tuple
from urllib import parse
from lxml import etree
import base64

from commonbaby.helpers import helper_crypto, helper_str, helper_time
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from commonbaby.mslog import MsLogManager, MsLogger, MsLogLevel, MsLogLevels
from datacontract.iscoutdataset import IscoutTask

from .fbbase import FbBase
from ....config_spiders import webdriver_path_debian, webdriver_path_win

logger = MsLogManager.get_logger("ChromeDriverInit")


class FBLogin(FbBase):
    """facebook login"""

    #https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    _loginlocker = threading.RLock()
    _is_logined: bool = False

    _driver: webdriver.Chrome = None
    _driver_path: str = None

    #
    # <label class="login_form_login_button uiButton uiButtonConfirm" id="loginbutton" for="u_0_2">
    #   <input value="Log In" aria-label="Log In" data-testid="royal_login_button" type="submit" id="u_0_2">
    # </label>
    _re_login_submit_button = re.compile(
        r'<label class=.*?id="loginbutton".*?>\s*?<input value="Log In".*?type="submit" id="([^"]+?)">',
        re.S | re.M)

    # "/bluebar/modern_settings_menu/?help_type=364455653583099&show_contextual_help=1",
    _re_helptype = re.compile(
        r'"/bluebar/modern_settings_menu/?help_type=(\d+)&show_contextual_help=1',
        re.S | re.M)

    _CK_KEY: str = "!((@)*@%)ASDasd1"
    # _a: str = "+97696481722"
    _a: str = "+97696481722"
    # _a: str = helper_crypto.aes_decrypt(_CK_KEY,
    #                                     helper_str.base64_decode_to_bytes(_a))
    # _p: str = "y9sulU7T7Qj"
    _p: str = "y9sulU7T7Qj"
    # _p: str = helper_crypto.aes_decrypt(_CK_KEY,
    #                                     helper_str.base64_decode_to_bytes(_p))

    _CK_SAVE_PATH: str = os.path.abspath(os.path.join("./resource/_fb/ck"))

    _class_logined_cookie_save: str = None

    ##################################################################
    # 新版docid集合，存在类属性里面，以免每次实例化要重新请求
    _docid_dict: dict = {}
    _docid_dict_locker = threading.RLock()
    # 新版取docid需要的正则表达式
    # "JXLs8": {
    #          "type": "js",
    #          "src": "https:\/\/static.xx.fbcdn.net\/rsrc.php\/v3\/yc\/r\/FGkOza0ZGEn.js?_nc_x=FaAZoUIvrE1",
    #          "p": ":272"
    #          }
    # '\/6SdB': {.....}
    _re_js_src = re.compile(
        r'"([^"]{5,6})"\s*?:\s*?{\s*?"type"\s*?:\s*?"js"\s*?,\s*?"src"\s*?:\s*?"([^"]+?)",.*?}',
        re.S)

    # 最外层是__d("UFI2CommentsProviderPaginationQuery.graphql"
    # params: {
    #     id: "4629548627085906",
    #     metadata: {},
    #     name: "UFI2CommentsProviderPaginationQuery",
    #     operationKind: "query",
    #     text: null
    # }
    _re_docid_ProfileCometTimelineFeedRefetchQuery = re.compile(
        r'__d\("ProfileCometTimelineFeedRefetchQuery.graphql".*?params:\s*?(.*?name:\s*?"ProfileCometTimelineFeedRefetchQuery".*?\s*?})',
        re.S)
    # 这个稍微有点不一样
    _re_docid_CometUFIReactionsDialogQuery = re.compile(
        r'__d\("CometUFIReactionsDialogQuery\$Parameters".*?params:\s*?(.*?name:\s*?"CometUFIReactionsDialogQuery".*?\s*?})',
        re.S)
    _re_docid_CometUFIReactionsDialogTabContentRefetchQuery = re.compile(
        r'__d\("CometUFIReactionsDialogTabContentRefetchQuery.graphql".*?params:\s*?(.*?name:\s*?"CometUFIReactionsDialogTabContentRefetchQuery".*?\s*?})',
        re.S)
    _re_docid_CometUFICommentsProviderPaginationQuery = re.compile(
        r'__d\("CometUFICommentsProviderPaginationQuery.graphql".*?params:\s*?(.*?name:\s*?"CometUFICommentsProviderPaginationQuery".*?\s*?})',
        re.S)
    _re_docid_ProfileCometTopAppSectionQuery = re.compile(
        r'__d\("ProfileCometTopAppSectionQuery.graphql".*?params:\s*?(.*?name:\s*?"ProfileCometTopAppSectionQuery".*?\s*?})',
        re.S)
    _re_docid_ProfileCometAppCollectionListRendererPaginationQuery = re.compile(
        r'__d\("ProfileCometAppCollectionListRendererPaginationQuery.graphql".*?params:\s*?(.*?name:\s*?"ProfileCometAppCollectionListRendererPaginationQuery".*?\s*?})',
        re.S)
    _re_docid_SearchCometResultsInitialResultsQuery = re.compile(
        r'__d\("SearchCometResultsInitialResultsQuery.graphql".*?params:\s*?(.*?name:\s*?"SearchCometResultsInitialResultsQuery".*?\s*?})',
        re.S)
    _re_docid_SearchCometResultsPaginatedResultsQuery = re.compile(
        r'__d\("SearchCometResultsPaginatedResultsQuery.graphql".*?params:\s*?(.*?name:\s*?"SearchCometResultsPaginatedResultsQuery".*?\s*?})',
        re.S)
    _re_docid_ProfileCometAboutAppSectionQuery = re.compile(
        r'__d\("ProfileCometAboutAppSectionQuery\$Parameters".*?params:\s*?(.*?name:\s*?"ProfileCometAboutAppSectionQuery".*?\s*?})',
        re.S)

    def __init__(self, task: IscoutTask):
        FbBase.__init__(self, task, loggername="ScoutFacebook")

        self._cookie: str = None

        if FBLogin._is_logined:
            self._ha._managedCookie.add_cookies(
                "facebook.com", FBLogin._class_logined_cookie_save)
            succ, msg = self._refresh_neccessary_fields()
            if not succ:
                self._logger.error(
                    "Facebook pre-login failed.1:msg={}".format(msg))
            return
        with FBLogin._loginlocker:
            if FBLogin._is_logined:
                self._ha._managedCookie.add_cookies(
                    "facebook.com", FBLogin._class_logined_cookie_save)
                return
            if self.__fb_pre_login():
                FBLogin._is_logined = True
                FBLogin._class_logined_cookie_save = self._ha._managedCookie.get_all_cookie(
                )
                self._logger.info(
                    "Facebook pre-account login succeed: {}({})".format(
                        self._username, self._userid))
            else:
                self._outprglog("Facebook预置账号登录失败")
                self._logger.error("Facebook pre-account login failed")

    def __init_driver(self):
        chrome_options = ChromeOptions()
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('blink-settings=imagesEnabled=false')
        chrome_options.add_argument('lang=en_US.UTF-8')
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36'
        )
        chrome_options.add_argument('log-level=3')
        #info(default) = 0
        #warning = 1
        #LOG_ERROR = 2
        #LOG_FATAL = 3

        chrome_options.add_argument('--no-sandbox')
        try:
            if platform == 'linux' or platform == 'linux2':
                self._driver_path = webdriver_path_debian
            elif platform == 'win32':
                self._driver_path = webdriver_path_win

            self._driver: webdriver.Chrome = webdriver.Chrome(
                executable_path=self._driver_path,
                chrome_options=chrome_options,
            )
            self._driver.set_page_load_timeout(30)
            self._driver.set_script_timeout(30)
            self._driver.implicitly_wait(30)

        except Exception:
            logger.error(traceback.format_exc())

    def __fb_pre_login(self):
        self._logger.info("Facebook pre-account logining...")

        logined: bool = False
        if os.path.isfile(self._CK_SAVE_PATH):
            eck: bytes = None
            with open(self._CK_SAVE_PATH, mode='r') as fs:
                eck = fs.read()
            if not eck is None and eck != "":
                # self._cookie = helper_crypto.aes_decrypt(self._CK_KEY, eck)
                self._cookie = eck
                logined = self._cookie_login_(self._cookie)

        if not logined:
            if os.path.isfile(self._CK_SAVE_PATH):
                os.remove(self._CK_SAVE_PATH)
            logined = self._login_pass(FBLogin._a, FBLogin._p)

        if logined:
            # save ck to fi
            if os.path.isfile(self._CK_SAVE_PATH):
                os.remove(self._CK_SAVE_PATH)
            di = os.path.dirname(self._CK_SAVE_PATH)
            if not os.path.isdir(di):
                os.makedirs(di)
            self._cookie = self._ha._managedCookie.get_all_cookie()
            with open(self._CK_SAVE_PATH, mode='w') as fs:
                # tmp = helper_crypto.aes_encrypt(self._CK_KEY, self._cookie)
                fs.write(self._cookie)

        return logined

    def _cookie_login_(self, cookie: str) -> bool:
        """用cookie登陆尝试"""
        res: bool = False
        try:
            if not isinstance(cookie, str) or cookie == "":
                return res
            self._ha._managedCookie.add_cookies(".facebook.com", cookie)

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
            self._logger.error("Cookie login error:%s" %
                               traceback.format_exc())
        return res

    def _login_pass(self, acc: str, pwd: str) -> bool:
        """"""
        res: bool = False
        try:

            self.__init_driver()

            self._driver.get('https://www.facebook.com/')

            eact = self._driver.find_element_by_id("email")
            if eact is None:
                self._logger.error("Account text box not found")
                return res
            eact.click()
            eact.send_keys(acc)

            epwd = self._driver.find_element_by_id("pass")
            if epwd is None:
                self._logger.error("Password text box not found")
                return res
            epwd.click()
            epwd.send_keys(pwd)

            esbm = self._driver.find_element_by_name("login")
            if esbm is None:
                self._logger.error("Submit button not found")
                return res
            esbm.click()
            time.sleep(2)

            if self._driver.page_source is None or not acc in self._driver.page_source:
                self._logger.error(
                    "Facebook pass login failed, acc not in page")
                return res

            cks = self._driver.get_cookies()
            for ck in cks:
                dm = ck["domain"]
                name = ck["name"]
                val = ck["value"]
                self._ha._managedCookie.add_one_cookie(
                    dm, '{}={};'.format(name, val))
            self._cookie = self._ha._managedCookie.get_all_cookie()

            res, msg = self._refresh_neccessary_fields()
            if not res:
                self._logger.error(
                    "Pre-set account refresh neccessary fields failed: {}".
                    format(msg))
                return res

            res, msg = self._access_profile()
            if not res:
                self._logger.error(
                    "Pre-set account access profile failed: {}".format(msg))
                return res

            if not isinstance(self._host, str) or self._host == "":
                self._host = 'facebook.com'

            res = True

        except Exception:
            res = False
            self._logger.error(
                "Facebook pre-set account pass login error: {}".format(
                    traceback.format_exc()))
        finally:
            if not self._driver is None:
                self._driver.close()
        return res

    def _refresh_neccessary_fields(self) -> Tuple[bool, str]:
        """refresh neccessary fields from homepage"""
        succ: bool = False
        msg: str = None
        try:
            # facebook
            url = "https://www.facebook.com/"
            homepage = self._ha.getstring(url,
                                          headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                upgrade-insecure-requests: 1""")
            if homepage is None or homepage == "":
                raise Exception("Get userid failed")
            self.homepage = homepage

            # 旧版 {"ajaxpipe_token":"AXirhyvLf1-VYeYT", 新版没有这个参数
            succ, self.ajaxpipe_token = helper_str.substringif(
                homepage, '"ajaxpipe_token":"', '"')
            if not succ or self.ajaxpipe_token is None or self.ajaxpipe_token == "":
                self.is_new_facebook = True

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
            # 旧版
            if not self.is_new_facebook:
                succ, self.fb_dtsg = self._get_fb_dtsg(homepage)
                if not succ or self.fb_dtsg is None or self.fb_dtsg == "":
                    raise Exception("fb_dtsg not found")
                # <input type="hidden" name="jazoest" value="26581721051157310249955787119586581729011111169104674510655" autocomplete="off" />
                succ, self.jazoest = helper_str.substringif(
                    homepage, 'name="jazoest" value="', '"')
                if not succ or self.jazoest is None or self.jazoest == "":
                    raise Exception("jazoest not found")

                # messenger
                url = "https://www.messenger.com/"  # login.php
                html = self._ha.getstring(url,
                                          headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                cache-control: no-cache
                pragma: no-cache
                upgrade-insecure-requests: 1
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36
                """)
                if html is None or html == "":
                    raise Exception("Refresh messenger neccessary fields failed")
                # //"pkg_cohort":"PHASED:messengerdotcom_pkg"
                # //post data
                succ, self._pc = helper_str.substringif(html, 'pkg_cohort":"', '"')
                if not succ:
                    raise Exception("_pc not found")
                # //{"server_revision":4201737,
                # //post data
                succ, self._rev = helper_str.substringif(html, 'server_revision":',
                                                         ',')
                if not succ:
                    raise Exception("__rev not found")
                # //<input type="hidden" name="lsd" value="AVoa4_T_" autocomplete="off" />
                # //post data
                succ, self.lsd = helper_str.substringif(html, 'name="lsd" value="',
                                                        '"')
                if not succ:
                    raise Exception("lsd not found")
                # ["QuicklingConfig",[],{version:"4250897;0;"
                succ, self.quickling_ver = helper_str.substringif(
                    html, '"QuicklingConfig",[],{version:"', '"')
                if not succ or self.quickling_ver is None or self.quickling_ver == "":
                    raise Exception("quickling_ver not found")
            # 新版
            else:
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

            succ = True
            msg = "Refresh neccessary fields succeed"
        except Exception:
            self._logger.error(
                "Refresh neccessary fields from homepage error, taskid:%s\nphone:%s\nex:%s"
                % (self.task.taskid, self.phone, traceback.format_exc()))
            succ = False
            msg = "Refresh neccessary fields failed"
        return (succ, msg)

    def _get_fb_dtsg(self, homepage) -> Tuple[bool, str]:
        succ: bool = False
        # <input type="hidden" name="fb_dtsg" value="AQHisIf1_9Ww:AQHZooEhC-j7" autocomplete="off" />
        succ, self.fb_dtsg = helper_str.substringif(homepage,
                                                    'name="fb_dtsg" value="',
                                                    '"')
        if succ and not self.fb_dtsg is None and self.fb_dtsg != "":
            return (succ, self.fb_dtsg)

        # ,["DTSGInitialData",[],{"token":"AQHc2zLY6NK2:AQF8SDhi9rv1"},258]
        # ["DTSGInitialData",[],{},258],
        succ, self.fb_dtsg = helper_str.substringif(
            homepage, '["DTSGInitialData",[],{"token":"', '"}')
        if succ and not self.fb_dtsg is None and self.fb_dtsg != "":
            return (succ, self.fb_dtsg)

        if not homepage.__contains__('modern_settings_menu'):
            raise Exception("Get menu param fb_dtsg failed")

        m: re.Match = self._re_helptype.match(self.homepage)
        if m is None:
            raise Exception("Get menu param fb_dtsg failed1")

        urlmenu = 'https://www.facebook.com' + m.group(0)
        data = ('')
        htmlmenu = self._ha.getstring(urlmenu, )
        return (succ, self.fb_dtsg)

    def _access_profile(self) -> Tuple[bool, str]:
        """access simple profile"""
        succ = False
        msg = None
        try:
            url = "https://www.facebook.com/"
            html = self._ha.getstring(url,
                                      headers="""
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                cache-control: no-cache
                referer: https://www.facebook.com/
                upgrade-insecure-requests: 1
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36"""
                                      )
            if html is None or html == "":
                raise Exception("Get profile page failed")
            # {"USER_ID":"100027859862248","ACCOUNT_ID":"100027859862248",
            # "NAME":"San Zhang","SHORT_NAME":"San Zhang","IS_MESSENGER_ON
            # LY_USER":false,"IS_DEACTIVATED_ALLOWED_ON_MESSENGER":false}
            succ, self._userid = helper_str.substringif(
                html, 'USER_ID":"', '"')
            if not succ or self._userid is None or self._userid == "":
                succ, self._userid = helper_str.substring(
                    html, 'user_id:"', '"')
                if not succ or self._username is None or self._username == "":
                    msg = "访问个人信息失败"
                    return (succ, msg)
            succ, self._username = helper_str.substringif(html, 'NAME":"', '"')
            if not succ or self._username is None or self._username == "":
                succ, self._username = helper_str.substring(
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
            self._logger.error("Access profile error:%s" %
                               traceback.format_exc())
            succ = False
            msg = "访问个人信息失败"
        return (succ, msg)

    def _get_js_resources(self) -> iter:
        """下载并迭代返回所有页面里的js资源，用于查找各种docid..."""
        try:
            html = None
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
                        parse.quote_plus(self._userid) + '&_a=1&' + '__req=' +
                        self._req.get_next() + '&__be=1&' +
                        '_pc=PHASED%3Aufi_home_page_pkg&dpr=1&' + '__rev=' +
                        parse.quote_plus(self._rev) + '&fb_dtsg_ag=' +
                        parse.quote_plus(self.fb_dtsg_ag) + '&jazoest=' +
                        self.jazoest + '&__spin_r=' +
                        parse.quote_plus(self._spin_r) + '&__spin_b=' +
                        parse.quote_plus(self._spin_b) + '&__spin_t=' +
                        parse.quote_plus(self._spin_t))

                    html = self._ha.getstring(url,
                                              headers="""
                            accept: */*
                            accept-encoding: gzip, deflate
                            accept-language: zh-CN,zh;q=0.9
                            referer: https://www.facebook.com/""")

                    if not isinstance(html, str) or html == "":
                        self._logger.error("Get docid js pages failed")
                        return

                    self._jspages_listpage = html

                if len(self._jspages_itemurls) < 1:
                    # 解析资源列表页面
                    matches = self.re_js_resoures.findall(html)
                    if matches is None or not any(matches):
                        raise Exception("Get js resources failed")
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
                            jspage = self._ha.getstring(jsurl[1],
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

    def _get_js_v1(self):
        """
        新版facebook获取js的方法
        分别从bulk-route-definitions请求 和 html源码里面遍历js
        从bulk-route-definitions中取（只有html里面没有的js才用这个去补充）
        """
        try:
            # 请求bulk-route-definitions，缺哪些请求哪些
            path = self._host[len('https://www.facebook.com'):]
            # 统一去掉结尾/,方便处理
            if path.endswith('/'):
                path = path[:-1]
            # https://www.facebook.com/profile.php?id=100010123548628&sk=friends
            if self._host.startswith('https://www.facebook.com/profile.php?id='):
                route_url = f'route_urls[0]={parse.quote_plus(path+"&sk=friends")}&route_urls[1]={parse.quote_plus("/search/people/")}'
            # https://www.facebook.com/bichhau.bui.5249/friends
            else:
                route_url = f'route_urls[0]={parse.quote_plus(path + "/friends")}&route_urls[1]={parse.quote_plus("/search/people/")}'
            url = 'https://www.facebook.com/ajax/bulk-route-definitions/'
            postdata = route_url + '&' + f'__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}'
            html = self._ha.getstring(url, postdata,
                                      headers="""
            accept: */*
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9
            content-type: application/x-www-form-urlencoded
            origin: https://www.facebook.com
            referer: {}
            sec-fetch-dest: empty
            sec-fetch-mode: cors
            sec-fetch-site: same-origin
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
            """.format(self._host))
            js_src_dict = dict()
            matches = FBLogin._re_js_src.findall(html)
            if matches is None or not any(matches):
                raise Exception("Get js src failed")
            for m in matches:
                try:
                    if len(m) != 2:
                        continue
                    n = m[0]
                    u = m[1]
                    u = u.replace('\\', '')
                    if not js_src_dict.__contains__(n):
                        js_src_dict[n] = u
                except Exception:
                    self._logger.trace("Parse js src error: {} {}".format(m, traceback.format_exc()))
            self._logger.info(
                "Got js resources list count={}".format(len(js_src_dict)))
            for jsurl in js_src_dict.values():
                js = self._ha.getstring(jsurl, headers='''
                                    Origin: https://www.facebook.com
                                    Referer: https://www.facebook.com/
                                    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36''')
                yield js

            # 从目标主页取js
            html = self._ha.getstring(self._host,
                                      headers="""
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9
            cache-control: no-cache
            content-type: application/x-www-form-urlencoded
            origin: https://www.facebook.com
            pragma: no-cache
            referer: https://www.facebook.com/search/people/?q={}&epa=SERP_TAB
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
                # 有一部分是base64编码的js代码
                if jsurl.startswith('https://'):
                    js = self._ha.getstring(jsurl, headers='''
                    Origin: https://www.facebook.com
                    Referer: https://www.facebook.com/
                    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36''')
                    yield js
                else:
                    js_b64 = jsurl.split(',')[-1]
                    js = base64.b64decode(js_b64).decode()
                    yield js
            # 取js代码里面的js
            js_src_dict = dict()
            matches = FBLogin._re_js_src.findall(html)
            if matches is None or not any(matches):
                raise Exception("Get js src failed")
            for m in matches:
                try:
                    if len(m) != 2:
                        continue
                    n = m[0]
                    u = m[1]
                    u = u.replace('\\', '')
                    if not js_src_dict.__contains__(n):
                        js_src_dict[n] = u
                except Exception:
                    self._logger.trace("Parse js src error: {} {}".format(m, traceback.format_exc()))
            self._logger.info(
                "Got js resources list count={}".format(len(js_src_dict)))
            for jsurl in js_src_dict.values():
                # 有一部分是base64编码的js代码
                if jsurl.startswith('https://'):
                    js = self._ha.getstring(jsurl, headers='''
                                        Origin: https://www.facebook.com
                                        Referer: https://www.facebook.com/
                                        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36''')
                    yield js
                else:
                    js_b64 = jsurl.split(',')[-1]
                    js = base64.b64decode(js_b64).decode()
                    yield js
        except Exception:
            self._logger.error(
                "Get js src error: {}".format(traceback.format_exc()))

    def _get_docid_dict(self) -> dict:
        """
        新版facebook获取必要的docid字段
        """
        try:
            # ProfileCometTimelineFeedRefetchQuery 推文获取
            # CometUFIReactionsDialogQuery 点赞页面获取
            # CometUFIReactionsDialogTabContentRefetchQuery 点赞翻页
            # CometUFICommentsProviderPaginationQuery 展开折叠的评论
            # ProfileCometAppCollectionListRendererPaginationQuery 好友页面翻页(这个单独请求)
            # ProfileCometTopAppSectionQuery 好友页面获取
            # SearchCometResultsInitialResultsQuery 搜索用户
            # SearchCometResultsPaginatedResultsQuery 搜索用户翻页
            # ProfileCometAboutAppSectionQuery 用户简介
            if FBLogin._docid_dict != {} and len(FBLogin._docid_dict) >= 8:
                return FBLogin._docid_dict

            with FBLogin._docid_dict_locker:
                # 访问非本号的个人页面能找到全部9个参数，但是还是从self._host里面取的，剩下一个用的时候单独请求
                for js in self._get_js_v1():
                    try:
                        if len(FBLogin._docid_dict) == 8:
                            return FBLogin._docid_dict

                        # params: {
                        #     id: "4629548627085906", # 取这个id
                        #     metadata: {},
                        #     name: "UFI2CommentsProviderPaginationQuery", # 不同请求名字不一样
                        #     operationKind: "query",
                        #     text: null
                        # }
                        if not js.__contains__('ProfileCometTimelineFeedRefetchQuery') and \
                            not js.__contains__('CometUFIReactionsDialogQuery') and \
                                not js.__contains__('CometUFIReactionsDialogTabContentRefetchQuery') and \
                                not js.__contains__('CometUFICommentsProviderPaginationQuery') and \
                                not js.__contains__('ProfileCometAppCollectionListRendererPaginationQuery') and \
                                not js.__contains__('ProfileCometTopAppSectionQuery') and \
                                not js.__contains__('SearchCometResultsInitialResultsQuery') and \
                                not js.__contains__('SearchCometResultsPaginatedResultsQuery') and \
                                not js.__contains__('ProfileCometAboutAppSectionQuery'):
                            continue

                        if js.__contains__('ProfileCometTimelineFeedRefetchQuery'):
                            m = FBLogin._re_docid_ProfileCometTimelineFeedRefetchQuery.search(js)
                            if not m is None:
                                docid = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                                FBLogin._docid_dict['ProfileCometTimelineFeedRefetchQuery'] = docid

                        if js.__contains__('CometUFIReactionsDialogQuery'):
                            m = FBLogin._re_docid_CometUFIReactionsDialogQuery.search(js)
                            if not m is None:
                                docid = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                                FBLogin._docid_dict['CometUFIReactionsDialogQuery'] = docid

                        if js.__contains__('CometUFIReactionsDialogTabContentRefetchQuery'):
                            m = FBLogin._re_docid_CometUFIReactionsDialogTabContentRefetchQuery.search(js)
                            if not m is None:
                                docid = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                                FBLogin._docid_dict['CometUFIReactionsDialogTabContentRefetchQuery'] = docid

                        if js.__contains__('CometUFICommentsProviderPaginationQuery'):
                            m = FBLogin._re_docid_CometUFICommentsProviderPaginationQuery.search(js)
                            if not m is None:
                                docid = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                                FBLogin._docid_dict['CometUFICommentsProviderPaginationQuery'] = docid

                        if js.__contains__('ProfileCometTopAppSectionQuery'):
                            m = FBLogin._re_docid_ProfileCometTopAppSectionQuery.search(js)
                            if not m is None:
                                docid = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                                FBLogin._docid_dict['ProfileCometTopAppSectionQuery'] = docid

                        if js.__contains__('ProfileCometAppCollectionListRendererPaginationQuery'):
                            m = FBLogin._re_docid_ProfileCometAppCollectionListRendererPaginationQuery.search(js)
                            if not m is None:
                                docid = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                                FBLogin._docid_dict['ProfileCometAppCollectionListRendererPaginationQuery'] = docid

                        if js.__contains__('SearchCometResultsInitialResultsQuery'):
                            m = FBLogin._re_docid_SearchCometResultsInitialResultsQuery.search(js)
                            if not m is None:
                                docid = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                                FBLogin._docid_dict['SearchCometResultsInitialResultsQuery'] = docid

                        if js.__contains__('SearchCometResultsPaginatedResultsQuery'):
                            m = FBLogin._re_docid_SearchCometResultsPaginatedResultsQuery.search(js)
                            if not m is None:
                                docid = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                                FBLogin._docid_dict['SearchCometResultsPaginatedResultsQuery'] = docid

                        if js.__contains__('ProfileCometAboutAppSectionQuery'):
                            m = FBLogin._re_docid_ProfileCometAboutAppSectionQuery.search(js)
                            if not m is None:
                                docid = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                                FBLogin._docid_dict['ProfileCometAboutAppSectionQuery'] = docid

                    except Exception:
                        self._logger.error(
                            "Access docid for more comments in one js file error: {}"
                            .format(traceback.format_exc()))

        except Exception:
            self._logger.error(
                "Access docid for more comments error: {}".format(
                    traceback.format_exc()))
