"""
验证手机号是否注册了outlook邮箱
20181023
"""
import base64
import datetime
import json
import time
import traceback
import io
from urllib.parse import quote_plus

from commonbaby.helpers import helper_str

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import EBackResult
from idownclient.clientdatafeedback import EML, Folder, PROFILE
from .spidermailbase import SpiderMailBase


class SpiderOutlook(SpiderMailBase):
    def __init__(self, task, appcfg, clientid):
        super(SpiderOutlook, self).__init__(task, appcfg, clientid)
        self._outlook_clientid: str = None
        self._outlook_canary: str = None

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

    def _check_registration(self):
        """
        查询手机号是否注册了mailoutlook
        # 中国的手机号需要加上+86
        :param account:
        :return:
        """
        res: PROFILE = None
        try:

            targetacc: str = self._get_uname_task()
            if helper_str.is_none_or_empty(targetacc):
                self._logger.error(
                    "Target acount is empty while checking registration")
                return res

            t = time.strftime('%Y-%m-%d %H:%M:%S')
            url = 'https://login.live.com/login.srf'
            headers = f"""
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: no-cache
            Connection: keep-alive
            Host: login.live.com
            Pragma: no-cache
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"""
            response = self._ha.getstring(url, headers=headers)
            succ, uaid = helper_str.substringif(response, 'uaid=', '"')
            if not succ or not isinstance(uaid, str) or uaid == "":
                self._logger.error(
                    "Get field 'uaid' failed for checking registration: {}".
                    format(targetacc))
                return res
            succ, flowToken = helper_str.substringif(response,
                                                     'id="i0327" value="', '"')
            if not succ or not isinstance(flowToken, str) or flowToken == "":
                self._logger.error(
                    "Get field 'flowToken' failed for checking registration: {}"
                    .format(targetacc))
                return res

            url = f'https://login.live.com/GetCredentialType.srf?vv=1600&mkt=ZH-CN&lc=2052&uaid={uaid}'
            headers = f"""
            Accept: application/json
            client-request-id: {uaid}
            Content-type: application/json; charset=UTF-8
            hpgact: 0
            hpgid: 33
            Origin: https://login.live.com
            Referer: https://login.live.com/login.srf
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"""

            postdata = '{"username":"' + targetacc + '","uaid":"' + uaid + '","isOtherIdpSupported":false,"checkPhones":true,"isRemoteNGCSupported":true,"isCookieBannerShown":false,"isFidoSupported":false,"forceotclogin":false,"otclogindisallowed":true,"flowToken":"' + flowToken + '"}'
            html = self._ha.getstring(url, headers=headers, req_data=postdata)
            if '"IfExistsResult":0,' in html:
                self._write_task_back(ECommandStatus.Succeed, 'Registered', t,
                                      EBackResult.Registerd)
            else:
                self._write_task_back(ECommandStatus.Succeed, 'Not Registered',
                                      t, EBackResult.UnRegisterd)
        except Exception:
            self._logger.error('Check registration fail: {}'.format(
                traceback.format_exc()))
            self._write_task_back(ECommandStatus.Failed,
                                  'Check registration fail.', t,
                                  EBackResult.CheckRegisterdFail)
        return

    def _cookie_login(self) -> bool:
        """
        cookie登陆
        :return:
        """
        res: bool = False
        try:
            # https://outlook.live.com/owa/
            if self.task.cookie:
                self._ha._managedCookie.add_cookies(".live.com", self.task.cookie)

            if not self._check_cookie_correction():
                return res

            url = 'https://outlook.live.com/owa/0/sessiondata.ashx?app=Mail'
            headers = """
            Host: outlook.live.com
            Connection: keep-alive
            Content-Length: 0
            Pragma: no-cache
            Cache-Control: no-cache
            Origin: https://outlook.live.com
            x-js-clienttype: 2
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
            Accept: */*
            Sec-Fetch-Site: same-origin
            Sec-Fetch-Mode: cors
            Referer: https://outlook.live.com/
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """
            html = self._ha.getstring(url, req_data='', headers=headers)
            self._userid = helper_str.substring(html, '"UserEmailAddress":"', '"')
            if self._userid:
                res = True

        except Exception:
            self._logger.error(
                "Cookie login failed: taskid={}, batchid={}, username:{}".
                format(self.task.taskid, self.task.batchid, self.uname_str))
        return res

    def _check_cookie_correction(self):
        """check outlook cookie correction"""
        res: bool = False
        try:
            check_keys = ["ClientId", "X-OWA-CANARY"]
            for k in check_keys:
                if not self._ha._managedCookie.contains_cookie(k):
                    return res
        except Exception:
            self._logger.error("Check cookie correction error: {}".format(
                traceback.format_exc()))
        self._outlook_clientid = self._ha._managedCookie.get_cookie_valuestr(
            "ClientId")
        self._outlook_canary = self._ha._managedCookie.get_cookie_valuestr(
            "X-OWA-CANARY")
        return True

    def _pwd_login(self) -> bool:
        res = False
        try:
            url = "https://outlook.live.com/owa/?nlp=1"
            headers = """
            Host: outlook.live.com
            Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
            Sec-Fetch-User: ?1
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Sec-Fetch-Site: same-origin
            Sec-Fetch-Mode: navigate
            Referer: https://outlook.live.com/owa/
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """
            html, loginPageUrl = self._ha.getstring_with_reurl(url, headers=headers)
            if not html or not loginPageUrl or not self.ParseUrlFields(loginPageUrl, html):
                self._logger.info("获取登录页面失败，或网站规则可能有变化。")
                return False

            url_0 = f'https://login.live.com/login.srf?wa={self.wa}&rpsnv={self.rpsnv}&ct={self.ct}&rver={self.rver}&wp=MBI_SSL&wreply={self.wreply}&id={self.id}&aadredir=1&CBCXT={self.cbcxt}&lw=1&fl=dob%2cflname%2cwld&cobrandid=90015'
            html_0 = self._ha.getstring(url_0, headers="""
            Host: login.live.com
            Connection: keep-alive
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
            Sec-Fetch-User: ?1
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Sec-Fetch-Site: same-site
            Sec-Fetch-Mode: navigate
            Referer: https://outlook.live.com/owa/
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """)
            url = helper_str.substring(html_0, "bf:'", "'")
            # 'https://login.live.com/GetCredentialType.srf?opid=9F5B57409099C1EB&wa=wsignin1.0&rpsnv=13&ct=1577154657&rver=7.0.6737.0&wp=MBI_SSL&wreply=https%3a%2f%2foutlook.live.com%2fowa%2f%3fnlp%3d1%26RpsCsrfState%3de3b9ed6a-c31e-1542-4b5f-e683f9e532a0&id=292841&aadredir=1&CBCXT=out&lw=1&fl=dob%2cflname%2cwld&cobrandid=90015&vv=1600&mkt=ZH-CN&lc=2052&uaid=4f20b195be86441f8b84dfed4eaa36af'
            # url = f"https://login.live.com/GetCredentialType.srf?wa={self.wa}&rpsnv={self.rpsnv}&ct={self.ct}&rver={self.rver}&wp=MBI_SSL&&wreply={self.wreply}&lc={self.lc}&id={self.id}&mkt={self.mkt}&cbcxt={self.cbcxt}&vv=1600"
            postdata = f'{{"username":"{self.task.account}","uaid":"{self.uaid}","isOtherIdpSupported":true,"checkPhones":false,"isRemoteNGCSupported":true,"isCookieBannerShown":false,"isFidoSupported":true,"forceotclogin":false,"otclogindisallowed":true,"isExternalFederationDisallowed":false,"isRemoteConnectSupported":false,"federationFlags":3,"flowToken":"{self.PPFT}"}}'
            html = self._ha.getstring(url, req_data=postdata, headers=f"""
            Host: login.live.com
            Connection: keep-alive
            Content-Length: 617
            Origin: https://login.live.com
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
            client-request-id: {self.uaid}
            Content-type: application/json; charset=UTF-8
            hpgid: 33
            Accept: application/json
            hpgact: 0
            Sec-Fetch-Site: same-origin
            Sec-Fetch-Mode: cors
            Referer: {url_0}
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """)

            # print("Outlook Pass 提交账密")
            # postPassurl = f"https://login.live.com/ppsecure/post.srf?wa={self.wa}&rpsnv={self.rpsnv}&ct={self.ct}&rver={self.rver}&wp=MBI_SSL&wreply={self.wreply}&lc={self.lc}&id={id}&mkt={self.mkt}&cbcxt={self.cbcxt}&contextid={self.contextid}&bk=1487815431{self.bk}&uaid={self.uaid}&pid={self.pid}"
            postPassurl = f"https://login.live.com/ppsecure/post.srf?wa={self.wa}&rpsnv={self.rpsnv}&ct={self.ct}&rver={self.rver}&wp=MBI_SSL&wreply={self.wreply}&id={id}&aadredir=1&CBCXT={self.cbcxt}&lw=1&fl=dob%2cflname%2cwld&cobrandid={self.cobrandid}&contextid={self.contextid}&bk={self.bk}&uaid={self.uaid}&pid={self.pid}"
            postdata = f'i13=0&login={self.task.account}&loginfmt={self.task.account}&type=11&LoginOptions=3&lrt=&lrtPartition=&hisRegion=&hisScaleUnit=&passwd={quote_plus(self.task.password)}&ps=2&psRNGCDefaultType=&psRNGCEntropy=&psRNGCSLK=&canary=&ctx=&hpgrequestid=&PPFT={self.PPFT}&PPSX=Passport&NewUser=1&FoundMSAs=&fspost=0&i21=0&CookieDisclosure=0&IsFidoSupported=1&isSignupPost=0&i2=1&i17=0&i18=&i19=30473'
            html = self._ha.getstring(postPassurl, req_data=postdata, headers=f"""
            Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
            Accept-Encoding:gzip, deflate, br
            Accept-Language:zh-CN,zh;q=0.8
            Connection:keep-alive
            Content-Type:application/x-www-form-urlencoded
            Origin:https://login.live.com
            Referer:{loginPageUrl}
            Upgrade-Insecure-Requests:1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
            """)

            # 跳转到是否保持登陆 页面
            postPassurl = f"https://login.live.com/ppsecure/post.srf?wa={self.wa}&rpsnv={self.rpsnv}&ct={self.ct}&rver={self.rver}&wp=MBI_SSL&wreply={self.wreply}&id={id}&aadredir=1&CBCXT={self.cbcxt}&lw=1&fl=dob%2cflname%2cwld&cobrandid={self.cobrandid}&contextid={self.contextid}&bk={self.bk}&uaid={self.uaid}&pid={self.pid}&opid={self.opid}"
            postdata = f'LoginOptions=1&type=28&ctx=&hpgrequestid=&PPFT={self.PPFT}&i2=&i17=0&i18=&i19=83140'
            html = self._ha.getstring(postPassurl, req_data=postdata, headers=f"""
                        Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
                        Accept-Encoding:gzip, deflate, br
                        Accept-Language:zh-CN,zh;q=0.8
                        Connection:keep-alive
                        Content-Type:application/x-www-form-urlencoded
                        Origin:https://login.live.com
                        Referer:{loginPageUrl}
                        Upgrade-Insecure-Requests:1
                        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
                        """)

            RpsCsrfState = helper_str.substring(html, 'RpsCsrfState=', '&')

            wbids = helper_str.substring(html, 'id="wbids" value="', '"')
            pprid = helper_str.substring(html, 'id="pprid" value="', '"')
            wbid = helper_str.substring(html, 'id="wbid" value="', '"')
            NAP = helper_str.substring(html, 'id="NAP" value="', '"')
            ANON = helper_str.substring(html, 'id="ANON" value="', '"')
            t = helper_str.substring(html, 'id="t" value="', '"')
            if not wbids or not pprid or not wbid or not NAP or not ANON or not t:
                print('login fail!')
                return res
            # 登录成功后跳转
            url = f'https://outlook.live.com/owa/?nlp=1&RpsCsrfState={RpsCsrfState}&wa={self.wa}'
            postdata = f'wbids={wbids}&pprid={pprid}&wbid={wbid}&NAP={quote_plus(NAP)}&ANON={quote_plus(ANON)}&t={quote_plus(t)}'
            html = self._ha.getstring(url, req_data=postdata, headers="""
            Host: outlook.live.com
            Connection: keep-alive
            Content-Length: 1008
            Cache-Control: max-age=0
            Origin: https://login.live.com
            Upgrade-Insecure-Requests: 1
            Content-Type: application/x-www-form-urlencoded
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Sec-Fetch-Site: same-site
            Sec-Fetch-Mode: navigate
            Referer: https://login.live.com/
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """)

            url = 'https://outlook.live.com/owa/0/'
            headers = """
            GET /owa/0/ HTTP/1.1
            Host: outlook.live.com
            Connection: keep-alive
            Cache-Control: max-age=0
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
            Sec-Fetch-Site: same-site
            Sec-Fetch-Mode: navigate
            Referer: https://login.live.com/
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """
            html = self._ha.getstring(url, headers=headers)

            # cookie检测
            if not self._check_cookie_correction():
                return res
            url = 'https://outlook.live.com/owa/0/sessiondata.ashx?app=Mail'
            headers = """
            Host: outlook.live.com
            Connection: keep-alive
            Content-Length: 0
            Pragma: no-cache
            Cache-Control: no-cache
            Origin: https://outlook.live.com
            x-js-clienttype: 2
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
            Accept: */*
            Sec-Fetch-Site: same-origin
            Sec-Fetch-Mode: cors
            Referer: https://outlook.live.com/
            Accept-Encoding: gzip, deflate, br
            Accept-Language: zh-CN,zh;q=0.9
            """
            html = self._ha.getstring(url, req_data='', headers=headers)
            self._username = helper_str.substring(html, '"UserEmailAddress":"', '"')
            if self._username:
                res = True

        except Exception as ex:
            self._logger.error('Pwd login fail: {}'.format(traceback.format_exc()))
            self._write_log_back("账密登录失败: {}".format(ex.args))
        return res

    def ParseUrlFields(self, loginUrl, loginPage):
        res = False
        try:
            self.wa = helper_str.substring(loginUrl, "wa=", "&")
            self.rpsnv = helper_str.substring(loginUrl, "rpsnv=", "&")
            self.ct = helper_str.substring(loginUrl, "ct=", "&")
            self.rver = helper_str.substring(loginUrl, "rver=", "&")
            self.wreply = helper_str.substring(loginUrl, "wreply=", "&")
            # self.lc = helper_str.substring(loginUrl, "lc=", "&")
            self.lc = '2052'
            self.id = helper_str.substring(loginUrl, "id=", "&")
            # self.mkt = helper_str.substring(loginUrl, "mkt=", "&")
            self.mkt = 'ZH-CN'
            self.cbcxt = helper_str.substring(loginUrl, "CBCXT=", "&")

            self.uaid = helper_str.substring(loginPage, "uaid=", '"')
            self.contextid = helper_str.substring(loginPage, "contextid=", "&")
            self.bk = helper_str.substring(loginPage, "bk=", "&")
            self.pid = helper_str.substring(loginPage, "pid=", "'")
            # self.ppftTmp = helper_str.substring(loginPage, "PPFT=", "'")
            self.PPFT = helper_str.substring(loginPage, "value=\"", "\"")
            self.cobrandid = helper_str.substring(loginPage, "cobrandid=", "&")
            self.opid = helper_str.substring(loginPage, "opid=", "&")
            if self.wa and self.rpsnv and self.ct and self.rver and self.wreply and self.lc and self.id and self.mkt and self.cbcxt and self.uaid and self.contextid and self.bk and self.pid and self.PPFT:
                res = True
        except Exception:
            self._logger.error('ParseUrlFields fail: {}'.format(traceback.format_exc()))
        return res

    def _get_folders(self) -> iter:
        try:
            url = "https://outlook.live.com/owa/sessiondata.ashx?appcacheclient=0"
            headers = """
        Accept:*/*
        Accept-Encoding:gzip, deflate
        Accept-Language:zh-CN,zh;q=0.8
        Cache-Control:max-age=0
        Connection:keep-alive
        Content-Length:0
        Origin:https://outlook.live.com
        Referer:https://outlook.live.com/
        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
        X-OWA-SmimeInstalled:1"""
            html = self._ha.getstring(url, headers=headers, req_data='')
            if not html.__contains__('findFolders'):
                self._logger.info('Got folder list fail!')
                return
            jshtml = json.loads(html)
            respMsgs = jshtml["findFolders"]["Body"]["ResponseMessages"]["Items"]
            if not respMsgs:
                self._logger.info('Folder list is none!')
                return
            for msg in respMsgs:
                items = msg['RootFolder']['Folders']
                for item in items:

                    try:
                        displayName = item["DisplayName"]
                        totalCount = item["TotalCount"]
                        if 'DistinguishedFolderId' in item.keys():
                            isDistingFolder = True
                            folderId = item["DistinguishedFolderId"]
                        else:
                            isDistingFolder = False
                            if totalCount < 1:
                                continue
                            elif 'FolderId' in item.keys() and 'Id' in item["FolderId"].keys():
                                folderId = item["FolderId"]["Id"]
                            else:
                                continue
                        fo = Folder()
                        fo.folderid = folderId
                        fo.name = displayName
                        fo.mailcount = totalCount
                        fo.other = isDistingFolder
                        yield fo
                    except Exception:
                        self._logger.error('Got folder id fail: {}'.format(traceback.format_exc()))

        except Exception:
            self._logger.error('Got folder fail: {}'.format(traceback.format_exc()))

    def _get_mails(self, fo: Folder) -> iter:
        try:
            self._logger.info(fo.name + ":" + str(fo.mailcount) + "个邮件")
            offset = 0
            while True:
                url = 'https://outlook.live.com/owa/service.svc?action=FindItem&EP=1&ID=-20&AC=1'
                if fo.other:
                    dis = 'DistinguishedFolderId:#Exchange'
                else:
                    dis = "FolderId:#Exchange"
                postdata = f"%7B%22__type%22%3A%22FindItemJsonRequest%3A%23Exchange%22,%22Header%22%3A%7B%22__type%22%3A%22JsonRequestHeaders%3A%23Exchange%22,%22RequestServerVersion%22%3A%22V2018_01_08%22,%22TimeZoneContext%22%3A%7B%22__type%22%3A%22TimeZoneContext%3A%23Exchange%22,%22TimeZoneDefinition%22%3A%7B%22__type%22%3A%22TimeZoneDefinitionType%3A%23Exchange%22,%22Id%22%3A%22China%20Standard%20Time%22%7D%7D%7D,%22Body%22%3A%7B%22__type%22%3A%22FindItemRequest%3A%23Exchange%22,%22ParentFolderIds%22%3A%5B%7B%22__type%22%3A%22{dis}%22,%22Id%22%3A%22{quote_plus(fo.folderid)}%22%7D%5D,%22ItemShape%22%3A%7B%22__type%22%3A%22ItemResponseShape%3A%23Exchange%22,%22BaseShape%22%3A%22IdOnly%22%7D,%22ShapeName%22%3A%22MailListItem%22,%22Traversal%22%3A%22Shallow%22,%22Paging%22%3A%7B%22__type%22%3A%22IndexedPageView%3A%23Exchange%22,%22BasePoint%22%3A%22Beginning%22,%22Offset%22%3A{offset},%22MaxEntriesReturned%22%3A{1000}%7D,%22FocusedViewFilter%22%3A-1,%22ViewFilter%22%3A%22All%22,%22SortOrder%22%3A%5B%7B%22__type%22%3A%22SortResults%3A%23Exchange%22,%22Order%22%3A%22Descending%22,%22Path%22%3A%7B%22__type%22%3A%22PropertyUri%3A%23Exchange%22,%22FieldURI%22%3A%22DateTimeReceived%22%7D%7D%5D,%22CategoryFilter%22%3Anull%7D%7D"
                headers = f"""
Host: outlook.live.com
Connection: keep-alive
Content-Length: 0
Pragma: no-cache
Cache-Control: no-cache
Origin: https://outlook.live.com
x-req-source: Mail
x-owa-canary: {self._outlook_canary}
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
x-owa-urlpostdata: {postdata}
action: FindItem
x-owa-correlationid: {self._outlook_clientid}
ms-cv: sfPFWXRQC/CB23TzXRI4L5.59
content-type: application/json; charset=utf-8
Accept: */*
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: cors
Referer: https://outlook.live.com/
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
"""
                message = self._ha.getstring(url, headers=headers, req_data='')
                for mi in self.parse_mail(message, fo):
                    if not mi:
                        continue
                    stm = self.download_mail(mi)
                    if stm:
                        mi.io_stream = stm
                        yield mi

                offset += 1000
                if offset >= fo.mailcount:
                    break
        except Exception:
            self._logger.error('Got mails fail: {}'.format(traceback.format_exc()))

    def parse_mail(self, message, fo: Folder):
        try:
            sj = json.loads(message)
            respMsgs = sj["Body"]["ResponseMessages"]["Items"]
            if not respMsgs:
                yield
        except:
            return

        for msg in respMsgs:
            items = msg["RootFolder"]["Items"]
            for item in items:
                size = 0
                rcvTime = None
                if not item.__contains__('ItemId') or not item.__contains__('Subject') or not item.__contains__(
                        'IsRead'):
                    continue
                if not item['ItemId'].__contains__('Id'):
                    continue
                id = item["ItemId"]["Id"]
                subject = item["Subject"]
                isRead = item["IsRead"]

                if item.__contains__('DateTimeReceived'):
                    # 2019-03-09T00:52:47+08:00
                    rcvTime = item["DateTimeReceived"]
                    rcvTime = datetime.datetime.strptime(rcvTime, '%Y-%m-%dT%H:%M:%S+08:00') + datetime.timedelta(hours=8)
                if item.__contains__('Size'):
                    size = item["Size"]

                # sender
                # if item.__contains__('IsDraft') and not item["IsDraft"]:
                #     if item.__contains__('Sender') and item['Sender'].__contains__('Mailbox'):
                #         if item["Sender"]["Mailbox"].__contains__('EmailAddress'):
                #             sender = item["Sender"]["Mailbox"]["EmailAddress"]
                #         elif item["Sender"]["Mailbox"].__contains__("Name"):
                #             sender = item["Sender"]["Mailbox"]["Name"]
                #         else:
                #             sender = "Unknow"
                #     elif item.__contains__("From") and item["From"].__contains__("Mailbox"):
                #         if item["From"]["Mailbox"].__contains__("EmailAddress"):
                #             sender = item["From"]["Mailbox"]["EmailAddress"]
                #         elif item["From"]["Mailbox"].__contains__("Name"):
                #             sender = item["From"]["Mailbox"]["Name"]
                #         else:
                #             sender = "Unknow"
                #     else:
                #         sender = "Unknow"
                # else:
                #     sender = self._userid

                m = EML(self._clientid, self.task, self._userid, id, fo, self.task.apptype)
                m.subject = subject
                m.sendtime = rcvTime
                m.provider = 'outlook.live.com'
                if isRead:
                    m.state = 1
                else:
                    m.state = 0
                m.stream_length = size
                yield m

    def download_mail(self, mi: EML):
        stm = None
        try:
            url = f'https://outlook.live.com/owa/service.svc?action=GetItem&EP=1&ID=-20&AC=1'
            postdata = f'%7B%22__type%22%3A%22GetItemJsonRequest%3A%23Exchange%22,%22Header%22%3A%7B%22__type%22%3A%22JsonRequestHeaders%3A%23Exchange%22,%22RequestServerVersion%22%3A%22V2016_06_24%22,%22TimeZoneContext%22%3A%7B%22__type%22%3A%22TimeZoneContext%3A%23Exchange%22,%22TimeZoneDefinition%22%3A%7B%22__type%22%3A%22TimeZoneDefinitionType%3A%23Exchange%22,%22Id%22%3A%22China%20Standard%20Time%22%7D%7D%7D,%22Body%22%3A%7B%22__type%22%3A%22GetItemRequest%3A%23Exchange%22,%22ItemShape%22%3A%7B%22__type%22%3A%22ItemResponseShape%3A%23Exchange%22,%22BaseShape%22%3A%22IdOnly%22,%22IncludeMimeContent%22%3Atrue%7D,%22ItemIds%22%3A%5B%7B%22__type%22%3A%22ItemId%3A%23Exchange%22,%22Id%22%3A%22{mi._mailid}%22%7D%5D,%22ShapeName%22%3Anull%7D%7D'
            heades = f"""
Accept: */*
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
action: GetItem
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 0
content-type: application/json; charset=utf-8
Host: outlook.live.com
ms-cv: sfPFWXRQC/CB23TzXRI4L5.86
Origin: https://outlook.live.com
Pragma: no-cache
Referer: https://outlook.live.com/
Sec-Fetch-Mode: cors
Sec-Fetch-Site: same-origin
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
x-owa-canary: {self._outlook_canary}
x-owa-correlationid: {self._outlook_clientid}
x-owa-urlpostdata: {postdata}
x-req-source: Mail
"""
            html = self._ha.getstring(url, headers=heades, req_data='')
            sj = json.loads(html)
            mailData = sj["Body"]["ResponseMessages"]["Items"][0]["Items"][0]["MimeContent"]["Value"]
            if not mailData:
                self._logger.info('Parse mail fail!')
                return None
            bytes_data = base64.b64decode(mailData)
            stm = io.BytesIO(bytes_data)

        except Exception:
            self._logger.error('Download mail fail: {}'.format(traceback.format_exc()))
        return stm

    def _get_profile(self) -> iter:
        try:
            url = 'https://outlook.live.com/owa/0/sessiondata.ashx?app=Mail'
            headers = """
Host: outlook.live.com
Connection: keep-alive
Content-Length: 0
Pragma: no-cache
Cache-Control: no-cache
Origin: https://outlook.live.com
x-js-clienttype: 2
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36
Accept: */*
Sec-Fetch-Site: same-origin
Sec-Fetch-Mode: cors
Referer: https://outlook.live.com/
Accept-Encoding: gzip, deflate, br
Accept-Language: zh-CN,zh;q=0.9
"""
            html = self._ha.getstring(url, req_data='', headers=headers)
            self._userid = helper_str.substring(html, '"UserEmailAddress":"', '"')
            res = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
            res.nickname = helper_str.substring(html, '"UserDisplayName":"', '"')
            yield res
        except Exception:
            self._logger.error('Got profile fail: {}'.format(traceback.format_exc()))