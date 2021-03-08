"""local proxy pool"""

# -*- coding:utf-8 -*-

import threading
import time
import traceback

from ..mslog.loghook import LogHook
from ..sql import ESqlOper, SqlCondition, SqlConditions, table_locker_manual
from .eproxyanonymity import EProxyAnonymity
from .eproxytype import EProxyType
from .proxydb import ProxyDB
from .proxydbconfig import ProxyDbConfig
from .proxyitem import ProxyItem
from .proxysetting import ProxySetting


class ProxyPool:
    """本地代理IP池"""

    _UnknowAnonymous: str = 'UnknowAnonymous'
    _UnknowCountry: str = "UnknowCountry"
    _UnknowMethod: str = "UnknowMethod"
    _UnkownProxyType: str = "UnknowProxyType"

    @property
    def full_filled(self) -> bool:
        """返回当前代理池是否已填满"""
        # 单位应该是秒，2秒检查一次数据库
        currtime = time.time()
        # 没满，且时间到达，则直接返回
        if not self._full_filled and currtime - self._last_check_time < 1:
            return self._full_filled
        with self._full_check_locker:
            if not self._full_filled and currtime - self._last_check_time < 1:
                return self._full_filled
            self._check_db_fullfilled()
        return self._full_filled

    @property
    def curr_proxy_count(self) -> int:
        """返回当前代理池中的代理IP总数量"""
        return self._current_item_count

    def __init__(
            self,
            dbconfig: ProxyDbConfig = None,
            maxitemcount: int = 100,
            logger_hook: callable = None,
    ):
        if not isinstance(maxitemcount, int) or maxitemcount < 0:
            raise Exception("Invalid maxitemcount")

        self._logger: LogHook = LogHook(logger_hook)

        self._maxitemcount = maxitemcount

        self._current_item_count: int = 0
        self._full_filled: bool = False
        self._last_check_time: float = 0
        self._full_check_locker = threading.RLock()

        # 先用内存表，，后面用着看需求再用其他的，或者用redis或es都行
        self._dbconfig: ProxyDbConfig = dbconfig
        self._tbproxy: ProxyDB = ProxyDB(
            dbcfg=self._dbconfig,
            logger_hook=logger_hook,
        )

#######################################
# data count check

    def _check_db_fullfilled(self):
        """查询数据库代理IP总条数"""
        try:
            result = self._tbproxy.execute("TbProxy",
                                           "select count() from TbProxy")

            with self._full_check_locker:
                if not result is None:
                    self._current_item_count = result[0]

                if self._current_item_count >= self._maxitemcount:
                    self._full_filled = True
                else:
                    self._full_filled = False

                self._last_check_time = time.time()
        except Exception:
            self._logger.error("Check proxydb fullfilled error: {}".format(
                traceback.format_exc()))

#######################################
# Add/update

# TbProxy
# 所有列
# IP
# Port
# IPType
# ProxyType
# Anonymous
# Country
# AliveSec
# UpdateTime
# CreateTime

    def append_proxyitem(self, proxyitem: ProxyItem,
                         update: bool = True) -> bool:
        """向当前代理池添加一个代理IP对象。返回是否添加成功（可能池IP数到达上限，导致添加失败）\n
        proxyitem: 代理对象\n
        update: 若IP已存在是否更新，默认True，否则若IP已存在则放弃"""
        res: bool = False
        try:
            # 先一条一条入了。。
            # 后面有空再开个新函数写 临时表过滤并批量更新插入操作...

            if self.full_filled:
                return res

            if update:
                res = self._tbproxy.save_new_proxyitem(proxyitem)
            else:
                exist_row: dict = self._tbproxy.select_proxyitem(
                    SqlConditions(
                        SqlCondition(colname="IP", val=proxyitem._ip),
                        SqlCondition(colname="Port", val=proxyitem._port),
                        SqlCondition(
                            colname="IP", val=proxyitem._proxytype.value),
                    ))

                if not isinstance(exist_row, dict) or len(exist_row) < 1:
                    res = self._tbproxy.save_new_proxyitem(proxyitem)

        except Exception:
            self._logger.error("Append proxyitem error: {}".format(
                traceback.format_exc()))
        return res


#######################################
# Select

