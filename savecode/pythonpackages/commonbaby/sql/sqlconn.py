"""sql connection abstraction class"""

# -*- coding:utf-8 -*-

from abc import ABCMeta, abstractmethod


class SqlConn:
    """表示一个数据库链接"""

    __metaclass = ABCMeta

    def __init__(self, dispose_func=None):
        self._dispose_func = lambda s: s
        if callable(dispose_func):
            self._dispose_func = dispose_func

    @abstractmethod
    def execute(self, *args, **kwargs) -> object:
        """子类执行sql并返回"""
        pass

    @abstractmethod
    def commit(self):
        """提交对当前连接做的操作"""
        pass

    def close(self):
        """关闭连接"""
        self._close_sub()
        self._dispose_func(self)

    @abstractmethod
    def _close_sub(self):
        """子类关闭链接"""
        pass

    @abstractmethod
    def dispose(self):
        """子类释放链接"""
        pass
