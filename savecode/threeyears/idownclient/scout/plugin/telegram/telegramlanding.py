"""
Author: judy
Date: 2020-11-10 10:18:24
LastEditTime: 2020-11-10 10:18:45
LastEditors: judy
Description: 
两种情况:
1.自己的账号，需要返回群id
2.别人的账号需要返回个人信息
FilePath: \idown_new\idownclient\scout\plugin\telegram\telegramlanding.py
"""
import json
import re
import threading
import traceback
from pathlib import Path

from datacontract.iscoutdataset import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import (
    EResourceType,
    NetworkGroup,
    NetworkMsg,
    NetworkProfile,
    NetworkResource,
)

from .telegrambase import TelegramBase


class TelegramLanding(TelegramBase):
    def __init__(self, task: IscoutTask) -> None:
        TelegramBase.__init__(self, task)

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

    def landing_target_phonenum(self, prephone, phone, level, reason=None):
        """
        用于telegram查询目标手机号的信息
        个人信息：昵称，userid,pic等
        :param prephone:
        :param phone
        :param level:
        :param reason:
        :return:
        """
        # 增加一个正则
        re_landres = re.compile("{.+?}.+?")
        if not phone.startswith("+"):
            phone = self._gcode + phone
        args = self._common_args(prephone)
        argnew = [
            f"-jar {self._jar.as_posix()}",
            "-search_user_id_by_phonenumber",
            f"-phone_number {phone}",
        ]
        argnew.extend(args)
        p = self._run_process(self._java.as_posix(), *argnew)
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
            # self.task.success_count()
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
            res = self._select_data(sql, pars, sqlpath)
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
                    gdata.reason = self.source
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

    def _get_profile(self, sqlpath: str, phone, reason=None):
        """
        在文件夹里扫描profile后缀的数据，添加task信息后返回
        因为profile里包含了userid并且只有一个文件，所以会优先将
        profile数据获取到再进行后续数据获取
        :param sqlpath:
        :return:
        """
        sql = """
        select * from users where self=?
        """
        par = (1,)
        res = self._select_data(sql, par, sqlpath)
        if len(res) == 0:
            self._logger.error("No profile in db")
            return
        eldict = res[0]
        if eldict.get("id") is None:
            self._logger.error("No profile in db")
            return
        _userid = eldict.get("id")
        phone = eldict.pop("phone")
        if phone is not None and phone != "":
            phone = self._output_format_str(phone)
        nickname = b""
        if eldict.get("last_name") is not None:
            nickname += eldict.pop("last_name")
        if eldict.get("first_name") is not None:
            nickname += eldict.pop("first_name")
        if nickname == b"" and eldict.get("username") is not None:
            nickname += eldict.pop("username")
        if nickname != b"":
            nickname = self._output_format_str(nickname)
        else:
            nickname = "UnknownUsername"
        nid = NetworkProfile(nickname, _userid, self.source)
        nid.reason = reason
        yield nid

    def landing_owner_phonenum(self, phonenum, level, reason=None):
        """
        自己的账号去拿grouid 和个人信息
        :param level:
        :param phonenum:
        :return:
        """
        # sqlite路径
        dbfile: Path = self._t_file / f"{phonenum}" / "database.sqlite"
        str_dbfile = dbfile.as_posix()
        # 0、下载数据库
        if not phonenum.startswith("+"):
            phonenum = self._gcode + phonenum
        # 1、账号登陆，这步需要自动检测账号是否有登录凭证，并且登陆凭证是否能用
        # 2、去下载数据库和资源文件
        log = f"Start download telegram db, taskid:{self.task.batchid}, phonenum:{phonenum}"
        self._logger.info(log)
        self._outprglog(log)
        downloadres = self._download_sqlitdb(phonenum)
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
        # 2、去拿所有的群
        # 下载群组数据
        try:
            for cdata in self._get_chats(str_dbfile, phonenum, reason):
                yield cdata
            # self.task.success_count()
        except:
            self.task.fail_count()
            self._logger.error(f"Get chats error,err:{traceback.format_exc()}")
        # 3、拿自己的个人信息
        try:
            for pdata in self._get_profile(str_dbfile, phonenum, reason):
                yield pdata
        except:
            self._logger.error(f"Get owner profile error, err:{traceback.format_exc()}")

    def landing(self, phone, level, reason=None):
        """
        description:账号落地查询
        1.自己的账号需要去下载数据库，返回个人信息和群id
        2.目标账号只需要去查询是否在线和个人信息，如果主账号没登陆，那么就还需要登陆主账号
        param {*}
        return {*}
        """
        # 1.无论是自己的账号还是目标账号第一步都是判断是否需要登陆下主账号
        # 判断主账号是否登录
        prephone = self.task.cmd.stratagyscout.preaccount.phone
        preglobaltelcode = self.task.cmd.stratagyscout.preaccount.globaltelcode
        major_phone = preglobaltelcode + prephone
        is_prephone_login = self._is_login(prephone, preglobaltelcode)
        if not is_prephone_login:
            # 需要登陆
            log = f"{major_phone}本地没有登陆凭证，需要登陆获取登陆凭证"
            self._outprglog(log)
            login_res = self.sms_login(major_phone)
            if not login_res:
                log = f"{major_phone}登陆失败，请重新尝试或者查询原因"
                self._outprglog(log)
                return
        # 然后进行下一步
        # 1、别人的账号
        if phone != major_phone:
            for ldata in self.landing_target_phonenum(
                major_phone, phone, level, reason
            ):
                yield ldata
        else:
            # 2.自己的账号
            for ldata in self.landing_owner_phonenum(phone, level, reason):
                yield ldata
        self.task.success_count()