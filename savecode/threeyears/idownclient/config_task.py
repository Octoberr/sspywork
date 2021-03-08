"""
config of inputer
输入文件夹的配置
所有输入文件夹和输出文件夹的配置都在这里,统一配置
避免多方自行增加
"""

# -*- coding:utf-8 -*-

from idownclient.taskmanagement.taskconfig import Taskconfig

clienttaskconfig = Taskconfig(
    sqlitpath=None,
    inputpath=None,
    successpath=None,
    errorpath=None,
    outputpath=None,
    tmppath=None,
    collectclienttimes=300,
    buffsize=None,
    rootdriver=None,  # linux:'/',windows:'D:\\', None表示当前文件所在的根目录
    concurrent_number=None  # 并发处理任务数，默认为5
)
