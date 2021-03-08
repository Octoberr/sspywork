

from .clientdbmanager.dbsqlite.sqliteconfig import SqliteConfig

sqlitecfg = SqliteConfig(
    dbdir='./_clientdb',
    # dbname='./data.db',
    maxdbfisize=500 * 1024 * 1024,
    maxconnperdb=30,
    errordbdelete=False,
    connecttimeoutsec=60,
    delete_on_error=True,
)
