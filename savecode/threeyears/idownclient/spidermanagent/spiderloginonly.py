"""
精简代码
仅登陆到spider
create by judy 2019/01/24
"""
import threading
import traceback

from idownclient.spidermanagent.spidermanagebase import SpiderManagebase
from idownclient.spider.spiderbase import SpiderBase
from datacontract import ECommandStatus
from datacontract.apps.appbase import AppConfig


class SpiderLoginOnly(SpiderManagebase):

    def __init__(self):
        SpiderManagebase.__init__(self)

    def login_only(self, task):
        with self._spider_threads_locker:
            if self._spider_dealing_dict.__contains__(task):
                self._logger.info("Task: {} is logging {}, return.".format(task.batchid, self._spider_dealing_dict[task].name))
                return

        appcfg: AppConfig = self._spideradapter.adapter(task)[0]
        if not isinstance(appcfg, AppConfig):
            self._logger.info("No spider match:\nbatchid:{}\ntasktpe:{}\napptype:{}"
                              .format(task.batchid, task.tasktype.name, task.apptype))
            return

        spider: SpiderBase = appcfg._appclass(task, self._get_appcfg(appcfg), self._clientid)

        t = threading.Thread(target=self._execute_login_only, daemon=True, args=(spider,))

        t.start()
        with self._spider_threads_locker:
            # 用元组存入 插件对象  和 线程对象
            self._spider_dealing_dict[task] = spider
        return

    def _execute_login_only(self, spider: SpiderBase):
        try:
            res = spider.login_only()
            if res:
                self._logger.info("Login success, this mission is complete.")
            else:
                self._logger.info("Login failed, this mission is complete.")
        except Exception:
            self._logger.error(f"Execute task error:\nbatchid:{spider.task.batchid}\nerror:{traceback.format_exc()}")
            self._write_tgback(spider.task, ECommandStatus.Failed, "登陆出错，请检查环境重新尝试")
        finally:
            with self._spider_threads_locker:
                if self._spider_dealing_dict.__contains__(spider.task):
                    self._spider_dealing_dict.pop(spider.task, None)
            if spider.task is not None:
                if callable(spider.task.on_complete):
                    spider.task.on_complete(spider.task)
