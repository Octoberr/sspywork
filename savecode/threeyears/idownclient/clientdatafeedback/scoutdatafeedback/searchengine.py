"""represents a searchengine info"""

# -*- coding:utf-8 -*-

from datacontract.iscoutdataset.iscouttask import IscoutTask


class SearchEngine(object):
    """represents a whoisr info.
    task: IScoutTask\n
    level: the recursion level\n
    domain: the domain which registered by object"""

    def __init__(self, task: IscoutTask, level: int, keyword: str, url: str, reason: str):
        if not isinstance(task, IscoutTask):
            raise Exception("Invalid iscouttask")
        if not isinstance(level, int):
            raise Exception("Invalid level")
        if not isinstance(keyword, str) or keyword == '':
            raise Exception("Invalid keyword for SearchEngine info")
        if not isinstance(url, str) or url == '':
            raise Exception("Invalid url for SearchEngine info")
        if not isinstance(reason, str) or reason == '':
            raise Exception("Invalid reason for SearchEngine info")

        self._task: IscoutTask = task
        self._level: int = level

        self._keyword: str = keyword
        self._url: str = url
        self._reason: str = reason

        self.page: str = None
        self.title: str = None
        self.meta: str = None
        # self.screenshot = None #这个字段不需要，是中心自己构建的
        self.source: str = None  # 信息来源/来源方式（比如：使用google搜索得到），与task.source不一样
        # 增加filename
        self.filename: str = None

    def get_output_dict(self) -> dict:
        """
        获取输出的字典
        :return: 
        """
        sgheaders: dict = {}
        sgheaders["keyword"] = self._keyword
        sgheaders["url"] = self._url
        sgheaders["reason"] = self._reason
        if isinstance(self.page, str) and not self.page == "":
            sgheaders["page"] = self.page
        if isinstance(self.title, str) and not self.title == "":
            sgheaders["title"] = self.title
        if isinstance(self.meta, str) and not self.meta == "":
            sgheaders["meta"] = self.meta
        if isinstance(self.source, str) and not self.source == "":
            sgheaders["source"] = self.source
        if isinstance(self.filename, str) and not self.filename == "":
            sgheaders["filename"] = self.filename
        return sgheaders
