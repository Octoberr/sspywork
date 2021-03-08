"""singleton"""

# -*- coding:utf-8 -*-

import threading


class SingletonInstance(object):
    """单例模式类型基类\n
    继承于此类的class会成为单例模式，多次实例化只会返回同一个实例，
    但多次使用不同的初始化参数进行class实例化c时，后一次实例化的属性参数
    总会覆盖前一次实例化的属性参数，也就是多次实例化class时属性参数会被覆盖\n
    Help implement singleton.\n
    Useage:
        class A(Singleton):
            pass
        
        # OK, now A is singleton."""

    __inst_locker = threading.RLock()

    def __new__(cls, *args, **kwargs):
        if hasattr(cls, '_singleton_instance'):
            return cls._singleton_instance

        with SingletonInstance.__inst_locker:
            if hasattr(cls, '_singleton_instance'):
                return cls._singleton_instance

            orig = super(SingletonInstance, cls)
            cls._singleton_instance = orig.__new__(cls)
            cls.__init__(orig, *args, **kwargs)

        return cls._singleton_instance


__instances: dict = {}
__instances_locker = threading.RLock()


def SingletonDecorator(cls):
    """单例模式装饰器\n
    被此装饰器装饰的class会成为单例，
    后面随便实例化多少个class对象，都只会有一个实例，
    且多次实例化只有第一次实例化生效\n
    Help implement singleton.\n
    Useage:
        @SingletonDecorator
        class A(object):
            pass
        
        # OK, now A is singleton."""

    SingletonDecorator.__doc__ = cls.__doc__ + '\n' + SingletonDecorator.__doc__

    def _singleton(*args, **kwargs):
        """"""

        if __instances.__contains__(cls):
            return __instances[cls]

        with __instances_locker:

            if __instances.__contains__(cls):
                return __instances[cls]

            inst = cls(*args, **kwargs)
            __instances[cls] = inst
            return inst

    _singleton.__doc__ = cls.__doc__
    return _singleton