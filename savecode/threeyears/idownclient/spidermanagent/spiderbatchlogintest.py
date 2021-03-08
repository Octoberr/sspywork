"""
精简代码
账密批量测试
create by judy 2019/01/24
"""
from datacontract import Task
from idownclient.spidermanagent.spidermanagebase import SpiderManagebase


class SpiderBatchLoginTest(SpiderManagebase):

    def __init__(self):
        SpiderManagebase.__init__(self)

    # todo
    def login_batch_test(self, tsk: Task):
        # 待处理
        # 1、解析账密文件
        # 2、批量使用账密测试网站
        # 3、生成回馈文件
        print("to do")
        tsk.on_complete(tsk)
        pass
