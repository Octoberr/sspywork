"""
auto task的管理基类
create by judy 2019/07/27
"""
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import ECommandStatus
from datacontract.automateddataset import AutomatedTask, AutotaskBatchBack
from idownclient.clientdbmanager import DbManager
from outputmanagement import OutputManagement


class AutoManagenBase(object):

    def __init__(self):
        self._sqlfunc = DbManager
        self._logger: MsLogger = MsLogManager.get_logger('Autotask Manager')

    @staticmethod
    def write_autotaskback(autotask: AutomatedTask, cmdstatus: ECommandStatus, recvmsg: str, currtime: str = None):
        """
        通用方法编写iscantask的回馈
        :param autotask:
        :param cmdstatus:
        :param recvmsg:
        :param currtime:
        :return:
        """
        if autotask is None:
            raise Exception('Write iscantaskback iscantask cannot be None')
        autoback = AutotaskBatchBack.create_from_task(autotask, cmdstatus, recvmsg, currtime)
        OutputManagement.output(autoback)
        return
