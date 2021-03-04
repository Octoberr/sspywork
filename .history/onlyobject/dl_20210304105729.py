"""
单例模式
"""


import time
import threading


class Singleton(object):
    _instance_lock = threading.Lock()

    def __init__(self):
        time.sleep(1)

    @classmethod
    def instance(cls, *args, **kwargs):
        with Singleton._instance_lock:
            if not hasattr(Singleton, "_instance"):
                Singleton._instance = Singleton(*args, **kwargs)
        return Singleton._instance


def task(arg):
    obj = Singleton.instance()
    print(obj)


for i in range(10):
    t = threading.Thread(
        target=task,
        args=[
            i,
        ],
    )
    t.start()
time.sleep(20)
obj = Singleton.instance()
print(obj)