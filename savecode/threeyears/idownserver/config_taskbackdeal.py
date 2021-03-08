"""回馈命令处理"""

# -*- coding:utf-8 -*-

from datacontract import ExtMatcher

from .taskbackdealer import (AutoTaskBackDealer, CmdBackDealer,
                             IScanTaskBackDealer, IScoutTaskBackDealer,
                             TaskBackConfig, TaskBackDealer)

taskbackconfig: TaskBackConfig = TaskBackConfig({
    "taskbackdealer":
    TaskBackDealer(
        uniquename="taskbackdealer",
        datamatcher=ExtMatcher([
            # "idown_task_back",
            "idown_btask_back",
        ]),
        relation_inputer_src=None,
    ),
    "cmdbackdealer":
    CmdBackDealer(
        uniquename="cmdbackdealer",
        datamatcher=ExtMatcher([
            "idown_cmd_back",
        ]),
        relation_inputer_src=None,
    ),
    "iscantaskbackdealer":
    IScanTaskBackDealer(
        uniquename="iscantaskbackdealer",
        datamatcher=ExtMatcher([
            "iscan_task_back",
        ]),
        relation_inputer_src=None,
    ),
    "iscouttaskbackdealer":
    IScoutTaskBackDealer(
        uniquename="iscouttaskbackdealer",
        datamatcher=ExtMatcher([
            # "iscout_task_back",
            "iscout_btask_back",
        ]),
        relation_inputer_src=None,
    ),
    "autotaskbackdealer":
    AutoTaskBackDealer(
        uniquename="autotaskbackdealer",
        datamatcher=ExtMatcher([
            # "iscout_task_back",
            "automated_btask_back",
        ]),
        relation_inputer_src=None,
    ),
})
