"""
bing search
类似于baidu，但是功能吊打bing
create by judy 2019/11/12
"""
import traceback
import time
import requests
import math

from idownclient.config_spiders import searchconfig
from ...scoutplugbase import ScoutPlugBase
from idownclient.clientdatafeedback.scoutdatafeedback import (SearchEngine,
                                                              SearchFile,
                                                              ScreenshotSE,
                                                              ScreenshotUrl,
                                                              Phone,
                                                              Email)
from datacontract.iscoutdataset import IscoutTask
from .azbing import AzBingApi
from ...urlinfo import UrlInfo


class BingSearchEngine(ScoutPlugBase):

    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        self.task = task
        self.search_limit = searchconfig.get('reslimit', 10)

    def get_search_link(self, query: str):
        """
        bing获取search link的方法
        :param query:
        :return:
        """
        page: int = math.ceil(self.search_limit / 10)
        for i in range(page):
            try:
                for data in AzBingApi.bing_web_search(query, i * 10):
                    link = data.get('url')
                    self._logger.debug(f"Bing search {query}, get a link {link}")
                    yield link
                # 这个bing这样就是正常的，如果超时会出错
                self.task.success_count()
            except:
                self.task.fail_count()
                self._logger.error(f"Get bing {i + 1} page error, err:{traceback.format_exc()}")
                continue

    def __download_file(self, link, level, reason=None):
        """
        如果是使用的文件那么会去下载文件,
        这里返回的应该是searchengine file的对象
        :param link:
        :param level:
        :param reason:
        :return:
        """
        suffix_info = link.split('.')
        suffix = suffix_info[-1]
        try:
            response = requests.request("GET", link, stream=True)
            status_code = response.status_code
            # 200才表示拿到了这数据，其他都是需要跳转的
            if status_code == 200:
                sf = SearchFile(self.task, level, self.task._object, self.task._objecttype, link)
                sf.filename = f"{int(time.time() * 1000)}.{suffix}"
                response.raw.decode_content = True
                sf._stream = response.raw
                self._logger.debug(f"Download file link {link} successed")
                return sf
        except:
            self._logger.error(
                f"Download {link} error, err:{traceback.format_exc()}")
            return None

    def get_bing_search_res(self, query, level, reason=None):
        """
        这是拿bing搜索引擎拿到的link去查相关数据
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
                # 这里要分两种情况，一种是去下载网站，一种是去下载文件
                if 'filetype' in query and len(ulink.split('.')) > 1:
                    # 只有符合这种情况才会去下载文件
                    sf = self.__download_file(ulink, level, reason)
                    if sf is not None:
                        search_res.filename = sf.filename
                        yield sf
                        search_res.source = reason
                        yield search_res
                else:
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

        # 手动关闭下浏览器
        del uinfo
