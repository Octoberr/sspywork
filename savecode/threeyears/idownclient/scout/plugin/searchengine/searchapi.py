"""
create by judy
根据不同的业务逻辑构建不同的查询语句
域名
邮箱
电话号码
网络id
"""
from datacontract.iscoutdataset import IscoutTask
from .baidu import BaiDuSearch
from .bing import BingSearchEngine
from .google import GoogleSearch
from ..scoutplugbase import ScoutPlugBase


class SearchApi(ScoutPlugBase):

    def __init__(self, task: IscoutTask):
        ScoutPlugBase.__init__(self)
        self.task = task

    def __assemble_query(self, keywords: list, filetype: list):
        """
        根据cmd带有的search keywords全词组装下
        如果只在一个方法里写的话可能会有3次循环
        公用方法，接受其他方法的传参
        这里应该有几种情况
        :keyword:默认为空的[]  intext
        :filetype:默认为空的[] filetype
        :return:
        """
        # 1、keywords不为空，filetype为空
        if len(keywords) > 0 and len(filetype) == 0:
            for k in keywords:
                query = f"intext:{k}"
                yield query
        elif len(keywords) == 0 and len(filetype) > 0:
            for f in filetype:
                query = f"filetype:{f}"
                yield query
            # yield ''
        elif len(keywords) > 0 and len(filetype) > 0:
            for k in keywords:
                for f in filetype:
                    query = f"intext:{k} filetype:{f}"
                    yield query
        else:
            self._logger.info(f"Keywords and filetype is None")
            yield ''

    # ------------------------------------------------------------ google hacking search
    def domain_google_search_engine(self, domain, level, reason):
        """
        domain的搜索引擎泄露
        :param domain: site
        :param level:
        :param reason:
        :return:
        """
        g_search = GoogleSearch(self.task)
        keywords: list = self.task.cmd.stratagyscout.cmddomain.searchengine.search_google.keywords
        filetype: list = self.task.cmd.stratagyscout.cmddomain.searchengine.search_google.filetypes
        dquery = f"site:{domain} "
        for cquery in self.__assemble_query(keywords, filetype):
            query = dquery + cquery
            for data in g_search.get_google_search_res(query.strip(), level, reason):
                yield data

    def text_google_search_engine(self, keywords: list, filetype: list, text, level, reason):
        """
        因为是通用方法，所以这里的keywords和filetype就由外面传了吧
        免得写很多
        邮箱的搜索引擎泄露
        电话，网络id
        :param keywords:
        :param filetype:
        :param text:
        :param level:
        :param reason:
        :return:
        """
        g_search = GoogleSearch(self.task)
        dquery = f"intext:{text} "
        for cquery in self.__assemble_query(keywords, filetype):
            query = dquery + cquery
            for data in g_search.get_google_search_res(query.strip(), level, reason):
                yield data

    # --------------------------------------------------------------------------------------------baidu search
    def domain_baidu_search_engine(self, domain, level, reason):
        """
        domain的搜索引擎泄露，百度版本
        :param domain: site
        :param level:
        :param reason:
        :return:
        """
        b_search = BaiDuSearch(self.task)
        keywords: list = self.task.cmd.stratagyscout.cmddomain.searchengine.search_baidu.keywords
        filetype: list = self.task.cmd.stratagyscout.cmddomain.searchengine.search_baidu.filetypes
        dquery = f"site:{domain} "
        querys = []

        if len(keywords) > 0:
            for keyword in keywords:
                querys.append(dquery + keyword)
        elif len(keywords) > 0 and len(filetype) > 0:
            for k in keywords:
                for f in filetype:
                    query = f"{k} filetype:{f}"
                    querys.append(query)
        else:
            querys.append(dquery)

        for query in querys:
            for data in b_search.get_baidu_search_res(query.strip(), level, reason):
                yield data

    def text_baidu_search_engine(self, keywords: list, filetype: list, text, level, reason):
        """
        baidu搜索引擎的text搜索，那么就只会去搜索自带的了
        find some problems by judy 2020/06/30
        :param keywords:
        :param filetype:
        :param text:
        :param level:
        :param reason:
        :return:
        """
        b_search = BaiDuSearch(self.task)
        # 百度hack的关键字搜索就直接搜索了
        querys = [text]
        if len(keywords) > 0:
            for keyword in keywords:
                querys.append(keyword)
        elif len(filetype) > 0:
            for f in filetype:
                query = f"{text} filetype:{f}"
                querys.append(query)
        elif len(keywords) > 0 and len(filetype) > 0:
            for k in keywords:
                for f in filetype:
                    query = f"{k} filetype:{f}"
                    querys.append(query)
        for query in querys:
            for data in b_search.get_baidu_search_res(query.strip(), level, reason):
                yield data

    # ------------------------------------------------------------------------------------------------bing

    def domain_bing_search_engine(self, domain, level, reason):
        """
        domain的搜索引擎泄露，百度版本
        :param domain: site
        :param level:
        :param reason:
        :return:
        """
        bing_search = BingSearchEngine(self.task)

        keywords: list = self.task.cmd.stratagyscout.cmddomain.searchengine.search_bing.keywords
        filetype: list = self.task.cmd.stratagyscout.cmddomain.searchengine.search_bing.filetypes

        dquery = f"site:{domain} "
        querys = []

        if len(keywords) > 0:
            for keyword in keywords:
                querys.append(dquery + keyword)
        elif len(filetype) > 0:
            for f in filetype:
                querys.append(dquery + f'filetype:{f}')
        elif len(keywords) > 0 and len(filetype) > 0:
            for k in keywords:
                for f in filetype:
                    query = f"{k} filetype:{f}"
                    querys.append(query)
        else:
            querys.append(dquery)

        for query in querys:
            for data in bing_search.get_bing_search_res(query.strip(), level, reason):
                yield data

    def text_bing_search_engine(self, keywords: list, filetype: list, text, level, reason):
        """
        bing搜索引擎的text搜索，那么就只会去搜索自带的了
        :param keywords:
        :param filetype:
        :param text:
        :param level:
        :param reason:
        :return:
        """
        bing_search = BingSearchEngine(self.task)
        # bing hack的关键字搜索就直接搜索了
        querys = [text]
        if len(keywords) > 0:
            for keyword in keywords:
                querys.append(keyword)
        elif len(filetype) > 0:
            for f in filetype:
                query = f"{text} filetype:{f}"
                querys.append(query)
        elif len(keywords) > 0 and len(filetype) > 0:
            for k in keywords:
                for f in filetype:
                    query = f"{k} filetype:{f}"
                    querys.append(query)
        for query in querys:
            for data in bing_search.get_bing_search_res(query.strip(), level, reason):
                yield data
