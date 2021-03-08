"""
登陆邮箱下载数据，包括邮件，联系人，登陆历史记录
create by judy 2018/10/18
"""
import datetime
import os
import time

import pytz
from commonbaby.helpers import helper_crypto, helper_str

from datacontract.outputdata import EStandardDataType

from .feedbackbase import FeedDataBase


class Folder:
    """表示一个邮箱文件夹"""
    def __init__(self):
        self.name: str = None  # 邮箱文件夹的显示名称
        self.folderid: str = None  # 邮箱文件夹的唯一标识id
        self.folderurl: str = None  # 邮箱文件夹的访问链接
        self.mailcount: int = None  # 邮件数量
        self.other = None  # 储存邮件文件夹必要的参数


class EML(FeedDataBase):
    """tsk: datacontract.Task\n
    userid: user unique id\n
    folder: the folder which owns the mail邮件所属文件夹对象\n
    captype: 邮件获取方式(webmail/imap/pop)"""

    # 邮件头，用于邮件有效性验证
    # 若文件中包含5个邮件头则判定为正常邮件
    _validation_fields = [
        "from:", "to:", "content-type:", "subject:", "date:", "sender:",
        "received:", "return-path:", "content-transfer-encoding:", "cc:",
        "bcc:", "mime-version:", "message-id:", "apparently-to:",
        "apparently-from:", "content-disposition:"
    ]

    @property
    def folder(self):
        """
        返回下载邮件的文件夹，用于过滤数据
        :return:
        """
        return self._folder

    def __init__(self,
                 clientid: str,
                 tsk,
                 userid: str,
                 mailid: str,
                 folder: Folder,
                 apptype: int,
                 captype: str = 'webmail'):
        FeedDataBase.__init__(self, '.eml', EStandardDataType.Email, tsk,
                              apptype, clientid, False)
        if userid is None:
            raise Exception('userid cant be None')
        if not isinstance(mailid, str) or mailid == "":
            raise Exception('Mailid canont be empty')
        if not isinstance(folder, Folder):
            raise Exception("Email folder is invalid.")

        self.time: str = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        self._mailid = mailid
        self._folder: Folder = folder
        self._userid = userid
        self.captype = captype  # pop, smtp, imap, webmail
        if self.captype is None:
            self.captype = 'webmail'
        self.owner = None  # 邮件所属账号
        self.provider = None  # 邮件服务提供者
        self.state = None  # 0:未读，1：已读
        self.user_agent = None  # ua
        self.source = None  # 临帧标准，cookie里面带有的

        # 邮件的字段，可能要用的
        self.sendtime: datetime.datetime = datetime.datetime.now(pytz.timezone('Asia/Shanghai'))  # 邮件发送时间
        self.subject: str = None  # 邮件标题

        # 其他可能要用到的字段
        self.downloadurl: str = None  # 邮件的下载链接

    def _get_output_fields(self) -> dict:
        self.append_to_fields('userid', self._userid)
        self.append_to_fields('captype', self.captype)
        self.append_to_fields('owner', self.owner)
        self.append_to_fields('provider', self.provider)
        self.append_to_fields('state', self.state)
        self.append_to_fields('folder', self._folder.name)
        if isinstance(self.sendtime, datetime.datetime):
            self.append_to_fields('sendtime', self.sendtime.strftime('%Y-%m-%d %H:%M:%S'))
        self.append_to_fields('subject', self.subject)
        return self._fields

    def get_uniqueid(self):
        return helper_crypto.get_md5_from_str("{}{}{}".format(
            self._apptype, self._userid, self._mailid))

    def get_display_name(self):
        if not helper_str.is_none_or_empty(self.subject):
            return self.subject
        else:
            return self._mailid

    def validate_file(self, fipath: str) -> bool:
        """验证一个邮件文件是否合法"""
        res: bool = False
        try:
            if not isinstance(fipath, str) or fipath == "":
                return res
            if not os.path.isfile(fipath):
                return res

            read_len = 0
            max_len = 50  # 最多读50行
            succ_count = 0
            with open(fipath, mode='rb') as fs:
                while True:
                    try:
                        line = fs.readline()
                        if line is None or len(line) < 1:
                            break
                        line = line.decode('utf-8').lower()
                        for field in self._validation_fields:
                            if line.__contains__(field):
                                succ_count += 1
                                break

                        if succ_count >= 5:
                            res = True
                            break
                        if read_len >= max_len:
                            break
                    except Exception:
                        # 这里报错就是数据行不是utf-8能解的
                        # 而邮件头必然能解，所以直接不管即可
                        continue
                    finally:
                        read_len += 1

        except Exception:
            res = False

        return res
