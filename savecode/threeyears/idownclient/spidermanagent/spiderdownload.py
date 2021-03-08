"""
精简代码
爬虫下载
create by judy 2019/01/24
"""
import threading
import traceback

from datacontract import ECommandStatus, ETaskStatus, Task
from datacontract.apps.appbase import AppConfig
from idownclient.spider.mailserver import ImapServer, POP3Server
from idownclient.spider.spiderbase import SpiderBase
from idownclient.spidermanagent.spidermanagebase import SpiderManagebase


class SpiderDownload(SpiderManagebase):
    def __init__(self):
        SpiderManagebase.__init__(self)

    def download_data(self, tsk: Task) -> bool:
        """
        用于下载任务下载数据
        这里现在要分两种情况
        1、webmail正常的走下载流程
        2、pop3和imap需要走的另外一套
        :param tsk:
        :return:
        """
        res = False
        try:
            dlprotocal = tsk.cmd.stratagymail.eml_priority_protocol
            if dlprotocal == "webmail":
                res = self._webmail_download(tsk)
            else:
                res = self._pop3_imap_download(tsk)
        except:
            self._logger.info(
                f"Webmail or pop3 or imap download error\nerr:{traceback.format_exc()}"
            )
        return res

    def _pop3_imap_download(self, tsk: Task) -> bool:
        """
        pop3和imap的download模式
        :param tsk:
        :return:
        """
        res = False
        dlprotocal = tsk.cmd.stratagymail.eml_priority_protocol
        if dlprotocal == "imap":
            spider = ImapServer(tsk, self._clientid)
        elif dlprotocal == "pop3":
            spider = POP3Server(tsk, self._clientid)

        try:
            # 你这里为啥又不开线程了？？导致业务不一致，外面怎么调用。。
            # 而且不开线程会导致外面调用线程阻塞？？
            t = threading.Thread(
                target=self._execute_download_data, daemon=True, args=(spider,)
            )
            # 你把start放在这里，万一线程里面先执行完，然后才把task加到spider_dealing_dict里，
            # 岂不是就烂了，迷之自信？
            with self._spider_threads_locker:
                # 用元组存入 插件对象  和 线程对象
                self._spider_dealing_dict[tsk] = spider

            t.start()
            res = True

            # if spider.download_all_data():
            #     self._logger.info(
            #         f"Task {spider.task.batchid} execute complete, misson accomplish"
            #     )
            # else:
            #     self._logger.info(
            #         f"Task {spider.task.batchid} execute failed, misson accomplish"
            #     )
            # res = True
        except Exception:
            self._logger.error(
                f"Execute task error:\nbatchid:{tsk.batchid}\nerror:{traceback.format_exc()}"
            )
        finally:
            # # 当前任务的完成dict
            # if tsk is not None:
            #     if callable(tsk.on_complete):
            #         tsk.on_complete(tsk)
            pass

        return res

    def _webmail_download(self, tsk: Task) -> bool:
        """
        webmail的下载方式
        :param tsk:
        :return:
        """
        res: bool = False
        try:
            with self._spider_threads_locker:
                if self._spider_dealing_dict.__contains__(tsk):
                    self._logger.info(
                        "{} is downloading in {}.".format(
                            tsk.batchid, self._spider_dealing_dict[tsk].name
                        )
                    )
                    return True
            appcfg: AppConfig = self._spideradapter.adapter(tsk)[0]
            if not isinstance(appcfg, AppConfig):
                self._logger.info(
                    "No spider match:\nbatchid:{}\ntasktpe:{}\napptype:{}".format(
                        tsk.batchid, tsk.tasktype.name, tsk.apptype
                    )
                )
                return res

            spider: SpiderBase = appcfg._appclass(
                tsk, self._get_appcfg(appcfg), self._clientid
            )
            t = threading.Thread(
                target=self._execute_download_data, daemon=True, args=(spider,)
            )
            # 你把start放在这里，万一线程里面先执行完，然后才把task加到spider_dealing_dict里，
            # 岂不是就烂了，迷之自信？
            # 好啦，这不是改了吗？先把执行的任务放入队列，然后才start，因为start是不会阻塞的
            with self._spider_threads_locker:
                # 用元组存入 插件对象  和 线程对象
                self._spider_dealing_dict[tsk] = spider

            t.start()
            res = True
        except Exception:
            self._logger.log(
                "Task downloading error: {}".format(traceback.format_exc())
            )
            self._write_tgback(tsk, ECommandStatus.Failed, "执行爬虫插件出错，请检查client环境重试")
            res = False
        finally:
            # 开线程完了出来就调用task.on_compelte22222222?
            # if tsk is not None:
            #     if callable(tsk.on_complete):
            #         tsk.on_complete(tsk)
            pass
        return res

    def _execute_download_data(self, spider: SpiderBase):
        """
        任务处理线程。
        spider: 已初始化好的spider对象
        """
        try:
            # 进来线程里更新任务状态为正在执行
            self._sqlfunc.update_status_by_taskid(
                "taskstatus",
                ETaskStatus.WaitForDeal.value,
                spider.task.batchid,
                spider.task.taskid,
            )
            if spider.download_all_data():
                self._logger.info(
                    f"Task {spider.task.batchid} execute complete, misson accomplish"
                )
            else:
                self._logger.info(
                    f"Task {spider.task.batchid} execute failed, misson accomplishs"
                )
        except Exception:
            self._logger.error(
                f"Execute task error:\nbatchid:{spider.task.batchid}\nerror:{traceback.format_exc()}"
            )
        finally:
            # 当前插件的完成dict
            with self._spider_threads_locker:
                if self._spider_dealing_dict.__contains__(spider.task):
                    self._spider_dealing_dict.pop(spider.task, None)
            # 当前任务的完成dict
            # 线程里面去调用才对，这里才调对了。
            # 但是，这个还能在多个地方调用？？？不怕调多了出问题？
            if spider.task is not None:
                if callable(spider.task.on_complete):
                    spider.task.on_complete(spider.task)
        return
