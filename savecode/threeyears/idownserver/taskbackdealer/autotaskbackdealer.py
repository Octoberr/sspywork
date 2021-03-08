"""task feedback data dealer"""

# -*- coding:utf-8 -*-

import math
import queue
import threading
import time
import traceback

from commonbaby.helpers import helper_time

from datacontract import (DataMatcher, DataSeg, ECommandStatus, InputData,
                          AutomatedTask, AutotaskBack, AutotaskBatchBack)
from dataparser import DataParser
from outputmanagement import OutputManagement

from ..dbmanager import EDBAutomic
from .taskbackdealerbase import TaskBackDealerBase


class AutoTaskBackDealer(TaskBackDealerBase):
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
        self._t_taskback_deal = threading.Thread(
            target=self._taskback_deal, name='taskback_deal', daemon=True)
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
                    tb: AutotaskBatchBack = AutotaskBatchBack.create_from_dataseg(
                        seg, data._platform)
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

    def _deal_data_back(self, tb: AutotaskBatchBack) -> bool:
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
        currperiodnum = tb.periodnum
        with self._dbmanager.get_automic_locker(
                EDBAutomic.ReduplicateAutoTask):
            task: AutomatedTask = self._dbmanager.get_auto_batch_task(
                tb._platform, tb.taskid, tb.batchid)
            if tb.periodnum < task.periodnum:
                self._logger.error(
                    "AutotaskBatchBack periodnum({}) < task.periodnum({}) in db:\ntaskid:{}\nbatchid:{}"
                    .format(tb.periodnum, task.periodnum, task.taskid,
                            task.batchid))
                return res
            # if tb._sequence > task._sequence:
            # 自循环任务不需要
            if not self._deal_equal_period(tb, task):
                return res

        # 回传子任务回馈文件
        if not OutputManagement.output(tb):
            tb._cmdrcvmsg = "输出AutomatedTask子任务回馈数据失败"
            self._logger.error(
                "Output AutotaskBatchBackBack file to center failed:\ndata:{}\ntaskid:{}\nbatchid:{}"
                .format(tb.inputdata.name, tb.taskid, tb.batchid))
            return res

        # 顺利跑到这里，子任务处理就是成功的了
        tb.ok = True
        self._logger.info(
            "AutotaskBatchBackBack dealt [{} {}]:\ndata:{}\ntaskid:{}\nbatchid:{}\nperiodnum:{}"
            .format(tb.cmdstatus.name, tb.progress, tb.inputdata.name,
                    tb.taskid, tb.batchid, currperiodnum))

        self._tbqueue.put(task)
        res = True
        return res

    def _deal_equal_period(self, tb: AutotaskBatchBack,
                           task: AutomatedTask) -> bool:
        res: bool = False
        try:
            # 查询对应的总任务对象
            # 子任务是这些状态，那么总任务的 batchcompletecount+=1
            # 把当前AutotaskBatchBack子任务查出来
            if tb._cmdstatus==ECommandStatus.Failed or \
                tb._cmdstatus==ECommandStatus.Succeed or \
                tb._cmdstatus==ECommandStatus.Timeout or \
                tb._cmdstatus==ECommandStatus.Cancelled:
                tb.progress = 1
                if not self._dbmanager.is_autobtask_batchcompletecount_increaced(
                        tb._platform, tb.taskid, tb.batchid):
                    if not self._dbmanager.increace_autotask_batch_complete_count(
                            tb._platform, tb.taskid, tb.batchid):
                        tb._cmdrcvmsg = "全自动子任务完成数量增加到数据库失败"
                        self._logger.error(
                            "Increace AutomatedTask batch complete count failed:\ndata:{}\ntaskid={}\nbatchid={}\nperiodnum={}\nbatchtask_cmdstatus={}"
                            .format(tb.inputdata.name, tb.taskid, tb.batchid,
                                    tb.periodnum, tb._cmdstatus.name))
                        return res
                    elif not task.isbatchcompletecountincreased:
                        task.batchcompletecount += 1
                        task.isbatchcompletecountincreased = True

                # PeriodNum=?,
                # Status=?,
                # Progress=?,
                # CmdRcvMsg=?,
                # Sequence=?,
                # UpdateTime=?
                if not self._dbmanager.update_automated_batch_task(
                        tb._platform,
                        tb.taskid,
                        tb.batchid,
                        updatefields={
                            # 'PeriodNum': tb.periodnum,
                            'Status': tb.cmdstatus.value,
                            'Progress': 1,
                            'CmdRcvMsg': tb.cmdrcvmsg,
                            'Sequence': tb.sequence,
                            'UpdateTime': tb.time,
                            'LastEndTime': helper_time.ts_since_1970_tz(),
                        }):
                    tb._cmdrcvmsg = "更新Autom子任务状态到本地数据库失败"
                    self._logger.error(
                        "Update AutotaskBatchBack to db failed:\ndata:{}\ntaskid:{}\nbatchid:{}"
                        .format(tb.inputdata.name, tb.taskid, tb.batchid))
                    return res

            res = True
        except Exception:
            self._logger.error(
                "Deal first period task back error:\ntaskid:{}\nbatchid:{}\nclientid:{}\nerror:{}"
                .format(task.taskid, task.batchid, task._clientid,
                        traceback.format_exc()))
        return res

    def _output_taskback(self, tb, status: ECommandStatus, msg: str):
        """返回总任务回馈"""
        if not isinstance(tb, AutotaskBatchBack):
            self._logger.error(
                "Invalid AutotaskBatchBack object for output taskback: {}".
                format(type(tb)))
            return

        tb: AutotaskBatchBack = tb
        tb.cmdstatus = status
        tb.cmdrcvmsg = msg
        if not OutputManagement.output(tb):
            self._logger.error(
                "Output TaskBack failed:\ntaskid={}\ndata={}".format(
                    tb._task.taskid, tb._task.inputdata._source))

    def _generate_err_taskbatchback(self, tb: AutotaskBatchBack):
        """返回控制端内部处理错误信息到中心"""
        try:
            tb._cmdrcvmsg = "内部错误：{}".format(tb._cmdrcvmsg)
            tb.cmdstatus = ECommandStatus.Failed
            if not OutputManagement.output(tb):
                self._logger.error(
                    "Generate error AutotaskBatchBack to center error:\ndata:{}\ntaskid:{}\nbatchid:{}\nerror:{}"
                    .format(tb.inputdata.name, tb.taskid, tb.batchid,
                            traceback.format_exc()))
        except Exception:
            self._logger.error(
                "Generate error AutotaskBatchBack to center error:\ndata:{}\ntaskid:{}\nbatchid:{}\nerror:{}"
                .format(tb.inputdata.name, tb.taskid, tb.batchid,
                        traceback.format_exc()))

    def _taskback_deal(self):
        """总任务回馈数据处理线程，失败重试机制"""
        got: bool = False
        while True:
            try:
                got = False
                task: AutomatedTask = self._tbqueue.get(timeout=3)
                got = True

                # 返回总任务回馈

                # 百分比回馈数据若失败重试，会涉及到sequence不对问题，暂时不重试
                # if task.batchtotalcount > task.batchcompletecount:
                # 如果总任务下的 部分子任务 是已完成状态，
                # 则返回总任务回馈数据百分比
                # 不是每一个子任务回馈数据都要对应返回一个总任务完成百分比
                # 可以根据一定条件返回，比如取模

                seq_in_db: int = self._dbmanager.get_autotask_sequence(
                    task._platform, task.taskid)
                task.sequence_set(seq_in_db)
                self._generate_task_back_percent(task)

                # 返回一次总任务已完成，由于sequence问题暂时不做失败重试
                if task.batchtotalcount <= task.batchcompletecount:
                    # 判定总任务是否完成，并返回总任务回馈数据
                    # 只要有一个成功的，就当作成功的返回
                    succcount: int = self._dbmanager.get_autobtask_count_by_cmdstatus(
                        task._platform, task.taskid, ECommandStatus.Succeed)
                    if succcount > 0:
                        task.cmdstatus = ECommandStatus.Succeed
                        task.cmdrcvmsg = "任务执行完成"
                    else:
                        task.cmdstatus = ECommandStatus.Failed
                        task.cmdrcvmsg = "任务执行失败"

                    # 先回传 AutomatedTaskBack 回中心，提升其 sequence 字段计数
                    # 若回传失败，则再上面加的那个循环检查线程中重复回传此回馈数据
                    taskback: AutotaskBack = AutotaskBack.create_from_task(
                        task,
                        task.cmdstatus,
                        task.cmdrcvmsg,
                        batchcompletecount=task.batchtotalcount)
                    if not OutputManagement.output(taskback):
                        self._logger.error(
                            "Output AutomatedTaskBack failed:\ntaskid={}".
                            format(task.taskid))
                    else:
                        self._logger.info(
                            "AutomatedTaskBack generated [{}]:\ntaskid={}".
                            format(task.cmdstatus.name, task.taskid))

                    # 更新总任务状态到数据库
                    # （加一个线程检测是否有总任务一直没有更新状态的，检查是否应该更新，并执行更新操作）
                    # task.periodnum += 1 子任务那加了1的
                    task.lastendtime = helper_time.ts_since_1970_tz()
                    with self._dbmanager.get_automic_locker(
                            EDBAutomic.ReduplicateAutoTask):
                        if not self._dbmanager.update_automated_task2(task):
                            self._logger.error(
                                "Update AutomatedTask status failed:\ntaskid={}\ncmdstatus={}"
                                .format(task.taskid, task.cmdstatus.name))

            except queue.Empty:
                pass
            except Exception:
                self._logger.error("Taskback deal error: {}".format(
                    traceback.format_exc()))
            finally:
                if got:
                    self._tbqueue.task_done()

    def _generate_task_back_percent(self, task: AutomatedTask) -> bool:
        """返回总任务百分比"""
        res: bool = False
        try:
            currpercent = math.floor(
                task.batchcompletecount / task.batchtotalcount * 100)

            lastprogress = task.progress * 100

            if task.batchtotalcount > 100:
                # 子任务数大于100个的，每1%返回一次
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
            if not self._dbmanager.update_automated_task2(task):
                self._logger.error(
                    "Update AutomatedTask with progress failed: taskid={} objecttype={} progress={}"
                    .format(task.taskid, task._objecttype.name, task.progress))
                return res

            taskback: AutotaskBack = AutotaskBack.create_from_task(
                task,
                ECommandStatus.Progress,
                recvmsg='{}%'.format(currpercent),
                batchcompletecount=task.batchtotalcount)

            if not OutputManagement.output(taskback):
                res = False
                self._logger.error(
                    "Output AutotaskBack progress failed:\ntaskid:{}\ncmdstatus:{}\nprogress:{}"
                    .format(task.taskid, task.cmdstatus.name, currpercent))
                return res

            res = True
            self._logger.info(
                "AutotaskBack generated [Progress {}]:\ntaskid={}".format(
                    task.progress, task.taskid))

        except Exception:
            res = False
            self._logger.error(
                "Generate AutomatedTaskBack for batch complete percent error:\ntaskid:{}\nerror:{}"
                .format(task.taskid, traceback.format_exc()))
        finally:
            pass

        return res
