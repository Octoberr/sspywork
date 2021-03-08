"""represents a network post"""

# -*- coding:utf-8 -*-

import threading

from .networkprofile import NetworkProfile
from .networkresource import NetworkResource
import datetime


class NetworkPost(object):
    """一个推文/博客信息"""

    @property
    def posttime_datetime(self) -> datetime.datetime:
        """用于计算推文时间范围 datetime 类型"""
        return self._posttime_datetime

    @posttime_datetime.setter
    def posttime_datetime(self, value: datetime.datetime):
        """用于计算推文时间范围 datetime 类型"""
        if not isinstance(value, datetime.datetime):
            raise Exception("Invalid datetime for posttime_datetime")
        # 用法
        # dt_now = datetime.datetime.utcnow()
        # dt_post = datetime.datetime.utcfromtimestamp(ts)
        # # 本来就是UTC时间，直接输出成字符串就是UTC的时间字符串
        # print(dt_post.strftime('%Y-%m-%d %H:%M:%S'))
        # timedelta = dt_now - dt_post
        # if timedelta.days > timerange:
        #    print("超出时间范围")
        self._posttime_datetime = value

    @property
    def postid(self) -> str:
        """开一个可以访问postid的接口"""
        return self._postid

    @postid.setter
    def postid(self, value):
        """开一个可以访问postid的接口"""
        if value is None:
            raise Exception("Invalid postid")
        self._postid = value

    def __init__(
        self,
        postid: str,
        source: str,
        userid: str,
        parentpostid: str = None,
        isroot: bool = True,
    ):
        if postid is None or postid == "":
            raise Exception("Invalid postid")
        if source is None or source == "":
            raise Exception("Invalid source")
        if userid is None or userid == "":
            raise Exception("Invalid userid")

        self._postid: str = str(postid)
        self._source: str = str(source)
        self._userid: str = str(userid)

        # self.parentpostid: str = str(parentpostid) # 这谁干的？parentpostid为None的时候直接就成了'None'字符串了
        self.parentpostid: str = (
            None if parentpostid is None else parentpostid.__str__()
        )
        self.isroot: bool = isroot

        self.nickname: str = None
        self.posttime: str = None
        self.posturl: str = None
        self.location: str = None
        self.likecount: int = 0
        self.replycount: int = 0
        self.text: str = None

        self._likes: dict = {}
        self._likes_locker = threading.RLock()

        self._resources: dict = {}
        self._resources_locker = threading.RLock()

        # posttime datetime
        # 用于计算推文时间范围
        self._posttime_datetime: datetime.datetime = None

    ###############################################
    # set items

    def set_likes(self, profile: NetworkProfile):
        """设置点赞人"""
        if not isinstance(profile, NetworkProfile):
            raise Exception("Invalid NetworkProfile")

        if self._likes.__contains__(profile._userid + profile._source):
            return
        with self._likes_locker:
            if self._likes.__contains__(profile._userid + profile._source):
                return
            self._likes[profile._userid, profile._source] = profile

    def set_resource(self, *rsc: NetworkResource):
        """设置关联资源数据"""
        if rsc is None or len(rsc) < 1:
            return

        with self._resources_locker:
            for r in rsc:
                if self._resources.__contains__(r._url + r._source):
                    continue
                self._resources[r._url + r._source] = r

    ###############################################
    # output

    def get_outputdict(self) -> dict:
        res: dict = {}

        if not self.parentpostid is None:
            res["parentpostid"] = self.parentpostid
        res["isroot"] = self.isroot
        res["userid"] = self._userid
        if not self.nickname is None:
            res["nickname"] = self.nickname
        res["source"] = self._source
        res["postid"] = self._postid
        if not self.posttime is None:
            res["posttime"] = self.posttime
        if not self.posturl is None:
            res["posturl"] = self.posturl
        if not self.location is None:
            res["location"] = self.location
        if isinstance(self.likecount, int):
            res["likecount"] = self.likecount
        if isinstance(self.replycount, int):
            res["replycount"] = self.replycount

        if not self.text is None:
            res["text"] = self.text

        if len(self._likes) > 0:
            res["likes"] = []
            for p in self._likes.values():
                p: NetworkProfile = p
                res["likes"].append(
                    {"userid": p._userid, "nickname": p.nickname, "source": p._source}
                )

        if len(self._resources) > 0:
            res["resources"] = []
            for r in self._resources.values():
                r: NetworkResource = r
                res["resources"].append({"resourceid": r.resourceid, "url": r._url})

        return res
