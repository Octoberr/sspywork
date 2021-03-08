"""
精简代码
check账号是否注册了spider

update by judy 2019/03/07
账号若注册返回btaskback
"""
import threading
import traceback

from datacontract import Task, ECommandStatus
from datacontract.apps.appbase import AppConfig
from idownclient.spider.spiderbase import SpiderBase
from idownclient.spidermanagent.spidermanagebase import SpiderManagebase


class SpiderRegisterCheck(SpiderManagebase):

    def __init__(self):
        SpiderManagebase.__init__(self)

    def check_registration(self, tsk: Task):
        """
        批量任务直接执行并返回回馈文件
        :param tsk:
        :return:
        """
        try:
            with self._spider_threads_locker:
                if self._spider_dealing_dict.__contains__(tsk):
                    self._logger.info("{} is processing {}.".format(tsk.batchid, self._spider_dealing_dict[tsk].name))
                    return
            spiders: AppConfig = self._spideradapter.adapter(tsk)
            t = threading.Thread(target=self._execute_check_registration, daemon=True, args=(spiders, tsk))
            t.start()
            with self._spider_threads_locker:
                # 用元组存入 插件对象  和 线程对象
                self._spider_dealing_dict[tsk] = spiders
        except Exception:
            self._logger.log("Task downloading error: {}".format(traceback.format_exc()))
            self._write_tgback(tsk, ECommandStatus.Failed, "执行爬虫插件出错，请检查client环境重试")
        return

    def _execute_check_registration(self, spiders: list, tsk: Task):
        """
        批量任务直接执行并返回回馈文件
        :param tsk:
        :return:
        """
        try:
            for appcfg in spiders:
                # 获取的结果为定义的结构体
                try:
                    spider: SpiderBase = appcfg._appclass(tsk, self._get_appcfg(appcfg), self._clientid)
                    spider.check_registration()
                except Exception:
                    self._write_tgback(tsk, ECommandStatus.Failed, "查询账号是否注册失败")
                    self._logger.error("Registration check err: {}".format(
                        traceback.format_exc()))
                    continue
            # 全平台的账号查询完成后结束任务
            self._logger.info("Task {} execute complete.".format(tsk.batchid))
        except Exception:
            self._logger.error(f"Execute task error:\nbatchid:{tsk.batchid}\nerror:{traceback.format_exc()}")
            self._write_tgback(tsk, ECommandStatus.Failed, "执行任务出现不可知错误")
        finally:
            with self._spider_threads_locker:
                if self._spider_dealing_dict.__contains__(tsk):
                    self._spider_dealing_dict.pop(tsk, None)
            if tsk is not None:
                if callable(tsk.on_complete):
                    tsk.on_complete(tsk)
