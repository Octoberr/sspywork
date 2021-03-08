"""
Author: judy
Date: 2020-11-10 10:18:04
LastEditTime: 2020-11-11 16:35:20
LastEditors: judy
Description: telegram的舆情监测，是根据手机号和groupid去下载相应的数据
因为如果是进行舆情监测，那么手机号就是和预置账号一样的，只需要使用预置账号的手机号即可

FilePath: \idown_new\idownclient\scout\plugin\telegram\telegrampublic.py
"""

import datetime
from pathlib import Path
import re
import sqlite3
import traceback
from .telegrambase import TelegramBase
from datacontract.iscoutdataset import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import (
    EResourceType,
    NetworkGroup,
    NetworkMsg,
    NetworkProfile,
    NetworkResource,
)


class TelegramPublic(TelegramBase):
    def __init__(self, task: IscoutTask) -> None:
        TelegramBase.__init__(self, task)

    def __get_group_userlist(self, groupid, sqlpath: str):
        """
        这里直接去拿这个群组的所有user，
        这个方法是确定不会出错的
        :param groupid:
        :return:
        """
        result = []
        try:
            sql = """SELECT * 
             FROM chats 
             WHERE id = ?
             """
            pars = (groupid,)
            res = self._select_data(sql, pars, sqlpath)
            if len(res) == 0:
                return result
            # 因为这里只查了一个groupid所以这个数据只会有一个
            chat_res = res[0]
            re_chatall = re.compile("\[(\d+)\]")
            chat_line = self._output_format_str(chat_res["participants"])
            result = re_chatall.findall(chat_line)
        except:
            self._logger.error(
                f"Select group userlist error, groupid:{groupid}, err:{traceback.format_exc()}"
            )
        return result

    def _get_user_info(self, phone, groupid, sqlpath: str, reason=None):
        """
        这里改成舆情后就是使用群里面的userid去查对应id的信息
        唉！这不是明显拖慢了节奏吗？这个方法写出来都觉得蠢
        2019/10/16
        这里修改了东西，传进来的是群组的id所以以前的逻辑改了后需要重新写
        :param groupid:
        :param reason:
        :return:
        """
        # 这里先去拿这个群联系人的列表
        chat_all: list = self.__get_group_userlist(groupid, sqlpath)
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
            res = self._select_data(sql, pars, sqlpath)
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
                    if c_id is None or c_id not in chat_all:
                        # if c_id is None:
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
                    messagetype = message_type.value
                    # if el.get('dialog_id') is not None:
                    # 私聊
                    # dialogid = el.get('dialog_id')

                    # if el.get('chat_id') is not None:
                    # 群聊
                    dialogid = el.get("chat_id")
                    if dialogid is None or dialogid == "":
                        continue
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

    def _get_messages(self, phone, groupid, sqlpath: str, reason=None):
        """
        根据groupid获取指定的群组信息
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
                   FROM Channels_Message 
                   WHERE chat_id = ?
                   LIMIT ? OFFSET ?"""
            pars = (
                groupid,
                limitdata,
                offsetdata,
            )
            offsetdata += limitdata
            res = self._select_data(sql, pars, sqlpath)
            if len(res) == 0:
                return
            for messinfo in self._process_messages(res, phone):
                yield messinfo
            if len(res) < limitdata:
                break

    def public_groupid(self, phone, groupid, sqlpath: str, reason=None):
        """
        description:
        根据传入的groupid去查询群消息
        2.然后再去拿群的信息
        param {*}
        return {*}
        """
        # 下载联系人数据
        try:
            # 根据groupid去查询群组成员
            for c_one in self._get_user_info(phone, groupid, sqlpath, reason):
                yield c_one
        except:
            self._logger.error(f"Get user error,err:{traceback.format_exc()}")

        # 下载聊天数据
        try:
            for messages in self._get_messages(phone, groupid, sqlpath, reason):
                yield messages
        except:
            self._logger.error(f"Get message error,err:{traceback.format_exc()}")

    def public(self, groupid, level, reason=None):
        """
        description:
        telegram舆情监测，根据groupid去监测群信息
        param {*}
        return {*}
        """
        prephone = self.task.cmd.stratagyscout.preaccount.phone
        preglobaltelcode = self.task.cmd.stratagyscout.preaccount.globaltelcode
        major_phone = preglobaltelcode + prephone
        # 下载数据库前需要判断账号是否登录，没有登陆需要手动登陆
        is_prephone_login = self._is_login(prephone, preglobaltelcode)
        if not is_prephone_login:
            # 需要登陆
            log = f"{major_phone}本地没有登陆凭证，需要登陆获取登陆凭证"
            self._outprglog(log)
            login_res = self.sms_login(major_phone)
            if not login_res:
                log = f"{major_phone}登陆失败，请重新尝试或排查原因"
                self._outprglog(log)
                return
                # sqlite路径
        dbfile: Path = self._t_file / f"{major_phone}" / "database.sqlite"
        str_dbfile = dbfile.as_posix()
        # 0、下载数据库
        if not major_phone.startswith("+"):
            major_phone = self._gcode + major_phone
            # 2、去下载数据库和资源文件
        log = f"Start download telegram db\nscout batchid:{self.task.batchid}\nphonenum:{major_phone}"
        self._logger.info(log)
        self._outprglog(log)
        downloadres = self._download_sqlitdb(major_phone)
        if not downloadres:
            log = "Download telegram sqlite error"
            self._outprglog(log)
            self._logger.error(log)
            return
            # 1、做查询之前的准备
        # 删除一列
        self._delete_data_row(str_dbfile)
        if not dbfile.exists():
            raise Exception(f"Sqlite db_file not exists, name:{str_dbfile}")
        # 查询信息
        for data in self.public_groupid(major_phone, groupid, str_dbfile, reason):
            yield data
