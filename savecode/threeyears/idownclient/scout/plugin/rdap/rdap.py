"""rdap api for ipwhois/asn/entities .etc search"""

# -*- coding:utf-8 -*-

#########################
# 需要实现的功能
# 1. 根据ip所属国家找到所属5大分配机构中的一个？（可略过，直接请求某一个，会自动跳转）
# 2. 查询ipwhois记录，包括ipwhois历史（ipwhois包没找到查历史的接口）
# 3. 解析，并构造数据
# 4. 参考ipwhois包，在服务端报访问频率过快时睡眠后重试。

import json
import traceback

from ....clientdatafeedback.scoutdatafeedback import (IPWhoisData,
                                                      IPWhoisEntityData)
from ..scoutplugbase import ScoutPlugBase


class Rdap(ScoutPlugBase):
    """rdap api"""

    __remark = "其实应该是有IP路由的，对不同ip地址应使用对应协议查找所属IANA或rdap地址，然后再进行rdap查询"

    def __init__(self):
        ScoutPlugBase.__init__(self)
