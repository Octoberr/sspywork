"""task feedback data dealer"""

# -*- coding:utf-8 -*-

import math
import queue
import threading
import time
import traceback

from datacontract import (DataMatcher, DataSeg, ECommandStatus, InputData,
                          Task, TaskBack, TaskBatchBack)
from dataparser import DataParser
from outputmanagement import OutputManagement

from ..dbmanager import EDBAutomic
from .taskbackdealerbase import TaskBackDealerBase


class TaskBackDealer(TaskBackDealerBase):
    """deal task feedback data"""
    def __init__(
            self,
            uniquename: str,
            datamatcher: DataMatcher,
            relation_inputer_src: list = None,
    ):
        TaskBackDealerBase.__init__(self, uniquename, datamatcher,
                                    relation_inputer_src)

        # 处理失败的 TaskBatchBack 队列，用于重新处理
        self._tbberrorq: queue.Queue = queue.Queue()

        # 处理总任务回馈文件的队列
        self._tbqueue: queue.Queue = queue.Queue()

        # 总任务处理线程
        self._t_taskback_deal = threading.Thread(target=self._taskback_deal,
                                                 name='taskback_deal',
                                                 daemon=True)
        # self._t_errortb_rehandle = threading.Thread(
        #     target=self._errortb_rehandle,
        #     name='errortb_rehandle',
        #     daemon=True)

    def _startsub(self):
        """开启处理线程"""
        if not self._t_taskback_deal._started._flag:
            self._t_taskback_deal.start()
        # if not self._t_errortb_rehandle._started._flag:
        #     self._t_errortb_rehandle.start()

    def _parse_data_back(self, data: InputData) -> iter:
        """解析数据，并返回每个数据段对应的 TaskBatchBack 结构"""
        try:

            for seg in DataParser.parse_standard_data(data.stream):
                seg: DataSeg = seg
                try:
                    tb: TaskBatchBack = TaskBatchBack.create_from_dataseg(seg)
                    tb.inputdata = data
                    yield tb

                except Exception:
                    self._logger.error(
                        "Parse one data segment error:\ndata:{}\nsegindex:{}\nerror:{}"
                        .format(data._source, seg.segindex,
                                traceback.format_exc()))
                    # 解析数据时，只要出错一个数据段，就算作错误数据
                    data.on_complete(False)

        except Exception:
            self._logger.error(
                "Parse TaskBatchBack data error:\ndata:{}\nerror:{}".format(
                    data._source, traceback.format_exc()))

    def _deal_data_back(self, tb: TaskBatchBack) -> bool:
        """处理TaskBatchBack数据"""
        # ==================
        # 更新指定的子任务的cmdstatus命令状态等字段
        # 综合判断总任务是否完成或结束，
        # 返回总任务完成进度或总任务最终结果

        # 当总任务下的所有子任务的命令状态均为以下枚举值时
        # Failed/Succeed/Cancelled/Timeout
        # 判定为总任务已结束

        # 子任务状态为 NeedSmsCode 时，需要在数据库添加
        # 标记，以确认中心是否收到消息并下发了验证码，若长时间
        # 未收到中心的验证码，且也未收到来自采集端的任务超时错误，
        # 需要控制端进行超时处理（此时认为采集端的此条任务挂了？）
        # ==================
        res: bool = False
        # 更新数据库子任务状态
        if tb._progress != 1 and (tb._cmdstatus == ECommandStatus.Succeed
                                  or tb._cmdstatus == ECommandStatus.Failed
                                  or tb._cmdstatus == ECommandStatus.Cancelled
                                  or tb._cmdstatus == ECommandStatus.Timeout):
            tb.progress = 1
        with self._dbmanager.get_automic_locker(EDBAutomic.ReduplicateTask):
            if not self._dbmanager.update_batchtask_back(tb):
                tb._cmdrcvmsg = "更新子任务状态到本地数据库失败"
                self._logger.error(
                    "Update TaskBatchBack to db failed:\ndata:{}\ntaskid:{}\nbatchid:{}"
                    .format(tb.inputdata.name, tb._taskid, tb._batchid))
                return res

            # 查询对应的总任务对象
            # 子任务是这些状态，那么总任务的 batchcompletecount+=1
            task: Task = self._dbmanager.get_task_by_taskid(tb._taskid)
            if tb._cmdstatus==ECommandStatus.Failed or \
                tb._cmdstatus==ECommandStatus.Succeed or \
                tb._cmdstatus==ECommandStatus.Timeout or \
                tb._cmdstatus==ECommandStatus.Cancelled:
                if not self._dbmanager.is_batch_complete_count_increaced(
                        tb._platform, tb._taskid, tb._batchid):
                    if not self._dbmanager.increace_task_batch_complete_count(
                            task._platform, task.taskid, tb._batchid):
                        tb._cmdrcvmsg = "子任务完成数量增加到数据库失败"
                        self._logger.error(
                            "Increace task batch complete count failed:\ndata:{}\ntaskid={}\nbatchid={}\nbatchtask_cmdstatus={}"
                            .format(tb.inputdata.name, tb._taskid, tb._batchid,
                                    tb._cmdstatus.name))
                        return res
                    else:
                        task.batchcompletecount += 1
                        task.isbatchcompletecountincreased = True

        # 回传子任务回馈文件
        if not OutputManagement.output(tb):
            tb._cmdrcvmsg = "输出子任务回馈数据失败"
            self._logger.error(
                "Output TaskBatchBack file to center failed:\ndata:{}\ntaskid:{}\nbatchid:{}"
                .format(tb.inputdata.name, tb._taskid, tb._batchid))
            return res

        # 顺利跑到这里，子任务处理就是成功的了
        tb.ok = True
        self._logger.info(
            "TaskBatchBack {}:\ndata:{}\ntaskid:{}\nbatchid:{}".format(
                task.tasktype.name, tb.inputdata.name, tb._taskid,
                tb._batchid))

        self._tbqueue.put(task)
        res = True
        return res

    def _output_taskback(self, tb, status: ECommandStatus, msg: str):
        """返回总任务回馈"""
        if not isinstance(tb, TaskBatchBack):
            self._logger.error(
                "Invalid task object for output taskback: {}".format(type(tb)))
            return

        tb: TaskBack = tb
        tb.cmdstatus = status
        tb.cmdrcvmsg = msg
        if not OutputManagement.output(tb):
            self._logger.error(
                "Output TaskBack failed:\ntaskid={}\ndata={}".format(
                    tb._task.taskid, tb._task.inputdata._source))

    def _generate_err_taskbatchback(self, tb: TaskBatchBack):
        """返回控制端内部处理错误信息到中心"""
        try:
            tb._cmdrcvmsg = "内部错误：{}".format(tb._cmdrcvmsg)
            tb.cmdstatus = ECommandStatus.Failed
            if not OutputManagement.output(tb):
                self._logger.error(
                    "Generate error taskbatchback to center error:\ndata:{}\ntaskid:{}\nbatchid:{}\nerror:{}"
                    .format(tb.inputdata.name, tb._taskid, tb._batchid,
                            traceback.format_exc()))
        except Exception:
            self._logger.error(
                "Generate error taskbatchback to center error:\ndata:{}\ntaskid:{}\nbatchid:{}\nerror:{}"
                .format(tb.inputdata.name, tb._taskid, tb._batchid,
                        traceback.format_exc()))

    def _taskback_deal(self):
        """总任务回馈数据处理线程，失败重试机制"""
        got: bool = False
        while True:
            try:
                got = False
                task: Task = self._tbqueue.get(timeout=3)
                got = True

                # 返回总任务回馈

                # 百分比回馈数据若失败重试，会涉及到sequence不对问题，暂时不重试
                # if task.batchtotalcount > task.batchcompletecount:
                # 如果总任务下的 部分子任务 是已完成状态，
                # 则返回总任务回馈数据百分比
                # 不是每一个子任务回馈数据都要对应返回一个总任务完成百分比
                # 可以根据一定条件返回，比如取模
                self._generate_task_back_percent(task)

                # 返回一次总任务已完成，由于sequence问题暂时不做失败重试
                if task.batchtotalcount <= task.batchcompletecount:
                    # 判定总任务是否完成，并返回总任务回馈数据
                    # 只要有一个成功的，就当作成功的返回
                    succcount: int = self._dbmanager.get_batch_task_count_by_cmdstatus(
                        task, ECommandStatus.Succeed)
                    if succcount > 0:
                        task.cmdstatus = ECommandStatus.Succeed
                        task.cmdrcvmsg = "任务执行完成"
                    else:
                        task.cmdstatus = ECommandStatus.Failed
                        task.cmdrcvmsg = "任务执行失败"

                    # 先回传TaskBack回中心，提升其 sequence 字段计数
                    # 若回传失败，则再上面加的那个循环检查线程中重复回传此回馈数据
                    taskback: TaskBack = TaskBack(task)
                    if not OutputManagement.output(taskback):
                        self._logger.error(
                            "Output TaskBack failed:\ntaskid={}".format(
                                task.taskid))
                    else:
                        self._logger.info(
                            "TaskBack generated, cmdstatus=[{}]:\ntaskid={}\ntasktype={}"
                            .format(task._cmdstatus.name, task.taskid,
                                    task.tasktype.name))

                    # 更新总任务状态到数据库
                    # （加一个线程检测是否有总任务一直没有更新状态的，检查是否应该更新，并执行更新操作）
                    with self._dbmanager.get_automic_locker(
                            EDBAutomic.ReduplicateTask):
                        if not self._dbmanager.update_idown_task2(task):
                            self._logger.error(
                                "Update task status failed:\ntaskid={}\ncmdstatus={}"
                                .format(task.taskid, task.cmdstatus))

            except queue.Empty:
                pass
            except Exception:
                self._logger.error("Taskback deal error: {}".format(
                    traceback.format_exc()))
            finally:
                if got:
                    self._tbqueue.task_done()

    def _generate_task_back_percent(self, task: Task) -> bool:
        """返回总任务百分比"""
        res: bool = False
        try:
            currpercent = math.floor(task.batchcompletecount /
                                     task.batchtotalcount * 100)

            if task.cmdstatus != ECommandStatus.Dealing and \
                task.cmdstatus != ECommandStatus.NeedSmsCode and \
                task.cmdstatus != ECommandStatus.Progress and \
                task.cmdstatus !=ECommandStatus.WaitForSend:
                task.progress = 1

            lastprogress = task.progress * 100

            if task.batchtotalcount > 100:
                # 自任务数大于100个的，每1%返回一次
                if currpercent - lastprogress < 1:
                    res = True
            elif 50 < task.batchtotalcount <= 100:
                # 50<x<=100个子任务的，总共返回25个百分比文件，每%4返回一次
                if currpercent - lastprogress < 4:
                    res = True
            else:
                # 0<x<=50个子任务的，每%10左右返回一次
                if currpercent - lastprogress < 10:
                    res = True
            if res:
                return res

            # 最新总任务Progress更新到数据库并发送回馈数据
            task.progress = currpercent / 100
            task.cmdstatus = ECommandStatus.Progress
            if not self._dbmanager.update_idown_task2(task):
                self._logger.error(
                    "Update Task with progress failed: taskid={} tasktype={} progress={}"
                    .format(task.taskid, task.tasktype.name, task.progress))
                return res

            taskback: TaskBack = TaskBack(
                task,
                ECommandStatus.Progress,
                cmdrcvmsg='{}%'.format(currpercent),
                batchcompletecount=task.batchcompletecount)

            if not OutputManagement.output(taskback):
                res = False
                self._logger.error(
                    "Output TaskBack progress failed:\ntaskid:{}\ntasktype:{}\ncmdstatus:{}\nprogress:{}"
                    .format(task.taskid, task.tasktype, task._cmdstatus.name,
                            currpercent))
                return res

            res = True
            self._logger.info(
                "TaskBack generated, cmdstatus=[Progress {}%]:\ntaskid={}\ntasktype:{}"
                .format(task.progress * 100, task.taskid, task.tasktype.name))

        except Exception:
            res = False
            self._logger.error(
                "Generate TaskBack for BatchTask complete percent error:\ntaskid:{}\nerror:{}"
                .format(task.taskid, traceback.format_exc()))
        finally:
            pass

        return res
