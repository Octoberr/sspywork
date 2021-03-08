"""
用户状态信息的回馈
create by judy 2019/05/17
"""
import datetime

import pytz

from datacontract.idowndataset import Task
from datacontract.outputdata import EStandardDataType
from .feedbackbase import FeedDataBase


class UserStatus(FeedDataBase):
    def __init__(self, task: Task, clientid, userid, apptype):
        FeedDataBase.__init__(
            self, ".user_status", EStandardDataType.UserStatus, task, apptype, clientid
        )
        if userid is None:
            raise Exception("userid cannot be None.")
        self._userid = userid
        self.downstatus = task.taskstatus.value
        self.monitorstatus = task.cmd.switch_control.monitor_switch
        # 实例化的时候可以这样写，值可以在外面被改变, modify by judy 20201118
        self.cookiestatus = 0
        if task.cookie is not None and task.cookie != "":
            self.cookiestatus = 1
        self.pwdstatus = 0
        if task.password is not None and task.password != "":
            self.pwdstatus = 1
        self.priority = task.cmd.stratagy.priority
        # 数据库的文件更新是按照时间来更新的，所以每次需要获取最新的时间
        self.updatetime = datetime.datetime.now(
            pytz.timezone("Asia/Shanghai")
        ).strftime("%Y-%m-%d %H:%M:%S")

    def _get_output_fields(self):
        self.append_to_fields("userid", self._userid)
        # 这个apptype不是在公用里使用过了吗？待会测试下看看191216
        self.append_to_fields("apptype", self._apptype)
        self.append_to_fields("downstatus", self.downstatus)
        self.append_to_fields("monitorstatus", self.monitorstatus)
        self.append_to_fields("cookiestatus", self.cookiestatus)
        self.append_to_fields("pwdstatus", self.pwdstatus)
        self.append_to_fields("priority", self.priority)
        self.append_to_fields("updatetime", self.updatetime)
        return self._fields
