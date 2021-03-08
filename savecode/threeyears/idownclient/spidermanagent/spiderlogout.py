"""
精简代码
爬虫退出登录
create by judy 2019/01/24
"""
import threading
import traceback

from datacontract import Task, ECommandStatus
from datacontract.apps.appbase import AppConfig
from idownclient.spider.spiderbase import SpiderBase
from idownclient.spidermanagent.spidermanagebase import SpiderManagebase


class SpiderLogout(SpiderManagebase):

    def __init__(self):
        SpiderManagebase.__init__(self)

    def _get_logout_data_info(self, tsk: Task):
        # 查询有效任务的cookie
        res = False
        sql = '''
        select * from task
        where taskid=? and batchid=?
        '''
        pars = (
            tsk.parenttaskid,
            tsk.parentbatchid,
        )
        res_info = self._sqlfunc.query_task_by_sql(sql, pars)
        if len(res_info) == 0:
            return res
        res_one = res_info[0]
        # 取出来的数据有cookie,并且目前的数据没有cookie就通过cookie赋值
        if res_one.get('cookie') is not None:
            self._logger.info(f"Apptype:{tsk.apptype} will logout out")
            res = True
            tsk.cookie = res_one.get('cookie')
        return res

    # 登出
    def logout(self, tsk: Task):
        # 同步要登出账号的cookie
        syn_res = self._get_logout_data_info(tsk)
        if not syn_res:
            self._write_tgback(tsk, ECommandStatus.Failed, "当前账号没有在机器上登陆")
            return
        try:
            with self._spider_threads_locker:
                if self._spider_dealing_dict.__contains__(tsk):
                    self._logger.info("{} is processing logout task {}".format(tsk.batchid, self._spider_dealing_dict[tsk].name))
                    return
            appcfg: AppConfig = self._spideradapter.adapter(tsk)[0]
            if not isinstance(appcfg, AppConfig):
                self._logger.info("No spider match:\nbatchid:{}\ntasktpe:{}\napptype:{}"
                                  .format(tsk.batchid, tsk.tasktype.name, tsk.apptype))
                return
            spider: SpiderBase = appcfg._appclass(tsk, self._get_appcfg(appcfg), self._clientid)
            t = threading.Thread(target=self._execute_logout, daemon=True, args=(spider,))
            t.start()
            with self._spider_threads_locker:
                # 用元组存入 插件对象  和 线程对象
                self._spider_dealing_dict[tsk] = spider
        except Exception:
            self._logger.log("Task logout error: {}".format(traceback.format_exc()))
            self._write_tgback(tsk, ECommandStatus.Failed, "执行爬虫插件出错，请检查client环境重试")
        return

    def _execute_logout(self, spider: SpiderBase):
        try:
            res = spider.logout()
            if res:
                self._logger.info("Logout task complete, this mission is over")
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
