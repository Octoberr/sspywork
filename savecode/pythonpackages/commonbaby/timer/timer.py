"""timer"""

# -*- coding:utf-8 -*-

import time
import traceback

from .kthread import KThread


class Timeout(Exception):
    """function run timeout"""


def timeout(seconds):
    """超时装饰器，指定超时时间
    若被装饰的方法在指定的时间内未返回，则抛出Timeout异常"""

    def timeout_decorator(func):
        """真正的装饰器"""

        def _new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
            result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))

        def _(*args, **kwargs):
            result = []
            new_kwargs = {  # create new args for _new_func, because we want to get the func return val to result list
                'oldfunc': func,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }
            thd = KThread(target=_new_func, args=(), kwargs=new_kwargs)
            thd.start()

            thd.join(seconds)
            alive = thd.isAlive()

            thd.kill()  # kill the child thread
            if alive:
                raise Timeout(
                    u'function run too long, timeout %d seconds.' % seconds)
            else:
                return result[0]

        _.__name__ = func.__name__
        _.__doc__ = func.__doc__
        return _

    return timeout_decorator


@timeout(3)
def _runsomething(sec: int = 5):

    flag = 0
    while flag <= sec:
        flag += 1
        time.sleep(1)


if __name__ == "__main__":
    try:
        _runsomething()

    except Exception as ex:
        traceback.print_exc()
