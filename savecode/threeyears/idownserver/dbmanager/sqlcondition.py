"""sql select condition"""

# -*- coding:utf-8 -*-

import threading
from enum import Enum


class ESqlOper(Enum):
    """ESqlOperator: sql 查询条件运算符枚举。
    例如： Col1=1 中的 '='"""
    # 原值 = 新值
    Equals = 1
    # 原值 < 新值
    Less = 2
    # 原值 <= 新值
    LessEquals = 3
    # 原值 > 新值
    Greater = 4
    # 原值 >= 新值
    GreaterEquals = 5
    # 原值 != 新值
    NotEquals = 6


class ESqlComb(Enum):
    """ESqlCombine: Sql 条件连接符枚举。
    例如： Col1=1 and Col2=2 中的 'and'"""
    And = 1
    Or = 2


class SqlCondition:
    """表示一个sql查询条件。以sql参数化方式组成。
    使用时需要调用：\n
    # 拿sql语句\n
    sql = cond.text_normal => Col1=?\n
    # 拿参数\n
    param = cond.param => value\n
    # 拼接到各数据库接口的参数化查询函数中\n
    # cursor.execute(sql,param)"""

    __normal_cond_map: dict = {
        ESqlOper.Equals: '=',
        ESqlOper.Less: '<',
        ESqlOper.LessEquals: '<=',
        ESqlOper.Greater: '>',
        ESqlOper.GreaterEquals: '>=',
        ESqlOper.NotEquals: '!=',
    }

    __normal_comb_map: dict = {
        ESqlComb.And: 'and',
        ESqlComb.Or: 'or',
    }

    @property
    def operator(self) -> str:
        """返回当前sql查询条件的计算符，
        例如：  Col1=1 中的 '=' """
        return SqlCondition.__normal_cond_map[self._cond]

    @property
    def combiner(self) -> str:
        """返回当前sql查询条件的条件间连接符，
        例如： Col1=1 and Col2=2 中的 'and'"""
        return SqlCondition.__normal_comb_map[self._comb]

    @property
    def text_normal(self) -> str:
        """以常规方式拼接sql查询条件"""
        return f'{self._colname}{self.operator}?'

    @property
    def param(self) -> object:
        """当前条件的参数值"""
        return self._val

    def __init__(self,
                 colname: str,
                 val,
                 cond: ESqlOper = ESqlOper.Equals,
                 comb: ESqlComb = ESqlComb.And):
        if not isinstance(colname, str) or colname == "":
            raise Exception("Invalid sql condition param 'colname'")
        # val不做验证
        # if val is None:
        #     raise Exception("Invalid sql condition param 'val'")
        if not isinstance(cond, ESqlOper):
            raise Exception("Invalid sql condition param 'cond'")
        if not isinstance(comb, ESqlComb):
            raise Exception("Invalid sql condition param 'comb'")

        self._colname: str = colname
        self._val = val
        self._cond: ESqlOper = cond
        self._comb: ESqlComb = comb

    def __repr__(self):
        return "{}{}{}".format(self._colname, self._cond, self._val)


class SqlConditions:
    """表示一组sql查询条件\n
    *conds: 一组SqlCondition对象
    使用时需要调用：\n
    # 拿sql语句\n
    sql = conds.text_normal => Col1=? and Col2=?\n
    # 拿参数\n
    params = conds.params => list(value1,value2)\n
    # 拼接到各数据库接口的参数化查询函数中\n
    # cursor.execute(sql,params)"""

    @property
    def cond_count(self) -> int:
        """返回当前sql查询条件集中的条件数量"""
        with self.__conds_locker:
            return len(self.__conds)

    @property
    def text_normal(self):
        """以常规方式拼接sql查询条件组"""
        sql = ''
        with self.__conds_locker:
            c = None
            for c in self.__conds:
                c: SqlCondition = c
                csql = c.text_normal
                sql += ' {} {}'.format(csql, c.combiner)
            if not c is None:
                sql = sql.rstrip(c.combiner).strip()

        return sql

    @property
    def params(self) -> list:
        """按拼接sql的顺序返回每个单个sql查询条件的参数化查询的参数param"""
        params: list = []
        with self.__conds_locker:
            for c in self.__conds:
                c: SqlCondition = c
                params.append(c.param)
        return params

    def __init__(self, *conds: SqlCondition):
        """"""
        self.__conds: list = []
        self.__conds_locker = threading.RLock()

        if len(conds) < 1:
            return
        self.append_conditions(*conds)

    def append_conditions(self, *conds: SqlCondition):
        """将一些SqlCondition条件对象添加到当前SqlConditions对象末尾，
        并返回当前SqlConditions对象本身"""
        if len(conds) < 1:
            return
        with self.__conds_locker:
            for c in conds:
                if not isinstance(c, SqlCondition):
                    raise Exception("Invalid SqlCondition: {}".format(c))
                # 不检查是否重复，直接添加
                self.__conds.append(c)
        return self

    def __iter__(self):
        return self.__conds.__iter__()

    def __repr__(self):
        return self.text_normal