# TbProxy
# 所有列
# IP
# Port
# IPType
# ProxyType
# Anonymous
# Country
# AliveSec
# UpdateTime
# CreateTime

    def __generate_sqlcondition(self, setting: ProxySetting) -> SqlConditions:
        conds: SqlConditions = SqlConditions()
        if isinstance(setting.port,
                      int) and setting.port > 0 and setting.port < 65535:
            conds.append_conditions(
                SqlCondition(colname="Port", val=setting.port))
        if isinstance(setting.proxytype, EProxyType):
            conds.append_conditions(
                SqlCondition(colname="ProxyType", val=setting.proxytype.value))
        if isinstance(setting.anonymous, EProxyAnonymity):
            conds.append_conditions(
                SqlCondition(colname="Anonymous", val=setting.anonymous.value))

    def get_one_by_setting(self, setting: ProxySetting) -> ProxyItem:
        """返回指定配置的代理IP对象，并将其从库中移除，若没有则返回None"""
        res: ProxyItem = None
        try:
            conds: SqlConditions = self.__generate_sqlcondition(setting)
            fields: dict = self._tbproxy.pop_proxyitem(conds)
            if not isinstance(fields, dict) or len(fields) < 1:
                return res

            res = ProxyItem.create_from_dict(fields)
        except Exception:
            self._logger.error("Get proxyitem error: {}".format(
                traceback.format_exc()))
        return res

    def get_one_crosswall(
            self,
            proxytype: EProxyType = EProxyType.HTTP,
            ssl: bool = True,
    ) -> ProxyItem:
        """返回一个国外的代理IP对象，并将其从库中移除，若没有则返回None"""
        res: ProxyItem = None
        try:

            conds: SqlConditions = SqlConditions(
                SqlCondition(
                    colname="CountryCode", val="CN", cond=ESqlOper.NotEquals))
            if isinstance(proxytype, EProxyType):
                conds.append_conditions(
                    SqlCondition(colname="ProxyType", val=proxytype.value))
            if isinstance(ssl, bool):
                conds.append_conditions(SqlCondition(colname="IsSsl", val=ssl))

            fields: dict = self._tbproxy.pop_proxyitem(conds)
            if not isinstance(fields, dict) or len(fields) < 1:
                return res

            res = ProxyItem.create_from_dict(fields)
        except Exception:
            self._logger.error("Get proxyitem error: {}".format(
                traceback.format_exc()))
        return res

    def get_one_internal(
            self,
            proxytype: EProxyType = EProxyType.HTTP,
            ssl: bool = True,
    ) -> ProxyItem:
        """返回一个国内的代理IP对象，并将其从库中移除，若没有则返回None"""
        res: ProxyItem = None
        try:

            conds: SqlConditions = SqlConditions(
                SqlCondition(colname="CountryCode", val="CN"))
            if isinstance(proxytype, EProxyType):
                conds.append_conditions(
                    SqlCondition(colname="ProxyType", val=proxytype.value))
            if isinstance(ssl, bool):
                conds.append_conditions(SqlCondition(colname="IsSsl", val=ssl))

            fields: dict = self._tbproxy.pop_proxyitem(conds)
            if not isinstance(fields, dict) or len(fields) < 1:
                return res

            res = ProxyItem.create_from_dict(fields)
        except Exception:
            self._logger.error("Get proxyitem error: {}".format(
                traceback.format_exc()))
        return res

    def _pop_items_verify_required(
            self,
            recheck_interval_sec: float = 600,
    ) -> iter:
        """返回需要重新检验的代理IP对象迭代器\n
        recheck_interval_sec: 重新检验时间间隔，秒，默认10分钟检验一次"""

        try:

            for fields in self._tbproxy.execute_search_all(
                    "TbProxy", "select * from TbProxy"):
                try:
                    if not isinstance(fields, dict) or len(fields) < 1:
                        continue
                    proxyitem: ProxyItem = ProxyItem.create_from_dict(fields)
                    if proxyitem.lastverifytime is None or \
                        proxyitem.lastverifytime + recheck_interval_sec <= time.time():
                        cnt = self._tbproxy.delete_proxyitem(
                            SqlConditions(
                                SqlCondition(colname="IP", val=proxyitem.ip),
                                SqlCondition(
                                    colname="Port", val=proxyitem.port),
                                SqlCondition(
                                    colname="ProxyType",
                                    val=proxyitem.proxytype.value),
                            ))
                        if cnt < 1:
                            self._logger.error(
                                "Delete proxyitem verify required form TbProxy failed: {}:{}    {}"
                                .format(proxyitem.ip, proxyitem.port,
                                        proxyitem.proxytype.name))
                        else:
                            yield proxyitem

                except Exception as ex:
                    self._logger.error(
                        "Select all items verify required form TbProxy error: {}"
                        .format(ex.args))

        except Exception:
            self._logger.error("Pop items verify required error: {}".format(
                traceback.format_exc()))
