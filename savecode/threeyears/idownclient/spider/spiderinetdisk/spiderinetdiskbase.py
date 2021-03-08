"""Mail 网站基类"""

# -*- coding: utf-8 -*-

import traceback
from abc import ABCMeta, abstractmethod

from datacontract.idowndataset.task import Task

from ...clientdatafeedback import INETDISKFILE
from ..appcfg import AppCfg
from ..spiderbase import SpiderBase


class SpiderInetdiskBase(SpiderBase):
    __metaclass = ABCMeta

    def __init__(self, task: Task, appcfg: AppCfg, clientid):
        SpiderBase.__init__(self, task, appcfg, clientid)
        self._root = None

    # def _get_items(self, parent):
    #     # TODO: request
    #     # itemlist
    #     # parse json
    #     for item in js:
    #         if item['type'] =='folder':
    #             currfolder = xxx
    #             parent.append(currentfolder)
    #             for inner in self._get_items(currfolder):
    #                 yield  inner
    #         else:
    #             fi = File(item)
    #             parent.append(fi)
    #             yield fi

    def _download(self) -> iter:
        """继承基类的下载方法，抽象出子类应实现的方法"""
        try:
            dirlist, url, self._root = self._get_folder()
            self._logger.info("Enter inetdisk file tree!")
            try:
                for disk in self._dirs_list(dirlist, url, self._root):
                    if isinstance(disk, INETDISKFILE):
                        yield disk
                        self._logger.info('Enter inetdisk file: {}'.format(disk.path))
                yield self._root
            except Exception:
                self._logger.error('Got inetdisk file fail: {}'.format(traceback.format_exc()))

        except Exception:
            self._logger.error("Download error: {}".format(traceback.format_exc()))

    @abstractmethod
    def _get_folder(self):
        """获取网盘结构树，返回
            dirlist: 根目录所有文件夹+文件列表
            url：根目录地址
            root： 根目录->INETDISKFILELIST
            """
        return '', '', ''

    def _dirs_list(self, dirlist, url, root):
        """递归遍历每个具体文件"""
        yield
