"""
精简代码
存储验证码
create by judy 2019/01/24
"""
from datacontract import Task, ECommandStatus

from idownclient.spidermanagent.spidermanagebase import SpiderManagebase


class SpiderStoreInput(SpiderManagebase):

    def __init__(self):
        SpiderManagebase.__init__(self)

    def store_input(self, tsk: Task):
        # 存储验证码
        try:
            self._write_tgback(tsk, ECommandStatus.Succeed, "任务处理成功，验证码已提取")
            self._sqlfunc.input_insert(tsk)
        except Exception as err:
            self._logger.error("Store input error:{}".format(err))
            self._write_tgback(tsk, ECommandStatus.Succeed, "执行任务出现不可知错误")
        finally:
            if callable(tsk.on_complete):
                tsk.on_complete(tsk)
