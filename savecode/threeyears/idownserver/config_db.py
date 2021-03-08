"""配置数据库"""

# -*- coding:utf-8 -*-

from .dbmanager.dbsqlite.sqlite_config import SqliteConfig

sqlitecfg = SqliteConfig(
    dbdir='./_serverdb',
    # dbname='./data.db',
    maxdbfisize=500 * 1024 * 1024,
    maxconnperdb=30,
    errordbdelete=False,
    connecttimeoutsec=60,
    delete_on_error=True,
)
