"""
一些scoutmanage通用的字段和方法
scoutmanagebase
create by swm 2019/07/05
"""
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import IscoutTask, ECommandStatus, IscoutBtaskBack
from idownclient.clientdbmanager import DbManager
from outputmanagement import OutputManagement


class ScoutManageBase(object):
    def __init__(self):
        self._sqlfunc = DbManager
        self._logger: MsLogger = MsLogManager.get_logger("IscoutManager")

    @staticmethod
    def write_iscoutback(
        iscouttask: IscoutTask,
        cmdstatus: ECommandStatus,
        scoutrecvmsg: str,
        currtime: str = None,
    ):
        """
        通用方法编写iscantask的回馈
        :param iscouttask:
        :param cmdstatus:
        :param scanrecvmsg:
        :param currtime:
        :return:
        """
        if iscouttask is None:
            raise Exception("Write iscantaskback iscantask cannot be None")
        scanback = IscoutBtaskBack.create_from_task(iscouttask, cmdstatus, scoutrecvmsg)
        OutputManagement.output(scanback)
        return

    @staticmethod
    def write_iscoutback_dict(
        iscouttask: dict,
        cmdstatus: ECommandStatus,
        scoutrecvmsg: str,
        currtime: str = None,
    ):
        """
        通用方法编写iscantask的回馈
        :param iscouttask:
        :param cmdstatus:
        :param scanrecvmsg:
        :param currtime:
        :return:
        """
        # 为了兼容以前的方法，所以在这里添加字段create by judy 20200327
        iscouttask["state"] = cmdstatus.value
        iscouttask["recvmsg"] = scoutrecvmsg
        platform = iscouttask.get("platform")
        if iscouttask is None:
            raise Exception("Write iscantaskback iscantask cannot be None")
        scanback = IscoutBtaskBack.create_from_dict(iscouttask, platform=platform)
        OutputManagement.output(scanback)
        return
