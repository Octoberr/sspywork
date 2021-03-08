"""idowncmd feedback data dealer"""

# -*- coding:utf-8 -*-

import traceback

from commonbaby.helpers import helper_time

from datacontract import (DataMatcher, DataSeg, ECommandStatus, InputData,
                          IscanTask, IscanTaskBack)
from dataparser import DataParser
from outputmanagement import OutputManagement
from .taskbackdealerbase import TaskBackDealerBase


class IScanTaskBackDealer(TaskBackDealerBase):
    """iscantaskbackdealer"""

    def __init__(
            self,
            uniquename: str,
            datamatcher: DataMatcher,
            relation_inputer_src: list = None,
    ):
        TaskBackDealerBase.__init__(self, uniquename, datamatcher, relation_inputer_src)

    def _parse_data_back(self, data: InputData) -> iter:
        """"""
        try:
            for seg in DataParser.parse_standard_data(data.stream):
                seg: DataSeg = seg
                try:
                    tb: IscanTaskBack = IscanTaskBack.create_from_dataseg(
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

    def _deal_data_back(self, tb) -> bool:
        """处理IDownCmd命令回馈"""
        res: bool = False
        try:
            if not isinstance(tb, IscanTaskBack):
                self._logger.error(
                    "Invalid IscanTaskBack for cmdbackdeal: {}".format(
                        type(tb)))
                return res

            tb: IscanTaskBack = tb

            # 判断周期数是否正确
            task: IscanTask = self._dbmanager.get_iscantask(tb._platform, tb._taskid)
            if not isinstance(task, IscanTask):
                self._logger.error(
                    "IscanTask not found in db:\ntaskid={}".format(tb._taskid))
                return res
            if tb.periodnum < task.periodnum:
                self._logger.error(
                    "IScanTaskBack periodnum({}) < task.periodnum({}) in db:\ntaskid:{}"
                        .format(
                        tb.periodnum,
                        task.periodnum,
                        task.taskid,
                    ))
                return res

            currperiodnum = tb.periodnum
            # 更新数据库
            # 只有当前序列号比数据库里面的大才去更新数据库，否则不需要更新，modify by judy 20201019
            if tb._sequence > task._sequence:
                if not self._deal_equal_period(tb, task):
                    return res
            tb.periodnum = currperiodnum

            # 发送回中心
            if not OutputManagement.output(tb):
                self._logger.error("Output IscanTaskBack to center failed.")
                res = False
                return res

            self._logger.info(
                "IScanTaskBack dealt [{} {}]:\ndata:{}\ntaskid:{}\nperiodnum:{}"
                    .format(tb.cmdstatus.name, tb.progress, tb.inputdata.name,
                            tb._taskid, currperiodnum))

            res = True

        except Exception:
            self._logger.error("Deal IDownCmdBack error:\n{}\n {}".format(
                tb, traceback.format_exc()))
        return res

    def _deal_equal_period(self, tb: IscanTaskBack, task: IscanTask) -> bool:
        res: bool = False
        try:
            # 查询对应的总任务对象
            # 子任务是这些状态，那么总任务的 batchcompletecount+=1
            # 把当前IScouTBatchTask子任务查出来
            updatefields: dict = {}
            if tb._cmdstatus == ECommandStatus.Failed or \
                    tb._cmdstatus == ECommandStatus.Succeed or \
                    tb._cmdstatus == ECommandStatus.Timeout or \
                    tb._cmdstatus == ECommandStatus.Cancelled:
                # 周期数+1
                # if task._is_period:
                #     tb.periodnum += 1
                #     task.periodnum += 1
                tb.progress = 1
                updatefields["LastEndTime"] = helper_time.ts_since_1970_tz()

            updatefields["PeriodNum"] = tb.periodnum
            updatefields["Status"] = tb.cmdstatus.value
            updatefields["Progress"] = tb.progress
            updatefields["CmdRcvMsg"] = tb.cmdrcvmsg
            updatefields["Sequence"] = tb._sequence
            updatefields["UpdateTime"] = tb.time

            if not self._dbmanager.update_iscantask2(
                    tb._platform,
                    tb._taskid,
                    updatefields=updatefields,
            ):
                tb._cmdrcvmsg = "更新IScout子任务状态到本地数据库失败"
                self._logger.error(
                    "Update IScanTask to db failed:\ndata:{}\ntaskid:{}\n".
                        format(tb.inputdata.name, tb._taskid))
                return res

            res = True
        except Exception:
            self._logger.error(
                "Deal first period task back error:\ntaskid:{}\nbatchid:{}\nclientid:{}\nerror:{}"
                    .format(task.taskid, task.batchid, task._clientid,
                            traceback.format_exc()))
        return res

    def _output_taskback(self, scantaskback, status: ECommandStatus, msg: str):
        if not isinstance(scantaskback, IscanTaskBack):
            self._logger.error(
                "Invalid CmdFeedBack object for output IscanTaskBack: {}".
                    format(type(scantaskback)))
            return

        scantaskback: IscanTaskBack = scantaskback
        scantaskback.cmdstatus = status
        scantaskback.cmdrcvmsg = msg
        if not OutputManagement.output(scantaskback):
            self._logger.error(
                "Output IscanTaskBack failed:\ntaskid={}".format(
                    scantaskback._taskid))
