"""
精简代码
插件下载数据
create by judy 2018/01/24

短信任务，同步之前短信登陆的登陆令牌
update by judy 2019/03/25
"""
import threading
import traceback

from idownclient.spidermanagent.spidermanagebase import SpiderManagebase
from idownclient.spider.spiderbase import SpiderBase
from datacontract import Task, ETokenType, ECommandStatus
from datacontract.apps.appbase import AppConfig
from idownclient.cmdmanagement import CmdProcess

# 这个是爬虫内部使用的appcfg
from idownclient.spider.appcfg import AppCfg


class SpiderDownloadTaskStore(SpiderManagebase):
    def __init__(self):
        SpiderManagebase.__init__(self)

    def _synchronize_login_cred(self, tsk: Task):
        """
        这个方法目前只用于同步短信登陆的登陆凭证，
        后面应该是要用来同步，短信，账密等类型的登陆凭证
        :param tsk:
        :return:
        """
        # 这个有待改进，需要查询有效的cookie
        # 同步短信登陆的登陆凭证
        # 2019/03/21修改phone和account任选一个，下载状态为成功或者登陆成功，确保cookie为能用的
        # 可能这个同步还需要继续修改，目前可以这样
        sql = """
        select * from task
        where apptype=? and phone=? 
        and (taskstatus=6 or taskstatus=3)
        """
        pars = (
            tsk.apptype,
            tsk.phone,
        )
        res_info = self._sqlfunc.query_task_by_sql(sql, pars)
        if len(res_info) == 0:
            return
        # 取最新的一个
        res_one = res_info[-1]
        # 取出来的数据有cookie,并且目前的数据没有cookie就通过cookie赋值
        if res_one.get("cookie") is not None and tsk.cookie is None:
            tsk.cookie = res_one.get("cookie")
        return

    def _store_sms_task(self, tsk: Task):
        """
        有关短信下载的任务，存入数据库
        :param tsk:
        :return:
        """
        try:
            if tsk.phone is None or tsk.phone == "":
                self._logger.error("Sms donwload phone cannot be none!")
                self._write_tgback(tsk, ECommandStatus.Failed, "phone不能为空")
                return

            self._logger.info("New sms task: {}".format(tsk.batchid))
            self._write_tgback(tsk, ECommandStatus.Dealing, "已将短信下载任务加入处理队列")
            self._sqlfunc.insert_task_to_sqlit(tsk)
        except Exception as err:
            self._logger.error("Store sms error: {}".format(err))
        finally:
            if callable(tsk.on_complete):
                tsk.on_complete(tsk)

    # 针对账号密码，cookie的查询账号是否能有效登陆
    def _checklogin(self, tsk: Task):
        """
        登陆测试，用于检测账密, cookie是否有效，
        如果账密或者cookie有效则进行数据下载
        :param tsk:
        :return:
        """
        if tsk.tokentype == ETokenType.Pwd:
            # 账密登陆，当账号和密码任意一个为空都要报错
            if tsk.account is None or tsk.password is None:
                self._logger.error("Pwd login:account and password cannot be None")
                self._write_tgback(tsk, ECommandStatus.Failed, "账密登陆，账号或者密码为空")
                return
        elif tsk.tokentype == ETokenType.Cookie:
            # cookie登陆，cookie为空也报错
            if tsk.cookie is None:
                self._logger.error("Cookie login: cookie cannot be None")
                self._write_tgback(tsk, ECommandStatus.Failed, "Cookie登陆，cookie为空")
                return
        try:
            with self._spider_threads_locker:
                if self._spider_dealing_dict.__contains__(tsk):
                    self._logger.info(
                        "{} is checking login in {}.".format(
                            tsk.batchid, self._spider_dealing_dict[tsk].name
                        )
                    )
                    return
            appcfg: AppConfig = self._spideradapter.adapter(tsk)[0]
            if not isinstance(appcfg, AppConfig):
                self._logger.info(
                    "No spider match:\nbatchid:{}\ntasktpe:{}\napptype:{}".format(
                        tsk.batchid, tsk.tasktype.name, tsk.apptype
                    )
                )
                return

            spider: SpiderBase = appcfg._appclass(
                tsk, self._get_appcfg(appcfg), self._clientid
            )
            self._logger.info("Test login start")
            t = threading.Thread(
                target=self._execute_checklogin, daemon=True, args=(spider,)
            )
            t.start()
            with self._spider_threads_locker:
                # 用元组存入 插件对象  和 线程对象
                self._spider_dealing_dict[tsk] = spider
        except:
            self._logger.error("Match spider error:\n{}".format(traceback.format_exc()))
            self._write_tgback(tsk, ECommandStatus.Failed, "执行爬虫插件出错，请检查client环境重试")
        return

    def _execute_checklogin(self, spider: SpiderBase):
        """
        任务处理线程。
        spider: 已初始化好的spider对象
        """
        try:
            login_result = spider.login_test()
            if login_result:
                # 成功，插入数据库， 返回回馈文件
                self._write_tgback(
                    spider.task, ECommandStatus.Dealing, "任务登陆测试成功， 已将任务加入处理队列"
                )
                self._sqlfunc.insert_task_to_sqlit(spider.task)
                self._logger.info("Test login succeed: {}".format(spider.uname_str))
            elif login_result == "":
                self._logger.info("Test login failed: {}".format(spider.task.batchid))
                self._write_tgback(
                    spider.task, ECommandStatus.Failed, "任务登录测试失败，暂不支持此类邮箱的账密/短信登录"
                )
            else:
                # 失败，直接返回回馈文件
                self._logger.info("Test login failed: {}".format(spider.task.batchid))
                self._write_tgback(
                    spider.task, ECommandStatus.Failed, "任务登陆测试失败，请更新信息重新尝试"
                )
        except Exception:
            self._logger.error(
                "Execute task error:\nbatchid:{}\nerror:{}".format(
                    spider.task.batchid, traceback.format_exc()
                )
            )
            self._write_tgback(spider.task, ECommandStatus.Failed, "执行任务出现不可知错误")
        finally:
            with self._spider_threads_locker:
                if self._spider_dealing_dict.__contains__(spider.task):
                    self._spider_dealing_dict.pop(spider.task, None)
            if spider.task is not None:
                if callable(spider.task.on_complete):
                    spider.task.on_complete(spider.task)

    def login_and_download_data(self, tsk: Task):
        """
        外界程序入口
        下载任务要存入本地sql，用来重复下载更新数据，或者是存储登陆令牌
        update by swm 191219
        1、webmail需要去验证账密或者cookie是否有效，有效才保存在数据库
        2、pop3和imap需要去验证apptype是否在mailserverl里面
        :param tsk:
        :return:
        """
        dlprotocal = tsk.cmd.stratagymail.eml_priority_protocol
        token = tsk.tokentype
        # 因为是分表存的，先存入cmd，防止查询的时候没有将cmd查询出来而导致错误
        if tsk.cmd_id is not None:
            try:
                self._sqlfunc.store_task_cmd(tsk.cmd_id, tsk.cmd.cmd_str)
                CmdProcess.write_cmd_back(tsk.cmd, ECommandStatus.Succeed, "任务设置应用成功")
            except:
                self._logger.error(
                    f"Store task cmd error, err:{traceback.format_exc()}"
                )
                CmdProcess.write_cmd_back(tsk.cmd, ECommandStatus.Failed, "任务设置应用失败")

        if token == ETokenType.Sms or token == ETokenType.SmsPwd:
            # 插入前同步下数据库的登陆凭证
            self._synchronize_login_cred(tsk)
            self._store_sms_task(tsk)
        # elif token == ETokenType.Pwd or token == ETokenType.Cookie:
        #     # 检测账号是否可用然后将任务保存到数据库
        #     self._checklogin(tsk)
        # else:
        #     self._logger.error("Tokentype is unknown, please check what the tokentype get!")
        #     self._write_tgback(tsk, ECommandStatus.Failed, "登陆下载数据，tokentype的值为空")
        #     if callable(tsk.on_complete):
        #         tsk.on_complete(tsk)
        # webmail
        elif dlprotocal == "webmail":
            # 现在的token只有pwd和cookie两种了，以前的东西都废弃了
            self._checklogin(tsk)
        else:
            # 然后就是pop3，imap需要去验证下数据库有没有保存相关的邮服地址
            # 因为pop和imap的插件继承了spiderbase,所以需要封装一个appcfg
            # 1、验证账号是否有效，是否能登陆pop或者imap
            # 2、将账号存入数据库
            self._sqlfunc.insert_task_to_sqlit(tsk)
            self._logger.info(
                f"Get a pop3/imap task\ntaskid:{tsk.taskid}\nbatchid:{tsk.batchid}"
            )
            self._write_tgback(tsk, ECommandStatus.Dealing, "pop3/imap下载任务已加入下载队列")
            # 3、结束任务
            if callable(tsk.on_complete):
                tsk.on_complete(tsk)
            # 好了这个就暂时这样
        # 这里如果任务有cmdid那么的话要保存设置,并且要给回馈，这里是处理带有设置的task
        # 这里为什么可以在后面存，是因为那边还需要验证cookie或者是账号是否有效
        # 而且那边的存储是多线程的不会造成阻塞，这样cmd是优先存入了数据库的
        return
