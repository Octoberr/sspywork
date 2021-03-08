"""task dispatch strategy"""

# -*- coding:utf-8 -*-

import traceback
from typing import Tuple

from commonbaby.helpers import helper_str

from datacontract import (ALL_APPS, AppConfig, Client, ETaskType, ETokenType,
                          Task)

from ...dbmanager.dbmanager import DbManager, SqlCondition, SqlConditions
from .strategybuibase import StrategyBuisinessBase
from .strategyconfig import StrategyConfig


class StrategyIDownTask(StrategyBuisinessBase):
    """"""
    def __init__(self):
        StrategyBuisinessBase.__init__(self)

    def match(self, task) -> bool:
        """"""
        if isinstance(task, Task):
            return True
        return False

    def _dispatch(self, task: Task, clients: dict) -> Tuple[bool, Client, str]:
        """按策略择最优采集端。\n
        task: 要分配的任务（必然为子任务对象，带有taskid和batchid）。\n
        clients: 要从中挑选出目标client的采集端 Client对象 列表。
        return:返回 唯一一个 选中的采集端对象 (bool是否成功,client,msg)"""
        succ: bool = False
        res: Client = None
        msg: str = None
        try:
            if task.tasktype == ETaskType.Input:
                # 如果是交互任务，直接找到父任务被分配到的ip
                if not isinstance(task.parenttaskid, str) or \
                    task.parenttaskid == "" or \
                    not isinstance(task.batchid, str) or \
                    task.batchid == "":
                    self._logger.error(
                        "Task dispatch relationship not found:\ntaskid={}\nbatchid={}\ntasktype={}"
                        .format(task.taskid, task.batchid, task.tasktype))
                    msg = '父任务不存在'
                    return (succ, res, msg)
                succ, res, msg = self._dispatch_to_parenttask(task, clients)
            elif task.tasktype == ETaskType.Logout:
                # 如果是登出任务，则按资源搜索有没有此任务
                succ, res, msg = self._dispatch_by_token(task, clients)
            else:
                # 此task尚未被分配过，则全部按默认策略分配到最优采集端
                succ, res, msg = self._dispatch_by_apptype(task, clients)

        except Exception:
            succ = False
            res = None
            self._logger.error("Dispatch task error:\ntaskid:%s\nerror:%s" %
                               (task.taskid, traceback.format_exc()))
        return (succ, res, msg)

    def _dispatch_to_parenttask(self, task: Task,
                                clients: dict) -> Tuple[bool, Client, str]:
        """找到指定task的parenttaskid被分配到的采集端"""
        succ: bool = False
        res: Client = None
        msg: str = None
        try:
            clientid = DbManager.get_parent_clientid_of_task(task)
            if not isinstance(clientid, str) or clientid == "" or not [
                    c._statusbasic._clientid for c in clients.keys()
            ].__contains__(clientid):
                self._logger.error(
                    "Task's parent task client not found:\ntaskid:{}\nparenttaskid:{}\nbatchid:{}\nparentbatchid:{}"
                    .format(task.taskid, task.parenttaskid, task.batchid,
                            task.parentbatchid))
                msg = '父任务所属采集端不存在'
                return (succ, res, msg)

            for c in clients.keys():
                if c._statusbasic._clientid == clientid:
                    res = c
                    break
            if res:
                succ = True

        except Exception:
            res = None
            succ = False
            self._logger.error(
                "Dispatch to parent task error:\ntaskid:{}\nerror:{}".format(
                    task.taskid, traceback.format_exc()))
            msg = '分发任务到父任务出错'
        return (succ, res, msg)

    def _dispatch_by_token(self, task: Task,
                           clients: dict) -> Tuple[bool, Client, str]:
        """搜索task的资源看有么有此条任务，并分配"""
        succ: bool = False
        res: Client = None
        msg: str = None
        try:
            # 业务逻辑：
            # 由于相同的令牌资源在分配时将会分配到固定的一个采集端，
            # 所以在根据令牌资源搜索采集端时将只会有一个结果。
            # 然后将原有任务关联到当前任务的parenttaskd和parentbatchid。

            # 过来这里必然是 tasktype=ETaskType.Logout的
            # 先看是不是可以搜索的资源类型
            if not isinstance(
                    task.tokentype, ETokenType
            ) or (task.tokentype != ETokenType.Sms and \
                 task.tokentype!=ETokenType.Pwd and \
                 task.tokentype != ETokenType.SmsPwd and \
                 task.tokentype!=ETokenType.Cookie):
                self._logger.error(
                    "Invalid tokentype for dispatching by token search:\ntaskid:{}\nbatchid:{}\ntokentype:{}"
                    .format(task.taskid, task.batchid, task.tokentype))
                msg = '无效的令牌资源类型'
                return (succ, res, msg)

            # 按资源类型搜索资源
            existtask: Task = DbManager.get_task_by_search_token(
                platform=task._platform,
                apptype=task.apptype,
                tokentype=task.tokentype,
                input_=task.input,
                preglobaltelcode=task.preglobaltelcode,
                preaccount=task.preaccount,
                globaltelcode=task.globaltelcode,
                phone=task.phone,
                account=task.account,
                password=task.password,
                url=task.url,
                host=task.host,
                cookie=task.cookie,
            )
            if not isinstance(existtask, Task):
                self._logger.error(
                    "Get client by search clientid from token searching failed:\ntaskid:{}\nbatchid:{}\nclientid:{}"
                    .format(task.taskid, task.batchid, task._clientid))
                return (succ, res, msg)

            existclient: Client = DbManager.get_client_status(
                existtask._clientid)
            if not isinstance(existclient, Client):
                self._logger.error(
                    "Got client by search clientid from token searching is invalid:\ntaskid:{}\nbatchid:{}\nclientid:{}"
                    .format(task.taskid, task.batchid, task._clientid))
                return (succ, res, msg)

            # 关联原任务taskid/batchid到当前任务parenttaskid/parentbatchid
            task.parenttaskid = existtask.taskid
            task.parentbatchid = existtask.batchid

            res = existclient
            succ = True

        except Exception:
            self._logger.error(
                "Dispatch by token error:\ntaskid:{}\nerror:{}".format(
                    task.taskid, traceback.format_exc()))
            msg = '根据令牌资源分配任务出错'
        return (succ, res, msg)

    def _dispatch_by_apptype(self, task: Task,
                             clients: dict) -> Tuple[bool, Client, str]:
        """按apptype分配给一个最优采集端"""
        succ: bool = False
        res: Client = None
        msg: str = None
        try:
            need_crosswall = True
            # 先看下是不是受支持的apptype
            if helper_str.is_none_or_empty(
                    task.apptype) or not ALL_APPS.__contains__(task.apptype):
                # 不受支持的apptype必然是邮件imap/pop下载，否则一律不支持
                # 不受支持的apptype，无法走webmail
                if task.cmd is None or \
                    task.cmd.stratagymail is None or \
                    task.cmd.stratagymail.eml_priority_protocol is None or \
                    task.cmd.stratagymail.eml_priority_protocol == 'webmail':
                    self._logger.error(
                        "Unknown apptype from task:\ntaskid:%s\napptype:%s" %
                        (task.taskid, task.apptype))
                    msg = '不支持的应用类型和协议'
                    return (succ, res, msg)
                # protocol非空，判断是否下发了邮服配置
                if not task.cmd.stratagymail.eml_priority_protocol in ["imap","pop3"] or \
                    task.cmd.stratagymail.mail_service is None:
                    self._logger.error(
                        "Require mailservice for unknown apptype:\ntaskid:%s\napptype:%s"
                        % (task.taskid, task.apptype))
                    msg = '未知的应用类型必须为IMAP/POP，且需配置邮服'
                    return (succ, res, msg)
                elif task.cmd.stratagymail.eml_priority_protocol == "imap" and \
                    (task.cmd.stratagymail.mail_service.imap_host is None or \
                     task.cmd.stratagymail.mail_service.imap_host ==""):
                    self._logger.error(
                        "Require imap server config for imap download:\ntaskid:%s\napptype:%s"
                        % (task.taskid, task.apptype))
                    msg = '缺少IMAP邮服配置'
                    return (succ, res, msg)
                elif task.cmd.stratagymail.eml_priority_protocol == "pop3" and \
                    (task.cmd.stratagymail.mail_service.pop3_host is None or \
                     task.cmd.stratagymail.mail_service.pop3_host ==""):
                    self._logger.error(
                        "Require pop3 server config for pop3 download:\ntaskid:%s\napptype:%s"
                        % (task.taskid, task.apptype))
                    msg = '缺少POP3邮服配置'
                    return (succ, res, msg)
                # 无错误情况，则拿是否需要翻墙
                need_crosswall = task.cmd.stratagymail.mail_service.crosswall
            else:
                # 受支持的apptype
                appcfg: AppConfig = ALL_APPS[task.apptype]
                need_crosswall = appcfg._crosswall

            # 过滤client，选择是否翻墙，不用翻墙的走哪都行
            if need_crosswall:
                crosswall_clients = {}
                for c, cross in clients.items():
                    c: Client = c
                    if cross == need_crosswall:
                        continue
                    crosswall_clients[c] = cross

                if len(crosswall_clients) < 1:
                    raise Exception(
                        "No Crosswall client found, iscout task need crosswall."
                    )
                clients = crosswall_clients

            # 再看数据库中是否有完全相同的令牌资源，有的话，就分配到同一个采集端
            # 返回的数据不会更新资源字段到数据库，所以前端下发的资源到这里一定是
            # 原始的一样的，直接用。
            res = DbManager.get_client_by_search_token(
                platform=task._platform,
                apptype=task.apptype,
                tokentype=task.tokentype,
                input_=task.input,
                preglobaltelcode=task.preglobaltelcode,
                preaccount=task.preaccount,
                globaltelcode=task.globaltelcode,
                phone=task.phone,
                account=task.account,
                password=task.password,
                url=task.url,
                host=task.host,
                cookie=task.cookie,
            )
            # 如果存在相同令牌资源的Task，说明已经分配过了相同的令牌资源的任务，
            # 否则说明没有被分配过，要进行新的分配
            if isinstance(res, Client):
                succ = True
                return (succ, res, msg)

            # 然后遍历每个策略进行分数计算
            clients = self._get_scores(task, clients, self.all_stgs)
            if not isinstance(clients, dict) or len(clients) < 1:
                msg = '内部计算出错'
                return (succ, res, msg)

            # highest = self._get_highest_score(clients)
            # 修改分发策略为轮询
            highest = self._get_polling_next(clients)

            if not isinstance(highest, Client):
                msg = '内部选择采集端出错'
                return (succ, res, msg)
            else:
                res = highest
                succ = True

        except Exception as ex:
            succ = False
            self._logger.info(
                "No client suites task:\nplatform={}\ntaskid={}\ntasktype={}\napptype={}\nerr:{}"
                .format(task._platform, task.taskid, task.tasktype,
                        task.apptype, traceback.format_exc()))
            msg = '内部分发任务出错:{}'.format(ex.args)
        return (succ, res, msg)
