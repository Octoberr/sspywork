"""
cmd 任务的管理
"""
import traceback

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import IdownCmd, ECommandStatus
from .cmdprocess import CmdProcess


class CmdManager(object):

    def __init__(self):
        self._logger: MsLogger = MsLogManager.get_logger('CmdManager')

    def manage_cmd(self, icmd: IdownCmd):
        """
        管理idown cmd,根据idowncmd中的不同字段进行不同的处理
        :param icmd:
        :return:
        """
        # 邮件不需要target,相当于是独立于设置的，目前暂时不在client上保存mailserver所以不太需要by swm 191220
        # if icmd.mail_service is not None:
        #     try:
        #         self._logger.info("Modify the mail service.")
        #         CmdProcess.modify_mail_service(icmd.mail_service)
        #         CmdProcess.write_cmd_back(icmd, ECommandStatus.Succeed, "邮件服务配置修改成功")
        #         self._logger.info("Modify mail service success,write the cmd feedback, cmd task done.")
        #     except:
        #         self._logger.error(f"Modify mail service error, err:{traceback.format_exc()}")
        #         CmdProcess.write_cmd_back(icmd, ECommandStatus.Failed, "邮件服务配置修改失败")
        #     return
        # target为空修改默认配置
        if icmd.target is None:
            try:
                # 目前已和wj确认，只要不是修改默认配置一定会带一个target
                # 但是目前数据库会存放3中默认cmd，会有idown,iscan, iscout，能修改的默认配置是idown的
                # 没有目标表示修改默认设置, 这里我需要的到一个完整的默认的配置
                if icmd.stratagy.type == 'idown':
                    CmdProcess.modify_default_idown_cmd(icmd)
                    self._logger.info("Modify the default idown cmd.")
                    CmdProcess.write_cmd_back(icmd, ECommandStatus.Succeed, "idown默认全局配置已修改成功")
                    self._logger.info("Modify default idown cmd success, write the cmd feedback, cmd task done.")
                elif icmd.stratagy.type == 'iscan':
                    self._logger.info('iscan 还没有增加修改全局配置的功能')
                elif icmd.stratagy.type == 'iscout':
                    self._logger.info('iscout 还没有修改增加全局配置的功能')
            except:
                self._logger.error(f"Modify default cmd error, err:{traceback.format_exc()}")
                CmdProcess.write_cmd_back(icmd, ECommandStatus.Failed, "默认全局配置修改失败")
            return
        # 有target，现在就可以修改属性，下载策略等等
        # 修改账号属性，是专属于idown的命令修改，
        elif icmd.attr_modify is not None:
            try:
                self._logger.info("Modify the attribute.")
                CmdProcess.modify_task_attr(icmd.attr_modify, icmd.target)
                CmdProcess.write_cmd_back(icmd, ECommandStatus.Succeed, "账号属性修改成功")
                self._logger.info("Modify task attribute success,write the cmd feedback, cmd task done.")
            except:
                self._logger.error(f"Modify the attribute error, err:{traceback.format_exc()}")
                CmdProcess.write_cmd_back(icmd, ECommandStatus.Failed, "账号属性修改失败")
            return
        # 更新task的设置,target,switch,stratagy,stratagymail
        # 这里三种任务使用的都是同一套idowncmd，所以界面直接使用永久的cmdid，直接修改cmd相关信息即可
        else:
            self._logger.info("Update a task cmd.")
            # 这里修改任务的cmd设置
            # 1、得先拿到任务的cmdid
            # 2、去cmd表拿cmdstr
            # 3、然后把拿到的cmdstr用现在的cmd更新下，然后再保存回去
            # --------------------------------------------后面估计还得改by swm 191224
            # 1、还得分两种情况，拿到cmdid和没有拿到cmdid

            try:
                # original_cmdid = CmdProcess.get_task_cmdid(icmd)
                # if original_cmdid is None:
                #     CmdProcess.update_task_cmd(icmd.cmd_id, icmd)
                # 拿到cmdid
                CmdProcess.update_origin_cmd(icmd, icmd.cmd_id)
                # 走到这才算成功
                CmdProcess.write_cmd_back(icmd, ECommandStatus.Succeed, "任务设置更新成功")
                self._logger.info("update task cmd success,write the cmd feedback, cmd task done.")
            except Exception as ex:
                self._logger.error(f"Update task cmd error\nerr:{ex}")
                CmdProcess.write_cmd_back(icmd, ECommandStatus.Failed, "任务设置更新失败")
            return
