"""represents a set of networkpost"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.helpers import helper_time

from datacontract.iscoutdataset.iscouttask import IscoutTask
from .networkpost import NetworkPost
from ..scoutjsonable import ScoutJsonable


class NetworkPosts(ScoutJsonable):
    """包装所有 networkpost 用于输出 所有 推文信息"""

    def __init__(self, task: IscoutTask):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid IscoutTask")

        ScoutJsonable.__init__(self, "iscout_networkid_post")

        self._task: IscoutTask = task

        self._posts: dict = {}
        self._posts_locker = threading.RLock()

    def __len__(self):
        return self._posts.__len__()

    ###############################################
    # set items

    def set_posts(self, *posts: NetworkPost):
        if posts is None or len(posts) < 1:
            return

        with self._posts_locker:
            for p in posts:
                if self._posts.__contains__(p._postid + p._source):
                    return
                self._posts[p._postid + p._source] = p

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

        res["posts"] = []

        for p in self._posts.values():
            try:
                p: NetworkPost = p
                p_one = p.get_outputdict()
                res["posts"].append(p_one)

            except Exception:
                continue

        return res
