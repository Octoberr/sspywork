"""social 网站基类"""

# -*- coding: utf-8 -*-

import traceback
from abc import ABCMeta, abstractmethod

from datacontract.idowndataset.task import Task
from idownclient.clientdatafeedback import CONTACT, CONTACT_ONE, ICHATGROUP, ICHATGROUP_ONE, ICHATLOG, ICHATLOG_ONE
from ..spiderbase import SpiderBase


class SpiderSocialBase(SpiderBase):
    __metaclass = ABCMeta

    def __init__(self, task: Task, appcfg, clientid):
        SpiderBase.__init__(self, task, appcfg, clientid)

    def _download(self) -> iter:
        """
        每个下载任务的子类必须实现的方法
        :return:
        """
        try:

            # 获取联系人
            self._logger.info("Get contacts: %s %s %s" %
                              (self._userid, self._username, self._phone))
            cts: CONTACT = CONTACT(self._clientid, self.task,
                                   self._appcfg._apptype)
            for ct in self._get_contacts():
                if not isinstance(ct, CONTACT_ONE):
                    yield ct
                else:
                    cts.append_innerdata(ct)
                    self._logger.info(
                        "Got contact: %s %s" % (ct._contactid, ct.nickname))
                    # 获取联系人聊天记录
                    logs: ICHATLOG = ICHATLOG(self._clientid, self.task,
                                              self._appcfg._apptype)
                    for log in self.__get_contact_chatlogs(ct):
                        if isinstance(log, ICHATLOG_ONE):
                            logs.append_innerdata(log)
                        else:

                            yield log
                    self._logger.info("Got %s chatlogs for %s" %
                                      (logs.innerdata_len, ct.nickname))
                    if logs.innerdata_len > 0:
                        yield logs

            if cts.innerdata_len > 0:
                self._logger.info("Got %s contacts of account %s" %
                                  (cts.innerdata_len, self._account))
                yield cts

            # 获取群组
            self._logger.info(
                "Get groups: %s %s" % (self._userid, self._username))
            grps: ICHATGROUP = ICHATGROUP(self._clientid, self.task,
                                          self._appcfg._apptype)
            for grp in self._get_groups():

                if not isinstance(grp, ICHATGROUP_ONE):
                    yield grp
                else:
                    grps.append_innerdata(grp)
                    self._logger.info(
                        "Got group: %s %s" % (grp._groupid, grp.groupname))

                    # 获取群组成员列表作为联系人返回
                    gcts: CONTACT = CONTACT(self._clientid, self.task,
                                            self._appcfg._apptype)
                    for gt in self._get_group_contacts(grp):
                        if not isinstance(gt, CONTACT_ONE):
                            yield gt
                        else:
                            gcts.append_innerdata(gt)
                    if gcts.innerdata_len > 0:
                        # 每一个群组返回一次群成员列表
                        self._logger.info(
                            "Got {} members in group {} {} of account {}".
                            format(gcts.innerdata_len, self._account,
                                   grp._groupid, grp.groupname))
                        yield gcts

                    # 获取群聊记录
                    logs: ICHATLOG = ICHATLOG(self._clientid, self.task,
                                              self._appcfg._apptype)
                    for log in self.__get_group_chatlogs(grp):
                        if isinstance(log, ICHATLOG_ONE):
                            logs.append_innerdata(log)
                        else:
                            yield log

                    self._logger.info("Got %s chatlogs for %s" %
                                      (logs.innerdata_len, grp.groupname))
                    if logs.innerdata_len > 0:
                        yield logs

            if grps.innerdata_len > 0:
                self._logger.info("Got %s groups of account %s" %
                                  (grps.innerdata_len, self._account))
                yield grps

        except Exception:
            self._logger.error("Social app download error:{}".format(
                traceback.format_exc()))

    def __get_contact_chatlogs(self, ct: CONTACT_ONE) -> iter:
        # self._logger.info("Get chatlogs for contact: %s %s" %
        #                   (self._userid, ct.nickname))
        return self._get_contact_chatlogs(ct)

    @abstractmethod
    def _get_contact_chatlogs(self, ct: CONTACT_ONE) -> iter:
        """获取给予的联系人的聊天记录，返回ICHATLOG_ONE"""
        return []

    @abstractmethod
    def _get_groups(self) -> iter:
        """获取群组信息，返回 ICHATGROUP_ONE 对象"""
        return []

    def __get_group_chatlogs(self, grp: ICHATGROUP_ONE) -> iter:
        # self._logger.info("Get chatlogs for group: %s %s" %
        #                   (self._userid, grp.groupname))
        return self._get_group_chatlogs(grp)

    @abstractmethod
    def _get_group_chatlogs(self, grp: ICHATGROUP_ONE) -> iter:
        """获取指定群组内的聊天记录，返回ICHATLOG_ONE"""
        return []

    @abstractmethod
    def _get_group_contacts(self, grp: ICHATGROUP_ONE) -> iter:
        return []
