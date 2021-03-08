"""
精简代码
check账号是否在线
create by judy 2019/01/24
"""
import threading
import traceback

from datacontract import Task, ETokenType, ECommandStatus
from datacontract.apps.appbase import AppConfig
from idownclient.spidermanagent.spidermanagebase import SpiderManagebase
from idownclient.spider.spiderbase import SpiderBase


class SpiderOnlineCheck(SpiderManagebase):

    def __init__(self):
        SpiderManagebase.__init__(self)

    def online_check(self, tsk: Task):
        """
        账号在线情况查询，
        telegram目前需要一个已登录的内置账号去查询目标账号是否在线
        :return:
        """
        tokentype = tsk.tokentype
        if tokentype is not None:
            if tokentype == ETokenType.Cookie:
                self._logger.error("Cookie cannot inquiry account online")
                self._write_tgback(tsk, ECommandStatus.Failed, "Cookie不能查询账号是否在线")
        try:
            with self._spider_threads_locker:
                if self._spider_dealing_dict.__contains__(tsk):
                    self._logger.info("{} is processing {}.".format(tsk.batchid, self._spider_dealing_dict[tsk].name))
                    return

            appcfg: AppConfig = self._spideradapter.adapter(tsk)[0]
            if not isinstance(appcfg, AppConfig):
                self._logger.info("No spider match:\nbatchid:{}\ntasktpe:{}\napptype:{}"
                                  .format(tsk.batchid, tsk.tasktype.name, tsk.apptype))
                return

            spider: SpiderBase = appcfg._appclass(tsk, self._get_appcfg(appcfg), self._clientid)
            t = threading.Thread(target=self._execute_online_check, daemon=True, args=(spider,))
            t.start()
            with self._spider_threads_locker:
                # 用元组存入 插件对象  和 线程对象
                self._spider_dealing_dict[tsk] = spider
        except Exception:
            self._logger.log("Task downloading error: {}".format(traceback.format_exc()))
            self._write_tgback(tsk, ECommandStatus.Failed, "执行爬虫插件出错，请检查client环境重试")
        return

    def _execute_online_check(self, spider: SpiderBase):
        try:
            res = spider.online_check()
            if res:
                self._logger.info("Online_check is over,this mission is complete.")
        except Exception:
            self._logger.error("Execute task error:\nbatchid:{}\nerror:{}"
                               .format(spider.task.batchid, traceback.format_exc()))
            self._write_tgback(spider.task, ECommandStatus.Failed, "执行任务出现不可知错误")
        finally:
            with self._spider_threads_locker:
                if self._spider_dealing_dict.__contains__(spider.task):
                    self._spider_dealing_dict.pop(spider.task, None)
            if spider.task is not None:
                if callable(spider.task.on_complete):
                    spider.task.on_complete(spider.task)
