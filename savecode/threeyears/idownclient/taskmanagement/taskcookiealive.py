"""
这里是cookie保活的任务
"""
import threading
import time
import traceback
from queue import Queue
from datetime import datetime
import pytz

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import Task, ETaskStatus
from datacontract.idowncmd import IdownCmd
from idownclient.clientdatafeedback import UserStatus
from idownclient.clientdbmanager import DbManager
from idownclient.spidermanagent import SpiderCookieKeep
from outputmanagement import OutputManagement


class TaskCookieAlive(object):
    def __init__(self):
        self._cookie_queue = Queue()
        self._sqlfunc = DbManager
        self._cookie_keeper = SpiderCookieKeep()
        self._logger: MsLogger = MsLogManager.get_logger("CookieKeepAlive")
        # 默认配置
        _defaultcmd: str = self._sqlfunc.get_default_idown_cmd().get("cmd")
        self.d_cmd = IdownCmd(_defaultcmd)

        # 正在处理的任务队列
        self._dealing_queue: dict = {}
        # 正在处理新任务队列,如果有新任务是不会执行循环下载任务的

        self._dealing_queue_locker = threading.Lock()

    def _selcet_cookie_keep_tasks(self):
        """
        查询数据库，将下载完成并且有cookie的任务查询出来
        1、下载成功
        2、有cookie
        :return:
        """
        sql = """SELECT 
                taskid,
                task.platform,
                clientid,
                parent_taskid,
                batchid,
                parentbatchid,
                apptype,
                tasktype,
                url,
                host,
                cookie,
                account,
                password,
                phone,
                input,
                taskstatus,
                createtime,
                lastexecutetime,
                failtimes,
                successtimes,
                globaltelcode,
                otherfileds,
                tokentype,
                sequence,
                progress,
                forcedownload,
                source,
                cmdid,
                cmd,
                cookiealive,
                cookielastkeeptime
                FROM task  LEFT OUTER JOIN idowncmd USING (cmdid)
                WHERE taskstatus=? AND cookie IS NOT NULL;"""
        par = (ETaskStatus.DownloadSucceed.value,)
        all_tasks = self._sqlfunc.query_task_by_sql(sql, par)
        return all_tasks

    def _judge_task_to_queue(self, task_dict):
        """
        判断task中的队列是否满足cookie保活的条件
        :return:
        """
        res = False
        cookiealive = task_dict.get("cookiealive")
        cookielastkeeptime = task_dict.get("cookielastkeeptime")
        # 查看是否满足cookie保活状态， 这个条件得待定，万一以后登录更新了cookie
        # 但是cookie保活状态没有更新那么也应该尝试下，但是应该打一句日志
        # cookie 已经失活就不去更新了
        # if int(cookiealive) != 1:
        # self._logger.info('Cookie has already lost effectiveness, may be cookie has been update,so try again')
        # return res
        cmd_str = task_dict.get("cmd")
        if cmd_str is None:
            cmd: IdownCmd = self.d_cmd
        else:
            cmd: IdownCmd = IdownCmd(cmd_str)
            cmd.fill_defcmd(self.d_cmd)
        # 1、修改流程，如果任务没开监控那么就不去进行cookie保活
        if int(cmd.switch_control.monitor_switch) != 1:
            return False
        # 2、开了监控，并且是第一次进行cookie保活
        if cookiealive is None and cookielastkeeptime is None:
            return True

        # 3、如果cookie已经失活那么就不再进入保活队列
        if cookiealive is not None and int(cookiealive) != 1:
            return False

        # 这里如果任务不是一个循环任务那么就不需要进行cookie保活
        # if int(cmd.stratagy.circulation_mode) != 2:
        #   return res
        # 4、最后判断下如果到了保活时间那么就开始进行保活
        unixtime_now = int(datetime.now(pytz.timezone("Asia/Shanghai")).timestamp())
        if unixtime_now - int(cookielastkeeptime) >= int(cmd.stratagy.cookie_keeplive):
            res = True
        return res

    def _get_cookie_keep_tasks(self):
        """
        从数据库获取需要进行cookie保活的任务
        不断从数据库取出需要进行保活的任务，放入处理队列
        :return:
        """
        while True:
            # self._logger.debug(f"Scan cookie in database")
            all_tasks = self._selcet_cookie_keep_tasks()
            if len(all_tasks) == 0:
                # 60秒扫描一次数据库
                time.sleep(60)
                continue
            try:
                for task_dict in all_tasks:
                    if self._judge_task_to_queue(task_dict):
                        # 实例化task的时候都需要加载设置
                        tsk: Task = Task(task_dict)
                        if tsk.cmd_id is None:
                            tsk.cmd = self.d_cmd
                        else:
                            tsk.cmd.fill_defcmd(self.d_cmd)
                        # -------------------------------------
                        if self._dealing_queue.__contains__(tsk.batchid):
                            continue
                        with self._dealing_queue_locker:
                            self._dealing_queue[tsk.batchid] = tsk
                        self._cookie_queue.put(tsk)
                        self._logger.info(
                            f"Get a cookie keep task\ntaskid:{tsk.taskid}\nbatchid:{tsk.batchid}"
                        )

            except:
                self._logger.error(
                    f"Make the task from sqlite wrong, err:{traceback.format_exc()}"
                )
            finally:
                time.sleep(1)

    def _update_cookie_keep_info(self, cookie_res, tsk: Task):
        """
        根据cookie keeper的结果来更新数据库中的信息
        :param cookie_res:
        :return:
        """
        # 1、更新idown数据库的cookie keep信息
        sql = """
        UPDATE task SET
        cookiealive=?,
        cookielastkeeptime=?
        WHERE taskid=? and batchid=?
        """
        if cookie_res:
            cookie_status = 1
            self._logger.info("Cookie is still alive")
        else:
            cookie_status = 2
            self._logger.info("Cookie is already lost affective")
        pars = (
            cookie_status,
            int(datetime.now(pytz.timezone("Asia/Shanghai")).timestamp()),
            tsk.taskid,
            tsk.batchid,
        )
        self._sqlfunc.update_task_by_sql(sql, pars)
        return

    def _feedback_userinfo(self, cookie_res, tsk: Task):
        """
        每次进行cookie更新后需要回馈cookie的信息
        modify by judy 2020/11/18
        """
        if cookie_res:
            cookie_status = 1
        else:
            cookie_status = 2
        userdict = self._sqlfunc.query_idown_userinfo(tsk.taskid, tsk.batchid)
        if not isinstance(userdict, dict):
            self._logger.error(
                f"Query idown userinfo error\ntaskid:{tsk.taskid}\nbatchid:{tsk.batchid}"
            )
            return
        userid = userdict.get("userid")
        clientid = userdict.get("clientid")
        if userid is None or clientid is None:
            self._logger.error(
                f"Idown userinfo is None, check the database whether or not exist"
            )
            return
        uinfo = UserStatus(tsk, clientid, userid, tsk.apptype)
        uinfo.cookiestatus = cookie_status
        OutputManagement.output(uinfo)
        return

    def _execute_cookie_keep_task(self):
        """
        不断从队列中取出cookie保活任务并执行
        :return:
        """
        got = False
        while True:
            if self._cookie_queue.empty():
                # 这个的等待时间可以长一点
                time.sleep(5)
                continue
            got = False
            tsk: Task = self._cookie_queue.get()
            got = True
            self._logger.info(
                "Cookie keep alive start\nbatchid:{}\ntasktype:{}\ntokentypename:{}\naccount:{}globaltelcode:{}\nphone:{}".format(
                    tsk.batchid,
                    tsk.tasktype,
                    tsk.tokentype.name,
                    tsk.account,
                    tsk.globaltelcode,
                    tsk.phone,
                )
            )
            try:
                res = self._cookie_keeper.cookie_keep(tsk)
                # 更新数据库中cookie的保活状态
                self._update_cookie_keep_info(res, tsk)
                # 回馈cookie保活的结果
                self._feedback_userinfo(res, tsk)
            except:
                self._logger.error(f"Cookie keep error\nerr:{traceback.format_exc()}")
            finally:
                if got:
                    self._cookie_queue.task_done()
                with self._dealing_queue_locker:
                    if self._dealing_queue.__contains__(tsk.batchid):
                        self._dealing_queue.pop(tsk.batchid, None)

    def start(self):
        """
        多线程开启任务执行
        :return:
        """
        thread1 = threading.Thread(
            target=self._get_cookie_keep_tasks, name="getcookiekeeptask"
        )
        thread2 = threading.Thread(
            target=self._execute_cookie_keep_task, name="taskexecute"
        )
        thread1.start()
        thread2.start()
