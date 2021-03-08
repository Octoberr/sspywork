"""
短信登陆telegram
下载设备数据，命令行
下载信息数据库，反馈为文本结构体
create by judy 2018/10/29

update by judy 2019/03/07
新增回调函数，删除读取后的文件
修改查询账号是否在线

update by judy 2020/05/18
即将新增边下边读功能，可能会新增很多函数，这里做了一些拆分
不然那就实在是太长了
"""

import datetime
import json
import re
import subprocess
import threading
import traceback
from pathlib import Path

from datacontract.ecommandstatus import ECommandStatus
from datacontract.idowndataset import Task, EBackResult
# 联系人信息
from idownclient.clientdatafeedback import CONTACT, CONTACT_ONE, ICHATGROUP, ICHATGROUP_ONE, ICHATLOG, ICHATLOG_ONE, \
    IdownLoginLog, IdownLoginLog_ONE, PROFILE, RESOURCES, EResourceType
from idownclient.spider.appcfg import AppCfg
from .telegrambase import TelegramBase


class SpiderTelegram(TelegramBase):

    def __init__(self, tsk: Task, appcfg: AppCfg, clientid):
        TelegramBase.__init__(self, tsk, appcfg, clientid)

    def _sms_login(self):
        if not self._environment:
            return self._environment
        # login_res = False
        is_login = self._is_login()
        if is_login:
            login_res = True
        else:
            login_res = self.__sms_login()
        return login_res

    def __sms_login(self):
        # login
        # 默认带了+86的
        args = self._common_args(self.task.phone)
        p = self._run_telegram(
            *args,
            cmdtype='login',
            taskid=self.task.batchid,
            # stdout=fsout,
            # stderr=fserr,
        )
        # 读取输出
        process_login = threading.Thread(
            target=self._login_process, args=(p,))
        process_login.start()
        process_flush = threading.Thread(target=self._std_flush, args=(p,))
        process_flush.start()
        process_err = threading.Thread(target=self._read_err_log, args=(p,))
        process_err.start()
        try:
            if self._sectimeout > 0:
                process_login.join(self._sectimeout)
                if process_login.isAlive and process_login.is_alive():
                    self._logger.error(f"timeout sec:{self._sectimeout}")
            else:
                process_login.join()
        except Exception:
            self._logger.error(traceback.format_exc())
            if p is not None:
                p.kill()
        finally:
            p.poll()
            p.terminate()
            process_flush.join()
            process_err.join()
        return self._result

    def _online_check(self):
        """
        查询telegram的账号是否在线，
        telegram账号需要预先登陆
        :return:
        """
        # if not self._environment:
        # return self._environment
        # 查询的手机号
        args = ["-file {}".format(self.task.globaltelcode + self.task.phone)]
        # 已经登录的账号
        res = [
            f"-account {self.task.preglobaltelcode + self.task.preaccount}",
            f"-target {self.accountsdir}",
            f"-phone {'Honor9'}",
        ]
        args.extend(res)
        p = self._run_telegram(
            *args,
            cmdtype='find_online',
            taskid=self.task.batchid,
            # stdout=fsout,
            # stderr=fserr,
        )
        # 读取error
        process_err = threading.Thread(target=self._read_err_log, args=(p,))
        process_err.start()
        # 刷新
        process_flush = threading.Thread(target=self._std_flush, args=(p,))
        process_flush.start()
        self._stopsigin = False
        while True:
            line = p.stdout.readline()
            if line is not None and line != '':
                msg: str = line.strip().rstrip()
                if not msg.startswith("#"):
                    self._logger.info(f"{msg}")
                    continue
                retcode = msg
                idx = msg.find(' ')
                if idx < 0:
                    idx = msg.find('\t')
                if idx > 0:
                    retcode = msg[:idx].strip().rstrip()
                if retcode == '#@1000':
                    self._logger.info(f"result code: {msg}")
                    self._write_task_back(ECommandStatus.Failed, msg[6:])
                    break
                elif retcode == '#@21':
                    self._logger.info(f"result code: {msg}")
                    self._write_task_back(ECommandStatus.Succeed, "目标账号在线", result=EBackResult.Online)
                    break
                elif retcode == '#@22':
                    self._logger.info(f"result code: {msg}")
                    if '0' in msg:
                        # 0 既然表示在线为啥要归类到离线里
                        self._write_task_back(ECommandStatus.Succeed, "目标账号在线", result=EBackResult.Online)
                    elif '-1' in msg:
                        self._write_task_back(ECommandStatus.Succeed, "目标账号已经很久没有登陆", result=EBackResult.Offline)
                    else:
                        self._write_task_back(ECommandStatus.Succeed, "目标账号离线", result=EBackResult.Offline)
                    break
                elif retcode == '#@24':
                    self._logger.info(f"result code: {msg}")
                    self._write_task_back(ECommandStatus.Succeed, "账号没有注册", result=EBackResult.UnRegisterd)
                    break
                else:
                    self._logger.info(f"result code: {msg}")
                    self._write_task_back(ECommandStatus.Failed, msg)
                    break
        exitcode = p.wait()
        self._logger.info(f"program return code: {str(exitcode)}")
        self._stopsigin = True
        return

    def _check_registration(self):
        """
        没必要，查询账号是否在线的功能和register是一样的，
        telegram账号默认手机号都注册了
        :return:
        """
        self._write_task_back(ECommandStatus.Succeed, description="telegram默认所有手机号都注册了", result=EBackResult.Registerd)
        return

    def _logout(self) -> bool:
        logout_res = False
        args = self._common_args(self.task.phone)
        p = self._run_telegram(
            *args,
            cmdtype='logout',
            taskid=self.task.batchid,
            # stdout=fsout,
            # stderr=fserr,
        )
        # 读取error
        process_err = threading.Thread(target=self._read_err_log, args=(p,))
        process_err.start()
        # 刷新
        process_flush = threading.Thread(target=self._std_flush, args=(p,))
        process_flush.start()
        self._stopsigin = False
        while True:
            line = p.stdout.readline()
            if line is not None and line != '':
                msg: str = line.strip().rstrip()
                if not msg.startswith("#"):
                    self._logger.info("{}".format(msg))
                    continue
                retcode = msg
                idx = msg.find(' ')
                if idx < 0:
                    idx = msg.find('\t')
                if idx > 0:
                    retcode = msg[:idx].strip().rstrip()
                if retcode == '#@1000':
                    self._logger.info(f"result code: {msg}")
                    self._write_task_back(ECommandStatus.Failed, msg)
                    break
                elif retcode == '#@51':
                    self._logger.info(f"result code: {msg}")
                    logout_res = True
                    break
                elif retcode == '#@52':
                    self._logger.info(f"result code: {msg}")
                    break
                else:
                    self._logger.info(f"result code: {msg}")
                    break
        exitcode = p.wait()
        self._logger.info(f"program return code: {str(exitcode)}")
        self._stopsigin = True
        return logout_res

    def _is_login(self):
        """
        测试telegram是否需要重新登陆
        :return:
        """
        is_login_status = False
        p = None
        try:
            args = ["-file {}".format(self.task.globaltelcode + self.task.phone)]
            args.extend(self._common_args(self.task.phone))
            p = self._run_telegram(
                *args,
                cmdtype='find_online',
                taskid=self.task.batchid,
                # stdout=fsout,
                # stderr=fserr,
            )
            # 读取error
            process_err = threading.Thread(target=self._read_err_log, args=(p,))
            process_err.start()
            # 刷新
            process_flush = threading.Thread(target=self._std_flush, args=(p,))
            process_flush.start()
            self._stopsigin = False
            while True:
                line = p.stdout.readline()
                if line is not None and line != '':
                    msg: str = line.strip().rstrip()
                    if not msg.startswith("#"):
                        self._logger.info(f"{msg}")
                        continue
                    # retcode = msg
                    # idx = msg.find(' ')
                    # if idx < 0:
                    #     idx = msg.find('\t')
                    # if idx > 0:
                    #     retcode = msg[:idx].strip().rstrip()
                    if '#@21' in msg or '#@22' in msg or '#@23' in msg or '#@24' in msg:
                        self._logger.info(f"result code: {msg}")
                        is_login_status = True
                        break
                    else:
                        self._logger.info(f"result code: {msg}")
                        break
        except Exception:
            self._logger.error(traceback.format_exc())
            if p is not None:
                p.kill()
        finally:
            if p is not None:
                exitcode = p.wait()
                self._logger.info(f"program return code: {str(exitcode)}")
            self._stopsigin = True
        return is_login_status

    def _login_process(self, p: subprocess.Popen):
        if p is None or not isinstance(p, subprocess.Popen):
            raise Exception("subprocess.Popen object is None while dealing the stdout stream")
        self._stopsigin = False
        try:
            while True:
                line = p.stdout.readline()
                if line is not None and line != '':
                    msg: str = line.strip().rstrip()
                    if not msg.startswith("#"):
                        self._logger.info(f"{msg}")
                        continue
                    retcode = msg
                    idx = msg.find(' ')
                    if idx < 0:
                        idx = msg.find('\t')
                    if idx > 0:
                        retcode = msg[:idx].strip().rstrip()
                    if retcode == '#@31':
                        self._logger.info(f"result code: {msg}")
                        try:
                            vercode = self._get_vercode()
                        except:
                            # 验证码超时做的事情
                            vercode = '00000'
                        p.stdin.write(f"{vercode}\n")
                        p.stdin.flush()
                    elif retcode == '#@36':
                        self._logger.info(f'result code: {msg}')
                    elif retcode == '#@32':
                        # 登陆成功
                        self._logger.info(f"result code: {msg}")
                        self._result = True
                        break
                    else:
                        self._logger.info(f"result code: {msg}")
                        self._result = False
                        break
        except Exception:
            self._logger.error(traceback.format_exc())
            self._result = False
            if p is not None:
                p.kill()
        finally:
            exitcode = p.wait()
            self._logger.info(f"program return code: {str(exitcode)}")
            self._stopsigin = True
        return

    def _download(self):
        # 先下载数据库是为了给userid赋值
        # 下载数据库， user表，charts表，messages表
        try:
            for dbdata in self._download_sqlitdb():
                yield dbdata
        except:
            self._logger.error(f"Error downloading database data, err:{traceback.format_exc()}")
        # 下载设备列表
        try:
            for clientlist in self.__get_loginlog():
                yield clientlist
        except:
            self._logger.error(f"Error downloading device list, err:{traceback.format_exc()}")

    def __get_loginlog(self):
        args = self._common_args(self.task.phone)
        p = self._run_telegram(*args, taskid=self.task.batchid, cmdtype='client_list')
        # 读取error
        process_err = threading.Thread(target=self._read_err_log, args=(p,))
        process_err.start()
        # 刷新
        process_flush = threading.Thread(target=self._std_flush, args=(p,))
        process_flush.start()
        clientlist = []
        # 读取数据
        self._stopsigin = False
        try:
            while True:
                line = p.stdout.readline()
                if line is not None and line != '':
                    msg: str = line.strip().rstrip()
                    if not msg.startswith("#"):
                        self._logger.info(f"{msg}")
                        continue
                    retcode = msg
                    idx = msg.find(' ')
                    if idx < 0:
                        idx = msg.find('\t')
                    if idx > 0:
                        retcode = msg[:idx].strip().rstrip()
                    if '#@71' in msg:
                        retcode = '#@71'
                    if retcode == '#@71':
                        clientlist.append(msg)
                    elif retcode == '#@72':
                        for msgline in clientlist:
                            if msgline is None or msgline == '':
                                continue
                            if not msgline.startswith('#@71'):
                                continue
                            tmp = msgline.replace('#@71', '').strip().rstrip()
                            lines = json.loads(tmp)
                            if lines is None or len(lines) == 0:
                                continue
                            idown_login_log_all = IdownLoginLog(
                                self._clientid,
                                self.task,
                                self.task.apptype)
                            for line in lines:
                                login_log = IdownLoginLog_ONE(self.task, self.task.apptype, self._userid)
                                if line.get('country') is not None:
                                    login_log.country = line['country']
                                if line['region'].strip() != '':
                                    login_log.region = line['region']
                                if line.get('dateCreated') is not None:
                                    login_log.logintime = str(datetime.datetime.fromtimestamp(int(line['dateActive'])))
                                if line.get('deviceModel') is not None:
                                    login_log.devicemodel = line.get('deviceModel')
                                if line['platform'].strip() != '':
                                    login_log.platform = line['platform']
                                if line.get('appName') is not None:
                                    login_log.appname = line.get('appName')
                                if line['appVersion'] is not None:
                                    login_log.appversion = line['appVersion']
                                if line['dateActive'] is not None:
                                    login_log.activetime = str(
                                        int(line['dateActive']) -
                                        int(line['dateCreated'])) + 'seconds'
                                if line['ip'] is not None:
                                    login_log.ip = line['ip']
                                idown_login_log_all.append_innerdata(login_log)
                            self._logger.info('Download clientlist complete')
                            yield idown_login_log_all
                        break
                    else:
                        self._logger.info(f'{msg}')
                        break
        except Exception:
            self._logger.error(f"Download telegram client list error:{traceback.format_exc()}")
            if p is not None:
                p.kill()
        finally:
            self._stopsigin = True
            exitcode = p.wait()
            self._logger.info(f"program return code: {str(exitcode)}")
            p.poll()
            p.terminate()
            process_flush.join()
            process_err.join()

    def _download_sqlitdb(self):
        """
        这里留给新接口，发送下载命令后，telegram会持续不断的下载数据，放在一个文件夹里
        里面会存在6种数据，但是里面的信息不全，需要补全相关的任务信息
        modify by judy 2020/05/19
        下载进度  .idown_btask_back
        profile .idown_profile
        联系人   .idown_contact
        群组信息 .ichat_group
        聊天记录 .ichat_log
        资源数据 .idown_resource
        :return:
        """
        args = self._common_args(self.task.phone)
        argnew = [
            f"-jar {self.telegram}",
            f"-{'download'}",
            f"-{'download_public_channel'}"
        ]
        argnew.extend(args)
        p = self._run_process(str(self.java), *argnew, taskid=self.task.batchid)
        # 读取error
        process_err = threading.Thread(target=self._read_err_log, args=(p,))
        process_err.start()
        # 刷新
        process_flush = threading.Thread(target=self._std_flush, args=(p,))
        process_flush.start()
        self._stopsigin = False
        try:
            while True:
                line = p.stdout.readline()
                if line is not None and line != '':
                    msg: str = line.strip().rstrip()
                    if not msg.startswith("#") or msg.startswith("#@2000"):
                        self._logger.info(f"{msg}")
                        continue
                    retcode = msg
                    idx = msg.find(' ')
                    if idx < 0:
                        idx = msg.find('\t')
                    if idx > 0:
                        retcode = msg[:idx].strip().rstrip()
                    if retcode == '#@43':
                        self._logger.info(f'{msg}')
                        download_process = self._downloadprogress.findall(msg)
                        if len(download_process) != 0:
                            cmdrecmsg = f'正在下载，当前下载进度: {float(download_process[-1])}%'
                            self.task.progress = float(download_process[-1]) / 100
                            self._write_task_back(ECommandStatus.Dealing, cmdrecmsg)
                    elif retcode == '#@41':
                        self._logger.info(f'{msg}')
                        try:
                            # 去数据库拿数据,没拿到userid之前不能break
                            for result in self._get_sqlite_dbdata():
                                yield result
                        except Exception:
                            self._logger.error(f"Sqlite get data wrong, err:{traceback.format_exc()}")
                        break
                    else:
                        # 出现意外情况停止
                        self._logger.info(f'{msg}')
                        break
        except:
            self._logger.error(f"There was a problem downloading the database， err:{traceback.format_exc()}")
            if p is not None:
                p.kill()
        finally:
            exitcode = p.wait()
            self._logger.info(f"program return code: {str(exitcode)}")
            self._stopsigin = True
            p.poll()
            p.terminate()
            process_flush.join()
            process_err.join()

    def _get_sqlite_dbdata(self):
        """
        这个接口会去不断地扫描telegram下的文件夹
        直到
        下载完成
        下载出错
        超时30分钟后没有数据出现表示telegram可能已经被卡死也结束
        modify by judy 2020/05/19
        :return:
        """
        dbfile: Path = self.accountsdir / f'{self.task.globaltelcode + self.task.phone}' / 'database.sqlite'
        if not dbfile.exists():
            raise Exception(f"Db file not exists: {dbfile}")
        # 同理先下载profile数据，是为了给userid赋值
        try:
            profile_data = self.__get_profile(str(dbfile))
            for profile in profile_data:
                yield profile
        except:
            self._logger.error(f"Get user error,err:{traceback.format_exc()}")
        # 再下载联系人数据
        try:
            contact_data = self._get_users(str(dbfile))
            for c_one in contact_data:
                yield c_one
        except:
            self._logger.error(f"Get user error,err:{traceback.format_exc()}")
        # 下载群组数据
        try:
            for chatsdata in self._get_chats(str(dbfile)):
                yield chatsdata
        except:
            self._logger.error(f"Get chats error,err:{traceback.format_exc()}")
        # 下载聊天数据
        try:
            for messages in self._get_messages(str(dbfile)):
                yield messages
        except:
            self._logger.error(f"Get message error,err:{traceback.format_exc()}")
        # 备份数据库，据说是实现了增量下载不需要备份
        # self.mvsqlitetobak(str(dbfile))
        return

    def __get_download_progress(self):
        """
        在文件夹里扫描回馈，取最新的进度，添加信息后返回
        :return:
        """
        pass

    def __get_profile(self, sqlpath: str):
        """
        在文件夹里扫描profile后缀的数据，添加task信息后返回
        因为profile里包含了userid并且只有一个文件，所以会优先将
        profile数据获取到再进行后续数据获取
        :param sqlpath:
        :return:
        """
        sql = '''
        select * from users where self=?
        '''
        par = (1,)
        res = self._select_data(sqlpath, sql, par)
        if len(res) == 0:
            self._logger.error("No profile in db")
            return
        eldict = res[0]
        if eldict.get('id') is None:
            self._logger.error("No profile in db")
            return
        self._userid = eldict.get('id')
        p_data = PROFILE(self._clientid, self.task, self.task.apptype, self._userid)
        phone = eldict.pop('phone')
        if phone is not None and phone != '':
            p_data.phone = self._output_format_str(phone)
        p_data.account = self._phone
        nickname = b''
        if eldict.get('last_name') is not None:
            nickname += eldict.pop('last_name')
        if eldict.get('first_name') is not None:
            nickname += eldict.pop('first_name')
        if nickname == b'' and eldict.get('username') is not None:
            nickname += eldict.pop('username')
        if nickname != b'':
            p_data.nickname = self._output_format_str(nickname)
        # if len(prodata) > 0:
        #     p_data.append_details(prodata)
        yield p_data

    def _get_users(self, sqlpath: str):
        """
        扫描联系人后缀的数据，添加task信息后返回
        :param sqlpath:
        :return:
        """
        limitdata = 1000
        offsetdata = 0
        while True:
            sql = '''SELECT 
            *
            FROM users LIMIT ? OFFSET ?'''
            pars = (
                limitdata,
                offsetdata,
            )
            offsetdata += limitdata
            res = self._select_data(sqlpath, sql, pars)
            if len(res) == 0:
                return
            all_contact = CONTACT(self._clientid, self.task, self.task.apptype)
            for el in res:
                try:
                    # 将为空的字段全部剔除
                    # eldict = {k: v for k, v in el.items() if v is not None}
                    eldict = el
                    if eldict.get('id') is None:
                        continue
                    contact_one = CONTACT_ONE(self._userid, eldict.get('id'), self.task, self.task.apptype)
                    if eldict.get('phone') is not None:
                        contact_one.phone = self._output_format_str(eldict.pop('phone'))
                    nickname = b''
                    if eldict.get('last_name') is not None:
                        nickname += eldict.pop('last_name')
                    if eldict.get('first_name') is not None:
                        nickname += eldict.pop('first_name')
                    if nickname == b'' and eldict.get('username') is not None:
                        nickname += eldict.pop('username')
                    if nickname != b'':
                        contact_one.nickname = self._output_format_str(nickname)
                    if eldict.get('contact') is not None:
                        contact_one.isfriend = eldict.pop('contact')
                    if eldict.get('mutualContact') is not None:
                        contact_one.bothfriend = eldict.pop('mutualContact')
                    if eldict.get('deleted') is not None:
                        contact_one.isdeleted = eldict.pop('deleted')
                    all_contact.append_innerdata(contact_one)
                except Exception:
                    self._logger.error(f"Get profile error,err:{traceback.format_exc()}")
                    continue
            if all_contact.innerdata_len != 0:
                yield all_contact
            if len(res) < limitdata:
                break

    def _get_chats(self, sqlpath: str):
        """
        扫描群组后缀的数据，添加task信息后返回
        :param sqlpath:
        :return:
        """
        limitdata = 1000
        offsetdata = 0
        while True:
            sql = '''SELECT
             * 
             FROM chats LIMIT ? OFFSET ?'''
            pars = (
                limitdata,
                offsetdata,
            )
            offsetdata += limitdata
            res = self._select_data(sqlpath, sql, pars)
            if len(res) == 0:
                return
            re_chatall = re.compile('\[(\d+)\]')
            ichat_all = ICHATGROUP(self._clientid, self.task, self.task.apptype)
            for el in res:
                if None in el.values():
                    continue
                try:
                    # self._output_format_str(el['participants'])
                    if el.get('participants') is None or el.get('participants') == '':
                        continue
                    chat_line = self._output_format_str(el['participants'])
                    chat_all = re_chatall.findall(chat_line)
                    userid = self._userid
                    ichat_data = ICHATGROUP_ONE(self.task, self.task.apptype, userid, el['id'])
                    ichat_data.append_participants(*chat_all)
                    ichat_data.grouptype = self._output_format_str(el['type'])
                    ichat_data.groupname = self._output_format_str(el['name'])
                    ichat_all.append_innerdata(ichat_data)
                except Exception:
                    self._logger.error(f"Get a chat error,err:{traceback.format_exc()}")
                    continue
            if ichat_all.innerdata_len > 0:
                yield ichat_all
            if len(res) < limitdata:
                break

    def _get_messages(self, sqlpath: str):
        """
        扫描聊天信息后缀，添加task信息后返回
        扫描资源文件后缀，添加task信息后返回
        :param sqlpath:
        :return:
        """
        # 获取个人聊天信息
        for mes in self.__get_all_message_data(sqlpath):
            yield mes
        # 获取群组聊天信息
        for channel_mes in self.__get_all_channel_message(sqlpath):
            yield channel_mes

    def __get_all_message_data(self, sqlpath: str):
        limitdata = 1000
        offsetdata = 0
        while True:
            sql = '''SELECT
            id,
            dialog_id,
            chat_id,
            sender_id, 
            text,
            time,
            has_media, 
            media_type,
            media_file
            FROM messages LIMIT ? OFFSET ?'''
            pars = (
                limitdata,
                offsetdata,
            )
            offsetdata += limitdata
            res = self._select_data(sqlpath, sql, pars)
            if len(res) == 0:
                return
            for messinfo in self._process_messages(res):
                yield messinfo
            if len(res) < limitdata:
                break

    def __get_all_channel_message(self, sqlpath: str):
        limitdata = 1000
        offsetdata = 0
        while True:
            sql_1 = '''SELECT
                   id,
                   message_type,
                   chat_id,
                   sender_id, 
                   text,
                   time,
                   has_media, 
                   media_type,
                   media_file
                   FROM Channels_Message LIMIT ? OFFSET ?'''
            pars = (
                limitdata,
                offsetdata,
            )
            offsetdata += limitdata
            res = self._select_data(sqlpath, sql_1, pars)
            if len(res) == 0:
                return
            for messinfo in self._process_messages(res):
                yield messinfo
            if len(res) < limitdata:
                break

    def _process_messages(self, res):
        ichat_log_all = ICHATLOG(self._clientid, self.task, self.task.apptype)
        for el in res:
            info = el.get('text')
            if (info is None or info == b'') and el.get('has_media') is None:
                continue
            try:
                # 频道信息只能是自己
                if el.get('message_type') == b'Channels_Message' and el.get('sender_id') is None:
                    el['sender_id'] = self._userid
                if el.get('sender_id') is not None:
                    strname = ''
                    # 私聊信息
                    if el.get('has_media') == 1 and len(self._output_format_str(el['media_file']).split('.')) == 2:
                        # 写入资源文件
                        strname = self._output_format_str(el['media_file'])
                        # if len(strname.split('.')) != 2:
                        #     self._logger.error(
                        #         "File name error，the file has no suffixes，messagefilename:{}".format(strname))
                        #     continue
                        # 这里获取文件的后缀名，并且转换为小写
                        file_extesnison = strname.split('.')[1]
                        messagetypetmp = [
                            key for key, value in self.datatype.items()
                            if file_extesnison.lower() in value
                        ]
                        messagetypefunc = lambda x: EResourceType.Other_Text if len(x) == 0 else x[0]
                        message_type = messagetypefunc(messagetypetmp)
                        # 寻找本地的resources文件并且读取
                        resourcefile = self._write_resource_file(el, strname, message_type)
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
                    if el.get('dialog_id') is not None:
                        # 私聊
                        ichat_log = ICHATLOG_ONE(
                            self.task, self.task.apptype, self._userid,
                            messagetype, el.get('dialog_id'), 0, str(el.get('id')),
                            el.get('sender_id'),
                            str(datetime.datetime.fromtimestamp(el['time'])))
                    elif el.get('chat_id') is not None:
                        # 群聊
                        ichat_log = ICHATLOG_ONE(
                            self.task, self.task.apptype, self._userid,
                            messagetype, el.get('chat_id'), 1, str(el.get('id')),
                            el.get('sender_id'),
                            str(datetime.datetime.fromtimestamp(el['time'])))
                    else:
                        continue
                    if strname == '' and el.get('text') is None:
                        # 如果文件是空的并且没有聊天数据那么这条数据就直接跳过了
                        continue
                    if strname != '':
                        # m_f_urls = [self._output_format_str(el.get('media_file'))]
                        ichat_log.append_resource(resourcefile)
                    if el.get('text') is not None:
                        ichat_log.content = self._output_format_str(el.get('text'))
                    ichat_log_all.append_innerdata(ichat_log)
            except:
                self._logger.error(f"Get single messages error,err:{traceback.format_exc()}")
                continue
        if ichat_log_all.innerdata_len > 0:
            yield ichat_log_all
        else:
            return

    def _write_resource_file(self, el: dict, strname, resourcetype):
        resource = RESOURCES(self._clientid, self.task, strname, resourcetype,
                             self.task.apptype)
        resource.filename = strname
        resource.extension = strname.split('.')[1]
        strtypename = self._output_format_str(el['media_type'])
        fileb, telegram_file_path = self.readtherbfile({
            "filetype": strtypename,
            "account": self.task.globaltelcode + self.task.phone,
            "filename": strname
        })
        if fileb is None:
            # None表示数据暂时没有下载或者是数据已经回写了并且删除了
            self._logger.info(f'No files were obtained locally, filename:{strname}')
            return None
        resource.io_stream = fileb
        # 这里进行oncomplete的赋值
        resource.isdeleteable = True
        resource.filepath_telegram = telegram_file_path
        resource.on_complete = self.delete_complete_file
        return resource

    def readtherbfile(self, fileinfo: dict):
        """
        找到telegram下载的文件并读取文件流
        :param fileinfo:
        :return:
        """
        fb = None
        te_path = None
        if fileinfo['filetype'] == 'sticker':
            stickerspath = self.accountsdir / 'stickers'
            stickername = stickerspath / fileinfo['filename']
            if stickername.exists():
                fb = open(stickername, 'rb+')
                te_path = stickername
        else:
            documentpath = self.accountsdir / fileinfo['account'] / 'files'
            documentname = documentpath / fileinfo['filename']
            if documentname.exists():
                fb = open(documentname, 'rb+')
                te_path = documentname
        return fb, te_path
