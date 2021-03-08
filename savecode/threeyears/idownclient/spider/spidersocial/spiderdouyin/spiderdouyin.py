"""spider douyin"""

# -*- coding:utf-8 -*-

import json
import os
import sqlite3
import time
import traceback

import requests

from idownclient.clientdatafeedback import (CONTACT, CONTACT_ONE, ICHATLOG,
                                            ICHATLOG_ONE, PROFILE, RESOURCES,
                                            EResourceType)
from idownclient.config_spiders import douyinip, douyinport
from idownclient.config_task import clienttaskconfig

from ..spidersocialbase import SpiderSocialBase
from .socketdouyin import SocketDouyin


class SpiderDouyin(SpiderSocialBase):
    """"""

    _so: SocketDouyin = SocketDouyin(douyinip, douyinport, None)

    def __init__(self, task, appcfg, clientid):
        super(SpiderDouyin, self).__init__(task, appcfg, clientid)
        self._userid = ''
        self._resources_type = {
            2: EResourceType.Picture,
            5: EResourceType.Picture,
            7: EResourceType.Other_Text,
            15: EResourceType.Picture,
            17: EResourceType.Audio,
        }

        # 要不要拼+86？
        self._phone = self.task.phone

    def _sms_login(self) -> bool:
        """sms login"""
        succ: bool = False
        try:
            # 连接
            succ, msg = SpiderDouyin._so.connect()
            if not succ:
                self._logger.error("Connect to server failed: {}".format(msg))
                return succ
            self._logger.info('Connected to server: {}:{}'.format(
                douyinip, douyinport))

            # 发送手机号
            succ, msg = SpiderDouyin._so.send_phonenum(self._phone, self.task)
            if not succ:
                self._logger.error(
                    "Send phone number failed, server return: {}".format(msg))
                return succ
            self._logger.info(msg)

            # 拿验证码
            smscode = self._get_vercode()
            if smscode is None or smscode == '':
                self._logger.error("Sms verify code is invalid or empty")
                return succ

            # 发送验证码
            succ, msg = SpiderDouyin._so.send_verify_code(smscode, self.task)
            if not succ:
                self._logger.error(
                    "Send sms verify code failed, server return: {}".format(
                        msg))
                return succ

            # 登陆成功
            self._logger.info(msg)
            self._logger.info("login success, sleep 10 seconds ..........")
            time.sleep(10)
        except Exception:
            succ = False
            self._logger.error("Sms login error: {}".format(
                traceback.format_exc()))
        return succ

    def _download(self) -> iter:
        """douyin business"""
        try:
            dbpath = self._download_douyin_db()
            if not dbpath:
                self._logger.error("No data in douyin db")
                return

            for data in self._read_datas(dbpath):
                yield data

        except Exception:
            self._logger.error("Download error: {} {}".format(
                self.uname_str, traceback.format_exc()))
        finally:
            pass

    def _download_douyin_db(self):
        try:
            db_res = False
            tmpdir = os.path.abspath(
                os.path.join(clienttaskconfig.tmppath, 'douyin'))
            if not os.path.exists(tmpdir):
                os.makedirs(tmpdir)
            dbpath = os.path.join(tmpdir, "{}.db".format(self._phone))
            # 发送下载数据的命令

            succ, data = SpiderDouyin._so.send_download(self.task)

            if not succ:
                self._logger.error("Read data from server failed: {}".format(
                    self._phone))
                return db_res

            if os.path.exists(dbpath) and os.path.isfile(dbpath):
                os.remove(dbpath)
            with open(dbpath, mode='wb') as fs:
                fs.write(data)
            db_res = True
        except Exception:
            self._logger.error("Download douyin db error, err:{}".format(
                traceback.format_exc()))
        finally:
            # 不管如何都发一个退出命令
            succ, msg = SpiderDouyin._so.send_exit(self.task)
            if not succ:
                self._logger.error("Send exit failed: {} {}".format(
                    self.uname_str, msg))
            else:
                self._logger.info("Exit user {} suceed: {}".format(
                    self.uname_str, msg))
            if db_res:
                return dbpath
            else:
                return db_res

    def _read_datas(self, dbpath) -> iter:
        """read datas from db"""
        try:
            # 下载数据成功
            sql = '''SELECT * FROM msg
            '''
            res_lines = self._select_data(dbpath, sql)
            if len(res_lines) == 0:
                return
            contacts_all = {}
            logs_all = ICHATLOG(self._clientid, self.task, self.task.apptype)
            for line in res_lines:
                if line.get('content') is None and line.get('content') == '':
                    continue
                try:
                    conversionid = line.get('conversation_id').split(':')
                    if len(conversionid) != 0:
                        if self._userid == '':
                            self._userid = conversionid[-1]
                        contact_id = conversionid[-2]
                        contacts_all[contact_id] = 1
                    else:
                        continue
                    messagetype: EResourceType = self._resources_type.get(line['type'])
                    sessionid = conversionid[-2]
                    messageid = line['msg_uuid']
                    senderid = line['sender']

                    cr_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                            time.localtime(
                                                line['created_time'] / 1000))
                    log_one = ICHATLOG_ONE(self.task, self.task.apptype,
                                           self._userid, messagetype.value,
                                           sessionid, 1, messageid, senderid,
                                           cr_time)
                    if messagetype == EResourceType.Picture or messagetype == EResourceType.Audio:
                        for res_file in self._get_resources(line, messagetype):
                            log_one.append_resource(res_file)
                            yield res_file
                    try:
                        json_text = json.loads(line['content'])
                    except Exception as err:
                        self._logger.error(
                            "Content data is not json, err:{}".format(err))
                        continue
                    # 文字
                    if json_text.get('text') is not None:
                        log_one.content = json_text.get('text')
                    logs_all.append_innerdata(log_one)
                except Exception:
                    self._logger.error(
                        "Parse one data line from db error: {} {}".format(
                            self.uname_str, traceback.format_exc()))
            if logs_all.innerdata_len > 0:
                yield logs_all
            if self._userid != '':
                p_data = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
                p_data.account = self._phone
                p_data.phone = self._phone
                yield p_data
            if len(contacts_all) != 0:
                ct_all = CONTACT(self._clientid, self.task, self.task.apptype)
                for ct in contacts_all:
                    ct_one = CONTACT_ONE(self._userid, ct, self.task,
                                         self.task.apptype)
                    ct_one.isfriend = 1
                    ct_one.isdeleted = 0
                    ct_all.append_innerdata(ct_one)
                yield ct_all
        except Exception:
            self._logger.error("Read datas from db error: {} {}".format(
                self.uname_str, traceback.format_exc()))

    def _get_resources(self, el: dict, resourcetype) -> iter:
        try:
            json_text = json.loads(el['content'])
        except Exception as err:
            self._logger.error(
                "Content data is not json data, err:{}".format(err))
            return
        # 本地图片
        if json_text.get('url') is not None:
            url_list = json_text.get('url').get('url_list')
            if len(url_list) != 0:
                for picurl in url_list:
                    resource = RESOURCES(self._clientid, self.task, picurl, resourcetype,
                                         self.task.apptype)
                    filename = json_text.get('display_name')
                    exten = json_text.get('image_type')
                    if filename is not None and exten is not None:
                        resource.filename = filename + '.' + exten
                        resource.extension = exten
                    resource.io_stream = self._download_data_url(picurl)
                    yield resource
        # 录音
        if json_text.get('resource_url') is not None:
            url_list = json_text.get('resource_url').get('url_list')
            if len(url_list) != 0:
                re_url = url_list[0]
                resource = RESOURCES(self._clientid, self.task, re_url, resourcetype,
                                     self.task.apptype)
                # 封装下本地下载音频
                resource.io_stream = self._download_data_url(re_url)
                yield resource
        # 表情
        if json_text.get('stickers') is not None:
            url_list = json_text.get('stickers')
            if len(url_list) != 0:
                for strick_data in url_list:
                    static_url = strick_data.get('static_url').get('url_list')
                    animate_url = strick_data.get('animate_url').get(
                        'url_list')
                    if len(static_url) == 0:
                        continue
                    filename = strick_data.get('display_name')
                    if len(animate_url) != 0:
                        strick_url = animate_url[0]
                        ext = strick_data.get('animate_type')
                    else:
                        strick_url = static_url[0]
                        ext = strick_data.get('animate_type')
                    resource = RESOURCES(self._clientid, self.task, strick_url, resourcetype,
                                         self.task.apptype)
                    resource.filename = filename + '.' + ext
                    resource.extension = ext
                    resource.io_stream = self._download_data_url(strick_url)
                    yield resource

    def _download_data_url(self, url):
        try:
            e = requests.get(url, stream=True)
            e.raw.decode_content = True
            return e.raw
        except Exception:
            self._logger.error("Download data from url error, err:{}".format(
                traceback.format_exc()))

    def _dict_factory(self, cursor, row):
        """
        格式化查询结果为字典
        :param cursor:
        :param row:
        :return:
        """
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def _try_decode(self, s: bytes, charset: str):
        try:
            if charset is None or charset == "":
                raise ValueError("charset is empty")

            if s is None:
                return ''

            return s.decode(charset)

        except Exception as ex:
            return None

    def _text_factory(self, x):
        """text factory"""
        if x is None or x == '':
            return ''
        res = self._try_decode(x, 'utf-8')
        if res is None:
            res = self._try_decode(x, 'gb2312')
        if res is None:
            res = self._try_decode(x, 'gbk')
        if res is None:
            res = self._try_decode(x, 'unicode')
        if res is None:
            self._logger.error("decode failed:" + str(x))
            res = ''
        return res

    def _select_data(self, sqlpath, sql):
        conn = sqlite3.connect(sqlpath)
        conn.row_factory = self._dict_factory
        conn.text_factory = self._text_factory
        c = conn.cursor()
        c.execute(sql)
        res = c.fetchall()
        conn.close()
        return res
