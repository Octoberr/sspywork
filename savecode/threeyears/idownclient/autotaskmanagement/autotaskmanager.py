"""
autotask文件的预先处理
create by judy 2019/07/27

update by judy 2019/08/06
"""
import traceback

from datacontract.automateddataset import AutomatedTask
from .automanagebase import AutoManagenBase


class AutoTaskManager(AutoManagenBase):

    def __init__(self):
        AutoManagenBase.__init__(self)

    def autotask_manage(self, autotask: AutomatedTask):
        """
        auto task的任务管理器
        :param autotask:
        :return:
        """
        self._logger.info(f'Insert auto task to sqlite, batchid:{autotask.batchid}')
        # self.write_autotaskback(autotask, ECommandStatus.Succeed, "Get the task.")
        # 这里cmd要先插入，不然task先插入后会发现task那边都开始在执行了，这边却还没有查到cmd
        if autotask.cmd_id is not None:
            try:
                self._sqlfunc.store_task_cmd(autotask.cmd_id, autotask.cmd.cmd_str)
                # CmdProcess.write_cmd_back(iscout.cmd, ECommandStatus.Succeed, '任务设置应用成功')
            except:
                self._logger.error(f"Store task cmd error, err:{traceback.format_exc()}")
                # CmdProcess.write_cmd_back(iscout.cmd, ECommandStatus.Failed, "任务设置应用失败")
        self._sqlfunc.insert_auot_task(autotask)
        return
