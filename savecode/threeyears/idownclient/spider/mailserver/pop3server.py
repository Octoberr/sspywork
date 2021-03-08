"""
pop3下载邮件
create by judy 2019/05/27
pop3 目前只能下载邮件这就很奇怪了
"""
import io
import traceback
from poplib import POP3_SSL, POP3

from datacontract.idowndataset.task import Task
from idownclient.spider.spidermail.spidermailbase import SpiderMailBase
from ..appcfg import AppCfg
from ...clientdatafeedback.idownfeedback import EML, PROFILE, Folder


class POP3Server(SpiderMailBase):

    def __init__(self, task: Task, clientid):
        appcfg = AppCfg(appname="POP3",
                        apphosts=None,
                        apptype=3101,
                        appclassify=3,
                        appclass=POP3Server,
                        crosswall=True,
                        enable=True)
        SpiderMailBase.__init__(self, task, appcfg, clientid, task.account)

        self._apptype = task.apptype
        if self._apptype is None:
            # 约定了apptype没有就是-1，
            # 约定了调用方必传apptype
            self._apptype = -1
        appcfg._apptype = self._apptype
        self._host: str = None
        self._port: int = None

        self._svr_class = None
        self._svr = None

        self._get_host_port()
        self._init_server()

    def _get_host_port(self):
        if self.task.cmd is None or \
                self.task.cmd.stratagymail is None or \
                self.task.cmd.stratagymail.mail_service is None or \
                self.task.cmd.stratagymail.mail_service.pop3_host is None or \
                self.task.cmd.stratagymail.mail_service.pop3_port is None:
            raise Exception(
                f"Missing pop3 mailserver host and port: taskid={self.task.taskid}, batchid={self.task.batchid}")
        self._host = self.task.cmd.stratagymail.mail_service.pop3_host
        self._port = int(self.task.cmd.stratagymail.mail_service.pop3_port)

    def _init_server(self):
        if self.task.cmd is None or \
                self.task.cmd.stratagymail is None or \
                self.task.cmd.stratagymail.mail_service is None or \
                self.task.cmd.stratagymail.mail_service.pop3_isssl is None:
            raise Exception(f"Missing pop3 mailserver cmd: taskid={self.task.taskid}, batchid={self.task.batchid}")
        if not self.task.cmd.stratagymail.mail_service.pop3_isssl:
            self._svr_class = POP3
        else:
            self._svr_class = POP3_SSL

    def _pwd_login(self) -> bool:
        """
        账号密码登陆
        :return:
        """
        res: bool = False
        try:
            # self._logger.info(f"Login start: {self._account}")
            # 超时设置为一分钟
            self._svr = self._svr_class(self._host, self._port)
            # self._svr.sock.send()
            # 用户名
            self._svr.user(self.task.account)
            # 密码
            self._svr.pass_(self.task.password)

            res = True
            self._userid = f"{self._apptype}_{self._account}"

            # 执行挂起操作
            self._svr.noop()

            # self._logger.info(f"Login succeed: {self._account}")

        except Exception:
            self._logger.error(f"Pwd Login error: {traceback.format_exc()}")
        return res

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
            yield p
        except Exception:
            self._logger.info("Get Profile error: {}".format(traceback.format_exc()))

    def _download(self) -> iter:
        """
        pop3 没有文件夹的说法直接就是下载邮件
        :return:
        """
        # 只能下载inbox的文件
        f = Folder()
        f.folderid = f'{self._userid}_1'
        f.name = 'inbox'

        emails, total_bytes = self._svr.stat()
        f.mailcount = emails
        self._logger.info(f'{emails} emails in the inbox, {total_bytes} bytes total')
        # 都不用去查看邮件的具体信息了
        # msg_list = self._svr.list()
        for i in range(emails):
            try:
                response = self._svr.retr(i + 1)
                raw_message = response[1]
                mbs = b'\n'.join(raw_message)
                mail = EML(
                    self._clientid,
                    self.task,
                    self._userid,
                    "{}_{}".format(self._userid, i + 1),
                    f,
                    self._apptype,
                    captype='imap',
                )
                mail.io_stream = io.BytesIO(mbs)
                mail.stream_length = len(mbs)
                yield mail
            except:
                self._logger.error(f'POP3 download mail error, err:{traceback.format_exc()}')
                continue

    def __del__(self):
        if self._svr is not None:
            self._svr.quit()
            self._svr = None
