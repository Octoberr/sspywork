"""
精简代码，管理spider
create by judy 2019/01/24
"""
import threading
from abc import ABCMeta

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import Task, ECommandStatus, TaskBatchBack
from datacontract.apps.appbase import AppConfig
from outputmanagement import OutputManagement
from idownclient.spider.appcfg import AppCfg
from idownclient.config_client import basic_client_config
from .spideradapter import SpiderAdapter
from idownclient.clientdbmanager import DbManager


class SpiderManagebase(object):
    __metaclass = ABCMeta

    def __init__(self):
        self._spideradapter = SpiderAdapter()
        self._sqlfunc = DbManager
        self._logger: MsLogger = MsLogManager.get_logger('SpiderManagent')
        self._spider_dealing_dict: dict = {}
        self._spider_threads_locker = threading.Lock()
        self._clientid = basic_client_config.clientid

    def _write_tgback(self, task: Task, taskstatus: ECommandStatus, taskres):
        """
        返回回馈文件
        :param task:
        :param taskstatus:
        :param taskres:
        :return:
        """
        if not isinstance(task, Task):
            raise Exception("Invalid task object for taskback")
        tginfo = TaskBatchBack.create_from_task(task, cmdstatus=taskstatus, cmdrcvmsg=taskres)
        OutputManagement.output(tginfo)
        return

    def _get_appcfg(self, appcfg: AppConfig) -> AppCfg:
        res: AppCfg = AppCfg(appcfg._appanme, appcfg._apphosts,
                             appcfg._apptype, appcfg._appclassify,
                             appcfg._appclass, appcfg._crosswall,
                             appcfg._enable, appcfg._ishttps)
        return res

    # 这个待会放在新任务刚好做好的那个方法里，这里不用判断
    # 这个方法主要用在下载任务里
    def _remove_duplicate_task(self, task: Task):
        if len(self._spider_dealing_dict) == 0:
            return
        for key, value in self._spider_dealing_dict.items():
            if task.apptype == key.apptype and task.tasktype == key.tasktype \
                    and (task.account == key.account or task.phone == key.phone or task.cookie == key.cookie):
                self._write_tgback(task, ECommandStatus.Failed, "有相同的任务正在处理中，请等待任务处理完成")
                break
        return
