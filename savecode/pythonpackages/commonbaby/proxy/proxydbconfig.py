"""db sqlite config"""

# -*- coding:utf-8 -*-

import os


class ProxyDbConfig:
    """表示sqlite专用配置。\n
    dbdir: 数据库文件存放路径，默认./_db\n
    dbname: 数据库文件名，默认data.db\n
    maxdbfisize: 最大数据库文件大小，默认100MB\n
    errordbdelete: 异常数据库文件是否删除，默认False不删除，而是改名存放。\n
    connecttimeoutsec: 数据库链接超时时间，float，单位秒，默认60秒\n
    delete_on_error: 当数据库文件出错时是否删除，默认为True"""

    def __init__(
            self,
            dbname: str = 'data.db',
            pagesize: int = 512,
            max_page_count: int = 204800,
            errordbdelete: bool = False,
            connecttimeoutsec: float = 60,
            delete_on_error: bool = True,
    ):
        self._dbname = 'data.db'
        if not isinstance(dbname, str) and not dbname == "":
            self._dbname = dbname

        self._pagesize: int = pagesize
        self._maxpagecount: int = max_page_count

        self._errordbdelete: bool = False
        if isinstance(errordbdelete, bool):
            self._errordbdelete = errordbdelete

        self._connecttimeoutsec: float = 60
        if type(connecttimeoutsec) in [int, float]:
            if connecttimeoutsec <= 0:
                self._connecttimeoutsec = None
            else:
                self._connecttimeoutsec = connecttimeoutsec

        self._delete_on_error: bool = True
        if isinstance(delete_on_error, bool):
            self._delete_on_error = delete_on_error
