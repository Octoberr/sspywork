"""messenger profile"""

# -*- coding:utf-8 -*-

import traceback
from urllib import parse

from commonbaby.helpers import helper_str
from commonbaby.httpaccess import ResponseIO

from datacontract.idowndataset import Task
from .messengerlogout import MessengerLogout
from ....clientdatafeedback import (PROFILE, RESOURCES, EGender, EResourceType,
                                    ESign)


class MessengerProfile(MessengerLogout):
    """"""

    def __init__(self, task: Task, appcfg, clientid):
        MessengerLogout.__init__(self, task, appcfg, clientid)

    def _get_profile_(self) -> iter:
        """拿个人信息和个人头像，返回两个数据"""
        try:
            if helper_str.is_none_or_empty(self.docid_profile):
                if not self._get_docid_profile():
                    return

            url = "https://www.facebook.com/api/graphqlbatch/"
            postdata = (
                    '__user=' + parse.quote_plus(self._userid) + '&__a=1&__req=' +
                    self._req.get_next() + '&__be=1&__pc=PHASED%3ADEFAULT&__rev=' +
                    parse.quote_plus(self._rev) + '&fb_dtsg=' + parse.quote_plus(
                self.fb_dtsg) + '&jazoest=' + parse.quote_plus(
                self.jazoest) + '&__spin_r=' +
                    parse.quote_plus(self._rev) + '&__spin_b=' + parse.quote_plus(
                self._spin_b) + '&__spin_t=' + parse.quote_plus(
                self._spin_t) +
                    r'&queries=%7B%22o0%22%3A%7B%22doc_id%22%3A%22' +
                    parse.quote_plus(self.docid_profile) + r'%22%7D%7D')
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
                referer: https://www.facebook.com/
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.84 Safari/537.36"""
            )

            if html is None or html == '':
                self._logger.error("Get profile failed")
                return

            html = html.strip().replace('\\', '').replace('\\r', '').replace(
                '\\n', '').replace(' ', '')
            # .replace('\r', '').replace('\n', '')
            sj = self._parse_js(html)
            if sj is None:
                html = html.strip().replace(' ', '')
                sj = self._parse_js(html)
                if sj is None:
                    raise Exception("Parse detailed profile json failed.")

            # 个人信息
            if not sj.__contains__('o0') or not sj['o0'].__contains__(
                    'data') or not sj['o0']['data'].__contains__('me'):
                raise Exception("Parse from detailed profile json failed.")
            sjme = sj['o0']['data']['me']

            profile = PROFILE(self._clientid, self.task, self.task.apptype,
                              self._userid)
            profile.phone = self.phone
            profile.account = self.uname_str

            if self._username is None or self._username == "":
                if sjme.__contains__('name'):
                    self._username = sjme['name']
            profile.nickname = self._username
            if sjme.__contains__('gender'):
                gender = sjme['gender']
                if gender == 'FEMALE':
                    profile.gender = EGender.Female
                if gender == 'MALE':
                    profile.gender = EGender.Male

            # 头像
            if sjme.__contains__('large_profile_picture') and sjme[
                'large_profile_picture'].__contains__('uri'):
                profilepicurl = sjme['large_profile_picture']['uri']
                resp: ResponseIO = self._ha.get_response_stream(
                    profilepicurl,
                    headers="""
                    accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                    accept-encoding: gzip, deflate, br
                    accept-language: zh-CN,zh;q=0.9
                    cache-control: no-cache
                    pragma: no-cache
                    upgrade-insecure-requests: 1""")

                profilepic = RESOURCES(self._clientid, self.task,
                                       profilepicurl, EResourceType.Picture,
                                       self.task.apptype)
                profilepic.io_stream = resp
                profilepic.sign = ESign.PicUrl
                profile.append_resource(profilepic)

                yield profilepic

            yield profile

        except Exception:
            self._logger.error(
                "Get profile errorex:%s" % traceback.format_exc())

    def _get_docid_profile(self):
        """获取个人信息的那个docid"""
        res: bool = False
        try:
            for urljs, js in self._get_js_resources():
                try:
                    if helper_str.is_none_or_empty(
                            js
                    ) or not '"FBStoriesBucketsQueryWebGraphQLQuery",["WebGraphQLQueryBase"]' in js:
                        continue

                    js = js[js.index(
                        '__d("FBStoriesBucketsQueryWebGraphQLQuery"'):]
                    # c.__getDocID=function(){"use strict";return"2392075840832371"};
                    res, self.docid_profile = helper_str.substringif(
                        js, '.__getDocID=function(){"use strict";return"', '"')
                    if res and not self.docid_profile is None and self.docid_profile != "":
                        break
                    res, self.docid_profile = helper_str.substringif(
                        js, '__getDocID=function(){return"', '"')
                    if res and not self.docid_profile is None and self.docid_profile != "":
                        break

                except Exception:
                    self._logger.error("Access urldocid error: {}".format(
                        traceback.format_exc()))

            if not res:
                self._logger.error("Get docid for profile failed: {}".format(
                    self.uname_str))

        except Exception:
            self._logger.error(
                "Get docid for profile error:%s" % traceback.format_exc())
        return res
