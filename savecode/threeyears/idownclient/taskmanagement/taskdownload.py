"""
扫描数据库，取下载任务，
更新数据库，
分配爬虫任务：账号下载和短信下载
更新数据库
create by judy 2018/10/10

管理下载任务
新增循环下载
modify by swm 2019/05/09

增加stratagy字段，修改stratagy字段
"""

from queue import PriorityQueue
import threading
import time
from datetime import datetime
import json
import traceback
import pytz
from ..clientdbmanager.sqlcondition import ESqlComb, SqlCondition, SqlConditions

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import Task, ETaskStatus
from datacontract.idowncmd import IdownCmd
from idownclient.config_task import clienttaskconfig
from idownclient.spidermanagent.spiderdownload import SpiderDownload
from idownclient.clientdbmanager import DbManager


class TaskDownload(object):
    def __init__(self):
        self._sqlfunc = DbManager
        # 新任务队列
        self._new_task_queue = PriorityQueue()
        # 循环任务队列
        self._cycle_task_queue = PriorityQueue()
        # 并发队列任务数
        self._concur_num = clienttaskconfig.concurrent_number

        self._spider_download = SpiderDownload()
        self._logger: MsLogger = MsLogManager.get_logger("TaskDownload")

        # 正在处理的任务队列
        self._dealing_queue: dict = {}
        # 正在处理新任务队列,如果有新任务是不会执行循环下载任务的
        self._dealing_queue_locker = threading.Lock()

        # 默认配置
        _defaultcmd: str = self._sqlfunc.get_default_idown_cmd().get("cmd")
        self.d_cmd = IdownCmd(_defaultcmd)

    def _process_task_execution_time(self, q_task: dict):
        """
        处理刚从数据库查出数据，检测任务是否在有效期
        和任务是否满足在执行时间段
        :param q_task:
        :return:
        """
        q_cmdid = q_task.get("cmdid")
        is_effective = True
        if q_cmdid is None or q_cmdid == "":
            # 这里的true表示默认的任务时没有任务活性和时间限制的
            # 目前来看是这样，如果使用时出问题再修改吧，judy190603
            return True
        cmd = IdownCmd(q_task.get("cmd"))
        # 因为任务里面保存的设置可能不是完整的，所以需要使用默认设置补齐
        cmd.fill_defcmd(self.d_cmd)
        # 每个任务都去判断一下并发数
        if int(cmd.stratagy.concur_num) != self._concur_num:
            self._concur_num = int(cmd.stratagy.concur_num)
        # 统一使用东8区的时间
        beijing = pytz.timezone("Asia/Shanghai")
        now_datetime = datetime.now(beijing)
        now_time = now_datetime.time()
        try:
            if cmd.stratagy.time_start is not None:
                task_time_start = datetime.strptime(
                    cmd.stratagy.time_start, "%Y-%m-%d %H:%M:%S"
                )
                if now_datetime >= beijing.localize(task_time_start):
                    is_effective = True
                else:
                    return False
            if cmd.stratagy.time_end is not None:
                task_time_end = datetime.strptime(
                    cmd.stratagy.time_end, "%Y-%m-%d %H:%M:%S"
                )
                if now_datetime <= beijing.localize(task_time_end):
                    is_effective = True
                else:
                    return False
            # ----------------------------------------------上面的判断为任务是否在有效时间
            if len(cmd.stratagy.period) == 0:
                return is_effective
            # 这里如果没有时间限制那么应该直接返回true

            for t_p in cmd.stratagy.period:
                t_p_list = t_p.split("-")
                # 处理界面发错了，列表里有个"null"
                try:
                    if (
                        datetime.strptime(t_p_list[0], "%H:%M:%S").time()
                        <= now_time
                        <= datetime.strptime(t_p_list[1], "%H:%M:%S").time()
                    ):
                        is_effective = True
                        break
                    else:
                        is_effective = False
                except Exception:
                    is_effective = True
            # ---------------------------------------------上面为判断任务是否在执行时间内

        except:
            self._logger.error(
                f"Determine the effective and execution time of the task error, err:{traceback.format_exc()}"
            )
        return is_effective

    def _get_pause_tasks(self):
        """
        获取被暂停的任务，如果任务开启了下载那么就开始下载
        这个任务是被暂停的任务，所以是一定会有cmdid的，同理cmd也是全的
        如果没有直接抛弃即可
        :return:
        """
        pause_task_list = []
        # pause_task = self._sqlfunc.query_task('taskstatus', ETaskStatus.TemporarilyStop.value)
        pause_task = self._sqlfunc.query_task(
            SqlConditions(
                SqlCondition(
                    colname="taskstatus",
                    val=ETaskStatus.TemporarilyStop.value,
                    comb=ESqlComb.Or,
                ),
            )
        )
        if len(pause_task) == 0:
            return pause_task_list
        for pt in pause_task:
            try:
                # 需要解析下设置里的下载开关
                cmd = IdownCmd(pt.get("cmd"))
                # 如果为None，就保持之前的状态不变（暂停着）
                if cmd.switch_control is None:
                    continue

                # 1表示开启下载
                if int(cmd.switch_control.download_switch) == 1:
                    pause_task_list.append(pt)
            except:
                self._logger.error(
                    f"Get pause task error, err:{traceback.format_exc()}"
                )
                continue
        return pause_task_list

    def _construct_task(self, filedata: dict) -> Task:
        """
        函数设计不合理，为什么构造Task会和put_task_to_queue放在一起??
        单独构造task
        """
        tsk: Task = Task(filedata)
        # 加载设置,包括补齐默认设置
        if tsk.cmd_id is None:
            tsk.cmd = self.d_cmd
        else:
            tsk.cmd.fill_defcmd(self.d_cmd)

        # 初始化task数据
        tsk._other_fields = json.loads(filedata["otherfileds"])
        # 为啥这里要赋值，不是在task里面给了吗？
        tsk._sequence = filedata["sequence"]
        # 使用配置里面的优先级，优先级只有在加入下载队列的时候才会使用，
        tsk.priority = tsk.cmd.stratagy.priority

        tsk.on_complete = self.on_task_complete
        return tsk

    def _put_task_to_queue(self, tsk: Task, queue: PriorityQueue):
        """
        将任务放进队列的通用方法，这个函数专职用于处理task放入队列的逻辑
        :param filedata:
        :param queue:
        :return:
        """
        if not isinstance(tsk, Task):
            raise Exception("Invalid Task")
        # 同时进行的最大的下载任务数,优先级高的任务直接处理
        # 正在下载的任务可能需要很久，所以每次sleep5秒即可
        # 需要使用即将进行处理的队列来查询，而不是用这个来查询 modify by judy 20201118
        while int(tsk.priority) < 4 and queue.qsize() > self._concur_num:
            time.sleep(1)
        # if int(tsk.priority) < 4 and len(self._dealing_queue) >= self._concur_num:
        # time.sleep(5)
        # 不睡眠，执行条件不达标则直接返回，不加到队列里，
        # 反正下次还要查出来，且查询有睡眠间隔，不会废太多cpu
        # return

        queue.put(tsk)
        self._logger.info(
            f"Put an idown task to queue: {tsk.tasktype} {tsk.tokentype}\ntaskid:{tsk.taskid}\nbatchid:{tsk.batchid}"
        )
        return

    def _get_new_task(self):
        new_task_list = []
        result_list = []
        try:
            # 目前就新任务去下载，注释的代码是为了调试方便，不排除以后会用
            # new_task = self._sqlfunc.query_task('taskstatus', ETaskStatus.New.value)
            with self._dealing_queue_locker:
                # 这里必须是查出来立即去重，避免多线程同步问题
                new_task = self._sqlfunc.query_task(
                    SqlConditions(
                        SqlCondition(
                            colname="taskstatus",
                            val=ETaskStatus.New.value,
                            comb=ESqlComb.Or,
                        ),
                        SqlCondition(
                            colname="taskstatus",
                            val=ETaskStatus.WaitForDeal.value,
                            comb=ESqlComb.Or,
                        ),
                        SqlCondition(
                            colname="taskstatus",
                            val=ETaskStatus.Logining.value,
                            comb=ESqlComb.Or,
                        ),
                        SqlCondition(
                            colname="taskstatus",
                            val=ETaskStatus.Downloading.value,
                            comb=ESqlComb.Or,
                        ),
                    )
                )

                pause_task = self._get_pause_tasks()
                if len(new_task) > 0:
                    # new_task_list.extend(new_task)
                    # 检查任务是否在执行时间
                    for t_a in new_task:
                        if self._process_task_execution_time(t_a):
                            new_task_list.append(t_a)
                if len(pause_task) > 0:
                    for t_p in pause_task:
                        if self._process_task_execution_time(t_p):
                            new_task_list.append(t_p)

                # 立即去重
                for dic in new_task_list:
                    if not isinstance(dic, dict):
                        continue
                    # 构造Task
                    task: Task = None
                    try:
                        task = self._construct_task(dic)
                    except Exception:
                        self._logger.error(
                            "Construct task from dict error: {}".format(
                                traceback.format_exc()
                            )
                        )
                    if not isinstance(task, Task):
                        continue

                    # 校验Task
                    if (
                        not isinstance(task.taskid, str)
                        or task.taskid == ""
                        or not isinstance(task.batchid, str)
                        or task.batchid == ""
                    ):
                        continue
                    if self._dealing_queue.__contains__(task.batchid):
                        continue

                    # 先更新状态
                    # 到这里就是所有result_list中的任务都是必须要执行的了，
                    # 所以在加锁时就更新其状态

                    # 修改任务状态为正在处理到对列
                    # tsk.taskstatus = ETaskStatus.WaitForDeal
                    # 修改数据库中的任务状态
                    self._sqlfunc.update_status_by_taskid(
                        "taskstatus",
                        ETaskStatus.WaitForDeal.value,
                        task.batchid,
                        task.taskid,
                    )

                    # 然后放到去重字典里
                    self._dealing_queue[task.batchid] = task
                    result_list.append(task)

        except Exception:
            self._logger.error(
                "Select executable tasks error: {}".format(traceback.format_exc())
            )
        return result_list

    def _put_new_task(self):
        """
        将新任务加入队列
        :return:
        """
        while True:
            new_tasks = self._get_new_task()
            if len(new_tasks) == 0:
                # 3秒钟扫描一次数据库
                time.sleep(1)
                continue
            try:
                for filedata in new_tasks:
                    self._put_task_to_queue(filedata, self._new_task_queue)
            except:
                self._logger.error(
                    f"Make the task from sqlite wrong, err:{traceback.format_exc()}"
                )
            finally:
                time.sleep(1)

    # ---------------------------------------------开始重复的任务
    def _task_usercfg_filter(self, l_e_time: int, cmdstr: str):
        """
        根据用户的设置来判断这个任务是否满足循环下载的条件
        :param l_e_time:
        :param cmdstr:
        :return:
        """
        res = False
        date_unix = int(datetime.now(pytz.timezone("Asia/Shanghai")).timestamp())
        if cmdstr is None or cmdstr == "":
            # 如果任务没有带有cmd，那么使用默认配置
            cmd: IdownCmd = self.d_cmd
        else:
            # 任务里带有的设置可能不是完整的，需要补齐设置
            cmd: IdownCmd = IdownCmd(cmdstr)
            cmd.fill_defcmd(self.d_cmd)
        # -----------新增判断任务模式,如果不是循环任务那么就不进行循环下载
        if int(cmd.stratagy.circulation_mode) != 2:
            return res

        # 2、下载开着，3、监控开着
        if int(cmd.switch_control.download_switch) != 1:
            return res
        # 监控现在只针对cookie保活
        # if int(cmd.switch_control.monitor_switch) != 1:
        #     return res
        # 通用设置
        # 4、在定义的下载时间段内
        # 同一天0-24
        # if cmd.cmd_stratagy.time_peroid_end > cmd.cmd_stratagy.time_peroid_start \
        #         and cmd.cmd_stratagy.time_peroid_start <= date_hour <= cmd.cmd_stratagy.time_peroid_end:
        #     res = True
        # 到了第二天
        # elif cmd.cmd_stratagy.time_peroid_end < cmd.cmd_stratagy.time_peroid_start and \
        #         (date_hour >= cmd.cmd_stratagy.time_peroid_start or date_hour <= cmd.cmd_stratagy.time_peroid_end):
        #     res = True
        # 这里判断下是否满足了在下载时间区间
        # if not res:
        #     return res
        # --------------------------------时间在得到任务时统一判断了
        # 5、现在的时间距离上次下载的时间过了定义的时间间隔
        if date_unix - int(l_e_time) >= int(cmd.stratagy.interval):
            res = True
        return res

    def _get_cycle_task(self):
        """
        获取需要循环下载的任务
        :return:
        """
        cycletask = []
        try:
            with self._dealing_queue_locker:
                # 1、任务已经下载完成
                # downloaded_tasks = self._sqlfunc.query_task('taskstatus', ETaskStatus.DownloadSucceed.value)
                downloaded_tasks = self._sqlfunc.query_task(
                    SqlConditions(
                        SqlCondition(
                            colname="taskstatus",
                            val=ETaskStatus.DownloadSucceed.value,
                            comb=ESqlComb.Or,
                        ),
                    )
                )
                for dic in downloaded_tasks:
                    try:
                        last_execute_time = dic.get("lastexecutetime")
                        # 只是判断是否满足循环下载的条件
                        filter_res = self._task_usercfg_filter(
                            last_execute_time, dic.get("cmd")
                        )
                        # 满足了任务的有效时间，并且满足循环任务的条件那么才开始下载
                        if not filter_res or not self._process_task_execution_time(dic):
                            continue

                        if not isinstance(dic, dict):
                            continue
                        # 构造Task
                        task: Task = None
                        try:
                            task = self._construct_task(dic)
                        except Exception:
                            self._logger.error(
                                "Construct task from dict error: {}".format(
                                    traceback.format_exc()
                                )
                            )
                        if not isinstance(task, Task):
                            continue

                        # 校验Task
                        if (
                            not isinstance(task.taskid, str)
                            or task.taskid == ""
                            or not isinstance(task.batchid, str)
                            or task.batchid == ""
                        ):
                            continue
                        if self._dealing_queue.__contains__(task.batchid):
                            continue

                        # 先更新状态
                        # 到这里就是所有result_list中的任务都是必须要执行的了，
                        # 所以在加锁时就更新其状态

                        # 修改任务状态为正在处理到对列
                        # tsk.taskstatus = ETaskStatus.WaitForDeal
                        # 修改数据库中的任务状态
                        self._sqlfunc.update_status_by_taskid(
                            "taskstatus",
                            ETaskStatus.WaitForDeal.value,
                            task.batchid,
                            task.taskid,
                        )

                        # 然后放到去重字典里
                        self._dealing_queue[task.batchid] = task
                        cycletask.append(task)
                    except:
                        self._logger.error(
                            f"Get cycle task error, err:{traceback.format_exc()}"
                        )
        except Exception:
            self._logger.error(
                "Get cycle task form db error: {}".format(traceback.format_exc())
            )
        return cycletask

    def _put_cycle_task(self):
        """
        将需要重复下载的任务假如队列
        这里考虑到因为是重复下载，所以不能和新任务抢资源
        每次等待的时间会比较长
        :return:
        """
        while True:
            cycle_tasks = self._get_cycle_task()
            if len(cycle_tasks) == 0:
                # 1分钟扫描一次数据库
                time.sleep(1)
                continue
            try:
                for filedata in cycle_tasks:
                    # 不占用新任务的资源，当有任务在下载时主动等待，可能下载时间比较长，等待30秒
                    if len(self._dealing_queue) > 2:
                        continue
                    self._put_task_to_queue(filedata, self._cycle_task_queue)
            except:
                self._logger.error(
                    f"Make the task from sqlite wrong, err:{traceback.format_exc()}"
                )
            finally:
                time.sleep(1)

    def execute_new_task(self):
        """
        不断的从新任务中取出任务,下载数据
        :return:
        """
        got = False
        while True:
            if self._new_task_queue.empty():
                time.sleep(1)
                continue
            got = False
            tsk: Task = self._new_task_queue.get()
            got = True
            self._logger.info(
                "Task start: {} {} {} {} {}{}".format(
                    tsk.batchid,
                    tsk.tasktype,
                    tsk.tokentype.name,
                    tsk.account,
                    tsk.globaltelcode,
                    tsk.phone,
                )
            )
            try:
                if not self._spider_download.download_data(tsk):
                    self._logger.info("Spider Download data error")
            except:
                self._logger.error(
                    f"Adapter spider wrong, err:{traceback.format_exc()}"
                )
            finally:
                time.sleep(1)  # 等待线程状态回执
                if got:
                    self._new_task_queue.task_done()

    def execute_cycle_task(self):
        """
        不断的从循环任务队列中取出任务执行,下载数据
        :return:
        """
        got = False
        while True:
            if self._cycle_task_queue.empty():
                # 这个的等待时间可以长一点
                time.sleep(1)
                continue
            got = False
            tsk: Task = self._cycle_task_queue.get()
            got = True
            self._logger.info(
                "Cycle task start: {} {} {} {} {}{}".format(
                    tsk.batchid,
                    tsk.tasktype,
                    tsk.tokentype.name,
                    tsk.account,
                    tsk.globaltelcode,
                    tsk.phone,
                )
            )
            try:
                if not self._spider_download.download_data(tsk):
                    self._logger.info("Spider Download data error")
            except:
                self._logger.error(
                    f"Adapter spider Wronge, err:{traceback.format_exc()}"
                )
            finally:
                time.sleep(1)  # 等待线程状态回执
                if got:
                    self._cycle_task_queue.task_done()

    def start(self):
        """
        多线程开启任务执行
        :return:
        """
        thread1 = threading.Thread(target=self._put_new_task, name="taskscan")
        thread2 = threading.Thread(target=self.execute_new_task, name="taskexecute")
        # 自循环任务
        thread3 = threading.Thread(target=self._put_cycle_task, name="cycletaskscan")
        thread4 = threading.Thread(
            target=self.execute_cycle_task, name="cycletaskexecute"
        )
        thread1.start()
        thread2.start()
        thread3.start()
        thread4.start()

    def on_task_complete(self, task: Task):
        """Task对象处理完毕的回调"""
        with self._dealing_queue_locker:
            # 这里面必须同时更新数据库状态，避免多线程同步问题
            self._sqlfunc.update_status_by_taskid(
                "taskstatus", task.taskstatus.value, task.batchid, task.taskid
            )
            if self._dealing_queue.__contains__(task.batchid):
                self._dealing_queue.pop(task.batchid, None)
