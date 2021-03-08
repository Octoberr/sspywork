"""
spider gmail

update by judy 2019/03/07
统一使用ha
"""

# -*- coding:utf-8 -*-

# python xpath 用法：
# https://www.cnblogs.com/zhangxinqi/p/9210211.html

import datetime
import random
import re
import time
import traceback
from urllib import parse

import requests
from commonbaby.helpers import helper_str
from commonbaby.httpaccess import ResponseIO
from dateutil import parser as dateparser
from lxml import etree
from selenium import webdriver
from selenium.webdriver import ChromeOptions

from .spidermailbase import SpiderMailBase
from ...clientdatafeedback import EML, Folder, PROFILE, CONTACT_ONE, CONTACT


class SpiderGmail(SpiderMailBase):
    def __init__(self, task, appcfg, clientid):
        super(SpiderGmail, self).__init__(task, appcfg, clientid)
        self._uname_task: str = None

        # cookie登陆时用到的字段
        self._hpurlbase: str = None  # homepage url base，基础版页面的url前面基础部分半截
        self._homepage: str = None  # 用于记录基础版主页完整html，用于提取文件夹列表
        # 匹配邮件发送时间
        self._resendtime = re.compile(r'^Date:\s*?(?P<date>[^\()]+?)(\(|$)',
                                      re.S | re.M)

    def _get_uname_task(self):
        """从task中搜索可用的用户名，包括手机/账号等，并返回，没有可用的
        用户名则返回None。适用于Gmail"""
        res: str = None
        try:

            if self.task is None:
                return res
            if not helper_str.is_none_or_empty(self.task.account):
                res = self.task.account
            elif not helper_str.is_none_or_empty(self.task.phone):
                if helper_str.is_none_or_empty(self.task.globaltelcode):
                    return res
                res = "+{}{}".format(
                    self.task.globaltelcode.strip().strip('+'),
                    self.task.phone.strip())

        except Exception:
            res = None
        return res

    def _check_registration(self) -> iter:
        """查询手机号是否注册了gmail
        # 中国的手机号需要加上+86
        :param account:
        :return: 返回PROFILE和其附带的RESOURCE资源信息"""
        # 此函数现应为返回PROFILE和其附带的RESOURCE资源信息
        res: PROFILE = None
        try:
            targetacc: str = self._get_uname_task()
            if helper_str.is_none_or_empty(targetacc):
                self._logger.error(
                    "Target acount is empty while checking registration")
                return res

            # 需要先访问一下主页，拿个cookie
            url = "https://mail.google.com"
            html = self._ha.getstring(url,
                                      headers="""
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"""
                                      )

            url = "https://accounts.google.com/_/signin/sl/lookup?hl=zh-CN&_reqid=238058&rt=j"
            postdata = """continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&service=mail&rm=false&ltmpl=default&ss=1&osid=1&f.req=%5B%22{account}%22%2C%22AEThLlwQTFRaZdGqR1ySvZpLCNWaG8r9DmMMnVXufvJis2SJJsqoidT0i9UrtAWrSFQpRCLNeiqj0L_XDWnfDK4gXbewbaCoxux2T2wqYutk7KfIW-BMDBov_woG3AtFesU-mmUAAkaw8sLDLabW9CRQUJEPeKzl-Jdj3hNiK9VvNgkFTeg-MJk%22%2C%5B%5D%2Cnull%2C%22KR%22%2Cnull%2Cnull%2C2%2Cfalse%2Ctrue%2C%5Bnull%2Cnull%2C%5B2%2C1%2Cnull%2C1%2C%22https%3A%2F%2Faccounts.google.com%2FServiceLogin%3Fcontinue%3Dhttps%253A%252F%252Fmail.google.com%252Fmail%252F%26osid%3D1%26service%3Dmail%26ss%3D1%26ltmpl%3Ddefault%26rm%3Dfalse%22%2Cnull%2C%5B%5D%2C4%2C%5B%5D%2C%22GlifWebSignIn%22%5D%2C10%2C%5Bnull%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B5%2C%2277185425430.apps.googleusercontent.com%22%2C%5B%22https%3A%2F%2Fwww.google.com%2Faccounts%2FOAuthLogin%22%5D%2Cnull%2Cnull%2C%2255f38eed-e452-4296-b42c-6b386d00a5a2%22%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C5%2Cnull%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2C%5B%5D%5D%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2C%5B%5D%5D%2Cnull%2Cnull%2Cnull%2Ctrue%5D%2C%22{account}%22%5D&bgRequest=%5B%22identifier%22%2C%22!IiGlIQBCh9g7QSu0Yu9EB9GEMHhDBNACAAAAlVIAAAAYmQGcbYCxJolG33I0aLTL3UDDeXekvvZ2D_ORjLR-jl96QQHU3r4uu1DaX9oqM3NRssfbOOAU5upc9lrn76TBv8Z4exkrfw-We-T3TDbi-4xf2n6uFlzf8CmwU7-FuYCgL_sscdc8HwiP03ADn_5wtaoowXB6wawSjW8_U4p1gkiaGtn9uM61X2-BUR8r3kIKgziDpNHj731K279e3u9YL0Wrye3BEKuydAv5FIsxD0mKpNXz5Ury2e8yX9Wdn1pf72vc8LvzZon7kf-yQePKquVP3MsiMzWyeBvglTxw2NU51U7Y0ZfS7uKn6BR6DvUZ9ZdomFVns0dak5xpmIpRKfEkBURZtD9WnD8hg2kVXgTzMXbQJYPDzAPLtjQDB5Uv5NmbTVSJVXPQeBwDmjeznvdrceOfae7zHUE8L7LWcNDe8iI8Jdpb-tQm6EafnFLTIzhIeYJcWrNupBDPE1q6sb2mzxZqJzFIdlsuAfKyUTRhRxxKt6zFHjGPZ64D384w5mi7ouRTXrNwM_XuhbPnPwCUNoWMwj14_BVwa6RbnQ%22%5D&azt=AFoagUVegOGq9-AhBRoAcTa3AQVNLlzmFw%3A1542793455384&cookiesDisabled=false&deviceinfo=%5Bnull%2Cnull%2Cnull%2C%5B%5D%2Cnull%2C%22KR%22%2Cnull%2Cnull%2C%5B%5D%2C%22GlifWebSignIn%22%2Cnull%2C%5Bnull%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B5%2C%2277185425430.apps.googleusercontent.com%22%2C%5B%22https%3A%2F%2Fwww.google.com%2Faccounts%2FOAuthLogin%22%5D%2Cnull%2Cnull%2C%2255f38eed-e452-4296-b42c-6b386d00a5a2%22%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C5%2Cnull%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2C%5B%5D%5D%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2C%5B%5D%5D%5D&gmscoreversion=undefined&checkConnection=youtube%3A248%3A1&checkedDomains=youtube&pstMsg=1&""".format(
                account=parse.quote_plus(targetacc))
            html = self._ha.getstring(url,
                                      req_data=postdata,
                                      headers="""
accept: */*
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
content-type: application/x-www-form-urlencoded;charset=UTF-8
google-accounts-xsrf: 1
origin: https://accounts.google.com
referer: https://accounts.google.com/signin/v2/identifier?flowName=GlifWebSignIn&flowEntry=ServiceLogin
pragma: no-cache
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"""
                                      )

            if isinstance(html, str) and '"5001":[]' in html:
                res = PROFILE(self._clientid, self.task, self.task.apptype,
                              self._userid)

        except Exception:
            self._logger.error("Check gmail registration error: {}".format(
                traceback.format_exc()))
        return res

    def _cookie_login(self) -> bool:
        """gmail cookie login"""
        res: bool = False
        try:
            if helper_str.is_none_or_empty(self.task.cookie):
                self._logger.warn("Cookie from task is empty")
            else:
                # 直接丢到google.com根域名下
                self._ha._managedCookie.add_cookies(".google.com",
                                                    self.task.cookie)

            # 直接从主页自动跳转
            url = "https://mail.google.com/mail/"
            html = self._ha.getstring(url,
                                      headers="""
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
referer: https://accounts.google.com/CheckCookie
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"""
                                      )

            succ, globals_ = helper_str.substringif(html, "GLOBALS=[", ",[")
            if not succ or helper_str.is_none_or_empty(globals_):
                self._logger.error("Get profile information failed")
                return res

            globalparams: list = globals_.split(',')
            if globalparams is None or len(globalparams) < 10:
                self._logger.error("Get field 'ik' failed")
                return res

            ik = globalparams[9].strip('"')
            if helper_str.is_none_or_empty(ik):
                self._logger.error("Feld 'ik' is empty")
                return res

            if len(globalparams) < 11:
                self._logger.error("Get username failed")
                return res

            self._username = globalparams[10].strip('"')
            if helper_str.is_none_or_empty(self._username):
                self._logger.info('Get username failed2')
                return res

            # self._logger.info("Got username: {}".format(self._username))

            # 尝试跳转到基础版页面
            gmail_at = self._ha._managedCookie.get_cookie_value_in_domain(
                'mail.google.com', 'GMAIL_AT')
            if helper_str.is_none_or_empty(gmail_at):
                succ, gmail_at = helper_str.substringif(
                    html, 'input type="hidden" name="at" value="', '"')
                if not succ or helper_str.is_none_or_empty(gmail_at):
                    gmail_at = self._ha._managedCookie.get_cookie_value(
                        'GMAIL_AT')
                    if helper_str.is_none_or_empty(gmail_at):
                        self._logger.error("Get field 'GMAIL_AT' failed")
                        return res

            self._ha._managedCookie.add_cookies('google.com',
                                                'GMAIL_AT={}'.format(gmail_at))
            url = 'https://mail.google.com/mail/u/0/?ui=html&zy=e'
            postdata = 'at={}'.format(gmail_at)
            html, redir = self._ha.getstring_with_reurl(url,
                                                        req_data=postdata,
                                                        headers="""
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
content-type: application/x-www-form-urlencoded
origin: https://mail.google.com
pragma: no-cache
referer: https://mail.google.com/mail/u/0/
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"""
                                                        )

            if helper_str.is_none_or_empty(redir):
                self._logger.error("Jump to basic page failed")
                return res

            redirs: list = redir.split('?')
            if redirs is None or len(redirs) < 1:
                self._logger.error("Get url root of basic page failed")
                return res

            self._hpurlbase = redirs[0]
            if helper_str.is_none_or_empty(self._hpurlbase):
                self._logger.error("Get url root of basic page failed2")
                return res
            self._hpurlbase = self._hpurlbase.strip().strip('/')

            self._homepage = html

            res = True

        except Exception:
            self._logger.error(traceback.format_exc())
        return res

    # def _pwd_login(self) -> bool:
    #     res = False
    #     try:
    #         chrome_options = ChromeOptions()
    #         # chrome_options.add_argument('--headless')
    #         chrome_options.add_argument('--disable-gpu')
    #         chrome_options.add_argument('blink-settings=imagesEnabled=false')
    #         chrome_options.add_argument('--no-sandbox')
    #         chrome_options.add_argument('--disable-gpu')
    #         chrome_options.add_argument('--disable-dev-shm-usage')
    #         driver = webdriver.Chrome(chrome_options=chrome_options)
    #         driver.get('https://accounts.google.com/')
    #         time.sleep(3)
    #         before_url = driver.current_url
    #         driver.find_element_by_css_selector('#identifierId').send_keys(self.task.account)
    #         driver.find_element_by_css_selector('#identifierNext > span > span').click()
    #         time.sleep(3)
    #         post_url = driver.current_url
    #         if before_url == post_url:
    #             self._logger.info('Account is wrong!')
    #             return res
    #         driver.find_element_by_css_selector('#password > div.aCsJod.oJeWuf > div > div.Xb9hP > input').send_keys(self.task.password)
    #         driver.find_element_by_css_selector('#passwordNext > span > span').click()
    #         time.sleep(3)
    #         end_url = driver.current_url
    #         if post_url == end_url:
    #             self._logger.info('Password is wrong!')
    #         cookie_l = driver.get_cookies()
    #         l_cookie = ''
    #         for cookie in cookie_l:
    #             l_cookie = l_cookie + cookie['name'] + '=' + cookie['value'] + '; '
    #         self.task.cookie = l_cookie
    #         res = self._cookie_login()
    #     except Exception:
    #         self._logger.error('Pwd login fail: {}'.format(traceback.format_exc()))
    #     return res

    def _get_profile(self) -> iter:
        """gmail profile"""

        url = f"https://mail.google.com/mail/u/0/h/1h3625ru{random.randint(10, 99)}n2y/"

        querystring = {"v": "pra"}
        headers = {
            'accept':
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'accept-encoding':
            "gzip, deflate, br",
            'accept-language':
            "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control':
            "no-cache,no-cache",
            'cookie':
            self.task.cookie,
            'pragma':
            "no-cache",
            'upgrade-insecure-requests':
            "1",
            'user-agent':
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        }

        try:
            response = requests.request("GET",
                                        url,
                                        headers=headers,
                                        params=querystring)
            re_text = response.text
            hdoc = etree.HTML(re_text, etree.HTMLParser())
            info = hdoc.xpath('//b')
            for data in info:
                if data.text is None:
                    continue
                if '@gmail.com>' in data.text:
                    all_p_info = data.text
            p_info = all_p_info.replace(' ', '').replace('>', '').split('<')
            nickname = p_info[0].strip()
            mail = p_info[1].strip()
            self._userid = mail
            p_data = PROFILE(self._clientid, self.task, self.task.apptype,
                             self._userid)
            p_data.nickname = nickname
            p_data.email = mail
            yield p_data
        except Exception:
            self._logger.error(
                f"Get gmail profile error, err:{traceback.format_exc()}")

    def _get_contacts(self) -> iter:

        url = f"https://mail.google.com/mail/u/0/h/twlxul{random.randint(100, 999)}bou/"

        querystring = {"pnl": "a", "v": "cl", "": ""}

        payload = ""
        headers = {
            'accept':
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            'accept-encoding':
            "gzip, deflate, br",
            'accept-language':
            "zh-CN,zh;q=0.9,en;q=0.8",
            'cache-control':
            "no-cache,no-cache",
            'cookie':
            self.task.cookie,
            'pragma':
            "no-cache",
            'upgrade-insecure-requests':
            "1",
            'user-agent':
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"
        }

        try:
            response = requests.request("GET",
                                        url,
                                        data=payload,
                                        headers=headers,
                                        params=querystring)

            hdoc = etree.HTML(response.text, etree.HTMLParser())
            info = hdoc.xpath('//td')
            cont_all = CONTACT(self._clientid, self.task, self.task.apptype)
            for data in info:
                if data.text is None or data.text == '' or '@' not in data.text:
                    continue
                con_one = CONTACT_ONE(self._userid, data.text.strip(),
                                      self.task, self.task.apptype)
                con_one.nickname = data.text.split('@')[0]
                con_one.email = data.text.strip()
                cont_all.append_innerdata(con_one)
            if cont_all.innerdata_len > 0:
                yield cont_all
        except Exception:
            self._logger.error(
                f"Get gmail contact error, err:{traceback.format_exc()}")

    def _get_folders(self) -> iter:
        """Get folders"""
        try:
            # 直接从主页解析

            hdoc = etree.HTML(self._homepage, etree.HTMLParser())
            if hdoc is None:
                self._logger.error(
                    "Parse html document for mail folders from homepage failed"
                )
                return

            xtd: list = hdoc.xpath('.//td[@width="120"]')
            if xtd is None or len(xtd) < 1:
                self._logger.error("Get folder list failed")
                return

            xtd = xtd[0]
            xfolders = xtd.xpath('.//tr')
            if xfolders is None or len(xfolders) < 1:
                self._logger.error("Get folder list fialed2")
                return

            folderkeys: dict = {}
            for xfolder in xfolders:
                try:
                    if xfolder is None:
                        continue

                    xas: list = xfolder.xpath('.//a')
                    if xas is None or len(xas) < 1:
                        continue

                    xa: etree._Element = xas[0]

                    xhrefs = xa.xpath('.//@href')
                    if xhrefs is None or len(xhrefs) < 1:
                        continue
                    href: str = str(xhrefs[0])
                    if helper_str.is_none_or_empty(href):
                        continue

                    xaccsskeys = xa.xpath('.//@accesskey')
                    if not xaccsskeys is None and len(xaccsskeys) > 1:
                        accesskey: str = str(xaccsskeys[0])
                    elif href.__contains__("s="):
                        idx = href.index('s=')
                        if idx is None or idx < 0:
                            continue
                        accesskey = href[idx + 2:]
                    if helper_str.is_none_or_empty(accesskey):
                        continue

                    foldername = xa.xpath('./text()')
                    if foldername is None or len(foldername) < 1:
                        continue
                    foldername = str(foldername[0])
                    if helper_str.is_none_or_empty(foldername):
                        continue

                    if accesskey == 'c' or foldername == '写邮件' or \
                            accesskey == '?&s=a' or foldername == '所有邮件' or \
                            accesskey == '?&v=cl' or foldername == '通讯录' or \
                            accesskey == '?&v=prl' or foldername == '修改标签':
                        continue

                    if not folderkeys.__contains__(accesskey):
                        folderkeys[accesskey] = href

                    folder = Folder()
                    folder.name = foldername
                    folder.folderid = accesskey
                    folder.folderurl = "{}/{}".format(self._hpurlbase,
                                                      href.lstrip('/'))

                    yield folder

                except Exception:
                    self._logger.error("Get one folder error: {}".format(
                        traceback.format_exc()))

        except Exception:
            self._logger.error("Get folders error: {}".format(
                traceback.format_exc()))

    def _get_mails(self, folder: Folder) -> iter:
        """Get mails in given folder"""
        try:
            if folder is None:
                self._logger.error("Given folder is None")
                return

            urlnext: str = folder.folderurl
            page: int = 0
            next_: bool = True
            maillastidx: int = 0
            mailidx: int = 0
            while next_:
                try:
                    html = self._ha.getstring(urlnext,
                                              headers="""
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"""
                                              )

                    hdoc = etree.HTML(html, etree.HTMLParser())
                    if hdoc is None:
                        # self._logger.error(
                        #     "Parse mail html document of folder '{}' failed.".
                        #     format(folder.name))
                        self._logger.info("No mail find in folder '{}'".format(
                            folder.name))
                        return

                    # 有无下一页
                    next_ = False
                    next_, urlnext, mailidx, maillastidx = self._get_next_page_url(
                        hdoc, folder, mailidx, maillastidx)

                    self._logger.info("Enter folder '{}' {}-{}".format(
                        folder.name, maillastidx,
                        str(mailidx) if mailidx > maillastidx else ""))

                    # 解析邮件列表
                    mailnodes = hdoc.xpath('.//tr[@bgcolor]')
                    if mailnodes is None or len(mailnodes) < 1:
                        self._logger.info(
                            "No mail found in folder '{}'".format(folder.name))
                        continue

                    for mailnode in mailnodes:
                        try:
                            if mailnode is None:
                                continue

                            # 已读未读状态
                            isread: bool = False
                            abgcolor = mailnode.xpath('./@bgcolor')
                            if not abgcolor is None and len(abgcolor) > 0:
                                strbgcolor = str(abgcolor[0]).strip()
                                if not helper_str.is_none_or_empty(
                                        strbgcolor
                                ) and strbgcolor == '#E8EEF7':
                                    isread = True

                            # 获取邮件详情页
                            # href="?&th=1671b647a79e227b&v=c"
                            xas = mailnode.xpath('.//td/a[@href]')
                            if xas is None or len(xas) < 1:
                                self._logger.error(
                                    "Get mail content url failed, skip this mail"
                                )
                                continue
                            xa = xas[0]
                            xhref = xa.xpath('./@href')
                            if xhref is None or len(xhref) < 1:
                                self._logger.error(
                                    "Get mail content url failed, skip this mail1"
                                )
                                continue
                            strhref = str(xhref[0]).strip()
                            if helper_str.is_none_or_empty(strhref):
                                self._logger.error(
                                    "Get mail content url failed, skip this mail2"
                                )
                                continue

                            mailurl = "{}/{}".format(self._hpurlbase, strhref)

                            succ, mailid = helper_str.substringif(
                                mailurl, 'th=', '&')
                            if not succ or helper_str.is_none_or_empty(mailid):
                                self._logger.error(
                                    "Get mail id failed, skip this mail")
                                continue

                            xsubjs: str = xa.xpath('.//text()')
                            if xsubjs is None or len(xsubjs) < 1:
                                self._logger.error(
                                    "Get mail subject failed: {}".format(
                                        mailid))
                                continue
                            subj = ''.join(str(xs) for xs in xsubjs)
                            if '-' in subj:
                                idx = subj.find('-')
                                subj = subj[0:idx - 1].strip()

                            # 点击 ‘显示原始邮件’
                            urlsrc = "{}/?&th={}&v=om".format(
                                self._hpurlbase, mailid)
                            html = self._ha.getstring(urlsrc,
                                                      headers="""
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
pragma: no-cache
referer: {}
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36"""
                                                      .format(mailurl))

                            if helper_str.is_none_or_empty(html):
                                self._logger.error(
                                    "Get source mail page failed: {}".format(
                                        urlsrc))
                                continue

                            hsrc = etree.HTML(html, etree.HTMLParser())
                            if hsrc is None:
                                self._logger.error(
                                    "Parse mail source document failed: {}".
                                    format(urlsrc))
                                continue

                            # 发送时间
                            sendtime = datetime.datetime(1970, 1, 1, 0, 0, 0)
                            strsendtime = None
                            m = self._resendtime.search(html)
                            if m is None:
                                self._logger.warn(
                                    "Get mail sendtime failed: {} {}".format(
                                        mailid, subj))
                            else:
                                strsendtime = m.group('date').strip()
                            if not helper_str.is_none_or_empty(strsendtime):
                                try:
                                    sendtime: datetime.datetime = dateparser.parse(
                                        strsendtime)
                                except Exception:
                                    try:
                                        sendtime = datetime.datetime.strptime(
                                            strsendtime,
                                            '%a, %d %b %Y %H:%M:%S %z'
                                        ).strftime('%a, %d %b %Y %H:%M:%S %z')
                                    except Exception:
                                        self._logger.warn(
                                            "Get mail sendtime failed: {} {}".
                                            format(mailid, subj))
                                        sendtime = datetime.datetime(
                                            1970, 1, 1, 0, 0, 0)

                            # 找 下载邮件 按钮
                            xbtns = hsrc.xpath(
                                './/a[@class="download-buttons"]')
                            if xbtns is None or len(xbtns) < 1:
                                self._logger.error(
                                    "Get mail download url failed: {} {}".
                                    format(mailid, subj))
                                continue
                            xbtn = xbtns[0]
                            xdurls = xbtn.xpath('.//@href')
                            if xdurls is None or len(xdurls) < 1:
                                self._logger.error(
                                    "Get mail download url failed: {} {}".
                                    format(mailid, subj))
                                continue
                            downurl = "{}/{}".format(
                                self._hpurlbase,
                                str(xdurls[0]).strip().lstrip('/'))

                            # 用uname_str会有问题的，应该固定使用一个值
                            mail = EML(self._clientid, self.task,
                                       self.uname_str, mailid, folder,
                                       self.task.apptype)
                            mail.owner = self.uname_str
                            mail.sendtime = sendtime
                            mail.downloadurl = downurl
                            headers = """
                            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                            accept-encoding: gzip, deflate, br
                            accept-language: zh-CN,zh;q=0.9
                            cache-control: no-cache
                            pragma: no-cache
                            referer: {}
                            upgrade-insecure-requests: 1
                            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36""".format(
                                urlsrc)
                            resp = self._ha.get_response(mail.downloadurl,
                                                         headers=headers)
                            mail.stream_length = resp.headers.get(
                                'Content-Length', 0)
                            mail.io_stream = ResponseIO(resp)
                            yield mail

                        except Exception:
                            self._logger.error(
                                "Parse one mail error: {}".format(
                                    traceback.format_exc()))

                except Exception:
                    self._logger.error(
                        "Get mails of folder '{}' error: {}".format(
                            folder.name, traceback.format_exc()))

        except Exception:
            self._logger.error("Get mails of folder '{}' error: {}".format(
                folder.name, traceback.format_exc()))

    def _get_next_page_url(
            self,
            hdoc,
            folder: Folder,
            mailidx: int,
            maillastidx: int,
    ) -> (bool, str, int, int):
        """get if has next page, return (succ, url)"""
        hasnext: bool = False
        nexturl: str = None
        mailidx: int = mailidx if isinstance(mailidx,
                                             int) and mailidx >= 0 else -1
        maillastidx: int = maillastidx if isinstance(
            maillastidx, int) and maillastidx >= 0 else -1
        try:

            xnext = hdoc.xpath(
                './/td[@align="right"]//a[@class="searchPageLink"]')
            if xnext is None or len(xnext) < 1:
                return (hasnext, nexturl, mailidx, maillastidx)

            for xn in xnext:
                if xn is None:
                    continue
                xhnexts = xn.xpath('.//@href')
                if xhnexts is None or len(xhnexts) < 1:
                    continue
                strnexturl = str(xhnexts[0]).strip()
                if not 'st=' in strnexturl:
                    continue
                idx = strnexturl.find('st=')
                if idx < 0:
                    continue
                strmailidx = strnexturl[idx + len("st="):]
                maillastidx = mailidx
                tmp: int = -1
                try:
                    tmp = int(strmailidx)
                except Exception as ex:
                    continue
                if tmp <= maillastidx:
                    continue
                mailidx = tmp
                nexturl = "{}/{}".format(self._hpurlbase, strnexturl)
                hasnext = True
                break
        except Exception:
            self._logger.error(
                "Get next page url of folder '{}' error: {}".format(
                    folder.name, traceback.format_exc()))
        return (hasnext, nexturl, mailidx, maillastidx)
