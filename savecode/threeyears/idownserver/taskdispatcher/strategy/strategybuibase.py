"""strategybase for diff tasktypes"""

# -*- coding:utf-8 -*-

import random
import threading
import traceback
from abc import ABCMeta, abstractmethod
from typing import Tuple

from commonbaby.helpers import helper_str
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import (ALL_APPS, AppConfig, AutomatedTask, Client,
                          EAppClassify, EClientBusiness, ETaskType, IscanTask,
                          IscoutTask, StatusBasic, Task)

from ...config_strategy import clientbusiness_mapping
from ...dbmanager.dbmanager import DbManager, SqlCondition, SqlConditions
from .score import Score
from .stgunits import StrategyBase
from .strategyconfig import ExplicitFilters, StrategyConfig


class StrategyBuisinessBase:
    """strategybase for diff tasktypes"""

    __metaclass = ABCMeta

    __stgconfig: StrategyConfig = None
    __initlocker = threading.RLock()
    __initialed: bool = False

    @staticmethod
    def static_init(stgconfig: StrategyConfig):
        if StrategyBuisinessBase.__initialed:
            return
        with StrategyBuisinessBase.__initlocker:
            if StrategyBuisinessBase.__initialed:
                return
            if not isinstance(stgconfig, StrategyConfig):
                raise Exception("Invalid strategyconfig")
            StrategyBuisinessBase.__stgconfig = stgconfig
            StrategyBuisinessBase.__initialed = True

    def __init__(self, explicitfilters: ExplicitFilters = None):
        # 其他
        self._logger: MsLogger = MsLogManager.get_logger(
            self.__class__.__name__)
        # 初始化策略器

        self._polling_index: int = 0
        self._polling_index_locker = threading.RLock()

        # 这里是直接手动排序好的...后面直接for循环调用即可...
        self.all_stgs: list = StrategyBuisinessBase.__stgconfig._strategies
        self.forced_stgs: list = [s for s in self.all_stgs if s._isforced]
        self.unforced_stgs: list = [
            s for s in self.all_stgs if not s._isforced
        ]

        self._explicit_filters: ExplicitFilters = explicitfilters

    @abstractmethod
    def match(self, task) -> bool:
        """子类实现匹配特定类型的任务"""
        raise NotImplementedError()

    def dispatch(self, task, clients: dict) -> Tuple[bool, Client, str]:
        succ: bool = False
        res: Client = None
        msg: str = None
        try:
            # 先将所有client初始化为0分
            clients: dict = dict.fromkeys(clients.values(), 0)
            clients = self._filter_clients(task, clients)
            succ, res, msg = self._dispatch(task, clients)

        except Exception:
            self._logger.error(
                "Dispatch error:\ntasktype:{}\ntaskid:{}\nerr:{}".format(
                    type(task), task.taskid, traceback.format_exc()))
        return (succ, res, msg)

    @abstractmethod
    def _dispatch(self, task, clients: list) -> Tuple[bool, Client, str]:
        """子类实现对特定任务的分发策略"""
        raise NotImplementedError()

    def _get_polling_next(self, clients: dict) -> str:
        """以轮询方式选择一个"""
        res: str = None
        if len(clients) < 1:
            raise Exception("No client suites task")
        elif len(clients) == 1:
            res = list(clients.keys())[0]
        else:
            # 选出轮询的下一个
            with self._polling_index_locker:
                if len(clients) < self._polling_index + 1:
                    self._polling_index = 0
                res = list(clients.keys())[self._polling_index]
                self._polling_index += 1
        return res

    def _choose_one_randomly(self, client_scores: dict) -> str:
        """从给予的采集端分数字典<client,score>中随机选一个"""
        res: str = None

        maxscore = 0
        result_clients: list = []
        for item in client_scores.items():
            if item[1] > maxscore:
                maxscore = item[1]
                result_clients.clear()
                result_clients.append(item[0])
            elif item[1] == maxscore:
                result_clients.append(item[0])
        chooseone = random.randint(0, (len(result_clients) - 1))
        res = result_clients[chooseone]

        return res

    def _get_scores(self, task, clients: dict, stgs: list) -> dict:
        """使用给与的stgs策略字典对指定task计算给与的clientstatus的分数，并返回<client,score>字典"""
        # 遍历每个策略进行分数计算
        for stg in stgs:
            if not issubclass(stg.__class__, StrategyBase):
                raise Exception("Given stgs has invalid member: %s" % stg)
            stg: StrategyBase = stg
            # 拿当前策略计算的分数结果字典
            client_scores: dict = stg.get_score(list(clients.keys()))
            for c_s in client_scores.items():
                client: str = c_s[0]
                score: float = c_s[1]
                # 如果结果集中没有此client
                if not clients.__contains__(client):
                    # 若当前策略为必要策略，但是结果集中没有，则算作没有符合标准的采集端
                    # 否则就是之前就被剔除了的，直接pass
                    if stg._isforced:
                        raise Exception("No suitable client found for task")
                # 如果当前采集端计算分数结果为0分
                if score == 0:
                    # 如果当前策略为硬性策略，则直接从初始化列表中剔除0分的
                    # 若不是硬性策略，不加分跳过
                    if stg._isforced and clients.__contains__(client):
                        clients.pop(client, None)
                # 若有分数，表示当前采集端较为符合需求，加分写入结果集
                else:
                    if clients.__contains__(client):
                        clients[client] += score

                # 若结果集的client被删完了，说明没有合适的采集端直接返回
                if len(clients) < 1:
                    return clients

        return clients

    def _get_highest_score(self, clients: dict) -> dict:
        """从给予的<client,score>字典中选出一个最高分的并返回"""
        res: str = None
        if len(clients) < 1:
            raise Exception("No client suites task")
        elif len(clients) == 1:
            res = list(clients.keys())[0]
        else:
            # 选出最高分
            hiscore = 0
            tmp: list = []
            for c in clients.items():
                client: str = c[0]
                score = c[1]
                if score > hiscore:
                    hiscore = score
                    tmp.clear()
                    tmp.append(client)
                elif score == hiscore:
                    tmp.append(client)
            # 添加到结果集
            if len(tmp) > 1:
                res = self._choose_one_randomly(clients)
            else:
                res = tmp[0]

        return res

    @abstractmethod
    def _filter_clients(self, task, clients: dict) -> dict:
        """根据当前任务类型，过滤可用于分发的采集端列表"""

        # 此处可用缓存优化一下性能
        clients = self._filter_by_explicit_filters(task, clients)
        if len(clients) < 1:
            raise Exception("No client suits explicit filter")
        clients = self._filter_platform(task, clients)
        if len(clients) < 1:
            raise Exception("No client suits platform filter")
        clients = self._filter_clientbusiness(task, clients)
        if len(clients) < 1:
            raise Exception("No client suits business filter")

        if hasattr(task, 'apptype'):
            clients = self._filter_apptype(task, clients)
        if hasattr(task, 'appclassify'):
            clients = self._filter_appclassify(task, clients)
        if hasattr(task, 'tasktype'):
            clients = self._filter_tasktype(task, clients)
        return clients

    @abstractmethod
    def _filter_by_explicit_filters(self, task, clients: dict) -> dict:
        """根据显示指定的过滤器过滤采集端"""
        if not isinstance(self._explicit_filters, ExplicitFilters):
            return clients

        choises: dict = {}
        for c in clients.keys():
            c: Client = c
            if not c._statusbasic.crosswall == self._explicit_filters.crosswall:
                continue
            choises[c] = clients[c]

        # if len(choises) > 0:
        #     clients = choises
        clients = choises

        return clients

    @abstractmethod
    def _filter_platform(self, task, clients: dict) -> dict:
        """根据platform过滤可用于分发任务的采集端"""
        platform: str = None
        if hasattr(task, 'platform'):
            platform = task.platform
        elif hasattr(task, '_platform'):
            platform = task._platform
        else:
            return clients

        if not isinstance(platform, str):
            raise Exception(
                "Invalid platform for task: platfrom={}".format(platform))

        choises: dict = {}
        for c in clients.keys():
            c: Client = c
            if c._statusbasic.platform == platform:
                choises[c] = clients[c]

        # if len(choises) > 0:
        #     clients = choises
        clients = choises

        return clients

    @abstractmethod
    def _filter_clientbusiness(self, task, clients: dict) -> dict:
        """跟采集端启用的任务类型过滤采集端"""
        target_business: int = 0

        if not clientbusiness_mapping.__contains__(type(task)):
            raise Exception("Unknow task: {}".format(task))
        else:
            target_business = clientbusiness_mapping[type(task)].value

        choises: dict = {}
        for c in clients.keys():
            c: Client = c

            if not isinstance(c._statusbasic.clientbusiness, list) or \
                len(c._statusbasic.clientbusiness) < 1 or \
                c._statusbasic.clientbusiness.__contains__(0) or \
                target_business in c._statusbasic.clientbusiness:
                choises[c] = clients[c]

        # if len(choises) > 0:
        #     clients = choises
        clients = choises

        return clients

    @abstractmethod
    def _filter_apptype(self, task, clients: dict) -> dict:
        """根据apptype过滤可用于分发任务的采集端"""
        if not hasattr(task, 'apptype'):
            return clients
        apptype: int = task.apptype
        if not isinstance(apptype, int):
            raise Exception(
                "Invalid apptype for task: apptype={}".format(apptype))
        if not ALL_APPS.__contains__(apptype):
            # 不支持的apptype，返回所有client供选择
            # raise Exception(
            #     "Unknow apptype for task: apptype={}".format(apptype))
            return clients

        app: AppConfig = ALL_APPS[apptype]

        # 根据翻墙情况，apptype支持情况过滤
        choises: dict = {}
        for c in clients.keys():
            c: Client = c
            if app._crosswall and c._statusbasic.crosswall == 0:
                continue
            elif not app._crosswall and c._statusbasic.crosswall == 1:
                continue

            if not isinstance(c._statusbasic.apptype, list) or len(
                    c._statusbasic.apptype
            ) < 1 or apptype in c._statusbasic.apptype:
                choises[c] = clients[c]

        # 如果所有采集端都是翻了墙的，但任务不需要翻墙，
        # 就发到翻墙的采集端即可
        if len(choises) < 1 and not app._crosswall:
            for c in clients.keys():
                c: Client = c
                if c._statusbasic.crosswall:
                    choises[c] = clients[c]

        # if len(choises) > 0:
        #     clients = choises
        clients = choises

        return clients

    @abstractmethod
    def _filter_appclassify(self, task, clients: dict) -> dict:
        """根据appclassify过滤可用于分发任务的采集端"""
        if not hasattr(task, 'appclassify'):
            return clients
        appclassify: int = task.appclassify
        if not isinstance(appclassify, EAppClassify):
            raise Exception(
                "Invalid appclassify for task: appclassify={}".format(
                    appclassify))

        choises: dict = {}
        for c in clients.keys():
            c: Client = c
            if not isinstance(c._statusbasic.appclassify, list) or len(
                    c._statusbasic.appclassify
            ) < 1 or appclassify in c._statusbasic.appclassify:
                choises[c] = clients[c]

        # if len(choises) > 0:
        #     clients = choises
        clients = choises

        return clients

    @abstractmethod
    def _filter_tasktype(self, task, clients: dict) -> dict:
        """根据tasktype过滤可用于分发任务的采集端"""
        if not hasattr(task, 'tasktype'):
            return clients
        tasktype: int = task.tasktype
        if not isinstance(tasktype, ETaskType):
            raise Exception(
                "Invalid tasktype for task: tasktype={}".format(tasktype))

        choises: dict = {}
        for c in clients.keys():
            c: Client = c
            if not isinstance(c._statusbasic.tasktype, list) or len(
                    c._statusbasic.tasktype
            ) < 1 or tasktype in c._statusbasic.tasktype:
                choises[c] = clients[c]

        # if len(choises) > 0:
        #     clients = choises
        clients = choises

        return clients
