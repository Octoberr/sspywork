"""timer test"""

# -*- coding:utf-8 -*-

import io
import time
import os
import traceback
import re

from commonbaby.httpaccess.httpaccess import HttpAccess, ManagedCookie
from commonbaby.timer.timer import Timeout, timeout
from commonbaby.helpers import helper_str, helper_time
from commonbaby.mslog import MsLogger, MsLogManager, MsFileLogConfig
from commonbaby import charsets

if __name__ == "__main__":
    try:

        tmp = helper_time.timespan_to_datestr(1523866774000)

        # f = r"F:\WorkSpace\PretendCollection\NetCore\Tests\Test\�t.txt"
        # aaa = '�'
        # aaa.encode('unicode-escape')
        f = r"F:\WorkSpace\PretendCollection\NetCore\Tests\Test"
        # ff = repr('\xfct.txt')
        nb = bytes([252, 116])
        n = nb.decode('utf-8', 'replace')
        n = n + '.txt'
        p = os.path.join(f, n)
        if os.path.isfile(p):
            print("yes")

        t = 't'
        tb = t.encode('ascii')

        s = '黷'
        # bs = s.encode('gb2312', errors='xmlcharrefreplace')
        bs = s.encode('gbk')

        ss = bs.decode('utf-8')

        print(ss)

        # raise Exception("aaaaaaa")
    except Exception as ex:
        print(ex.args)
        print(str(ex))
        traceback.print_exc()
