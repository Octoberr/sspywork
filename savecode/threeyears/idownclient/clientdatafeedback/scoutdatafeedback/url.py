"""object url"""

# -*- coding:utf-8 -*-

import threading

from commonbaby.helpers import helper_time

from datacontract.iscoutdataset import IscoutTask

from .component import Component
from datacontract.iscoutdataset import EObjectType
from .scoutfeedbackbase import ScoutFeedBackBase


class URL(ScoutFeedBackBase):
    """scout object IP"""

    def __init__(
            self,
            task: IscoutTask,
            level: int,
            url: str,
    ):
        ScoutFeedBackBase.__init__(self, task, level, EObjectType.Url, url, 'iscout_url')

        # subitems
        self._hp_code: str = None
        self._hp_title: str = None
        self._hp_meta: str = None

        self._components: dict = {}
        self._components_locker = threading.RLock()

        self._wafs: dict = {}  # 先写成字典，但是输出时只输出第一个
        self._wafs_locker = threading.RLock()

    def _subitem_count(self) -> int:
        """子类实现 返回当前根节点的 子数据 总条数"""
        res = 0
        if not self._hp_code is None:
            res += 1
        if not self._hp_title is None:
            res += 1
        if not self._hp_meta is None:
            res += 1
        with self._components_locker:
            res += len(self._components)
        with self._wafs_locker:
            res += len(self._wafs)
        return res

    # set items ###############################################
    def set_homepage_code(self, code: str):
        """向当前URL根节点添加 首页源码\n
        code: str 首页源码"""
        if not isinstance(code, str) or code == "":
            raise Exception("Invalid code for URL")
        self._hp_code = code

    def set_homepage_summary(self, title: str, meta: str):
        """向当前URL根节点添加 摘要信息\n
        title: str 页面标题\n
        meta: str 页面meta"""
        if title is None:
            raise Exception("Invalid title for URL")
        # if not isinstance(meta, str) or meta == "":
        #     raise Exception("Invalid meta for URL")

        self._hp_title = title
        self._hp_meta = meta

    def set_component(self, component: Component):
        """向当前URL根节点添加 组件信息\n
        component: Component对象"""
        if not isinstance(component, Component):
            raise Exception("Invalid component for URL")

        with self._components_locker:
            self._components[component] = component

    def set_waf(self, waf: str):
        """向当前域名对象中设置waf字段"""
        if not isinstance(waf, str):
            return

        with self._wafs_locker:
            if self._wafs.__contains__(waf):
                return
            self._wafs[waf] = None

    # output dict ###############################################
    def _get_outputdict_sub(self, rootdict: dict):
        if not isinstance(rootdict, dict):
            raise Exception("Invalid rootdict")

        if not rootdict.__contains__("homepage"):
            rootdict["homepage"] = {}

        rootdict["homepage"]["page"] = self._hp_code
        rootdict["homepage"]["title"] = self._hp_title
        rootdict["homepage"]["meta"] = self._hp_meta

        # 添加waf节点
        self._outputdict_add_waf(rootdict)

        if len(self._components) < 1:
            return

        if not rootdict.__contains__("component"):
            rootdict["component"] = []
        for cm in self._components.values():
            cm: Component = cm
            cmdict: dict = cm.get_outputdict()
            rootdict["component"].append(cmdict)

    def _outputdict_add_waf(self, rootdict: dict):
        if len(self._wafs) < 1:
            return
        if not rootdict.__contains__("waf"):
            rootdict["waf"] = {}

        # 暂时只取第1个，后面测试下是否有网站能探测到2个或以上的waf,再改标准
        for waf in self._wafs.keys():
            rootdict["waf"]["name"] = waf
            break
