"""facebook contacts"""

# -*- coding:utf-8 -*-

import re
import time
import traceback
from urllib import parse
import json
import random
import base64

from commonbaby.helpers import helper_str, helper_time

from datacontract.iscoutdataset import IscoutTask

from ....clientdatafeedback.scoutdatafeedback import (NetworkProfile,
                                                      NetworkProfiles)
from .fbprofile_new import FBProfile_new
from .fblogin import FBLogin


class FBContacts_new(FBProfile_new):
    """FB contacts"""

    # "node": {
    #     "displayable_count": 224,
    #     "name": "\u597d\u53cb",
    #     "section_type": "FRIENDS",
    #     "tab_key": "friends",
    #     "tracking": "friends",
    #     "url": "https:\/\/www.facebook.com\/bichhau.bui.5249\/friends",
    #     "all_collections": {
    #         "nodes": [{"tab_key": "friends_all",
    #                   "id": "YXBwX2NvbGxlY3Rpb246MTAwMDU0NDc3NTg1MDg5OjIzNTYzMTgzNDk6Mg=="},
    #                   {...}]
    #     },
    #     "id": "YXBwX3NlY3Rpb246MTAwMDU0NDc3NTg1MDg5OjIzNTYzMTgzNDk="
    # }
    _re_friends = re.compile(
        r'"name":"\\u597d\\u53cb","section_type":"FRIENDS".*?"all_collections":\{"nodes":(\[.*?\])\},"id":"(.*?)"\}',
        re.S)

    # [{"tab_key": "friends_all", "id": "YXBwX2NvbGxlY3Rpb246MTAwMDUwMzYyMTUzNTk2OjIzNTYzMTgzNDk6Mg=="},
    #  {"tab_key": "friends_mutual", "id": "YXBwX2NvbGxlY3Rpb246MTAwMDUwMzYyMTUzNTk2OjIzNTYzMTgzNDk6Mw=="},
    #  {"tab_key": "friends_recent",
    _re_collection_token = re.compile(
        r'\{"tab_key":"friends_all","id":"(.*?)"', re.S)

    def __init__(self, task: IscoutTask):
        super(FBContacts_new, self).__init__(task)

    def _get_contacts_by_userid_v1(self,
                                   task: IscoutTask,
                                   userid: str,
                                   reason: str = None,
                                   get_profile_pic: bool = False) -> iter:
        '''根据userid确定用户，并获取此用户的好友'''
        try:
            hostuser: NetworkProfile = self._get_user_by_userid_v1(userid)
            if not isinstance(hostuser, NetworkProfile):
                return

            for ct in self._get_contacts_v1(task,
                                            hostuser,
                                            reason,
                                            get_profile_pic=get_profile_pic):
                yield ct

        except Exception as ex:
            self._logger.error("Get contacts by userid error: {}".format(
                ex.args))

    def _get_contacts_by_url_v1(self,
                                task: IscoutTask,
                                userurl: str,
                                reason: str = None,
                                get_profile_pic: bool = False) -> iter:
        """get contacts by url"""
        try:
            hostuser: NetworkProfile = self._get_user_by_url_v1(
                userurl, reason=reason, get_profile_pic=get_profile_pic)
            if not isinstance(hostuser, NetworkProfile):
                return

            for ct in self._get_contacts_v1(task,
                                            hostuser,
                                            reason,
                                            get_profile_pic=get_profile_pic):
                yield ct

        except Exception as ex:
            self._logger.error("Get contacts by userurl error: {}".format(
                ex.args))

    def _get_contacts_v1(self,
                         task: IscoutTask,
                         hostuser: NetworkProfile,
                         reason: str = None,
                         get_profile_pic: bool = False) -> iter:
        """
        get contacts
        只抓了好友
        """
        try:
            if not isinstance(hostuser, NetworkProfile):
                return

            collection_token, section_token = self._get_contacts_params_v1(hostuser)
            if collection_token == '' or section_token == '':
                return
            docid_dict = self._get_docid_dict()
            if docid_dict == {} or docid_dict is None:
                self._logger.error("Get docid failed")
                return

            total_count = 0
            url = 'https://www.facebook.com/api/graphql/'
            variables = '{' + f'"collectionToken":"{collection_token}","scale":1,"sectionToken":"{section_token}","userID":"{hostuser._userid}"' + '}'
            postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=ProfileCometTopAppSectionQuery&variables=' + parse.quote(
                variables) + f'&doc_id={docid_dict["ProfileCometTopAppSectionQuery"]}'
            html = self._ha.getstring(url, postdata,
                                      headers="""
                        accept: */*
                        accept-encoding: gzip, deflate
                        accept-language: en-US,en;q=0.9,zh;q=0.8
                        content-length: {}
                        content-type: application/x-www-form-urlencoded
                        origin: https://www.facebook.com
                        referer: {}
                        sec-fetch-dest: empty
                        sec-fetch-mode: cors
                        sec-fetch-site: same-origin
                        user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                        """.format(len(postdata), hostuser.url))
            res = json.loads(html)
            if not res.__contains__('data') \
                    or not res['data'].__contains__('node') \
                    or not res['data']['node'].__contains__('all_collections') \
                    or not res['data']['node']['all_collections'].__contains__('nodes'):
                return
            nodes: list = res['data']['node']['all_collections']['nodes']
            # nodes为[]表示好友不可见
            if not nodes:
                self._logger.info("Fb contacts not visible of user {}({})".format(hostuser.nickname, hostuser._userid))
                return
            # 获取好友列表翻页需要的docid
            if not FBLogin._docid_dict.__contains__('ProfileCometAppCollectionListRendererPaginationQuery'):
                with FBLogin._docid_dict_locker:
                    resources: list = res['extensions']['sr_payload']['ddd']['allResources']
                    rsrcmap: dict = res['extensions']['sr_payload']['ddd']['hsrp']['hblp']['rsrcMap']
                    for rs in resources:
                        if rs in rsrcmap and rsrcmap[rs]['type'] == 'js':
                            js_src = rsrcmap[rs]['src']
                            if js_src.startswith('https://'):
                                js = self._ha.getstring(js_src, headers='''
                                                    Origin: https://www.facebook.com
                                                    Referer: https://www.facebook.com/
                                                    user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36''')
                            else:
                                js_b64 = js_src.split(',')[-1]
                                js = base64.b64decode(js_b64).decode()
                            if js.__contains__('ProfileCometAppCollectionListRendererPaginationQuery'):
                                m = FBLogin._re_docid_ProfileCometAppCollectionListRendererPaginationQuery.search(js)
                                if not m is None:
                                    docid = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                                    FBLogin._docid_dict['ProfileCometAppCollectionListRendererPaginationQuery'] = docid
                                    break
                if not FBLogin._docid_dict.__contains__('ProfileCometAppCollectionListRendererPaginationQuery'):
                    raise Exception('get contacts nextpage docid fail!')
                docid_dict = FBLogin._docid_dict

            # 开始处理好友信息
            for node in nodes:
                if not node.__contains__('style_renderer') \
                        or not node['style_renderer'].__contains__('collection'):
                    continue
                collection = node['style_renderer']['collection']
                count = collection['items']['count']
                self._logger.info("Find fb contacts count {} of user {}({})".format(
                    count, hostuser.nickname, hostuser._userid))

                edges: list = collection['pageItems']['edges']
                for ct in self._parse_contact_edges_v1(edges, hostuser, reason, get_profile_pic):
                    yield ct
                    total_count += 1

                end_cursor = collection['pageItems']['page_info']['end_cursor']
                has_next_page = collection['pageItems']['page_info']['has_next_page']

                if has_next_page:
                    for ct in self._get_contacts_nextpage_v1(collection_token, end_cursor, hostuser, reason, get_profile_pic):
                        yield ct
                        total_count += 1

            self._logger.info("Got {} contacts of user {}({})".format(
                total_count, hostuser.nickname, hostuser._userid))
        except Exception as ex:
            self._logger.error("Get contacts by userurl error: {}".format(
                ex.args))

    def _get_contacts_nextpage_v1(self,
                                  collection_token: str,
                                  end_cursor: str,
                                  hostuser: NetworkProfile,
                                  reason: str = None,
                                  get_profile_pic: bool = False) -> iter:
        """get contacts"""
        try:
            docid_dict = self._get_docid_dict()
            if docid_dict == {} or docid_dict is None:
                self._logger.error("Get docid failed")
                return

            url = 'https://www.facebook.com/api/graphql/'
            has_next_page = True
            while has_next_page:
                has_next_page = False
                # 一次最多能拉16人, count超过16没用
                # 每次请求间隔
                time.sleep(random.randint(1, 2))
                variables = '{' + f'"count":16,"cursor":"{end_cursor}","scale":1,"search":null,"id":"{collection_token}"' + '}'
                postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=ProfileCometAppCollectionListRendererPaginationQuery&variables=' + parse.quote(
                    variables) + f'&doc_id={docid_dict["ProfileCometAppCollectionListRendererPaginationQuery"]}'
                html = self._ha.getstring(url, postdata,
                                          headers="""
                accept: */*
                accept-encoding: gzip, deflate
                accept-language: en-US,en;q=0.9,zh;q=0.8
                content-length: {}
                content-type: application/x-www-form-urlencoded
                origin: https://www.facebook.com
                referer: {}
                sec-fetch-dest: empty
                sec-fetch-mode: cors
                sec-fetch-site: same-origin
                user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36
                """.format(len(postdata), hostuser.url))
                res = json.loads(html)
                if not res.__contains__('data') \
                        or not res['data'].__contains__('node') \
                        or not res['data']['node'].__contains__('pageItems'):
                    return
                page_items = res['data']['node']['pageItems']
                if page_items.__contains__('edges'):
                    edges: list = page_items['edges']
                    for ct in self._parse_contact_edges_v1(edges, hostuser, reason, get_profile_pic):
                        if not ct is None:
                            yield ct

                end_cursor = page_items['page_info']['end_cursor']
                has_next_page = page_items['page_info']['has_next_page']
        except Exception:
            self._logger.error(
                "Get fb contacts next page error:\nuserid={}\nusername={}\nerror:{}".
                format(hostuser._userid, hostuser.nickname,
                       traceback.format_exc()))

    def _get_contacts_params_v1(self, hostuser: NetworkProfile) -> tuple:
        """
        获取contact必要的参数
        """
        collection_token = ''
        section_token = ''
        try:
            html = self._ha.getstring(hostuser.url,
                                      headers="""
            accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
            accept-encoding: gzip, deflate
            accept-language: en-US,en;q=0.9
            sec-fetch-dest: document
            sec-fetch-mode: navigate
            sec-fetch-site: none
            upgrade-insecure-requests: 1
            user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36"""
            )

            if html is None or not html.__contains__(hostuser._userid):
                self._logger.error("Access user homepage failed: {}".format(hostuser.url))
                return collection_token, section_token

            matches = FBContacts_new._re_friends.findall(html)
            if matches is None or not any(matches):
                raise Exception("Get fb Contacts params failed")
            for m in matches:
                if len(m) != 2:
                    continue
                m_token = re.search(FBContacts_new._re_collection_token, m[0])
                if not m_token is None:
                    collection_token = m_token.group(1)
                section_token = m[1]
            if collection_token == '' or section_token == '':
                raise Exception("Get fb Contacts params failed")
        except Exception:
            self._logger.error(
                "Get fb contacts params failed:\nuserid={}\nusername={}\nerror:{}".
                    format(hostuser._userid, hostuser.nickname,
                           traceback.format_exc()))
        return collection_token, section_token

    def _parse_contact_edges_v1(self,
                                edges: list,
                                hostuser: NetworkProfile,
                                reason: str = None,
                                get_profile_pic: bool = False) -> iter:
        """处理返回的edges字段"""
        try:
            for edge in edges:
                ctid = edge['node']['node']['id']
                cturl = edge['node']['node']['url']
                ctname = edge['node']['title']['text']
                ct: NetworkProfile = NetworkProfile(
                    ctname, ctid, self._SOURCE)
                ct.url = cturl
                ct.reason = reason if not reason is None else "facebook动态监测"
                if get_profile_pic:
                    pic_url = edge['node']['image']['uri']
                    pic = self._ha.get_response_stream(pic_url)
                    ct._profile_pic = helper_str.base64bytes(pic.read())

                ct.set_contacts(hostuser, isfriend=True)
                hostuser.set_contacts(ct)
                yield ct
        except GeneratorExit:
            pass
        except:
            self._logger.error("Parse contacts edges failed: {}".format(
                traceback.format_exc()))