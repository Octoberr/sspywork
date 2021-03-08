"""represents a network messege"""

# -*- coding:utf-8 -*-

import threading

from .networkresource import NetworkResource


class NetworkMsg(object):
    """一条消息"""

    def __init__(self, dialogid: str, msgid: str, userid: str, source: str):
        if dialogid is None or dialogid == '':
            raise Exception("Invalid dialogid for networkid profile")
        if msgid is None or msgid == '':
            raise Exception("Invalid msgid for networkid profile")
        if userid is None or userid == '':
            raise Exception("Invalid userid for networkid profile")
        if source is None or source == '':
            raise Exception("Invalid source for networkid profile")

        # current fields
        self._dialogid: str = str(dialogid)
        self._msgid: str = str(msgid)
        self._userid: str = str(userid)
        self._source: str = str(source)

        self.nickname: str = None
        self.msgtime: str = None
        self.location: str = None
        self.likecount: int = 0
        self.text: str = None

        self._resources: dict = {}
        self._resources_locker = threading.RLock()

    ###############################################
    # set items

    def set_resource(self, *resources: NetworkResource):
        """设置资源数据"""
        if resources is None or len(resources) < 1:
            return

        with self._resources_locker:
            for r in resources:
                if self._resources.__contains__(r._url + r._source):
                    continue
                self._resources[r._url + r._source] = r

    ###############################################
    # output

    def get_outputdict(self) -> dict:
        """输出"""
        res: dict = {}
        res["dialogid"] = self._dialogid
        res["userid"] = self._userid
        if not self.nickname is None:
            res["nickname"] = self.nickname
        res["source"] = self._source
        res["msgid"] = self._msgid
        if not self.msgtime is None:
            res["msgtime"] = self.msgtime
        if not self.location is None:
            res["location"] = self.location

        res["likecount"] = self.likecount

        if not self.text is None:
            res["text"] = self.text

        if len(self._resources) > 0:
            res["resources"] = []
            for r in self._resources.values():
                r: NetworkResource = r
                res["resources"].append({
                    "resourceid": r.resourceid,
                    "url": r._url
                })

        return res
