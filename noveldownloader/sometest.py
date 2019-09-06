__name__ = 'noveldownloader'

from . import biquge
import inspect
import sys
from enum import Enum

__name__ = '__main__'


class EObjectType(Enum):
    """
    目标类型
    """
    # 域名
    Domain = 1
    # IP
    Ip = 2
    # 端口
    Port = 3
    # URL
    Url = 4
    # mail account
    MailAccount = 5
    # phone number
    PhoneNum = 6
    # 网络id
    NetId = 7
    # 未知99
    Unknown = 99


if __name__ == '__main__':
    a = {}
    for name, obj in inspect.getmembers(biquge):
        if inspect.isclass(obj):
            # if obj is novel.Novel:
            print(obj.namel)
            print(obj)

            a[EObjectType.Unknown] = obj
    print(a)
