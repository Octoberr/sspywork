"""
用于cookie保活任务
create by jufy
2019/05/13
"""

from idownclient.spidermanagent.spidermanagebase import SpiderManagebase
from idownclient.spider.spiderbase import SpiderBase
from datacontract.apps.appbase import AppConfig


class SpiderCookieKeep(SpiderManagebase):

    def __init__(self):
        SpiderManagebase.__init__(self)

    def cookie_keep(self, task):
        appcfg: AppConfig = self._spideradapter.adapter(task)[0]
        if not isinstance(appcfg, AppConfig):
            self._logger.info("No spider match:\nbatchid:{}\ntasktpe:{}\napptype:{}".format(
                task.batchid, task.tasktype.name, task.apptype))
            return
        spider: SpiderBase = appcfg._appclass(task, self._get_appcfg(appcfg), self._clientid)
        res = spider.keep_cookie_live()
        return res
