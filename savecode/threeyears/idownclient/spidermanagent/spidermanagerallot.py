"""
精简代码
管理spider,分配任务
"""
import threading
import time
import traceback

from datacontract import Task, ETaskType
from commonbaby.mslog import MsLogger, MsLogManager
from idownclient.config_task import clienttaskconfig
from .spiderbatchlogintest import SpiderBatchLoginTest
from .spiderdownloadtaskstore import SpiderDownloadTaskStore
from .spiderloginonly import SpiderLoginOnly
from .spiderlogout import SpiderLogout
from .spideronlinecheck import SpiderOnlineCheck
from .spiderregistercheck import SpiderRegisterCheck
from .spiderstoreinput import SpiderStoreInput
from datacontract.idowncmd import IdownCmd
from idownclient.clientdbmanager import DbManager


class SpiderManagerAllot(object):
    def __init__(self):
        # 正在处理的任务队列
        self._spider_manage_queue_dict: dict = {}
        self._spider_manage_dealing_queue_locker = threading.Lock()
        self._logger: MsLogger = MsLogManager.get_logger("SpiderManagerAllot")
        self._batch_login_test = SpiderBatchLoginTest()
        self._download_task_store = SpiderDownloadTaskStore()
        self._login_only = SpiderLoginOnly()
        self._logout = SpiderLogout()
        self._online_check = SpiderOnlineCheck()
        self._register_check = SpiderRegisterCheck()
        self._store_vercode = SpiderStoreInput()
        # 默认配置
        _defcmdstr: str = DbManager.get_default_idown_cmd().get("cmd")
        self.defcmd: IdownCmd = IdownCmd(_defcmdstr)

    def on_complete(self, task: Task):
        """
        task任务完成专用
        :param task:
        :return:
        """
        with self._spider_manage_dealing_queue_locker:
            if self._spider_manage_queue_dict.__contains__(task.batchid):
                self._spider_manage_queue_dict.pop(task.batchid, None)

    def _distribute_tasktype(self, tsk: Task):
        """
        分配任务到spider
        :param tsk:
        :return:
        """
        # 存入数据库之前加载一次加载一次cmd
        if tsk.cmd_id is None:
            tsk.cmd = self.defcmd
        else:
            # 这里是属于预处理的东西不能依靠前端发的字段去补齐，所以还是自己去补齐
            tsk.cmd.fill_defcmd(self.defcmd)
        self._logger.info(f"Task start to processing, apptype={tsk.apptype}")
        if tsk.tasktype == ETaskType.LoginOnly:
            self._login_only.login_only(tsk)
        elif tsk.tasktype == ETaskType.LoginDownload:
            # 登陆并下载的数据会存入数据库执行下载策略
            # 现在都是进这个方法，那么就需要增加两步验证
            self._download_task_store.login_and_download_data(tsk)
        elif tsk.tasktype == ETaskType.CheckOnline:
            self._online_check.online_check(tsk)
        elif tsk.tasktype == ETaskType.CheckRegistration:
            self._register_check.check_registration(tsk)
        elif tsk.tasktype == ETaskType.LoginTest:
            self._batch_login_test.login_batch_test(tsk)
        elif tsk.tasktype == ETaskType.Input:
            # 验证码直接存入数据库，验证码会等待15分钟
            self._store_vercode.store_input(tsk)
        elif tsk.tasktype == ETaskType.Logout:
            self._logout.logout(tsk)
        else:
            raise Exception("Unknown tasktype!")
        return

    def manage_task(self, task: Task):
        """
        对队列中的任务进行处理
        :param task:
        :return:
        """

        with self._spider_manage_dealing_queue_locker:
            if self._spider_manage_queue_dict.__contains__(task.batchid):
                self._logger.error("Task is on dealing: {}".format(task.batchid))
                return
            self._spider_manage_queue_dict[task.batchid] = task
            task.on_complete = self.on_complete
        try:
            # 进行任务处理
            self._distribute_tasktype(task)
        except:
            self._logger.error(f"Manage idown task error\nerr:{traceback.format_exc()}")
        finally:
            # 因为一些意外情况可能会导致任务提前结束，导致任务仍在处理队列
            if task is not None:
                if callable(task.on_complete):
                    task.on_complete(task)
