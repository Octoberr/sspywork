"""
iscan task的预先处理或者是些零时性任务啥的
create by judy 2019/06/18
"""
import traceback

from datacontract import IscanTask, ECommandStatus
from .scanmanagebase import ScanManageBase
from idownclient.cmdmanagement import CmdProcess


class ScanManager(ScanManageBase):
    """
    iscan task预先处理
    目前：
    1、存储
    """

    def __init__(self):
        ScanManageBase.__init__(self)

    def iscantask_manage(self, iscan: IscanTask):
        """
        目前只有一种情况，直接存储
        不排除以后会做什么处理现在直接保存task
        :param iscan:
        :return:
        """
        self._logger.info(f"Store iscan task to sqlite, taskid:{iscan.taskid}")
        try:
            # 这边如果给界面回的是等待执行，那么就说明暂停成功了吧，所以client是不太需要改的
            # self.write_iscanback(iscan, ECommandStatus.Dealing, "任务加入下载队列成功，等待执行")
            # 这里如果任务有cmdid那么的话要保存设置,并且要给回馈，这里是处理带有设置的task
            # 这里cmd要先插入，不然task先插入后会发现task那边都开始在执行了，这边却还没有查到cmd
            if iscan.cmd_id is not None:
                try:
                    self._sqlfunc.store_task_cmd(iscan.cmd_id, iscan.cmd.cmd_str)
                    CmdProcess.write_cmd_back(
                        iscan.cmd, ECommandStatus.Succeed, "任务设置应用成功"
                    )
                except:
                    self._logger.error(
                        f"Store task cmd error, err:{traceback.format_exc()}"
                    )
                    CmdProcess.write_cmd_back(
                        iscan.cmd, ECommandStatus.Failed, "任务设置应用失败"
                    )
            self._sqlfunc.insert_iscantask(iscan)
            self._logger.info(f"Store iscan task succeed, taskid:{iscan.taskid}")
        except:
            self._logger.error(
                f"Store iscan task error, checkout the iscantask\nerror:{traceback.format_exc()}"
            )
            self.write_iscanback(iscan, ECommandStatus.Failed, "任务处理失败")
        return
