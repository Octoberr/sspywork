"""represents a set of networkid profiles"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.helpers import helper_time

from datacontract.iscoutdataset.iscouttask import IscoutTask
from .networkprofile import NetworkProfile
from ..scoutjsonable import ScoutJsonable


class NetworkProfiles(ScoutJsonable):
    """包装所有networkprofile，用于输出 所有 人员信息"""

    def __init__(self, task: IscoutTask):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid IscoutTask")

        ScoutJsonable.__init__(self, "iscout_networkid_profile")

        self._task: IscoutTask = task

        self._profiles: dict = {}
        self._profiles_locker = threading.RLock()

    def __len__(self):
        """当前NetworkProfiles包装里的NetworkProfile的数量"""
        return self._profiles.__len__()

    ###############################################
    # set items

    def set_profile(self, profile: NetworkProfile):
        if not isinstance(profile, NetworkProfile):
            raise Exception("Invalid NetworkProfile")

        if self._profiles.__contains__(profile._source + profile._userid):
            return
        with self._profiles_locker:
            if self._profiles.__contains__(profile._source + profile._userid):
                return
            self._profiles[profile._source + profile._userid] = profile

    ###############################################
    # output

    def get_outputdict(self) -> dict:
        res: dict = {}
        res["taskid"] = self._task.taskid
        res["batchid"] = self._task.batchid
        res["source"] = self._task.source
        res["time"] = helper_time.get_time_sec_tz()
        # 新增字段
        res['relationfrom'] = self._task.cmd.stratagyscout.relationfrom

        jid = res["networkids"] = []

        for profile in self._profiles.values():
            try:
                # jpro_wapper = {}

                profile: NetworkProfile = profile
                jpro_one = profile.get_outputdict()

                # jpro_wapper["profile"] = jpro_one

                jid.append(jpro_one)

            except Exception:
                pass

        return res
