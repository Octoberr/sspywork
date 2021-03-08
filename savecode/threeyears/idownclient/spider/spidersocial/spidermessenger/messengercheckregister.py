"""messenger check register"""

# -*- coding:utf-8 -*-

from datacontract.idowndataset import Task

from .messengerchatlog import MessengerChatlog


class MessengerCheckRegister(MessengerChatlog):
    """"""

    def __init__(self, task: Task, appcfg, clientid):
        MessengerChatlog.__init__(self, task, appcfg, clientid)

    def _check_registration_(self) -> iter:
        """
        返回btaskback，数据参照datafeedback
        有个人信息则返回个人信息
        :return:
        """
        pass