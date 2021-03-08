"""
scan回馈数据的base文件
create by swm 2019/06/13
"""
from datacontract import IscanTask


class ScanFeedBackBase(object):

    def __init__(self, tsk: IscanTask):
        self.taskid = tsk.taskid
        # self.batchid = tsk.batchid
        self.source = tsk.source
        self.time = tsk.time_now
        self.periodnum = tsk.periodnum

