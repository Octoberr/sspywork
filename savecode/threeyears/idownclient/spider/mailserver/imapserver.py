"""imap下载邮件"""

import email
import errno
import io
import re
import socket
import time
import traceback
from imaplib import IMAP4, IMAP4_SSL

from datacontract.idowndataset.task import Task

from ...clientdatafeedback.idownfeedback import EML, PROFILE, Folder
from ..appcfg import AppCfg
from ..spidermail.spidermailbase import SpiderMailBase


class ImapServer(SpiderMailBase):
    # _re_folder = re.compile(r'^(\(.*?\))\s(".*?")\s"?([^"]+)"?$', re.S)
    _re_folder = re.compile(
        r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')

    def __init__(self, task: Task, clientid):
        appcfg = AppCfg(appname="IMAP",
                        apphosts=None,
                        apptype=3100,
                        appclassify=3,
                        appclass=ImapServer,
                        crosswall=True,
                        enable=True)
        SpiderMailBase.__init__(self, task, appcfg, clientid, task.account)

        self._apptype = task.apptype
        if self._apptype is None:
            # 约定了apptype没有就是-1，
            # 约定了调用方必传apptype
            self._apptype = -1

        self._host: str = None
        self._port: int = None

        self._svr_class = None
        self._svr: IMAP4 = None

        self._get_host_port()
        self._init_server()

    def __del__(self):
        if not self._svr is None:
            self._svr.logout()
            self._svr = None

    def _get_host_port(self):
        if self.task.cmd is None or \
                self.task.cmd.stratagymail is None or \
                self.task.cmd.stratagymail.mail_service is None or \
                self.task.cmd.stratagymail.mail_service.imap_host is None or \
                self.task.cmd.stratagymail.mail_service.imap_port is None:
            raise Exception(
                "Missing IMAP mailserver host and port: taskid={}, batchid={}".
                format(self.task.taskid, self.task.batchid))
        self._host = self.task.cmd.stratagymail.mail_service.imap_host
        self._port = self.task.cmd.stratagymail.mail_service.imap_port

    def _init_server(self):
        if self.task.cmd is None or \
                self.task.cmd.stratagymail is None or \
                self.task.cmd.stratagymail.mail_service is None or \
                self.task.cmd.stratagymail.mail_service.imap_isssl is None:
            raise Exception(
                "Missing IMAP mailserver cmd: taskid={}, batchid={}".format(
                    self.task.taskid, self.task.batchid))
        if not self.task.cmd.stratagymail.mail_service.imap_isssl:
            # self._svr = IMAP4(self._host, self._port)
            self._svr_class = IMAP4
        else:
            # self._svr = IMAP4_SSL(self._host, self._port)
            self._svr_class = IMAP4_SSL

    def _connect_to_server(self) -> bool:
        """connect to server, return succeed or not"""
        res: bool = False
        try:
            if self._svr_class is None:
                try:
                    self._init_server()
                except Exception:
                    pass

            self._svr = self._svr_class(self._host, self._port)
            # self._svr.sock.setblocking(False)
            self._svr.sock.settimeout(2)
            # self._svr.print_log()
            # for log in self._svr._cmd_log_idx
            # print(self._svr._cmd_log)
            for k, v in self._svr._cmd_log.items():
                self._logger.info("{}:{}".format(k, v[0]))

            datastr = "00002 ID (\"name\" \"com.tencent.foxmail\" \"version\" \"7.2.7.26\" \"os\" \"windows\" \"os - version\" \"6.2\" \"vendor\" \"tencent limited\" \"contact\" \"foxmail@foxmail.com\")\r\n"
            self._logger.info(datastr)
            data = datastr.encode(encoding='utf-8')
            self._svr.send(data)
            time.sleep(1)
            msg = self._read_str_to_end()

            if msg.__contains__("OK ID completed") or msg.__contains__(
                    "OK Success"):
                self._logger.info(msg)

            res = True

        except Exception:
            self._logger.warn(
                "Connect to mailserver error: taskid={}, batchid={}, mailserver={}:{} {}"
                .format(self.task.taskid, self.task.batchid, self._host,
                        self._port, traceback.format_exc()))
        return res

    def _read_bytes_blocks(self) -> iter:
        """read bytes blocks"""
        if self._svr is None:
            raise Exception("Server not connected: {}:{}".format(
                self._host, self._port))

        while True:
            try:
                bs = self._svr.sock.recv(1024)
                if len(bs) < 1:
                    break

                yield bs

            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    # No data available
                    pass
                else:
                    self._logger.trace(
                        "read str to end error: {}:{} {}".format(
                            self._host, self._port, traceback.format_exc()))
                break
            except Exception:
                self._logger.trace("Read bytes to end error: {}:{} {}".format(
                    self._host, self._port, traceback.format_exc()))
                break

    def _read_bytes_to_end(self) -> bytes:
        """read bytes to the end of the stream"""
        if self._svr is None:
            raise Exception("Server not connected: {}:{}".format(
                self._host, self._port))
        res: bytes = bytes()
        try:

            for bs in self._read_bytes_blocks():
                res += bs
        except Exception:
            self._logger.error("Read str to end error: {}:{} {}".format(
                self._host, self._port, traceback.format_exc()))
        return res

    def _read_str_to_end(self) -> str:
        """read str to the end of the stream"""
        if self._svr is None:
            raise Exception("Server not connected: {}:{}".format(
                self._host, self._port))
        res: str = ''
        try:
            bs = self._read_bytes_to_end()
            if not isinstance(bs, bytes) or len(bs) < 1:
                return res
            res = bs.decode(encoding='utf-8')

        except Exception:
            self._logger.error("Read str to end error: {}:{} {}".format(
                self._host, self._port, traceback.format_exc()))
        return res

    ###############################
    # login

    def _pwd_login(self) -> bool:
        """
        账号密码登陆
        :return:
        """
        res: bool = False
        try:
            self._logger.info("Login start: {}".format(self._account))
            if not self._connect_to_server():
                self._logger.error("Login failed.")
                return res

            res = self._svr.login(self.task.account, self.task.password)
            if res is None or len(
                    res
            ) < 1 or not 'OK' in res or not self._svr.state == 'AUTH':
                self._logger.error("Login failed: {}".format(res))
                return res

            self._userid = "{}_{}".format(self._apptype, self._account)

            # 执行挂起操作
            self._svr.noop()

            # self._logger.info("Login succeed: {}".format(res))

        except Exception:
            self._logger.error("Pwd Login error: {}".format(
                traceback.format_exc()))
        return res

    ###############################
    # download

    def _get_profile(self) -> iter:
        """返回 Profile"""
        try:
            # 为了userid唯一性，userid = apptype + account
            userid = "{}_{}".format(self._apptype, self._account)
            p: PROFILE = PROFILE(
                self._clientid,
                self.task,
                self.task.apptype,
                userid,
            )

            p.account = self.task.account

            yield p
        except Exception:
            self._logger.info("Get Profile error: {}".format(
                traceback.format_exc()))

    def _get_folders(self) -> iter:
        try:
            self._logger.info("Start get folders")

            # Get folder list
            tp, data = self._svr.list()
            if data is None or len(data) < 1:
                self._logger.info("No folder found.")
                return

            for d in data:
                f = self._parse_folder(d.decode())
                if not isinstance(f, Folder):
                    continue
                yield f

        except Exception:
            self._logger.error("Get folders error: {}".format(
                traceback.format_exc()))

    def _parse_folder(self, datastr: str) -> Folder:
        folder: Folder = None
        try:
            if not isinstance(datastr, str) or datastr == "":
                return folder

            m = self._re_folder.match(datastr)
            if m is None:
                return folder
            flags, delimiter, folder_name = m.groups()
            folder = Folder()
            folder.name = folder_name
            folder.folderid = folder_name

        except Exception:
            self._logger.error("Parse folder error: {} {}".format(
                datastr, traceback.format_exc()))
        return folder

    def _get_mails(self, folder: Folder) -> iter:
        try:
            if not isinstance(folder, Folder):
                self._logger.error("Invalid Folder for getting mails")
                return

            tp, data = self._svr.select(folder.name, readonly=True)
            if tp == "NO" or not isinstance(data, list) or len(
                    data) != 1 or not self._svr.state == "SELECTED":
                self._logger.info("Select folder failed: {} {}".format(
                    folder.name, data))
                return
            folder.folderid = data[0].decode()
            tp, items = self._svr.search(None, "ALL")
            if not tp == "OK" or not isinstance(items, list) or len(items) < 1:
                self._logger.info("Search mail failed: {}".format(folder.name))
                return

            items = items[0].decode().split(' ')
            datas = []
            for i in items:
                if i is None or i == "":
                    continue
                datas.append(i)
            if len(datas) < 1:
                self._logger.info("No mail find in folder: {}".format(
                    folder.name))
                return
            self._logger.info("Start get mails of folder: {}({})".format(
                folder.name, len(datas)))

            for i in datas:
                try:
                    mail = self._fetch_mail(i, folder, 0)
                    if not isinstance(mail, EML):
                        continue

                    yield mail

                except Exception:
                    self._logger.error(
                        "Fetch one mail(id={}) error: {}".format(
                            i, traceback.format_exc()))

        except Exception:
            self._logger.error("Get mails error: {}".format(
                traceback.format_exc()))

    def _fetch_mail(self, mid: str, folder: Folder,
                    recursive_lvl: int = 0) -> EML:
        """download mail"""
        res: EML = None
        try:
            if not isinstance(mid, str):
                self._logger.error(
                    "Invalid mailid for fetching email: mid={}".format(mid))
                return res
            if not isinstance(folder, Folder):
                self._logger.error(
                    "Invalid Folder for fetching email: mid={}".format(mid))
                return res
            if recursive_lvl > 3:
                self._logger.info(
                    "Retry fetch mail(id={}) failed 3 times, continue to the next"
                )
                return res

            try:
                a = int(mid)
            except Exception:
                self._logger.error(
                    "Invalid mailid for fetching email: mid={}".format(mid))
                return res
            tp, data = self._svr.fetch(mid, '(RFC822)')
            if data is None or len(data) < 1:
                self._logger.error(
                    "Invalid email response data: mid={}".format(mid))
                return res
            msg = data[0]
            if msg is None or len(msg) < 1:
                self._logger.error(
                    "Invalid email response data.msg: mid={}".format(mid))
                return res
            mbs = msg[1]

            res = EML(
                self._clientid,
                self.task,
                self._userid,
                "{}_{}_{}".format(self._userid, folder.name, mid),
                folder,
                self._apptype,
                captype='imap',
            )

            # msg = email.message_from_string(mbs.decode())
            # mbs = msg.as_bytes()
            res.io_stream = io.BytesIO(mbs)
            res.stream_length = len(mbs)

        except OSError as oe:
            res = None
            self._logger.warn("Get mail failed, retrying login: {}".format(
                oe.args))
            if not self._pwd_login():
                self._logger.error("Retry login failed")
            else:
                self._logger.info("Retry login succeed")
                res = self._fetch_mail(
                    mid,
                    folder,
                    recursive_lvl=recursive_lvl + 1,
                )
        except Exception:
            res = None
            self._logger.error("Fetch mail(id={}) error: {}".format(
                mid, traceback.format_exc()))

        return res
