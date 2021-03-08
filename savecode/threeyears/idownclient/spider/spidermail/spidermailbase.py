"""Mail 网站基类"""

# -*- coding: utf-8 -*-

import traceback
from datetime import datetime
from abc import ABCMeta, abstractmethod

from datacontract.idowndataset.task import Task

from ...clientdatafeedback import Folder
from ..appcfg import AppCfg
from ..spiderbase import SpiderBase


class SpiderMailBase(SpiderBase):
    __metaclass = ABCMeta

    def __init__(self,
                 task: Task,
                 appcfg: AppCfg,
                 clientid,
                 logger_name_ext: str = ""):
        SpiderBase.__init__(self, task, appcfg, clientid,logger_name_ext)
        # 这里没有的值都应该给默认值，但是因为有任务会测试登陆导致加载的设置是不全的
        self.email_folder_filter: list = self.task.cmd.stratagymail.eml_folders_filter
        self.email_download_limit: dict = self.task.cmd.stratagymail.eml_download_limit
        # 允许邮件下载出错的次数，需要子类实现
        self.email_fail_times: int = self.task.cmd.stratagymail.eml_failures_times
        # 下载邮件大小限制，定义的是MB，需要转换为B
        self.email_file_size_limit = int(
            self.task.cmd.stratagy.data_limit_size) * 1024 * 1024
        # 下载邮件的时间范围，单位是换算成秒
        self.email_time_range = int(
            self.task.cmd.stratagy.data_limit_time) * 86400
        self.now = datetime.utcnow()

    def __judge_download_email(self, mail):
        """
        判断单个邮件邮件是否满足当前下载条件
        :param mail:
        :return:
        False 表示不下载
        True 表示下载
        默认下载
        """
        res = True
        # 下载邮件大小限制,如果没有拿到邮件的大小和没有设置邮件大小限制那么邮件还是会下载回来
        try:
            if int(mail.stream_length) != 0 and 0 < self.email_file_size_limit < int(
                       mail.stream_length):
                return False
            # 下载邮件时间限制
            # 没有拿到下载时间，这封邮件会下载回来
            if not isinstance(mail.sendtime, datetime):
                return res
            time_r = datetime.utcnow().timestamp() - mail.sendtime.timestamp()

            # 这里是超出了时间限制，所以就不要这封邮件了
            if 0 < self.email_time_range < time_r:
                return False
        except:
            self._logger.error(traceback.format_exc())
        # 其他没考虑的情况先下载
        return res

    def _download(self) -> iter:
        """
        继承基类的下载方法，抽象出子类应实现的方法
        使用当前流程才能应用下载设置，否则数据可能不会回来
        """
        # 获取需要过滤的文件夹长度
        filter_length = len(self.email_folder_filter)
        try:
            self._logger.info("Start getting contacts")
            for data in self._get_contacts():
                yield data

            self._logger.info("Start getting mails")
            for folder in self._get_folders():
                # 定义这个文件夹中已下载的邮件数
                # 邮箱文件夹过
                if filter_length <= 0:
                    pass
                else:
                    if folder.name in self.email_folder_filter:
                        # 过滤文件夹
                        continue
                self._logger.info(f"Enter folder: {folder.name}")
                # 限制下载
                if self.email_download_limit.__contains__(folder.name):
                    total_downloads = int(
                        self.email_download_limit.get(folder.name))
                    has_download_count = 0
                else:
                    total_downloads = -1
                    has_download_count = -1
                try:
                    for mail in self._get_mails(folder):

                        if not self.__judge_download_email(mail):
                            continue
                        # 大于0表示有限制
                        if total_downloads > 0 and has_download_count > 0:
                            has_download_count += 1
                            if has_download_count > total_downloads:
                                break

                        yield mail
                except:
                    self._logger.error("Get mails error: {} {}".format(
                        folder.name, traceback.format_exc()))
        except:
            self._logger.error("Download error: {}".format(
                traceback.format_exc()))

    @abstractmethod
    def _get_folders(self) -> iter:
        """获取邮箱文件夹，返回Folder对象"""
        return []

    @abstractmethod
    def _get_mails(self, folder: Folder) -> iter:
        """获取给予的邮箱文件夹里的邮件，返回EML对象"""
        return []
