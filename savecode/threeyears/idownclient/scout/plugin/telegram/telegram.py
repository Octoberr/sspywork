"""
目前需要telegram下载的信息
把以前idown的东西复制进来
create by swm 2019/09/18
需要增加time out 不然在查询userid当登陆凭证失效的时候iscout的线程会被卡死
"""
import base64
import datetime
import os
import random
import re
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
import json
from pathlib import Path
from datacontract.outputdata import OutputData

from datacontract.iscoutdataset import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import (
    NetworkProfile,
    NetworkGroup,
    NetworkMsg,
    NetworkResource,
    EResourceType,
)
from idownclient.config_spiders import telegramaccount
from ..scoutplugbase import ScoutPlugBase


class Telegram(ScoutPlugBase):
    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        # 默认账号，下载直通车
        # 备注by judy 2020/03/03 这个电话号码应该是前端传进来的，目前使用配置里面的主要是为了方便
        # 首先用户应该是能知道自己登录了哪几个账号，有哪几个账号的登陆令牌，所以直接接受的应该是前端传进来的电话号码
        self._pre_tel = telegramaccount.get("phone", "+8618161224132")
        self._stopsigin = False
        self.source = "Telegram"
        # sqlite路径
        self.dbfile: Path = self._t_file / f"{self._pre_tel}" / "database.sqlite"
        self.str_dbfile = self.dbfile.as_posix()

    def __get_group_userlist(self, groupid):
        """
        这里直接去拿这个群组的所有user，
        这个方法是确定不会出错的
        :param groupid:
        :return:
        """
        try:
            sql = """SELECT * 
             FROM chats 
             WHERE id = ?
             """
            pars = (groupid,)
            res = self._select_data(sql, pars)
            if len(res) == 0:
                return []
            # 因为这里只查了一个groupid所以这个数据只会有一个
            chat_res = res[0]
            re_chatall = re.compile("\[(\d+)\]")
            chat_line = self._output_format_str(chat_res["participants"])
            chat_all = re_chatall.findall(chat_line)
            return chat_all
        except:
            self._logger.error(
                f"Select group userlist error, groupid:{groupid}, err:{traceback.format_exc()}"
            )
            return []

    def _get_user_info(self, phone, reason=None):
        """
        这里改成舆情后就是使用群里面的userid去查对应id的信息
        唉！这不是明显拖慢了节奏吗？这个方法写出来都觉得蠢
        2019/10/16
        这里修改了东西，传进来的是群组的id所以以前的逻辑改了后需要重新写
        :param phone:
        :param reason:
        :return:
        """
        # 这里先去拿这个群联系人的列表
        # chat_all: list = self.__get_group_userlist(groupid)
        # 分段查询user表然后找用户，不能用userid去多次查询数据库，因为这个数量级可能会很大会导致许多问题
        limitdata = 1000
        offsetdata = 0
        while True:
            sql = """SELECT 
                    *
                    FROM users LIMIT ? OFFSET ?"""
            pars = (
                limitdata,
                offsetdata,
            )
            offsetdata += limitdata
            res = self._select_data(sql, pars)
            # 以防万一搞的这么一个判断，以后出问题了就在这里
            if len(res) == 0:
                return
            for el in res:
                try:
                    # 将为空的字段全部剔除
                    # eldict = {k: v for k, v in el.items() if v is not None}
                    eldict = el
                    c_id = eldict.get("id")
                    # 如果不是group的user那么就不去拿信息
                    # if c_id is None or c_id not in chat_all:
                    if c_id is None:
                        continue
                    contact_one: NetworkProfile = NetworkProfile(
                        phone, c_id, self.source
                    )
                    if eldict.get("phone") is not None:
                        contact_one.set_phone(
                            self._output_format_str(eldict.pop("phone"))
                        )
                    nickname = b""
                    if eldict.get("first_name") is not None:
                        nickname += eldict.pop("first_name")

                    if eldict.get("last_name") is not None:
                        nickname += b" " + eldict.pop("last_name")

                    if nickname == b"" and eldict.get("username") is not None:
                        nickname += eldict.pop("username")
                    if nickname != b"":
                        contact_one.nickname = self._output_format_str(nickname)
                    # 拿不到账号的好友关系，所以目前可以先不用管
                    # if eldict.get('contact') is not None:
                    #     friend = eldict.pop('contact')
                    #     if friend == '1':
                    #         isfriend = True
                    #     else:
                    #         isfriend = False
                    # self_data.set_contacts(contact_one, isfriend=isfriend)
                    yield contact_one
                except Exception:
                    self._logger.error(
                        f"Get profile error,err:{traceback.format_exc()}"
                    )
                    continue
            # 这个退出条件表示此时的数据已经没有达到量级了，所以这是最后一次查询，退出即可
            if len(res) < limitdata:
                break

    def _get_chats(self, sqlpath: str, phone, reason=None):
        limitdata = 1000
        offsetdata = 0
        while True:
            sql = """SELECT * 
             FROM chats 
             WHERE type = ?
             LIMIT ? OFFSET ?
             """
            pars = ("chat", limitdata, offsetdata)
            offsetdata += limitdata
            res = self._select_data(sql, pars)
            if len(res) == 0:
                return
            re_chatall = re.compile("\[(\d+)\]")
            for el in res:
                if None in el.values():
                    continue
                try:
                    # self._output_format_str(el['participants'])
                    if el.get("participants") is None or el.get("participants") == "":
                        continue
                    gid = el.get("id")
                    chat_line = self._output_format_str(el["participants"])
                    chat_all = re_chatall.findall(chat_line)
                    groupname = self._output_format_str(el["name"])
                    gdata: NetworkGroup = NetworkGroup(gid, self.source)
                    gdata.groupname = groupname
                    gdata.grouptype = "chat"
                    # gdata.reason = 'telegram群组信息下载'
                    gdata.reason = reason
                    gdata.membercount = len(chat_all)
                    gdata.phone = phone
                    for chat_one in chat_all:
                        gdata.set_participant(
                            NetworkProfile(phone, chat_one, self.source)
                        )
                    yield gdata
                except Exception:
                    self._logger.error(f"Get a chat error,err:{traceback.format_exc()}")
                    continue
            if len(res) < limitdata:
                break

    def _get_messages(self, phone, reason):
        """
        因为有两种数据类型，所以需要将舆情信息分开
        :param phone:
        :param reason:
        :return:
        """
        # 获取个人聊天信息
        # for mes in self.__get_all_message_data(phone, reason):
        #     yield mes
        # 获取群组聊天信息
        for channel_mes in self.__get_all_channel_message(phone, reason):
            yield channel_mes

    def __get_all_message_data(self, phone, reason):
        """
        这里是根据groupid去拿舆情信息
        修改 2019/10/31
        直接去拿所有的信息
        :param phone:
        :param reason:
        :return:
        """
        limitdata = 1000
        offsetdata = 0
        while True:
            sql = """SELECT
            id,
            chat_id,
            sender_id, 
            text,
            time,
            has_media, 
            media_type,
            media_file
            FROM messages 
            WHERE chat_id is not null 
            LIMIT ? OFFSET ?"""
            pars = (
                limitdata,
                offsetdata,
            )
            offsetdata += limitdata
            res: list = self._select_data(sql, pars)
            if len(res) == 0:
                return
            for messinfo in self._process_messages(res, phone):
                yield messinfo
            if len(res) < limitdata:
                break

    def __get_all_channel_message(self, phone, reason):
        """
        也是根据phone去拿舆情信息
        这里获取的是channel的message
        修改需求 2019/10/31
        直接去拿所有的数据
        :param groupid:
        :param reason:
        :return:
        """
        limitdata = 1000
        offsetdata = 0
        while True:
            sql_1 = """SELECT
                   id,
                   chat_id,
                   sender_id, 
                   text,
                   time,
                   has_media, 
                   media_type,
                   media_file
                   FROM Channels_Message 
                   WHERE chat_id is not null 
                   LIMIT ? OFFSET ?"""
            pars = (
                limitdata,
                offsetdata,
            )
            offsetdata += limitdata
            res = self._select_data(sql_1, pars)
            if len(res) == 0:
                return
            for messinfo in self._process_messages(res, phone):
                yield messinfo
            if len(res) < limitdata:
                break

    def _process_messages(self, res: list, phone):
        """
        无论是个人信息还是群组信息，字段都是一样的，
        所以在这个方法里统一处理
        :param res:
        :return:
        """
        for el in res:
            info = el.get("text")
            # 这里判断没有文本信息和资源信息那么就直接跳过
            if (info is None or info == b"") and el.get("has_media") is None:
                continue
            try:
                resourcefile = None
                # 频道信息只能是自己,这里是把频道的数据屏蔽了的，因为我做群组数据的时候根本没有把频道做了
                if el.get("sender_id") is not None:
                    strname = ""
                    # 私聊信息
                    if (
                        el.get("has_media") == 1
                        and len(self._output_format_str(el["media_file"]).split("."))
                        == 2
                    ):
                        # 写入资源文件
                        strname = self._output_format_str(el["media_file"])
                        # 这里获取文件的后缀名，并且转换为小写
                        file_extesnison = strname.split(".")[1]
                        messagetypetmp = [
                            key
                            for key, value in self.datatype.items()
                            if file_extesnison.lower() in value
                        ]
                        messagetypefunc = (
                            lambda x: EResourceType.Other_Text if len(x) == 0 else x[0]
                        )
                        message_type = messagetypefunc(messagetypetmp)
                        # 寻找本地的resources文件并且读取
                        resourcefile = self._write_resource_file(
                            el, strname, message_type
                        )
                        if resourcefile is None:
                            # file文件在本地没有就直接跳过吧
                            # 这个跳过显然不是很合理，但是一般如果资源文件里面还带有信息
                            # 如果我找不到文件那么这条信息也就没有意义，所以现在目前的方式就是不输出这条信息
                            continue
                        yield resourcefile
                    else:
                        message_type = EResourceType.Other_Text
                    # ichat_log = None
                    # 这里的messagetype用的是resources的type，但是在ichat_log的数据类型中需要的是int所以要取值
                    # 暂时没有使用到messagetype参数，相关功能先注释 modify by judy 20201112
                    # messagetype = message_type.value
                    # if el.get('dialog_id') is not None:
                    # 私聊
                    # dialogid = el.get('dialog_id')

                    # if el.get('chat_id') is not None:
                    # 群聊
                    dialogid = el.get("chat_id")
                    # else:
                    #     continue
                    # 构建一条聊天信息
                    chat_log = NetworkMsg(
                        dialogid, str(el.get("id")), el.get("sender_id"), self.source
                    )
                    chat_log.msgtime = str(datetime.datetime.fromtimestamp(el["time"]))
                    if strname == "" and el.get("text") is None:
                        # 如果文件是空的并且没有聊天数据那么这条数据就直接跳过了
                        continue
                    if strname != "":
                        # m_f_urls = [self._output_format_str(el.get('media_file'))]
                        chat_log.set_resource(resourcefile)
                    if el.get("text") is not None:
                        chat_log.text = self._output_format_str(el.get("text"))
                    yield chat_log
            except:
                self._logger.error(
                    f"Get single messages error,err:{traceback.format_exc()}"
                )
                continue

    def readtherbfile(self, fileinfo: dict):
        """
        找到telegram下载的文件并读取文件流
        :param fileinfo:
        :return:
        """
        fb = None
        te_path = None
        if fileinfo["filetype"] == "sticker":
            stickerspath = self._t_file / "stickers"
            stickername = stickerspath / fileinfo["filename"]
            if stickername.exists():
                fb = open(stickername, "rb+")
                te_path = stickername
        else:
            documentpath = self._t_file / fileinfo["account"] / "files"
            documentname = documentpath / fileinfo["filename"]
            if documentname.exists():
                fb = open(documentname, "rb+")
                te_path = documentname
        return fb, te_path

    def _write_resource_file(self, el: dict, strname, resourcetype):
        resource = NetworkResource(
            self.task,
            self.task.platform,
            "telegram/" + strname,
            self.source,
            resourcetype,
        )
        resource.filename = strname
        resource.extension = strname.split(".")[1]
        strtypename = self._output_format_str(el["media_type"])
        fileb, telegram_file_path = self.readtherbfile(
            {"filetype": strtypename, "account": self._pre_tel, "filename": strname}
        )
        if fileb is None:
            # None表示数据暂时没有下载或者是数据已经回写了并且删除了
            self._logger.info(f"No files were obtained locally, filename:{strname}")
            return None
        resource.stream = fileb
        # 这里进行oncomplete的赋值
        resource.isdeleteable = True
        resource.filepath_telegram = telegram_file_path
        resource.on_complete = self.delete_complete_file
        return resource

    def delete_complete_file(self, succ: bool, data: OutputData):
        """
        回调函数，在文件被读完后删除
        :param filename:
        :return:
        """
        res = True
        try:
            if not hasattr(data, "isdeleteable") or not hasattr(
                data, "filepath_telegram"
            ):
                return res
            if not data.isdeleteable:
                return res
            if data.filepath_telegram is None:
                self._logger.error("Telegram deleteable filepath is None")
                return res

            stm = data.get_stream()
            if stm is not None and not stm.closed:
                stm.close()
            if not data.filepath_telegram.exists():
                self._logger.error(
                    "Telegram deletable file is not found: {}".format(
                        data.filepath_telegram
                    )
                )
                return res

            data.filepath_telegram.unlink()
            # filename.unlink()
        except:
            res = False
        return res

    def get_groupsid(self, level, phonenum, reason=None):
        """
        落地方法就只能拿到群主信息Networkgroups
        :param level:
        :param phonenum:
        :return:
        """
        # 0、下载数据库
        if not phonenum.startswith("+"):
            phonenum = self._gcode + phonenum
        # 1、账号登陆，这步需要自动检测账号是否有登录凭证，并且登陆凭证是否能用
        # 2、去下载数据库和资源文件
        self._logger.info(
            f"Start download telegram db, taskid:{self.task.taskid}, phonenum:{phonenum}"
        )
        downloadres = self._download_sqlitdb()
        if not downloadres:
            raise Exception("Download telegram sqlite error")
        # 1、做查询之前的准备
        # 删除一列
        self._delete_data_row(self.str_dbfile)
        if not self.dbfile.exists():
            raise Exception(f"Sqlite db_file not exists, name:{self.str_dbfile}")
        # 2、去拿所有的群
        # 下载群组数据
        try:
            for cdata in self._get_chats(self.str_dbfile, phonenum, reason):
                yield cdata
            self.task.success_count()
        except:
            self.task.fail_count()
            self._logger.error(f"Get chats error,err:{traceback.format_exc()}")

    def public(self, phone, reason=None):
        """
        这里是根据传入的networkgroup数据
        来单独去查信息
        2019/10/16逻辑修改后写出来就合理很多了
        :param phone:
        :param reason:
        :return:
        """
        # 下载联系人数据
        try:
            for c_one in self._get_user_info(phone, reason=reason):
                yield c_one
        except:
            self._logger.error(f"Get user error,err:{traceback.format_exc()}")

        # 下载聊天数据
        try:
            for messages in self._get_messages(phone, reason):
                yield messages
        except:
            self._logger.error(f"Get message error,err:{traceback.format_exc()}")

    def _deal_landing(self, msg: dict, level, reason):
        """
        处理获取到的user信息
        :param msg:
        :return:
        """
        # 成功
        data = msg.get("data")
        if data is None:
            return
        dmsg = data.get("msg", "没有获取到任何信息")
        if dmsg == "已注册":
            userid = data.get("accountId")
            username = data.get("username", "UnknownUsername")
            nid = NetworkProfile(username, userid, self.source)
            # nid.userid = userid
            # nid.source = 'Telegram landing'
            nid.reason = reason
            yield nid
        else:
            self._logger.info(dmsg)

    def landing(self, phone, level, reason=None):
        """
        只能用于telegram查询手机号的信息
        个人信息：昵称，userid,pic等
        :param phone:
        :param level:
        :param reason:
        :return:
        """
        # 增加一个正则
        re_landres = re.compile("{.+?}.+?")
        if not phone.startswith("+"):
            phone = self._gcode + phone
        args = self._common_args(self._pre_tel)
        argnew = [
            f"-jar {self._jar.as_posix()}",
            "-search_user_id_by_phonenumber",
            f"-phone_number {phone}",
        ]
        argnew.extend(args)
        p = self._run_process(self._java.as_posix(), *argnew)
        # # 读取error
        # process_err = threading.Thread(target=self._read_err_log, args=(p,))
        # process_err.start()
        # # 刷新
        # process_flush = threading.Thread(target=self._std_flush, args=(p,))
        # process_flush.start()
        self._stopsigin = False
        try:
            # 只查询一次就出结果，直接就拿输出的，需要考虑timeout,不需要考虑刷新问题，不然会把iscout这个线程卡死
            # modify by judy 2020/07/20
            outs, errs = p.communicate(timeout=30)
            if isinstance(outs, bytes):
                res = outs.decode("utf-8")
            else:
                res = outs
            if res is not None and res != "":
                self._logger.debug(f"Telegram get line:{res}")
                lres = re_landres.search(res)
                if lres:
                    msg = lres.group()
                    msg_dict = json.loads(msg)
                    for nid in self._deal_landing(msg_dict, level, reason):
                        yield nid

            # while True:
            #     line = p.stdout.readline()
            #     if line is not None and line != '':
            #         self._logger.debug(f"Telegram get line:{line}")
            #         res = re_landres.search(line)
            #         if res:
            #             msg = res.group()
            #             msg_dict = json.loads(msg)
            #             for nid in self._deal_landing(msg_dict, level, reason):
            #                 yield nid
            #             break
            self.task.success_count()
        except:
            self.task.fail_count()
            res = False
            self._logger.error(
                f"Search phonenum error, phone:{phone}， err:{traceback.format_exc()}"
            )
            # print('There was a problem downloading the database， err:{traceback.format_exc()}')
            if p is not None:
                p.kill()
        finally:
            exitcode = p.wait()
            self._logger.info(f"program return code: {str(exitcode)}")
            # print(f"program return code: {str(exitcode)}")
            self._stopsigin = True
            p.poll()
            p.terminate()
            # process_flush.join()
            # process_err.join()
