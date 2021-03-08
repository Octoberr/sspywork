""""""

# -*- coding:utf-8 -*-

from enum import Enum


class ECommandStatus(Enum):
    """命令本身状态"""

    # 失败
    Failed = 0
    # 成功
    Succeed = 1
    # 等待下发
    WaitForSend = 2
    # 执行中（此状态不需要回传中心，仅用于与中心的数据状态统一）
    Dealing = 3
    # 回馈当前任务进度
    Progress = 4
    # 任务被取消
    Cancelled = 8
    # 任务超时
    Timeout = 9
    # 需要手机短信验证码
    NeedSmsCode = 10
