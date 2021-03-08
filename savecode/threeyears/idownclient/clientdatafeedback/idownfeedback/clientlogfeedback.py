"""
task下载日志的回馈文件
create by judy 20190517
"""
from datacontract.idowndataset import Task
from datacontract.outputdata import EStandardDataType

from .feedbackbase import FeedDataBase
from commonbaby.helpers.helper_str import base64format


class ClientLog(FeedDataBase):

    def __init__(self, task: Task, clientid, apptype, log):
        FeedDataBase.__init__(self, '.client_log', EStandardDataType.Client_log, task, apptype, clientid)
        self.sequence = task.sequence
        self.log = log

    def _get_output_fields(self):
        self.append_to_fields('sequence', self.sequence)
        self.append_to_fields('log', base64format(self.log))
        return self._fields
