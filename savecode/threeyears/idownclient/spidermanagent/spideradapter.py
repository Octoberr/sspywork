"""
爬虫适配器
根据不同的任务类型分配不同的爬虫插件
create by judy 2018/10/11
"""
from commonbaby.mslog import MsLogger, MsLogManager

from datacontract import ETaskType, Task
from datacontract.appconfig import ALL_APPS


class SpiderAdapter(object):
    """
    根据传入的tasktype和apptype来决定返回的app子类列表
    """
    # 1：短信，2：账密 + 短信，3：账号注册情况查询，4：账密批量测试，5：Cookie,6:账密直接登陆 10: 交互

    __ALL_SPIDERS: dict = {}

    def __init__(self):
        self._logger: MsLogger = MsLogManager.get_logger('spideradapter')

    def adapter(self, task: Task) -> list:
        """匹配插件，直接返回插件实例列表"""
        res: list = []
        try:
            if task is None:
                return res

            # if task.apptype is None:
            #     if task.tasktype == ETaskType.CheckRegistration:
            #         res.extend([cfg for cfg in ALL_APPS.values()])
            #     else:
            #         self._logger.error("Tasktype:{} with None!".format(
            #             task.tasktype.value))
            # else:
            if ALL_APPS.__contains__(task.apptype):
                res.append(ALL_APPS[task.apptype])
            else:
                # log
                self._logger.error("Apptype not find:{}!".format(task.apptype))

        except Exception as err:
            self._logger.error("Get plugin error, err:{}".format(err))

        return res
