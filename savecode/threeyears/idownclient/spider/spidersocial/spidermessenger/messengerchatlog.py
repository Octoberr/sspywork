"""messenger chatlog download"""

# -*- coding:utf-8 -*-

import traceback
import websocket
import random
from datetime import datetime
from urllib import parse
import re

from commonbaby.helpers import helper_crypto, helper_str, helper_time
from commonbaby.httpaccess import ResponseIO

from datacontract.idowndataset import Task
from .messengergroup import MessengerGroup
from ....clientdatafeedback import (CONTACT_ONE, ICHATGROUP_ONE, ICHATLOG_ONE,
                                    RESOURCES, EResourceType)


class MessengerChatlog(MessengerGroup):
    """"""

    def __init__(self, task: Task, appcfg, clientid):
        MessengerGroup.__init__(self, task, appcfg, clientid)

    def _get_contact_chatlogs_(self, ct: CONTACT_ONE) -> iter:
        """fetch privacy chat logs"""
        try:
            # fb未聊过天的联系人不处理
            if not self.is_get_chatlog:
                return

            if not self.js_res:
                self._logger.error(f'Get contact chatlogs error: js_res is empty')
                return

            # 拿当前联系人的所有聊天记录，一句话就是一条聊天记录
            for data in self._fetch_chatlog_one(ct):
                yield data

        except Exception:
            self._logger.error(
                "Fetch privacy chatlog error:%s" % traceback.format_exc())

    def _fetch_chatlog_one(self, ct: CONTACT_ONE) -> iter:
        """fetch chatlogs of one contact"""
        try:
            if ct is None:
                return

            # 先返回第一条消息，再发wss请求
            first_msg = None
            for dict_one in self.js_res:
                # 联系人对应的第一条消息
                if dict_one['type'] == 'messages' and dict_one['thread_id'] == ct._contactid:
                    first_msg = dict_one
                    break
            if first_msg is None:
                self._logger.error(f'first message not found: {ct.nickname}')
                return
            # 系统提示信息不返回
            if first_msg['from_sys'] == 'false':
                sendtime = datetime.fromtimestamp(first_msg['time'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
                ctg = ICHATLOG_ONE(self.task, self._appcfg._apptype, self._userid,
                                   4, ct._contactid, 0, first_msg['msg_id'],
                                   first_msg['member_id'], sendtime)
                ctg.content += first_msg['content']
                for dict_one in self.js_res:
                    # gif按照url1下载的格式为mp4,应该没有影响
                    if dict_one['type'] == 'attachments' and dict_one['msg_id'] == first_msg['msg_id']:
                        if dict_one['atta_url1'] != 'undefined':
                            rsc = self._parse_chatlogs_rsc(ctg, dict_one)
                            if rsc is not None:
                                yield rsc
                yield ctg

            # wss获取更多消息
            has_next_page = True
            last_msg_time = first_msg['time']
            last_msg_id = first_msg['msg_id']
            while has_next_page:
                has_next_page = False
                ws = self._get_wss_obj()
                if ws is None:
                    self._logger.error('get wss object error!')
                    return
                epoch_id = random.randint(6753201641581840000, 6755042416160449999)
                # ws.send_binary(f'2\xd6\x03\x00\x07/ls_req\x04t{{"request_id":25,"type":3,"payload":"{{\\"version_id\\":\\"{self.schema_version}\\",\\"tasks\\":[{{\\"label\\":\\"228\\",\\"payload\\":\\"{{\\\\\\"thread_key\\\\\\":{ct._contactid},\\\\\\"direction\\\\\\":0,\\\\\\"reference_timestamp_ms\\\\\\":{last_msg_time},\\\\\\"reference_message_id\\\\\\":\\\\\\"{last_msg_id}\\\\\\"}}\\",\\"queue_name\\":\\"mrq.{ct._contactid}\\",\\"task_id\\":23,\\"failure_count\\":null}}],\\"epoch_id\\":{epoch_id},\\"data_trace_id\\":null}}","app_id":"{self.appid}"}}')
                payload = f'{{"request_id":{self.request_id},"type":3,"payload":"{{\\"version_id\\":\\"{self.schema_version}\\",\\"tasks\\":[{{\\"label\\":\\"228\\",\\"payload\\":\\"{{\\\\\\"thread_key\\\\\\":{ct._contactid},\\\\\\"direction\\\\\\":0,\\\\\\"reference_timestamp_ms\\\\\\":{last_msg_time},\\\\\\"reference_message_id\\\\\\":\\\\\\"{last_msg_id}\\\\\\"}}\\",\\"queue_name\\":\\"mrq.{ct._contactid}\\",\\"task_id\\":23,\\"failure_count\\":null}}],\\"epoch_id\\":{epoch_id},\\"data_trace_id\\":null}}","app_id":"{self.appid}"}}'
                msg = self._build_ls_req_request(payload)
                ws.send_binary(msg)
                retry_count = 0
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
                        self._logger.error(f'websocket send error! retry: {retry_count}')
                        # 重连wss，并重发请求
                        ws = self._get_wss_obj()
                        if ws is None:
                            self._logger.error('get wss object error!')
                            return
                        payload = f'{{"request_id":{self.request_id},"type":3,"payload":"{{\\"version_id\\":\\"{self.schema_version}\\",\\"tasks\\":[{{\\"label\\":\\"228\\",\\"payload\\":\\"{{\\\\\\"thread_key\\\\\\":{ct._contactid},\\\\\\"direction\\\\\\":0,\\\\\\"reference_timestamp_ms\\\\\\":{last_msg_time},\\\\\\"reference_message_id\\\\\\":\\\\\\"{last_msg_id}\\\\\\"}}\\",\\"queue_name\\":\\"mrq.{ct._contactid}\\",\\"task_id\\":23,\\"failure_count\\":null}}],\\"epoch_id\\":{epoch_id},\\"data_trace_id\\":null}}","app_id":"{self.appid}"}}'
                        msg = self._build_ls_req_request(payload)
                        ws.send_binary(msg)
                self.message_identifier += 1
                self.request_id += 1
                js_func = res.decode('latin1')
                temp_js_res = self._parse_chatlogs_js(js_func)
                # 遍历列表返回数据
                for dict_one in temp_js_res:
                    if dict_one['type'] == 'messages' and dict_one['from_sys'] == 'false':
                        sendtime = datetime.fromtimestamp(dict_one['time'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
                        ctg = ICHATLOG_ONE(self.task, self._appcfg._apptype, self._userid,
                                           4, ct._contactid, 0, dict_one['msg_id'],
                                           dict_one['member_id'], sendtime)
                        ctg.content += dict_one['content']
                        for temp_one in temp_js_res:
                            if temp_one['type'] == 'attachments' and temp_one['msg_id'] == dict_one['msg_id']:
                                if temp_one['atta_url1'] != 'undefined':
                                    rsc = self._parse_chatlogs_rsc(ctg, temp_one)
                                    if rsc is not None:
                                        yield rsc
                        yield ctg
                    elif dict_one['type'] == 'message_range' and dict_one['has_next_page'] == 'true':
                        last_msg_time = dict_one['time']
                        last_msg_id = dict_one['msg_id']
                        has_next_page = True

        except Exception:
            self._logger.error(
                "Fetch chatlog of one contact error:\ncontactid:%s\nex:%s" %
                (ct._userid, traceback.format_exc()))

    def _parse_chatlogs_js(self, js_func):
        """"""
        temp_res = []
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
                param_list = self._parse_js_one_v2(js_one)
                dict_one = dict()
                if param_list[0] == '\\"396\\"':
                    self.last_applied_cursor = param_list[4][2:-2]
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
                elif param_list[0] == '\\"41\\"':
                    dict_one['type'] = 'message_range'
                    dict_one['time'] = self.J(self._parse_n(param_list[2]))
                    dict_one['msg_id'] = param_list[4][2:-2]
                    dict_one['has_next_page'] = param_list[8]  # true, false字符串
                if dict_one != {}:
                    temp_res.append(dict_one)

        except Exception:
            self._logger.error("Parse contact chatlogs error: {}".format(
                traceback.format_exc()))
        return temp_res

    def _parse_chatlogs_rsc(self, ctg: ICHATLOG_ONE, dict_one: dict):
        rsc = None
        try:
            url = dict_one['atta_url1']
            resp: ResponseIO = self._ha.get_response_stream(
                url,
                headers="""
                        accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
                        accept-encoding: gzip, deflate
                        accept-language: zh-CN,zh;q=0.9
                        upgrade-insecure-requests: 1""")
            if resp is not None:
                if dict_one['rsc_type1'] == 'image/png' or \
                        dict_one['rsc_type1'] == 'image/webp' or \
                        dict_one['rsc_type1'] == 'image/gif':
                    rsc = RESOURCES(self._clientid, self.task, url, EResourceType.Picture,
                                    self._appcfg._apptype)
                    rsc.io_stream = resp
                    ctg._messagetype = 0
                elif dict_one['rsc_type1'] == 'video/mp4':
                    rsc = RESOURCES(self._clientid, self.task, url, EResourceType.Video,
                                    self._appcfg._apptype)
                    rsc.io_stream = resp
                    ctg._messagetype = 1
                else:
                    rsc = RESOURCES(self._clientid, self.task, url, EResourceType.Other_Text,
                                    self._appcfg._apptype)
                    rsc.io_stream = resp
                    ctg._messagetype = 4
                ctg.append_resource(rsc)
        except:
            self._logger.debug(f'Download error: {dict_one["atta_url1"]}')
        return rsc

    def _get_group_chatlogs_(self, grp: ICHATGROUP_ONE) -> iter:
        """获取群聊聊天信息"""
        try:
            if not self.js_res:
                self._logger.error(f'Get contact chatlogs error: js_res is empty')
                return

            # 拿当前联系人的所有聊天记录，一句话就是一条聊天记录
            for data in self._fetch_group_chat_one(grp):
                yield data

        except Exception:
            self._logger.error(
                "Fetch group chatlogs error:%s" % traceback.format_exc())

    def _fetch_group_chat_one(self, group: ICHATGROUP_ONE) -> iter:
        """获取一个群的群聊记录。其实群聊记录和私聊记录获取规则是一样的？只是那个id
        一个填好友id，一个填群id。"""
        try:
            if group is None:
                return

            # 先返回第一条消息，再发wss请求
            first_msg = None
            for dict_one in self.js_res:
                # 联系人对应的第一条消息
                if dict_one['type'] == 'messages' and dict_one['thread_id'] == group._groupid:
                    first_msg = dict_one
                    break
            if first_msg is None:
                self._logger.error(f'first message not found: {group._groupid}')
                return
            # 系统提示信息不返回
            if first_msg['from_sys'] == 'false':
                sendtime = datetime.fromtimestamp(first_msg['time'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
                ctg = ICHATLOG_ONE(self.task, self._appcfg._apptype, self._userid,
                                   4, group._groupid, 1, first_msg['msg_id'],
                                   first_msg['member_id'], sendtime)
                ctg.content += first_msg['content']
                for dict_one in self.js_res:
                    # gif按照url1下载的格式为mp4,应该没有影响
                    if dict_one['type'] == 'attachments' and dict_one['msg_id'] == first_msg['msg_id']:
                        if dict_one['atta_url1'] != 'undefined':
                            rsc = self._parse_chatlogs_rsc(ctg, dict_one)
                            if rsc is not None:
                                yield rsc
                yield ctg

            # wss获取消息
            has_next_page = True
            last_msg_time = first_msg['time']
            last_msg_id = first_msg['msg_id']
            while has_next_page:
                has_next_page = False
                ws = self._get_wss_obj()
                if ws is None:
                    self._logger.error('get wss object error!')
                    return
                epoch_id = random.randint(6753201641581840000, 6755042416160449999)
                # ws.send_binary(f'2\xd6\x03\x00\x07/ls_req\x04t{{"request_id":23,"type":3,"payload":"{{\\"version_id\\":\\"{self.schema_version}\\",\\"tasks\\":[{{\\"label\\":\\"228\\",\\"payload\\":\\"{{\\\\\\"thread_key\\\\\\":{group._groupid},\\\\\\"direction\\\\\\":0,\\\\\\"reference_timestamp_ms\\\\\\":{last_msg_time},\\\\\\"reference_message_id\\\\\\":\\\\\\"{last_msg_id}\\\\\\"}}\\",\\"queue_name\\":\\"mrq.{group._groupid}\\",\\"task_id\\":23,\\"failure_count\\":null}}],\\"epoch_id\\":{epoch_id},\\"data_trace_id\\":null}}","app_id":"{self.appid}"}}')
                payload = f'{{"request_id":{self.request_id},"type":3,"payload":"{{\\"version_id\\":\\"{self.schema_version}\\",\\"tasks\\":[{{\\"label\\":\\"228\\",\\"payload\\":\\"{{\\\\\\"thread_key\\\\\\":{group._groupid},\\\\\\"direction\\\\\\":0,\\\\\\"reference_timestamp_ms\\\\\\":{last_msg_time},\\\\\\"reference_message_id\\\\\\":\\\\\\"{last_msg_id}\\\\\\"}}\\",\\"queue_name\\":\\"mrq.{group._groupid}\\",\\"task_id\\":23,\\"failure_count\\":null}}],\\"epoch_id\\":{epoch_id},\\"data_trace_id\\":null}}","app_id":"{self.appid}"}}'
                msg = self._build_ls_req_request(payload)
                ws.send_binary(msg)
                retry_count = 0
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
                        self._logger.error(f'websocket send error! retry: {retry_count}')
                        # 重连wss，并重发请求
                        ws = self._get_wss_obj()
                        if ws is None:
                            self._logger.error('get wss object error!')
                            return
                        payload = f'{{"request_id":{self.request_id},"type":3,"payload":"{{\\"version_id\\":\\"{self.schema_version}\\",\\"tasks\\":[{{\\"label\\":\\"228\\",\\"payload\\":\\"{{\\\\\\"thread_key\\\\\\":{group._groupid},\\\\\\"direction\\\\\\":0,\\\\\\"reference_timestamp_ms\\\\\\":{last_msg_time},\\\\\\"reference_message_id\\\\\\":\\\\\\"{last_msg_id}\\\\\\"}}\\",\\"queue_name\\":\\"mrq.{group._groupid}\\",\\"task_id\\":23,\\"failure_count\\":null}}],\\"epoch_id\\":{epoch_id},\\"data_trace_id\\":null}}","app_id":"{self.appid}"}}'
                        msg = self._build_ls_req_request(payload)
                        ws.send_binary(msg)
                self.message_identifier += 1
                self.request_id += 1
                js_func = res.decode('latin1')
                temp_js_res = self._parse_chatlogs_js(js_func)
                # 遍历列表返回数据
                for dict_one in temp_js_res:
                    if dict_one['type'] == 'messages' and dict_one['from_sys'] == 'false':
                        sendtime = datetime.fromtimestamp(dict_one['time'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
                        ctg = ICHATLOG_ONE(self.task, self._appcfg._apptype, self._userid,
                                           4, group._groupid, 1, dict_one['msg_id'],
                                           dict_one['member_id'], sendtime)
                        ctg.content += dict_one['content']
                        for temp_one in temp_js_res:
                            if temp_one['type'] == 'attachments' and temp_one['msg_id'] == dict_one['msg_id']:
                                if temp_one['atta_url1'] != 'undefined':
                                    rsc = self._parse_chatlogs_rsc(ctg, temp_one)
                                    if rsc is not None:
                                        yield rsc
                        yield ctg
                    elif dict_one['type'] == 'message_range' and dict_one['has_next_page'] == 'true':
                        last_msg_time = dict_one['time']
                        last_msg_id = dict_one['msg_id']
                        has_next_page = True

        except Exception:
            self._logger.error(
                "Fetch group chatlogs error :%s" % traceback.format_exc())

    def _parse_chatlog(self, msg: map, threadtype: str, ownerid: str) -> iter:
        """接收 json解出来的map消息msg对象，返回ICHATLOG_ONE和RESOURCE对象迭代器\n
        msg:json解出来的map消息msg对象\n
        threadtype:一个json中解出来的字段，应该是表示会话类型"""
        try:
            if msg is None:
                self._logger.error(
                    "Invalid msg map object for parseing chat log: {}".format(
                        msg))
                return
            chattype: int = 0  # 0私聊，1群聊
            msgtype: str = None  # 图片视频等
            sendtime: str = None  # 发送时间
            if not msg.__contains__('message_sender') or not msg[
                'message_sender'].__contains__(
                'id') or not msg.__contains__('message_id'):
                return
            if not threadtype is None:
                if threadtype != "ONE_TO_ONE":
                    chattype = 1
                else:
                    chattype = 0
            # 消息类型
            if not msg.__contains__('__typename') or msg[
                '__typename'] is None or msg['__typename'] == '':
                return
            msgtype = self._judge_message_type(msg['__typename'])
            # 发送时间戳
            timestamp_precise = None
            if msg.__contains__('timestamp_precise'):
                try:
                    tmp = msg['timestamp_precise']
                    tmp = int(tmp)
                    timestamp_precise = tmp
                    sendtime = helper_time.timespan_to_datestr(tmp)
                except Exception:
                    sendtime = helper_time.timespan_to_datestr(
                        helper_time.ts_since_1970())

            # 构建消息对象
            ctg = ICHATLOG_ONE(self.task, self._appcfg._apptype, self._userid,
                               msgtype, ownerid, chattype, msg['message_id'],
                               msg['message_sender']['id'], sendtime)
            ctg.remarks = timestamp_precise

            # 已读未读
            if msg.__contains__('unread'):
                if msg['unread'].strip().lower() == 'true':
                    ctg.isread = 0
                else:
                    ctg.isread = 1
            # 表情资源
            if msg.__contains__(
                    'sticker'
            ) and not msg['sticker'] is None and msg['sticker'].__contains__(
                'url') and msg['sticker'].__contains__('label'):
                sjstk = msg['sticker']
                if sjstk.__contains__('url'):
                    url = sjstk['url'].replace('\\', '').rstrip()
                    rscid = helper_crypto.get_md5_from_str(url)
                    if sjstk.__contains__('id'):
                        rscid = sjstk['id']
                    for rsc in self._fetch_resources(
                            url, EResourceType.Picture, rscid):
                        ctg.append_resource(rsc)
                        yield rsc
            # 片段，系统消息说明
            if msg.__contains__('snippet'):
                ctg.content += msg['snippet']
            # answered对方是否响应
            if msg.__contains__('answered'):
                if msg['answered'] == 'false':
                    ctg.answered = 0
                else:
                    ctg.answered = 1
            # blob_attachments
            if msg.__contains__('blob_attachments'
                                ) and not msg['blob_attachments'] is None:
                for blob in msg['blob_attachments']:
                    if not blob.__contains__('__typename'):
                        continue
                    # 拿附件url，附件类型/type
                    url, rsctype = self._get_attachments_type_and_url(blob)
                    if not isinstance(url, str) or url == "":
                        self._logger.warn(
                            "Get attachment url failed: {}".format(blob))
                        continue
                    rscid: str = None
                    if blob.__contains__('legacy_attachment_id'):
                        rscid = blob['legacy_attachment_id']
                    elif blob.__contains__('message_file_fbid'):
                        rscid = blob['message_file_fbid']
                    if not isinstance(rscid, str) or rscid == "":
                        rscid = helper_crypto.get_md5_from_str(url)
                    # 附件名
                    finame = None
                    if blob.__contains__('filename'):
                        finame = blob['filename']
                    # 下载
                    for rsc in self._fetch_resources(url, rsctype, rscid,
                                                     finame):
                        ctg.append_resource(rsc)
                        yield rsc
            if msg.__contains__(
                    'extensible_attachment'
            ) and not msg['extensible_attachment'] is None and msg[
                'extensible_attachment'].__contains__(
                'legacy_attachment_id'):
                resourceid = msg['extensible_attachment'][
                    'legacy_attachment_id']
                if msg['extensible_attachment'].__contains__("story_attachment") \
                        and msg['extensible_attachment']['story_attachment'].__contains__('media'):
                    jmedia = msg['extensible_attachment']['story_attachment'][
                        'media']

                    if jmedia.__contains__('is_playable') and jmedia[
                        'is_playable'] == 'true' and jmedia.__contains__(
                        'playable_url'):
                        url = jmedia['playable_url'].rstrip().replace(
                            '\\', '').rstrip()
                        for rsc in self._fetch_resources(
                                url, EResourceType.Video, resourceid):
                            ctg.append_resource(rsc)
                            yield rsc

                    if jmedia.__contains__('image') \
                            and jmedia['image'].__contains__('uri'):
                        url = jmedia['image']['uri'].rstrip().replace(
                            '\\', '').rstrip()

                        for rsc in self._fetch_resources(
                                url, EResourceType.Picture, resourceid):
                            ctg.append_resource(rsc)
                            yield rsc
            # message
            if msg.__contains__('message') and not msg['message'] is None:
                if msg['message'].__contains__('text'):
                    if not msg['message']['text'] is None and not msg[
                                                                      'message']['text'] == '':
                        ctg.content += msg['message']['text']

            yield ctg

        except Exception:
            self._logger.error(
                "Parse one chatlog msg error:\nmsg:{}\nerror:{}".format(
                    msg, traceback.format_exc()))
