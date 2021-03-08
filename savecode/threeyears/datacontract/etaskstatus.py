"""task status"""

# -*- coding:utf-8 -*-

from enum import Enum


class ETaskStatus(Enum):
    """任务执行状态枚举"""

    New = 0  # 新任务，没下载过的
    WaitForDeal = 1  # 已从数据库取出并排在等待队列
    Logining = 2  # 正在登陆
    LoginSucceed = 3  # 已登陆成功
    LoginFailed = 4  # 登陆失败
    Downloading = 5  # 正在下载
    DownloadSucceed = 6  # 下载全部成功
    DownloadFailed = 7  # 下载全部失败
    DownloadCompleted = 8  # 下载完成（有成功有失败的）
    Inefficient = 10  # 失效的任务
    Logout = 11  # 退出登录后的任务，不再进行下载
    TemporarilyStop = 11  # 任务被中途停止，有一个单独的状态，被恢复后会开始下载,本地使用
