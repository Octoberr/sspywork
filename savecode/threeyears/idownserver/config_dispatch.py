"""配置命令数据分配器"""

# -*- coding:utf-8 -*-

from datacontract.datamatcher import ExtMatcher

from .taskdispatcher import (
    AutoTaskDispatcher,
    CmdDispatcher,
    DispatchConfig,
    IScanDispatcher,
    IScoutDispatcher,
    TaskDispatcher,
)

# 分配器配置
dispatchconfig = DispatchConfig(
    taskdispatchers={
        "idowntask": TaskDispatcher(
            uniquename="idowntask",
            datamatcher=ExtMatcher(["idown_task", "an_cookie"]),
            maxwaitcount=1,
            maxwaittime=3,
            relation_inputer_src=None,
        ),
        "cmd": CmdDispatcher(
            uniquename="cmd",
            datamatcher=ExtMatcher(["idown_cmd"]),
            maxwaitcount=1,
            maxwaittime=3,
            relation_inputer_src=None,
        ),
        "iscantask": IScanDispatcher(
            uniquename="iscantask",
            datamatcher=ExtMatcher(["iscan_task"]),
            maxwaitcount=1,
            maxwaittime=3,
            relation_inputer_src=None,
        ),
        "iscouttask": IScoutDispatcher(
            uniquename="iscouttask",
            datamatcher=ExtMatcher(["iscout_task"]),
            maxwaitcount=1,
            maxwaittime=3,
            relation_inputer_src=None,
        ),
        "autotask": AutoTaskDispatcher(
            uniquename="autotask",
            datamatcher=ExtMatcher(["automated_task"]),
            maxwaitcount=1,
            maxwaittime=3,
            relation_inputer_src=None,
        ),
    }
)
