"""
iscout任务管理
create by judy 2019/06/18
"""
import traceback

from datacontract import IscoutTask, ECommandStatus
from idownclient.cmdmanagement import CmdProcess
from .scoutmanagebase import ScoutManageBase


class ScoutManager(ScoutManageBase):
    def __init__(self):
        ScoutManageBase.__init__(self)

    def iscouttask_manage(self, iscout: IscoutTask):
        """
        目前只有一种情况，直接存储
        不排除以后会做什么处理现在直接保存task
        在这里接到iscout后会进行处理，可能根据不同的object_type会有不同的处理
        所以在这里把接口留着
        :param iscout:
        :return:
        """
        insert_status: bool = False
        self._logger.info(
            f"Start inserting iscout task to sqlite, batchid:{iscout.batchid}"
        )
        try:
            # self.write_iscoutback(iscout, ECommandStatus.Dealing, "任务加入下载队列成功，等待执行")
            # 这里如果任务有cmdid那么的话要保存设置,并且要给回馈，这里是处理带有设置的task
            # 这里cmd要先插入，不然task先插入后会发现task那边都开始在执行了，这边却还没有查到cmd
            if iscout.cmd_id is not None:
                try:
                    self._sqlfunc.store_task_cmd(iscout.cmd_id, iscout.cmd.cmd_str)
                    CmdProcess.write_cmd_back(
                        iscout.cmd, ECommandStatus.Succeed, "任务设置应用成功"
                    )
                except:
                    # 数据插入出了问题，目前来看问题没有复现，create by judy 2020/03/27等以后再看看
                    self._logger.error(
                        f"Store task cmd error, err:{traceback.format_exc()}"
                    )
                    CmdProcess.write_cmd_back(
                        iscout.cmd, ECommandStatus.Failed, "任务设置应用失败"
                    )
                    # 这里写入cmd失败了那么就代表这个任务失败了
                    self.write_iscoutback(
                        iscout, ECommandStatus.Failed, "client端保存任务cmd失败，请检查运行环境"
                    )
                    return
            # 存储数据
            self._sqlfunc.insert_iscouttask(iscout)
            insert_status = True
        except:
            self.write_iscoutback(iscout, ECommandStatus.Failed, "任务处理失败")
        finally:
            if insert_status:
                self._logger.info(
                    f"Insert to sqlite success, waiting for scouter, batchid:{iscout.batchid}"
                )
            else:
                self._logger.error(
                    f"Store iscout task error, checkout the iscouttask\n error:{traceback.format_exc()}"
                )
