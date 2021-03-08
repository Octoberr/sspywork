"""messenger base"""
"""zimbra 6.0.6_GA_2330"""

# -*- coding:utf-8 -*-

import datetime
import json
import re
import traceback
import base64

from urllib import parse
from commonbaby.helpers import helper_str
from commonbaby.httpaccess import ResponseIO

from ...clientdatafeedback import CONTACT_ONE, CONTACT, EML, Folder, PROFILE
from .spidermailbase import SpiderMailBase


class SpiderZimbra(SpiderMailBase):

    _re_folders = re.compile(r'var batchInfoResponse = (.*?);', re.S)

    # 匹配邮箱地址
    _re_email = re.compile(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
    # "xxx" <156846131@mail.com>, "admin" <admin@nmsb.com>, "dotatom233" <dotatom233@tom.com>
    _re_name_email = re.compile(r'"(.+)" <([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)>')

    def __init__(self, task, appcfg, clientid):
        super(SpiderZimbra, self).__init__(task, appcfg, clientid)

        self._host: str = None
        self._version: str = None
        self._sessionid: str = None
        self._authtoken: str = None
        self._homepage: str = None
        # 本地测试用的http
        self._scheme = 'http'
        if appcfg._ishttps:
            self._scheme = 'https'

    def _check_registration(self) -> bool:
        """check if an email account registered"""
        return False

    def _cookie_login(self):
        res = False
        try:
            if not self.task.host:
                self._logger.error("Login failed: Task's host is None")
                return res
            self._host = self.task.host.strip()
            self._ha._managedCookie.add_cookies(self.task.host, self.task.cookie)

            url = '{}://{}/zimbra/'.format(self._scheme, self._host)
            html = self._ha.getstring(url,
                                      headers='''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: max-age=0
            Connection: keep-alive
            Host: {0}
            Referer: http://{0}/
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36
            '''.format(self._host))

            # "refresh":{"version":"6.0.6_GA_2330.UBUNTU8_64 20100505202919 20100505-2031 FOSS",
            succ, self._version = helper_str.substringif(
                html, '"refresh":{"version":"', '"')
            if not succ:
                self._logger.error("Get 'version' failed, login failed.")
                return res
            self._version = self._version.split(' ')[0]
            if self._version is None or self._version == "":
                self._logger.error("Get 'version' failed, login failed.")
                return res

            # var batchInfoResponse = {"Header":{"context":{"session":{"id":"1109","_content":"1109"},"refresh"
            succ, self._sessionid = helper_str.substringif(
                html, '{"Header":{"context":{"session":{"id":"', '"')
            if not succ or self._sessionid is None or self._sessionid == "":
                self._logger.error("Get 'sessionid' failed, login failed.")
                return res

            # "zimbraPrefFromAddress":"nmsb@nmsb.com"
            succ, self._account = helper_str.substringif(
                html, '"zimbraPrefFromAddress":"', '"')
            if not succ or self._account is None or self._account == "":
                self._logger.error("Get account failed, login failed.")
                return res

            # 只在cookie里面找到了这个参数
            self._authtoken = self._ha.cookies.get('ZM_AUTH_TOKEN')
            if not self._authtoken:
                self._logger.error("Get 'authtoken' failed, login failed.")
                return res

            self._homepage = html

            res = True

        except Exception:
            self._logger.error(f'cookielogin failed: {traceback.format_exc()}')
        return res

    def _pwd_login(self) -> bool:
        res = False
        try:
            if not self.task.host:
                self._logger.error("Login failed: Task's host is None")
                return res
            self._host = self.task.host.strip()
            # 登录页面
            url = '{}://{}'.format(self._scheme, self._host.strip())
            self._ha.getstring(url, headers='''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Host: {}
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36
            '''.format(self._host))

            # post
            url = '{}://{}/zimbra/'.format(self._scheme, self._host)
            form_data = 'loginOp=login&username={}&password={}&client=preferred'.format(
                parse.quote_plus(self.task.account),
                parse.quote_plus(self.task.password))
            html, reurl = self._ha.getstring_unredirect(url,
                                                        form_data,
                                                        headers='''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Content-Type: application/x-www-form-urlencoded
            Host: {0}
            Origin: http://{0}
            Referer: http://{0}/
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36
            '''.format(self._host))

            if reurl is None or reurl == "":
                self._logger.error(
                    "Get redirect url failed, login failed".format())
                return res

            html = self._ha.getstring(reurl,
                                      headers='''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: max-age=0
            Connection: keep-alive
            Host: {0}
            Referer: http://{0}/
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36
            '''.format(self._host))

            # "refresh":{"version":"6.0.6_GA_2330.UBUNTU8_64 20100505202919 20100505-2031 FOSS",
            succ, self._version = helper_str.substringif(
                html, '"refresh":{"version":"', '"')
            if not succ:
                self._logger.error("Get 'version' failed, login failed.")
                return res
            self._version = self._version.split(' ')[0]
            if self._version is None or self._version == "":
                self._logger.error("Get 'version' failed, login failed.")
                return res

            # var batchInfoResponse = {"Header":{"context":{"session":{"id":"1109","_content":"1109"},"refresh"
            succ, self._sessionid = helper_str.substringif(
                html, '{"Header":{"context":{"session":{"id":"', '"')
            if not succ or self._sessionid is None or self._sessionid == "":
                self._logger.error("Get 'sessionid' failed, login failed.")
                return res

            # "zimbraPrefFromAddress":"nmsb@nmsb.com"
            succ, self._account = helper_str.substringif(
                html, '"zimbraPrefFromAddress":"', '"')
            if not succ or self._account is None or self._account == "":
                self._logger.error("Get account failed, login failed.")
                return res

            # 只在cookie里面找到了这个参数
            self._authtoken = self._ha.cookies.get('ZM_AUTH_TOKEN')
            if not self._authtoken:
                self._logger.error("Get 'authtoken' failed, login failed.")
                return res

            self._homepage = html

            res = True

        except Exception:
            self._logger.error('Pwd login failed: {}'.format(
                traceback.format_exc()))
        return res

    def _get_folders(self):
        try:
            m = SpiderZimbra._re_folders.search(self._homepage)
            if m is None:
                self._logger.error("Get folder list json failed.")
                return

            jf = json.loads(m.group(1))
            if not jf.__contains__("Header") or \
                not jf["Header"].__contains__("context") or \
                not jf["Header"]["context"].__contains__("refresh") or\
                not jf["Header"]["context"]["refresh"].__contains__("folder"):
                self._logger.error("Folder list not found in json.")
                return
            infos = jf["Header"]["context"]["refresh"]["folder"][0]["folder"]
            for info in infos:
                # 取Drafts,Inbox,Junk,Sent,Trash和其他用户创建的文件夹
                if info['name'] not in ['Briefcase', 'Calendar', 'Chats', 'Contacts', 'Emailed Contacts', 'Notebook', 'Tasks']:
                    f = Folder()
                    f.name = info['name']
                    f.folderid = info['id']
                    yield f

        except Exception:
            self._logger.error('Get folder fail:{}'.format(
                traceback.format_exc()))

    def _get_mails(self, folder: Folder):
        try:
            url = '{}://{}/service/soap/SearchRequest'.format(self._scheme, self._host)
            payload = {
                "Header": {
                    "context": {
                        "_jsns": 'urn:zimbra',
                        "userAgent": {
                            "name": "ZimbraWebClient - SAF3 (Win)",
                            "version": self._version
                        },
                        "session": {
                            "_content": self._sessionid,
                            "id": self._sessionid
                        },
                        "account": {
                            "_content": self._account,
                            "by": "name"
                        },
                        "authToken": self._authtoken
                    }
                },
                "Body": {
                    "SearchRequest": {
                        "_jsns": "urn:zimbraMail",
                        "sortBy": "dateDesc",
                        "tz": {
                            "id": "Asia/Hong_Kong"
                        },
                        "locale": {
                            "_content": "zh_CN"
                        },
                        "offset": 0,
                        "limit": 100,
                        "query": "in:\"{}\"".format(folder.name),
                        "types": "conversation",
                        "recip": 1
                    }
                }
            }
            html = self._ha.getstring(url,
                                      req_data='',
                                      json=payload,
                                      headers='''
            Accept: */*
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Connection: keep-alive
            Content-Type: application/soap+xml; charset=UTF-8
            Host: 169.254.75.129
            Origin: http://{0}
            Referer: http://{0}/zimbra/
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36
            '''.format(self._host))
            res = json.loads(html)

            if not res.__contains__('Body') or \
                    not res['Body'].__contains__('SearchResponse') or \
                    not res['Body']['SearchResponse'].__contains__('c'):
                return

            mail_list = res['Body']['SearchResponse']['c']
            for mail_info in mail_list:
                # mailid是负数
                mailid = str(mail_info['id'])
                sendtime = int(mail_info['sf'])//1000
                eml = EML(self._clientid, self.task, self._userid, mailid, folder, self.task.apptype)
                eml.sendtime = datetime.datetime.fromtimestamp(sendtime)
                eml_info = self._download_eml(mailid[1:])
                eml.io_stream = eml_info[0]
                eml.stream_length = eml_info[1]
                yield eml
            last_mail_id = mail_list[-1]['id']
            last_mail_sendtime = mail_list[-1]['sf']
            more = res['Body']['SearchResponse']['more']
            if more:
                for eml in self._get_mails_next_page(last_mail_id, last_mail_sendtime, folder):
                    yield eml
        except:
            self._logger.error('Get mail fail: {}'.format(
                traceback.format_exc()))

    def _get_mails_next_page(self, last_mail_id, last_mail_sendtime, folder: Folder):
        try:
            has_next_page = True
            offset = 100
            while has_next_page:
                url = '{}://{}/service/soap/SearchRequest'.format(self._scheme, self._host)
                payload = {
                    "Header": {
                        "context": {
                            "_jsns": "urn:zimbra",
                            "userAgent": {
                                "name": "ZimbraWebClient - SAF3 (Win)",
                                "version": self._version
                            },
                            "session": {
                                "_content": self._sessionid,
                                "id": self._sessionid
                            },
                            "account": {
                                "_content": self._account,
                                "by": "name"
                            },
                            "authToken": self._authtoken
                        }
                    },
                    "Body": {
                        "SearchRequest": {
                            "_jsns": "urn:zimbraMail",
                            "sortBy": "dateDesc",
                            "tz": {
                                "id": "Asia/Hong_Kong"
                            },
                            "locale": {
                                "_content": "zh_CN"
                            },
                            "cursor": {
                                "id": last_mail_id,
                                "sortVal": last_mail_sendtime
                            },
                            "offset": offset,
                            "limit": 50,
                            "query": "in:\"{}\"".format(folder.name),
                            "types": "conversation",
                            "fetch": 1
                        }
                    }
                }
                html = self._ha.getstring(url,
                                          req_data='',
                                          json=payload,
                                          headers='''
                            Accept: */*
                            Accept-Encoding: gzip, deflate
                            Accept-Language: zh-CN,zh;q=0.9
                            Connection: keep-alive
                            Content-Type: application/soap+xml; charset=UTF-8
                            Host: 169.254.75.129
                            Origin: http://{0}
                            Referer: http://{0}/zimbra/
                            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36
                            '''.format(self._host))
                res = json.loads(html)
                if not res.__contains__('Body') or \
                        not res['Body'].__contains__('SearchResponse') or \
                        not res['Body']['SearchResponse'].__contains__('c'):
                    return

                mail_list = res['Body']['SearchResponse']['c']
                for mail_info in mail_list:
                    # mailid是负数
                    mailid = str(mail_info['id'])
                    sendtime = int(mail_info['sf'])//1000
                    eml = EML(self._clientid, self.task, self._userid, mailid, folder, self.task.apptype)
                    eml.sendtime = datetime.datetime.fromtimestamp(sendtime)
                    eml_info = self._download_eml(mailid[1:])
                    eml.io_stream = eml_info[0]
                    eml.stream_length = eml_info[1]
                    yield eml
                last_mail_id = mail_list[-1]['id']
                last_mail_sendtime = mail_list[-1]['sf']
                has_next_page = res['Body']['SearchResponse']['more']
                offset += 50
        except Exception:
            self._logger.error('Get mail next page fail: {}'.format(
                traceback.format_exc()))

    def _download_eml(self, mailid):
        try:
            url = '{}://{}/service/home/~/?auth=co&id={}'.format(self._scheme, self._host, mailid)
            resp = self._ha.get_response(url, headers='''
            Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            Accept-Encoding: gzip, deflate
            Accept-Language: zh-CN,zh;q=0.9
            Cache-Control: max-age=0
            Connection: keep-alive
            Host: {}
            Upgrade-Insecure-Requests: 1
            User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36
            '''.format(self._host))
            stream_length = resp.headers.get('Content-Length', 0)
            eml = ResponseIO(resp)
            return eml, stream_length
        except Exception:
            self._logger.error('Download mail fail: {}'.format(
                traceback.format_exc()))

    def _get_profile(self) -> PROFILE:
        try:
            if self._account is None:
                self._logger.error('Get account failed')
                return
            self._userid = self._account
            profile = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
            yield profile
        except Exception:
            self._logger.error('Get profile failed: {}'.format(
                traceback.format_exc()))

    def _get_contacts(self) -> iter:
        """把联系人和联系人组都当做Contact输出"""
        try:
            url = '{}://{}/service/soap/SearchRequest'.format(self._scheme, self._host)
            payload = {
                "Header": {
                    "context": {
                        "_jsns": "urn:zimbra",
                        "userAgent": {
                            "name": "ZimbraWebClient - SAF3 (Win)",
                            "version": self._version
                        },
                        "session": {
                            "_content": self._sessionid,
                            "id": self._sessionid
                        },
                        "notify": {
                            "seq": 1
                        },
                        "account": {
                            "_content": self._account,
                            "by": "name"
                        },
                        "authToken": self._authtoken
                    }
                },
                "Body": {
                    "SearchRequest": {
                        "_jsns": "urn:zimbraMail",
                        "sortBy": "nameAsc",
                        "tz": {
                            "id": "Asia/Hong_Kong"
                        },
                        "locale": {
                            "_content": "zh_CN"
                        },
                        "offset": 0,
                        "limit": 100,
                        "query": "in:\"contacts\"",
                        "types": "contact",
                        "fetch": 1
                    }
                }
            }
            html = self._ha.getstring(url,
                                      req_data='',
                                      json=payload,
                                      headers='''
                        Accept: */*
                        Accept-Encoding: gzip, deflate
                        Accept-Language: zh-CN,zh;q=0.9
                        Connection: keep-alive
                        Content-Type: application/soap+xml; charset=UTF-8
                        Host: 169.254.75.129
                        Origin: http://{0}
                        Referer: http://{0}/zimbra/
                        User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36
                        '''.format(self._host))
            res = json.loads(html)
            if not res.__contains__('Body') or \
                    not res['Body'].__contains__('SearchResponse') or \
                    not res['Body']['SearchResponse'].__contains__('cn'):
                return
            contact_list = res['Body']['SearchResponse']['cn']
            con_all = CONTACT(self._clientid, self.task, self.task.apptype)

            # 建两个字典用来去重
            c_temp, g_temp = {}, {}
            for contact in contact_list:
                contact_id = contact['id']
                attrs = contact['_attrs']
                # 联系人组
                if 'type' in attrs and attrs['type'] == 'group':
                    group_name = attrs['nickname']
                    email_info = attrs['dlist']
                    g_temp[group_name] = email_info
                # 联系人
                elif 'email' in attrs:
                    email = attrs['email']
                    if email not in c_temp:
                        con_one = CONTACT_ONE(self._userid, contact_id, self.task, self.task.apptype)
                        con_one.nickname = contact['fileAsStr']
                        con_one.email = attrs['email']
                        c_temp[email] = con_one
            # 翻页
            more = res['Body']['SearchResponse']['more']
            if more:
                last_contact_id = contact_list[-1]['id']
                last_contact_sf = contact_list[-1]['sf']
                c_temp, g_temp = self._get_contacts_next_page(last_contact_id, last_contact_sf, c_temp, g_temp)
            # 去重,处理分组
            for group_name in g_temp:
                email_info: str = g_temp[group_name]
                for group_one in email_info.strip().split(','):
                    group_one = group_one.strip()
                    m1 = SpiderZimbra._re_name_email.match(group_one)
                    m2 = SpiderZimbra._re_email.match(group_one)
                    email, nickname = None, None
                    if m1 is not None:
                        email = m1.group(2)
                        nickname = m1.group(1)
                    elif m2 is not None:
                        email = m2.group(1)

                    if email is not None:
                        # 不是重复的就加到c_temp里面
                        if email not in c_temp:
                            con_one = CONTACT_ONE(self._userid, email, self.task, self.task.apptype)
                            if nickname is not None:
                                con_one.nickname = nickname
                            con_one.email = email
                            con_one.group = group_name
                            c_temp[email] = con_one
                        # 如果存在，添加分组信息
                        else:
                            for con_one in c_temp.values():
                                if con_one.email == email:
                                    if con_one.group is not None:
                                        con_one.group += ' ' + group_name
                                    else:
                                        con_one.group = group_name
                                    break

            # 返回
            for con_one in c_temp.values():
                if con_one.group is not None:
                    con_one.group = '=?utf-8?b?' + str(base64.b64encode(con_one.group.encode('utf-8')), 'utf-8')
                con_all.append_innerdata(con_one)
            if con_all.innerdata_len > 0:
                yield con_all
        except Exception:
            self._logger.error('Get contacts failed: {}'.format(
                traceback.format_exc()))

    def _get_contacts_next_page(self, last_contact_id, last_contact_sf, c_temp, g_temp):
        try:
            has_next_page = True
            offset = 100
            while has_next_page:
                url = '{}://{}/service/soap/SearchRequest'.format(self._scheme, self._host)
                payload = {
                    "Header": {
                        "context": {
                            "_jsns": "urn:zimbra",
                            "userAgent": {
                                "name": "ZimbraWebClient - SAF3 (Win)",
                                "version": self._version
                            },
                            "session": {
                                "_content": self._sessionid,
                                "id": self._sessionid,
                            },
                            "notify": {
                                "seq": 1
                            },
                            "account": {
                                "_content": self._account,
                                "by": "name"
                            },
                            "authToken": self._authtoken
                        }
                    },
                    "Body": {
                        "SearchRequest": {
                            "_jsns": "urn:zimbraMail",
                            "sortBy": "nameAsc",
                            "tz": {
                                "id": "Asia/Hong_Kong"
                            },
                            "locale": {
                                "_content": "zh_CN"
                            },
                            "cursor": {
                                "id": last_contact_id,
                                "sortVal": last_contact_sf
                            },
                            "offset": offset,
                            "limit": 50,
                            "query": "in:\"contacts\"",
                            "types": "contact"
                        }
                    }
                }
                html = self._ha.getstring(url,
                                          req_data='',
                                          json=payload,
                                          headers='''
                Accept: */*
                Accept-Encoding: gzip, deflate
                Accept-Language: zh-CN,zh;q=0.9
                Connection: keep-alive
                Content-Type: application/soap+xml; charset=UTF-8
                Host: 169.254.75.129
                Origin: http://{0}
                Referer: http://{0}/zimbra/
                User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36
                '''.format(self._host))
                res = json.loads(html)
                if not res.__contains__('Body') or \
                        not res['Body'].__contains__('SearchResponse') or \
                        not res['Body']['SearchResponse'].__contains__('cn'):
                    return
                contact_list = res['Body']['SearchResponse']['cn']
                for contact in contact_list:
                    contact_id = contact['id']
                    attrs = contact['_attrs']
                    # 联系人组
                    if 'type' in attrs and attrs['type'] == 'group':
                        group_name = attrs['nickname']
                        email_info = attrs['dlist']
                        g_temp[group_name] = email_info
                    # 联系人
                    elif 'email' in attrs:
                        email = attrs['email']
                        if email not in c_temp:
                            con_one = CONTACT_ONE(self._userid, contact_id, self.task, self.task.apptype)
                            con_one.nickname = contact['fileAsStr']
                            con_one.email = attrs['email']
                            c_temp[email] = con_one
                # 翻页
                last_contact_id = contact_list[-1]['id']
                last_contact_sf = contact_list[-1]['sf']
                has_next_page = res['Body']['SearchResponse']['more']
                offset += 50
            return c_temp, g_temp
        except Exception:
            self._logger.error('Get contacts next page failed: {}'.format(
                traceback.format_exc()))
