"""facebook search name"""

# -*- coding:utf-8 -*-

import html as ht
import random
import re
import time
import traceback
import uuid
import urllib
from urllib import parse
import json

from commonbaby.helpers import (helper_crypto, helper_num, helper_str,
                                helper_time)

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import (Email, NetworkProfile,
                                                      Phone)

from .fbsearchuserid_new import FBSearchUserid_new


class FBSearchName_new(FBSearchUserid_new):

    def __init__(self, task: IscoutTask):
        super(FBSearchName_new, self).__init__(task)

    def _search_users_v1(self,
                         account: str,
                         level: int,
                         reason,
                         search_index: int = 0,
                         search_count: int = 10) -> iter:
        """返回 NetworkProfile """
        try:

            if not self._is_logined:
                return
            if reason is None or reason == "":
                raise Exception("Invalid param 'reason', cannot be None.")

            for profile in self.__search_users_v1(account, level, reason,
                                                  search_index, search_count):
                yield profile

        except Exception as ex:
            self._logger.error("搜索用户关键字出错: {}".format(ex.args))

    def __search_users_v1(self,
                          account: str,
                          level: int,
                          reason,
                          search_index: int = 0,
                          search_count: int = 10) -> iter:
        """返回 NetworkProfile """
        try:
            docid_dict = self._get_docid_dict()
            if docid_dict == {} or docid_dict is None:
                self._logger.error("Get docid failed")
                return

            total_count = 0
            bsid = str(uuid.uuid1())
            tsid = str(random.uniform(0, 1))
            # 搜索第一页
            url = 'https://www.facebook.com/api/graphql/'
            variables = f'{{"allow_streaming":false,"args":{{"callsite":"COMET_GLOBAL_SEARCH","config":{{"bootstrap_config":null,"exact_match":false,"high_confidence_config":null,"watch_config":null}},"context":{{"bsid":"{bsid}","tsid":"{tsid}"}},"experience":{{"encoded_server_defined_params":null,"fbid":null,"grammar_bqf":null,"role":null,"type":"PEOPLE_TAB"}},"filters":[],"text":"{account}"}},"cursor":null,"feedbackSource":23,"fetch_filters":true,"renderLocation":null,"scale":1,"stream_initial_count":0}}'
            postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=SearchCometResultsInitialResultsQuery&variables=' + parse.quote(
                variables) + f'&doc_id={docid_dict["SearchCometResultsInitialResultsQuery"]}'
            html = self._ha.getstring(url, postdata,
                                      headers="""
            accept: */*
            accept-encoding: gzip, deflate
            accept-language: zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6
            cache-control: no-cache
            content-type: application/x-www-form-urlencoded
            origin: https://www.facebook.com
            pragma: no-cache
            referer: https://www.facebook.com/search/top?q={}
            sec-fetch-dest: empty
            sec-fetch-mode: cors
            sec-fetch-site: same-origin
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36
            """.format(parse.quote_plus(account)))
            res = json.loads(html)
            if not res.__contains__('data') or \
                    not res['data'].__contains__('serpResponse') or \
                    not res['data']['serpResponse'].__contains__('results'):
                return
            results = res['data']['serpResponse']['results']
            edges: list = results['edges']
            for profile in self._parse_searchname_edges_v1(edges, reason):
                yield profile
                total_count += 1
                if total_count >= search_count:
                    return
            # 翻页
            end_cursor = results['page_info']['end_cursor']
            has_next_page = results['page_info']['has_next_page']
            while has_next_page:
                time.sleep(random.randint(1, 2))
                variables = f'{{"UFI2CommentsProvider_commentsKey":"SearchCometResultsInitialResultsQuery","allow_streaming":false,"args":{{"callsite":"COMET_GLOBAL_SEARCH","config":{{"bootstrap_config":null,"exact_match":false,"high_confidence_config":null,"watch_config":null}},"context":{{"bsid":"{bsid}","tsid":"{tsid}"}},"experience":{{"encoded_server_defined_params":null,"fbid":null,"grammar_bqf":null,"role":null,"type":"PEOPLE_TAB"}},"filters":[],"text":"bobby johnson"}},"count":5,"cursor":"{end_cursor}","displayCommentsContextEnableComment":false,"displayCommentsContextIsAdPreview":false,"displayCommentsContextIsAggregatedShare":false,"displayCommentsContextIsStorySet":false,"displayCommentsFeedbackContext":null,"feedLocation":"SEARCH","feedbackSource":23,"fetch_filters":true,"focusCommentID":null,"locale":null,"privacySelectorRenderLocation":"COMET_STREAM","renderLocation":null,"scale":1,"stream_initial_count":0,"useDefaultActor":false}}'
                postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=SearchCometResultsPaginatedResultsQuery&variables=' + parse.quote(
                    variables) + f'&doc_id={docid_dict["SearchCometResultsPaginatedResultsQuery"]}'
                html = self._ha.getstring(url, postdata,
                                          headers="""
                                accept: */*
                                accept-encoding: gzip, deflate
                                accept-language: zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6
                                cache-control: no-cache
                                content-type: application/x-www-form-urlencoded
                                origin: https://www.facebook.com
                                pragma: no-cache
                                referer: https://www.facebook.com/search/top?q={}
                                sec-fetch-dest: empty
                                sec-fetch-mode: cors
                                sec-fetch-site: same-origin
                                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36
                                """.format(parse.quote_plus(account)))
                res = json.loads(html)
                if not res.__contains__('data') or \
                        not res['data'].__contains__('serpResponse') or \
                        not res['data']['serpResponse'].__contains__('results'):
                    return
                results = res['data']['serpResponse']['results']
                edges: list = results['edges']
                for profile in self._parse_searchname_edges_v1(edges, reason):
                    yield profile
                    total_count += 1
                    if total_count >= search_count:
                        return
                end_cursor = results['page_info']['end_cursor']
                has_next_page = results['page_info']['has_next_page']

        except Exception as ex:
            self._logger.error(
                "Search user by name error: name:{} error:{}".format(
                    account, ex.args))

    def _parse_searchname_edges_v1(self,
                                   edges: list,
                                   reason: str = None) -> iter:
        try:
            for edge in edges:
                if not edge.__contains__('relay_rendering_strategy') or \
                    not edge['relay_rendering_strategy'].__contains__('view_model') or \
                        not edge['relay_rendering_strategy']['view_model'].__contains__('profile'):
                    continue
                profile_info = edge['relay_rendering_strategy']['view_model']['profile']
                username = profile_info['name']
                userid = profile_info['id']
                userurl = profile_info['url']

                profile = NetworkProfile(username, userid, self._SOURCE)
                profile.url = userurl
                profile.reason = reason
                yield profile
        except Exception:
            self._logger.error("Parse searchname edges failed: {}".format(
                traceback.format_exc()))