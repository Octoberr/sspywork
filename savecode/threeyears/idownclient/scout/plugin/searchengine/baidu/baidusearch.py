"""
百度搜索
create by judy 2019/11/11
"""
import math
import traceback

from datacontract.iscoutdataset import IscoutTask
from idownclient.clientdatafeedback.scoutdatafeedback import (SearchEngine,
                                                              ScreenshotSE,
                                                              ScreenshotUrl,
                                                              Phone,
                                                              Email)
from idownclient.config_spiders import searchconfig
from .baidu import BaiDu
from ...scoutplugbase import ScoutPlugBase
from ...urlinfo import UrlInfo


class BaiDuSearch(ScoutPlugBase):

    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        self.task = task
        self.search_limit = searchconfig.get('reslimit', 10)
        # self.uinfo = UrlInfo(self.task)

    def get_search_link(self, query: str):
        """
        百度获取search link的方法
        :param query:
        :return:
        """
        page: int = math.ceil(self.search_limit / 10)

        # bsearch = MagicBaidu()
        # for i in range(page):
        #     try:
        #         for link in bsearch.search_url(query=query, start=i * 10):
        #             # print(mb.get_real_url(url))
        #             self._logger.debug(f"Baidu search {query}, get a link {link}.")
        #             yield link
        #         self.task.success_count()
        #     except:
        #         self.task.fail_count()
        #         self._logger.error(f"Get baidu {i + 1} page error, err:{traceback.format_exc()}")
        #         continue
        baidu = BaiDu()
        links = baidu.get_reslinks(query)
        # 搜索引擎出错了返回的是None
        if links is not None:
            self.task.success_count()
            for link in links:
                self._logger.debug(f"Baidu search {query}, get a link {link}")
                yield link
        else:
            self.task.fail_count()

    def get_baidu_search_res(self, query, level, reason=None):
        """
        这是拿百度搜索引擎拿到的link去查相关数据
        :param query:
        :param level:
        :param reason:
        :return:
        """
        uinfo = UrlInfo(self.task)
        for ulink in self.get_search_link(query):
            # ulink为google search的搜索结果url
            try:
                search_res = SearchEngine(self.task, level, query, ulink, reason)
                # 下载网页
                for data in uinfo.visit_url(ulink, level, reason):
                    if data is None:
                        continue
                    datatype = data[-1]
                    if datatype == 'homecode':
                        search_res.page = data[0]
                    elif datatype == 'summary':
                        search_res.title = data[0]
                        search_res.meta = data[1]
                    elif datatype == 'screenshot':
                        surl: ScreenshotUrl = data[0]
                        if not isinstance(surl, ScreenshotUrl):
                            # 搜索引擎接口的返回数据不是 URL侦查里的 screenshoturl
                            # 而是screenshotse，两者有区别就是后者多了个
                            # keyword字段且为必要。
                            # 且这里调用 uinfo.visit_url 返回的必须是ScreenshotUrl
                            yield surl
                        else:
                            se = ScreenshotSE(self.task, level,
                                              self.task._object,
                                              self.task._objecttype,
                                              surl.url, query)
                            se.stream = surl.stream
                            yield se
                    # 新镇email和phone
                    elif datatype == 'phone':
                        phone: Phone = data[0]
                        yield phone
                    elif datatype == 'email':
                        email: Email = data[0]
                        yield email

                search_res.source = reason
                if search_res.title is not None or search_res.page is not None:
                    yield search_res
            except:
                self._logger.error(
                    f"Get link info error, err:{traceback.format_exc()}")
                continue

        # 最后手动关闭下浏览器
        del uinfo
