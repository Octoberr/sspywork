"""messenger logout"""

# -*- coding:utf-8 -*-

import traceback
from urllib import parse

from commonbaby.helpers import helper_str

from datacontract.idowndataset import Task
from .messengerlogin import MessengerLogin


class MessengerLogout(MessengerLogin):
    """messenger logout"""

    def __init__(self, task: Task, appcfg, clientid):
        MessengerLogin.__init__(self, task, appcfg, clientid)

    def _logout(self) -> bool:
        """logout"""
        res: bool = False
        try:
            # 相当于必须先重新登陆一下，拿一下主页和必要参数字段。。
            res, msg = self._refresh_neccessary_fields()
            if not res:
                self._logger.error(
                    "It may is already logout state currently, due to get param failed. user={}"
                        .format(self.uname_str))
                return res

            # 主页里拿一个参数
            # ,"setHelpType",[],[364455653583099]] 或
            # ,"/bluebar/modern_settings_menu/?help_type=364455653583099&show_contextual_help=1"
            helptype = ''
            succ, helptype = helper_str.substringif(
                self.homepage, '/bluebar/modern_settings_menu/?help_type=',
                '&')
            if not succ:
                succ, helptype = helper_str.substringif(
                    self.homepage, '\"setHelpType\",[],[', ']')
            if not succ or helptype is None or helptype == '':
                self._logger.error(
                    "Param 'helptype' not found: user={}".format(
                        self.uname_str))
                return res

            # 属表移到顶部菜单栏触碰时，会触发一个菜单栏html动态加载:
            # 拿参数h，jazoest等
            # autocomplete=\"off\" name=\"h\" value=\"AfduFV_U3PMJdr4b\" \/>\u003C
            url = 'https://www.facebook.com/bluebar/modern_settings_menu/?help_type={}&show_contextual_help=1'.format(
                helptype)
            # pmid=0&__user=100027859862248&__a=1&__req=12&__be=1&
            # __pc=PHASED%3Aufi_home_page_pkg&dpr=1&
            # __rev=1000539655&fb_dtsg=AQFHBj8zGV6M%3AAQHJdLD-nebQ&
            # jazoest=21955&__spin_r=1000539655&__spin_b=trunk&
            # __spin_t=1553744049
            data = (
                    'pmid=0&__user=' + self._userid + '&__a=1&__req=' +
                    self._req.get_next() +
                    '&__be=1&__pc=PHASED%3Aufi_home_page_pkg&dpr=1' + '&__rev=' +
                    # 这个__rev=要用__spin_r
                    self._spin_r + '&fb_dtsg=' + parse.quote_plus(
                self.fb_dtsg) + '&jazoest=' + self.jazoest + '&__spin_r=' +
                    self._spin_r + '&__spin_b=trunk&__spin_t=' + self._spin_t)
            html = self._ha.getstring(
                url,
                req_data=data,
                headers='''
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: zh-CN,zh;q=0.9
                cache-control: no-cache
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                pragma: no-cache
                referer: https://www.facebook.com/''',
            )

            # {"__html":"\u003Cform class=\"_w0d _w0d\"
            # action=\"https:\/\/www.facebook.com\/login\/
            # device-based\/regular\/logout\/?button_name=
            # logout&amp;button_location=settings\" data-n
            # ocookies=\"1\" id=\"u_m_3\" method=\"post\"
            # onsubmit=\"\">\u003Cinput type=\"hidden\"
            # name=\"jazoest\" value=\"22125\"
            # autocomplete=\"off\" \/>\u003Cinput type=\"hidden\"
            # name=\"fb_dtsg\" value=\"AQEjVSxhw9hB:AQERcXYelK4b\"
            # autocomplete=\"off\" \/>\u003Cinput type=\"hidden\"
            # autocomplete=\"off\" name=\"ref\" value=\"mb\" \/>
            # \u003Cinput type=\"hidden\" autocomplete=\"off\"
            # name=\"h\" value=\"AfcAWHcA5wDjZQl2\" \/>
            # \u003C\/form>\u9000\u51fa"}
            succ, h = helper_str.substringif(html, 'name=\\"h\\" value=\\"',
                                             '\\"')
            if not succ or h == None or h == "":
                self._logger.error(
                    "Get param 'h' for logout failed, user={}".format(
                        self.uname_str))
                return res

            # 点击退出按钮
            url = 'https://www.facebook.com/login/device-based/regular/logout/?button_name=logout&button_location=settings'
            data = 'jazoest={}&fb_dtsg={}&ref=mb&h=AffuTa5jisGLhYoR{}'.format(
                self.jazoest,
                parse.quote_plus(self.fb_dtsg),
                h,
            )
            html, redir = self._ha.getstring_unredirect(
                url,
                req_data=data,
                headers='''
                accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
                accept-encoding: gzip, deflate, br
                accept-language: zh-CN,zh;q=0.9
                cache-control: no-cache
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                pragma: no-cache
                referer: https://www.facebook.com/
                upgrade-insecure-requests: 1''')
            if not isinstance(redir, str) or redir == '':
                self._logger.error(
                    "Logout jump location is empty, user={}".format(
                        self.uname_str))
                return res

            html = self._ha.getstring(
                redir,
                headers='''
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            accept-encoding: gzip, deflate
            accept-language: zh-CN,zh;q=0.9
            cache-control: no-cache
            pragma: no-cache
            referer: https://www.facebook.com/
            upgrade-insecure-requests: 1''',
                encoding='utf-8')

            # class="fbIndex UIPage_LoggedOut _-kb _61s0 _605a
            # b_c3pyn-ahh chrome webkit win x1 Locale_zh_CN cores-lt4 _19_u hasAXNavMenubar"
            if not isinstance(
                    html,
                    str) or not html.__contains__('fbIndex UIPage_LoggedOut'):
                self._logger.error(
                    "Logout failed, 'fbIndex UIPage_LoggedOut' element not found, user={}"
                        .format(self.uname_str))
                return res

            res = True

        except Exception:
            self._logger.error("Logout error:\nuser:{}\nerror:{}".format(
                self.uname_str, traceback.format_exc()))
        return res
