"""
存储iscan和下载iscan的base方法
里面只要是manage都要继承该方法
"""
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import IscanTask, ECommandStatus, IscanTaskBack
from idownclient.clientdbmanager import DbManager
from outputmanagement import OutputManagement


class ScanManageBase(object):

    def __init__(self):
        self._sqlfunc = DbManager
        self._logger: MsLogger = MsLogManager.get_logger('IscanManager')

    @staticmethod
    def write_iscanback(iscantask: IscanTask,
                        cmdstatus: ECommandStatus,
                        scanrecvmsg: str,
                        currtime: str = None,
                        elapsed: float = None):
        """
        通用方法编写iscantask的回馈
        :param elapsed:
        :param iscantask:
        :param cmdstatus:
        :param scanrecvmsg:
        :param currtime:
        :return:
        """
        if iscantask is None:
            raise Exception('Write iscantaskback iscantask cannot be None')
        scanback = IscanTaskBack.create_from_task(iscantask, cmdstatus, scanrecvmsg, currtime, elapsed)
        OutputManagement.output(scanback)
        return
