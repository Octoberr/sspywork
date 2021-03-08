"""represents a set of network messeges"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.helpers import helper_time

from datacontract.iscoutdataset.iscouttask import IscoutTask

from ..scoutjsonable import ScoutJsonable
from .networkmsg import NetworkMsg


class NetworkMsgs(ScoutJsonable):
    """包装所有 networkpost 用于输出 所有 推文信息"""
    def __init__(self, task: IscoutTask):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid IscoutTask")

        ScoutJsonable.__init__(self, "iscout_networkid_msg")

        self._task: IscoutTask = task

        self._msgs: dict = {}
        self._msgs_locker = threading.RLock()

    def __len__(self):
        return self._msgs.__len__()

    ###############################################
    # set items

    def set_msgs(self, *msgs: NetworkMsg):
        if msgs is None or len(msgs) < 1:
            return

        with self._msgs_locker:
            for m in msgs:
                if self._msgs.__contains__(m._msgid + m._source):
                    return
                self._msgs[m._msgid + m._source] = m

    ###############################################
    # output

    def get_outputdict(self) -> dict:
        res: dict = {}
        res["taskid"] = self._task.taskid
        res["batchid"] = self._task.batchid
        res["source"] = self._task.source
        res["time"] = helper_time.get_time_sec_tz()
        res['relationfrom'] = self._task.cmd.stratagyscout.relationfrom
        res["msgs"] = []

        for m in self._msgs.values():
            try:
                m: NetworkMsg = m
                m_one = m.get_outputdict()
                res["msgs"].append(m_one)

            except Exception:
                pass

        return res
