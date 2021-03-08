"""db sqlite config"""

# -*- coding:utf-8 -*-

import os


class SqliteConfig:
    """表示sqlite专用配置。\n
    dbdir: 数据库文件存放路径，默认./_serverdb\n
    dbname: 数据库文件名，默认data.db\n
    maxdbfisize: 最大数据库文件大小，默认100MB\n
    errordbdelete: 异常数据库文件是否删除，默认False不删除，而是改名存放。\n
    connecttimeoutsec: 数据库链接超时时间，float，单位秒，默认60秒\n
    delete_on_error: 当数据库文件出错时是否删除，默认为True"""

    def __init__(
            self,
            dbdir: str = './_serverdb',
            # dbname: str = 'data.db',
            maxdbfisize: float = 100 * 1024 * 1024,
            maxconnperdb: int = 20,
            errordbdelete: bool = False,
            connecttimeoutsec: float = 60,
            delete_on_error: bool = True,
    ):
        self._dbdir = os.path.abspath('./_serverdb')
        if not isinstance(dbdir, str) and not dbdir == "":
            self._dbdir = os.path.abspath(dbdir)

        # self._dbname = 'data.db'
        # if not isinstance(dbname, str) and not dbname == "":
        #     self._dbname = dbname

        self._maxdbfisize = 100 * 1024 * 1024
        if type(maxdbfisize) in [int, float] and maxdbfisize >= 1024 * 1024:
            self._maxdbfisize = maxdbfisize

        self._maxconnperdb = 20
        if isinstance(maxconnperdb, int) and maxconnperdb > 0:
            self._maxconnperdb = maxconnperdb

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
