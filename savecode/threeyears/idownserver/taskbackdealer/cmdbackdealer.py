"""idowncmd feedback data dealer"""

# -*- coding:utf-8 -*-

import math
import queue
import threading
import time
import traceback

from datacontract import (CmdFeedBack, DataMatcher, DataSeg, ECommandStatus,
                          InputData)
from dataparser import DataParser
from outputmanagement import OutputManagement

from ..dbmanager import EDBAutomic
from .taskbackdealerbase import TaskBackDealerBase


class CmdBackDealer(TaskBackDealerBase):
    """aaa"""

    def __init__(
            self,
            uniquename: str,
            datamatcher: DataMatcher,
            relation_inputer_src: list = None,
    ):
        TaskBackDealerBase.__init__(self, uniquename, datamatcher,
                                    relation_inputer_src)

    def _parse_data_back(self, data: InputData) -> iter:
        try:

            for seg in DataParser.parse_standard_data(data.stream):
                seg: DataSeg = seg
                try:
                    tb: CmdFeedBack = CmdFeedBack.create_from_dataseg(
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
            if not isinstance(tb, CmdFeedBack):
                self._logger.error(
                    "Invalid CmdFeedBack for cmdbackdeal: {}".format(type(tb)))
                return res

            tb: CmdFeedBack = tb

            # 更新到数据库
            # if tb._sequence > task._sequence:只有一个cmdback,不需要查询了
            if not self._dbmanager.update_cmdback(tb):
                self._logger.error(
                    "Update CmdFeedBack failed:\ncmdid:{}\nstatus:{}\nmsg:{}".
                    format(tb.cmd_id, tb.cmdstatus.name, tb.cmdrcvmsg))
                tb.cmdrcvmsg = "合并更新命令状态失败"
                return res

            self._logger.info("CmdFeedBack ok, cmdid:{}, cmdstatus:{}".format(
                tb.cmd_id, tb._cmdstatus.name))

            # 检查，如果是分发到所有采集端的cmd任务，需要统计所有采集端的执行状态后
            # 才能发回中心
            status: ECommandStatus = self._dbmanager.get_cmd_merge_status(
                tb.cmd_id, tb._platform)

            if status == ECommandStatus.Dealing or status == ECommandStatus.Progress:
                res = True
                return res

            tb.cmdstatus = status
            tb.cmdrcvmsg = "命令执行成功"
            # 发送回中心
            if not OutputManagement.output(tb):
                self._logger.error("Output CmdFeedBack to center failed.")
                res = False
                return res

            self._logger.info(
                "CmdFeedBack generated, cmdid:{}, cmdstatus:{}".format(
                    tb.cmd_id, tb._cmdstatus.name))

            res = True

        except Exception:
            self._logger.error("Deal IDownCmdBack error:\n{}\n {}".format(
                tb, traceback.format_exc()))
        return res

    def _output_taskback(self, cmdback, status: ECommandStatus, msg: str):
        if not isinstance(cmdback, CmdFeedBack):
            self._logger.error(
                "Invalid CmdFeedBack object for output CmdFeedBack: {}".format(
                    type(cmdback)))
            return

        cmdback: CmdFeedBack = cmdback
        cmdback.cmdstatus = status
        cmdback.cmdrcvmsg = msg
        if not OutputManagement.output(cmdback):
            self._logger.error("Output CmdFeedBack failed:\ncmdid={}".format(
                cmdback.cmd_id))
