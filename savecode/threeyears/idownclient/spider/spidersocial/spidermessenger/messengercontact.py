"""messenger contacts download"""

# -*- coding:utf-8 -*-

import traceback
from urllib import parse
import re
import json
import random
import base64
import time

from commonbaby.helpers import helper_str
from commonbaby.httpaccess import ResponseIO

from datacontract.idowndataset import Task
from .messengerprofile import MessengerProfile
from ....clientdatafeedback import (CONTACT_ONE, RESOURCES, EGender,
                                    EResourceType, ESign)


class MessengerContact(MessengerProfile):
    """"""

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
        r'"section_type":"FRIENDS".*?"all_collections":\{"nodes":(\[.*?\])\},"id":"(.*?)"\}',
        re.S)

    # [{"tab_key": "friends_all", "id": "YXBwX2NvbGxlY3Rpb246MTAwMDUwMzYyMTUzNTk2OjIzNTYzMTgzNDk6Mg=="},
    #  {"tab_key": "friends_mutual", "id": "YXBwX2NvbGxlY3Rpb246MTAwMDUwMzYyMTUzNTk2OjIzNTYzMTgzNDk6Mw=="},
    #  {"tab_key": "friends_recent",
    _re_collection_token = re.compile(
        r'\{"tab_key":"friends_all","id":"(.*?)"', re.S)

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
    _re_docid_ProfileCometTopAppSectionQuery = re.compile(
        r'__d\("ProfileCometTopAppSectionQuery.graphql".*?params:\s*?(.*?name:\s*?"ProfileCometTopAppSectionQuery".*?\s*?})',
        re.S)
    _re_docid_ProfileCometAppCollectionListRendererPaginationQuery = re.compile(
        r'__d\("ProfileCometAppCollectionListRendererPaginationQuery.graphql".*?params:\s*?(.*?name:\s*?"ProfileCometAppCollectionListRendererPaginationQuery".*?\s*?})',
        re.S)

    def __init__(self, task: Task, appcfg, clientid):
        MessengerProfile.__init__(self, task, appcfg, clientid)

    def _get_contacts_(self) -> iter:
        """get friends"""
        try:
            # 获取messenger初始的js结果，包括第一页会话的联系人和每个会话的第一条消息等
            if not self.js_res:
                res = self._get_init_js_res()
                if not res:
                    return
            # 翻页获取更多会话，保存再js_res中
            self._get_contact_wss()

            # 先返回fb中未聊过天的好友，聊过天的再之后处理js_res的时候统一返回
            for data in self._get_contacts_fb():
                yield data

            # 可以开始拉取聊天记录了
            self.is_get_chatlog = True

            # 统一处理js_res
            for data in self._parse_contact_js_res():
                yield data

        except Exception:
            self._logger.error("Get contacts error: {}".format(
                traceback.format_exc()))

    ##########################
    #  wss获取会话联系人
    def _get_contact_wss(self) -> iter:
        """获取更多会话联系人存入js_res"""
        try:
            # wss拉取更多联系人
            while self.threads_ranges_time != 0 and self.threads_ranges_id != 0:
                ws = self._get_wss_obj()
                if ws is None:
                    self._logger.error('get wss object error!')
                    return
                epoch_id = random.randint(6753201641581840000, 6755042416160449999)
                # ws.send_binary(
                #     f'2\x9a\x04\x00\x07/ls_req\x00?{{"request_id":20,"type":3,"payload":"{{\\"version_id\\":\\"{self.schema_version}\\",\\"tasks\\":[{{\\"label\\":\\"145\\",\\"payload\\":\\"{{\\\\\\"is_after\\\\\\":false,\\\\\\"parent_thread_key\\\\\\":0,\\\\\\"reference_thread_key\\\\\\":{self.threads_ranges_id},\\\\\\"reference_activity_timestamp\\\\\\":{self.threads_ranges_time},\\\\\\"additional_pages_to_fetch\\\\\\":0,\\\\\\"cursor\\\\\\":\\\\\\"{self.last_applied_cursor}\\\\\\",\\\\\\"messaging_tag\\\\\\":null}}\\",\\"queue_name\\":\\"trq\\",\\"task_id\\":23,\\"failure_count\\":null}}],\\"epoch_id\\":{epoch_id},\\"data_trace_id\\":null}}","app_id":"{self.appid}"}}')
                payload = f'{{"request_id":{self.request_id},"type":3,"payload":"{{\\"version_id\\":\\"{self.schema_version}\\",\\"tasks\\":[{{\\"label\\":\\"145\\",\\"payload\\":\\"{{\\\\\\"is_after\\\\\\":false,\\\\\\"parent_thread_key\\\\\\":0,\\\\\\"reference_thread_key\\\\\\":{self.threads_ranges_id},\\\\\\"reference_activity_timestamp\\\\\\":{self.threads_ranges_time},\\\\\\"additional_pages_to_fetch\\\\\\":0,\\\\\\"cursor\\\\\\":\\\\\\"{self.last_applied_cursor}\\\\\\",\\\\\\"messaging_tag\\\\\\":null}}\\",\\"queue_name\\":\\"trq\\",\\"task_id\\":23,\\"failure_count\\":null}}],\\"epoch_id\\":{epoch_id},\\"data_trace_id\\":null}}","app_id":"{self.appid}"}}'
                msg = self._build_ls_req_request(payload)
                ws.send_binary(msg)
                retry_count = 0
                # 循环接收数据，直到返回需要的，最多尝试3次
                while True:
                    try:
                        res = ws.recv()
                        if '"request_id":null' in res.decode('latin1'):
                            break
                    except:
                        # 最多重试3次
                        retry_count += 1
                        if retry_count > 3:
                            return
                        self._logger.error(f'websocket get more contact send error! retry: {retry_count}')
                        # 重连wss，并重发请求
                        ws = self._get_wss_obj()
                        if ws is None:
                            self._logger.error('get wss object error!')
                            return
                        payload = f'{{"request_id":{self.request_id},"type":3,"payload":"{{\\"version_id\\":\\"{self.schema_version}\\",\\"tasks\\":[{{\\"label\\":\\"145\\",\\"payload\\":\\"{{\\\\\\"is_after\\\\\\":false,\\\\\\"parent_thread_key\\\\\\":0,\\\\\\"reference_thread_key\\\\\\":{self.threads_ranges_id},\\\\\\"reference_activity_timestamp\\\\\\":{self.threads_ranges_time},\\\\\\"additional_pages_to_fetch\\\\\\":0,\\\\\\"cursor\\\\\\":\\\\\\"{self.last_applied_cursor}\\\\\\",\\\\\\"messaging_tag\\\\\\":null}}\\",\\"queue_name\\":\\"trq\\",\\"task_id\\":23,\\"failure_count\\":null}}],\\"epoch_id\\":{epoch_id},\\"data_trace_id\\":null}}","app_id":"{self.appid}"}}'
                        msg = self._build_ls_req_request(payload)
                        ws.send_binary(msg)
                # 处理返回数据
                self.message_identifier += 1
                self.request_id += 1
                js_func = res.decode('latin1')
                temp_js_res = self._parse_contact_js(js_func)
                self.js_res.extend(temp_js_res)

        except Exception:
            self._logger.error("Parse contacts error: {}".format(
                traceback.format_exc()))

    def _parse_contact_js(self, js_func):
        """和_parse_init_js方法差不多，wss返回的数据转义符号要多一层， 并且参数位置有点不一样"""
        temp_res = []
        try:
            temp_res = []
            re_js_seq = re.search(r'return LS.seq\(\[(.*?)\]\)\}', js_func)
            if re_js_seq is None:
                self._logger.error('处理js代码失败')
            req_js = re_js_seq.group(1)
            re_js_sp = re.compile(r'_=>LS.sp\((.*?)\)')
            m = re_js_sp.findall(req_js)
            if m is None:
                self._logger.error('处理js代码失败')
            for js_one in m:
                param_list = self._parse_js_one_v2(js_one)
                dict_one = dict()
                if param_list[0] == '\\"396\\"':
                    self.last_applied_cursor = param_list[4][2:-2]
                # LSMailboxDeleteThenInsertThreadStoredProcedure
                # 聊天通道
                elif param_list[0] == '\\"130\\"':
                    dict_one['type'] = 'threads'
                    dict_one['thread_id'] = self.J(self._parse_n(param_list[8]))
                    self.messenger_thread_id.append(dict_one['thread_id'])
                    # 判断是否为群聊
                    is_group = self._parse_n(param_list[10])
                    if is_group == [0, 2] or is_group == [0, 8]:
                        dict_one['is_group'] = 1
                    else:
                        dict_one['is_group'] = 0
                    dict_one['group_name'] = param_list[4][1:-1] if param_list[4] != 'undefined' else 'undefined'
                    # 头像
                    dict_one['pic_url'] = param_list[5][2:-2].replace('\\\\\\/', '/')
                # LSMailboxAddParticipantIdToGroupThreadStoredProcedure
                # 成员
                elif param_list[0] == '\\"40\\"':
                    dict_one['type'] = 'participants'
                    dict_one['thread_id'] = self.J(self._parse_n(param_list[1]))
                    dict_one['member_id'] = self.J(self._parse_n(param_list[2]))
                # 联系人会话翻页，94和135都可以，但是参数和参数位置有变化
                elif param_list[0] == '\\"94\\"':
                    if param_list[2] == 'n`2`' or param_list[3] == 'undefined':
                        self.threads_ranges_time = 0
                        self.threads_ranges_id = 0
                    else:
                        self.threads_ranges_time = self.J(self._parse_n(param_list[2]))
                        self.threads_ranges_id = self.J(self._parse_n(param_list[3]))
                # LSMailboxUpsertMessageStoredProcedure
                # 消息
                elif param_list[0] == '\\"123\\"':
                    dict_one['type'] = 'messages'
                    thread_id = self._parse_n(param_list[4])
                    dict_one['thread_id'] = self.J(thread_id)
                    dict_one['time'] = self.J(self._parse_n(param_list[6]))  # 6 or 7，还没找出差别
                    dict_one['content'] = param_list[1][2:-2]
                    dict_one['msg_id'] = param_list[9][2:-2]  # mid.$cAAAAAJQIzuh9Ih48hV28Nj1p8EeN
                    dict_one['member_id'] = self.J(self._parse_n(param_list[11]))  # 发送者的thread_id
                    dict_one['unknow'] = param_list[10][2:-2]  # 6754333178547160973不知道有用没,和请求的epoch_id有点像
                    dict_one['from_sys'] = param_list[13]  # 是否是系统消息
                # LSMailboxInsertAttachmentStoredProcedure
                elif param_list[0] == '\\"138\\"':
                    dict_one['type'] = 'attachments'
                    thread_id = self._parse_n(param_list[35])
                    dict_one['thread_id'] = self.J(thread_id)
                    dict_one['msg_id'] = param_list[38][2:-2]
                    # 如果是视频的话，第二个url是缩略图，如果是gif的话，第一个url是mp4，第二个url是gif
                    dict_one['atta_url1'] = param_list[8][2:-2].replace('\\\\\\/', '/') if param_list[8] != 'undefined' else 'undefined'
                    dict_one['rsc_type1'] = param_list[11][2:-2].replace('\\\\\\/', '/') if param_list[11] != 'undefined' else 'undefined'
                    dict_one['atta_url2'] = param_list[13][2:-2].replace('\\\\\\/', '/') if param_list[13] != 'undefined' else 'undefined'
                    dict_one['rsc_type2'] = param_list[16][2:-2].replace('\\\\\\/', '/') if param_list[16] != 'undefined' else 'undefined'
                # LSContactVerifyContactRowExistsStoredProcedure
                # 联系人或群员
                elif param_list[0] == '\\"533\\"':
                    dict_one['type'] = 'contacts'
                    thread_id = self._parse_n(param_list[1])
                    dict_one['thread_id'] = self.J(thread_id)
                    # 头像
                    dict_one['pic_url'] = param_list[3][2:-2].replace('\\\\\\/', '/')
                    # 名称或备注 4 or 9 ?
                    dict_one['nick_name'] = param_list[4][2:-2]
                if dict_one != {}:
                    temp_res.append(dict_one)
        except Exception:
            self._logger.error("Parse contacts error: {}".format(
                traceback.format_exc()))
        return temp_res

    def _parse_contact_js_res(self):
        try:
            # 统一处理处理js_res
            for dict_one in self.js_res:
                # 返回私聊
                if dict_one['type'] == 'threads' and dict_one['is_group'] == 0:
                    ctid = dict_one['thread_id']
                    ct: CONTACT_ONE = CONTACT_ONE(self._userid, ctid, self.task, self._appcfg._apptype)
                    # 判断是否是fb好友
                    if ctid not in self.fb_contact_id:
                        ct.isfriend = 0
                        ct.bothfriend = 0
                        ct.isdeleted = 0
                    # 头像
                    if dict_one['pic_url'] != 'undefined':
                        uri = dict_one['pic_url']
                        try:
                            respstm: ResponseIO = self._ha.get_response_stream(uri)
                            if not respstm is None:
                                rsc: RESOURCES = RESOURCES(
                                    self._clientid, self.task, uri,
                                    EResourceType.Picture, self._appcfg._apptype)
                                rsc.io_stream = respstm
                                rsc.sign = ESign.PicUrl
                                ct.append_resource(rsc)
                                yield rsc
                        except:
                            self._logger.debug(f'get contact avatar failed: {uri}')
                    # 名字
                    for temp_one in self.js_res:
                        if temp_one['type'] == 'contacts':
                            if temp_one['thread_id'] == dict_one['thread_id']:
                                ct.nickname = temp_one['nick_name']
                                break

                    yield ct
        except:
            self._logger.error("Parse contact js_res error: {}".format(
                traceback.format_exc()))

    ##########################
    #  fb联系人
    def _get_contacts_fb(self) -> iter:
        try:
            collection_token, section_token = self._get_contacts_params_fb()
            if collection_token == '' or section_token == '':
                return
            res = self._get_contact_docid()
            if not res:
                self._logger.error("Get contact docid failed")
                return

            total_count = 0
            url = 'https://www.facebook.com/api/graphql/'
            variables = '{' + f'"collectionToken":"{collection_token}","scale":1,"sectionToken":"{section_token}","userID":"{self._userid}"' + '}'
            postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=ProfileCometTopAppSectionQuery&variables=' + parse.quote(
                variables) + f'&doc_id={self.docid_contact}'
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
                        """.format(len(postdata), self._host))
            res = json.loads(html)
            if not res.__contains__('data') \
                    or not res['data'].__contains__('node') \
                    or not res['data']['node'].__contains__('all_collections') \
                    or not res['data']['node']['all_collections'].__contains__('nodes'):
                return
            nodes: list = res['data']['node']['all_collections']['nodes']
            # nodes为[]表示好友不可见
            if not nodes:
                self._logger.info("Fb contacts not visible of user {}({})".format(self._username, self._userid))
                return
            # 获取好友列表翻页需要的docid
            if self.docid_contact_next is None:
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
                            m = MessengerContact._re_docid_ProfileCometAppCollectionListRendererPaginationQuery.search(js)
                            if not m is None:
                                self.docid_contact_next = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                                break
                if self.docid_contact_next is None:
                    raise Exception('get contacts nextpage docid fail!')

            # 开始处理好友信息
            for node in nodes:
                if not node.__contains__('style_renderer') \
                        or not node['style_renderer'].__contains__('collection'):
                    continue
                collection = node['style_renderer']['collection']
                count = collection['items']['count']
                self._logger.info("Find fb contacts count {} of user {}({})".format(
                    count, self._username, self._userid))

                edges: list = collection['pageItems']['edges']
                for ct in self._parse_contact_edges_fb(edges):
                    yield ct
                    total_count += 1

                end_cursor = collection['pageItems']['page_info']['end_cursor']
                has_next_page = collection['pageItems']['page_info']['has_next_page']

                if has_next_page:
                    for ct in self._get_contacts_nextpage_fb(collection_token, end_cursor):
                        yield ct
                        total_count += 1

            self._logger.info("Got {} contacts of user {}({})".format(
                total_count, self._username, self._userid))
        except Exception as ex:
            self._logger.error("Get contacts by userurl error: {}".format(
                ex.args))

    def _get_contacts_nextpage_fb(self, collection_token: str, end_cursor: str) -> iter:
        """get contacts"""
        try:
            url = 'https://www.facebook.com/api/graphql/'
            has_next_page = True
            while has_next_page:
                has_next_page = False
                # 一次最多能拉16人, count超过16没用
                # 每次请求间隔
                time.sleep(random.randint(1, 2))
                variables = '{' + f'"count":16,"cursor":"{end_cursor}","scale":1,"search":null,"id":"{collection_token}"' + '}'
                postdata = f'av={self._userid}&__user={self._userid}&__a=1&__csr=&__beoa=0&__pc={parse.quote(self._pc)}&dpr=1&__ccg=EXCELLENT&__hsi={self.hsi}&__comet_req=1&fb_dtsg={parse.quote(self.fb_dtsg)}&jazoest={self.jazoest}&__spin_r={self._spin_r}&__spin_b={self._spin_b}&__spin_t={self._spin_t}&fb_api_caller_class=RelayModern&fb_api_req_friendly_name=ProfileCometAppCollectionListRendererPaginationQuery&variables=' + parse.quote(
                    variables) + f'&doc_id={self.docid_contact_next}'
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
                """.format(len(postdata), self._host))
                res = json.loads(html)
                if not res.__contains__('data') \
                        or not res['data'].__contains__('node') \
                        or not res['data']['node'].__contains__('pageItems'):
                    return
                page_items = res['data']['node']['pageItems']
                if page_items.__contains__('edges'):
                    edges: list = page_items['edges']
                    for ct in self._parse_contact_edges_fb(edges):
                        if not ct is None:
                            yield ct

                end_cursor = page_items['page_info']['end_cursor']
                has_next_page = page_items['page_info']['has_next_page']
        except Exception:
            self._logger.error(
                "Get fb contacts next page error:\nuserid={}\nusername={}\nerror:{}".
                format(self._userid, self._username,
                       traceback.format_exc()))

    def _get_contacts_params_fb(self) -> tuple:
        """
        获取contact必要的参数
        """
        collection_token = ''
        section_token = ''
        try:
            html = self._ha.getstring(self._host,
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

            if html is None or not html.__contains__(self._userid):
                self._logger.error("Access user homepage failed: {}".format(self._host))
                return collection_token, section_token

            matches = MessengerContact._re_friends.findall(html)
            if matches is None or not any(matches):
                raise Exception("Get fb Contacts params failed")
            for m in matches:
                if len(m) != 2:
                    continue
                m_token = re.search(MessengerContact._re_collection_token, m[0])
                if not m_token is None:
                    collection_token = m_token.group(1)
                section_token = m[1]
            if collection_token == '' or section_token == '':
                raise Exception("Get fb Contacts params failed")
        except Exception:
            self._logger.error(
                "Get fb contacts params failed:\nuserid={}\nusername={}\nerror:{}".
                    format(self._userid, self._username,
                           traceback.format_exc()))
        return collection_token, section_token

    def _parse_contact_edges_fb(self, edges: list) -> iter:
        """处理返回的edges字段， 返回未聊过天的好友"""
        try:
            for edge in edges:
                ctid = edge['node']['node']['id']
                # 用来判断会话联系人是否为好友
                if int(ctid) in self.messenger_thread_id:
                    self.fb_contact_id.append(int(ctid))
                # 只返回没有说过话的好友
                else:
                    cturl = edge['node']['node']['url']
                    ctname = edge['node']['title']['text']
                    ct: CONTACT_ONE = CONTACT_ONE(self._userid, ctid, self.task, self._appcfg._apptype)
                    ct.nickname = ctname
                    # 用户头像先不输出
                    # pic_url = edge['node']['image']['uri']
                    # respstm: ResponseIO = self._ha.get_response_stream(pic_url)
                    # if not respstm is None:
                    #     rsc: RESOURCES = RESOURCES(
                    #         self._clientid, self.task, pic_url,
                    #         EResourceType.Picture, self._appcfg._apptype)
                    #     rsc.io_stream = respstm
                    #     rsc.sign = ESign.PicUrl
                    #     ct.append_resource(rsc)
                    #     yield rsc
                    yield ct
        except GeneratorExit:
            pass
        except:
            self._logger.error("Parse contacts edges failed: {}".format(
                traceback.format_exc()))

    def _get_contact_docid_js(self):
        """找获取好友列表docid的js"""
        try:
            # 请求bulk-route-definitions，缺哪些请求哪些
            path = self._host[len('https://www.facebook.com'):]
            # 统一去掉结尾/,方便处理
            if path.endswith('/'):
                path = path[:-1]
            # https://www.facebook.com/profile.php?id=100010123548628&sk=friends
            if self._host.startswith('https://www.facebook.com/profile.php?id='):
                route_url = f'route_urls[0]={parse.quote_plus(path + "&sk=friends")}'
            # https://www.facebook.com/bichhau.bui.5249/friends
            else:
                route_url = f'route_urls[0]={parse.quote_plus(path + "/friends")}'
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
            matches = MessengerContact._re_js_src.findall(html)
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
                    self._logger.trace("Parse contact docid js src error: {} {}".format(m, traceback.format_exc()))
            self._logger.info(
                "Got js resources list count={}".format(len(js_src_dict)))
            for jsurl in js_src_dict.values():
                js = self._ha.getstring(jsurl, headers='''
                                               Origin: https://www.facebook.com
                                               Referer: https://www.facebook.com/
                                               user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36''')
                yield js

        except Exception:
            self._logger.error(
                "Get contact docid js src error: {}".format(traceback.format_exc()))

    def _get_contact_docid(self) -> bool:
        """fb联系人需要的docid"""
        if self.docid_contact is not None:
            return True
        res: bool = False
        try:
            # ProfileCometTopAppSectionQuery
            for js in self._get_contact_docid_js():
                try:
                    if helper_str.is_none_or_empty(js) or 'ProfileCometTopAppSectionQuery' not in js:
                        continue
                    if js.__contains__('ProfileCometTopAppSectionQuery'):
                        m = MessengerContact._re_docid_ProfileCometTopAppSectionQuery.search(js)
                        if not m is None:
                            self.docid_contact = re.search(r'id:\s*?"(\d+)"', m.group(1)).group(1)
                            res = True
                except Exception:
                    self._logger.debug(
                        "Parse init message docid error: {}".format(traceback.format_exc()))

        except Exception:
            self._logger.error(
                "Get docid for init message error: {} {}".format(
                    self.uname_str, traceback.format_exc()))
        return res