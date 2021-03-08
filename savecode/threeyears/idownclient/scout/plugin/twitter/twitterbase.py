"""
twitter base
存储一些twitter的基本信息
不然后面太难写了
create by judy 2020/09/15

获取新版twitter的时候添加一个代理，不然twitter会有流量现值
modify by judy 2020/11/30
"""
import datetime
import traceback
from io import BytesIO

import pytz
import requests

from datacontract import IscoutTask

# 引用networkid的数据结构
from idownclient.clientdatafeedback.scoutdatafeedback import (
    NetworkResource,
    EResourceType,
)
from ..scoutplugbase import ScoutPlugBase
from proxymanagement.proxymngr import ProxyMngr


class TwitterBase(ScoutPlugBase):
    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        self.task = task
        self.proxydict = ProxyMngr.get_static_proxy()
        self._now = datetime.datetime.now(pytz.timezone("Asia/Shanghai")).date()
        self.source = "twitter"
        # 取现在的时间
        self.time_now: int = int(
            datetime.datetime.now(pytz.timezone("Asia/Shanghai")).timestamp()
        )
        # 取限制的时间 秒
        self.time_limit = (
            int(
                self.task.cmd.stratagyscout.cmdnetworkid.posttime.public_twitter.timerange
            )
            * 86400
        )

    def _get_network_resource(
        self, resource_url, resource_type: EResourceType, extension="jpg"
    ):
        """
        获取推文内容的resource
        新版本的twitter可以拿到更多的资源类型所以需要修改
        :param resource_url:
        :return:
        """
        try:
            # 下载资源文件先不挂代理，挂了代理出现无法连接的情况
            res = requests.get(resource_url, timeout=180)
            content = res.content
            if content == b"" or content is None:
                return None
            imgdata = BytesIO(res.content)
            resource = NetworkResource(
                self.task,
                self.task.platform,
                resource_url,
                self.source,
                resource_type,
            )
            rid = int(
                datetime.datetime.now(pytz.timezone("Asia/Shanghai")).timestamp() * 1000
            )
            resource.resourceid = rid
            resource.filename = f"{rid}.{extension}"
            resource.extension = extension
            resource.stream = imgdata
            return resource
        except:
            self._logger.error(
                f"Get media resource error, type:{extension}, url:{resource_url}\nerr:{traceback.format_exc()}"
            )
            return None
