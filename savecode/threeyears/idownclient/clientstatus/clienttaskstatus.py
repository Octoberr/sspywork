"""
采集端任务状态统计
直接在数据库查找数据
create by judy 2018/10/22

update by judy 2019/03/05
更改统一输出为output
"""
from datetime import datetime
import time
import traceback

import pytz

from datacontract import ETaskStatus
from datacontract.clientstatus.statustask import StatusTask
from idownclient.clientdbmanager import DbManager
from idownclient.config_task import clienttaskconfig
from outputmanagement import OutputManagement
from ..clientdbmanager.sqlcondition import (ESqlComb, SqlCondition,
                                            SqlConditions)


class ClientTaskStatus(object):

    def __init__(self):
        self._taskstatus = {}
        self._sqlres = DbManager
        self.times = clienttaskconfig.collect_client_times  # 默认是5秒搜集一次

    def get_task_status_info(self):
        self._taskstatus['time'] = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        self._taskstatus['clientid'] = 'clientid'
        # 正在执行任务的数量
        # tasking = self._sqlres.query_task('taskstatus', ETaskStatus.New.value)
        tasking = self._sqlres.query_task(
            SqlConditions(
                SqlCondition(
                    colname='taskstatus',
                    val=ETaskStatus.New.value,
                    comb=ESqlComb.Or),
        ))
        self._taskstatus['tasknewcnt'] = len(tasking)
        # taskwaiting = self._sqlres.query_task('taskstatus', ETaskStatus.WaitForDeal.value)
        taskwaiting = self._sqlres.query_task(
            SqlConditions(
                SqlCondition(
                    colname='taskstatus',
                    val=ETaskStatus.WaitForDeal.value,
                    comb=ESqlComb.Or),
        ))
        self._taskstatus['taskwaitingcnt'] = len(taskwaiting)
        # taskdownloading = self._sqlres.query_task('taskstatus', ETaskStatus.Downloading.value)
        taskdownloading = self._sqlres.query_task(
            SqlConditions(
                SqlCondition(
                    colname='taskstatus',
                    val=ETaskStatus.Downloading.value,
                    comb=ESqlComb.Or),
        ))
        self._taskstatus['taskdownloadingcnt'] = len(taskdownloading)
        return

    def start(self):
        while True:
            try:
                self.get_task_status_info()
                lines = StatusTask(self._taskstatus)
                OutputManagement.output(lines)
            except:
                print(f"Collect taskinfo error,err:{traceback.format_exc()}")
            finally:
                time.sleep(self.times)
