"""sqlite test"""

# -*- coding:utf-8 -*-

import threading
import time
import traceback

from commonbaby.mslog import MsFileLogConfig, MsLogLevels, MsLogManager
MsLogManager.static_initial(
    dft_lvl=MsLogLevels.INFO, msficfg=MsFileLogConfig(fi_dir=r'./_serverlog'))
logger = MsLogManager.get_logger("idownserver")

from commonbaby.sql import (SqlConn, SqliteColumn, SqliteConn,
                            SqliteConnManager, SqliteCursor, SqliteIndex,
                            SqliteTable, table_locker)
from commonbaby.helpers import helper_time
__locker = threading.RLock()
__locker2 = threading.RLock()

tables: dict = {
    "TableA":
    SqliteTable(
        "TableA",
        True,
        SqliteColumn("Col1", 'INTEGER', None, False, True, True,
                     True).set_index_new("Idx1"),
        SqliteColumn("Col2", nullable=False, defaultval='DFT'),
        SqliteColumn("Col3", 'INTEGER', defaultval=1),
    ),
}

# tables: dict = {
#     "ClientStatus":
#     SqliteTable(
#         "ClientStatus",
#         True,
#         SqliteColumn(
#             colname="Id",
#             coltype='INTEGER',
#             nullable=False,
#             is_primary_key=True,
#             is_auto_increament=True,
#             is_unique=True).set_index_new(),
#         SqliteColumn(colname="ClientId", nullable=False).set_index_new(),
#         SqliteColumn(colname="SystemVer"),
#         SqliteColumn(colname="IP"),
#         SqliteColumn(colname="Mac"),
#         SqliteColumn(colname="CrossWall", coltype='INTEGER'),
#         SqliteColumn(colname="Country"),
#         SqliteColumn(colname="Platform"),
#         SqliteColumn(colname="AppType", coltype='INTEGER'),
#         SqliteColumn(colname="TaskType", coltype='INTEGER'),
#         SqliteColumn(colname="AppClassify", coltype='INTEGER'),
#         SqliteColumn(colname="CpuSize", coltype='REAL'),
#         SqliteColumn(colname="CpuPerc", coltype='REAL'),
#         SqliteColumn(colname="MemSize", coltype='REAL'),
#         SqliteColumn(colname="MemPerc", coltype='REAL'),
#         SqliteColumn(colname="BandWidthd", coltype='REAL'),
#         SqliteColumn(colname="BandWidthdPerc", coltype='REAL'),
#         SqliteColumn(colname="DiskSize", coltype='REAL'),
#         SqliteColumn(colname="DiskPerc", coltype='REAL'),
#         SqliteColumn(colname="TaskNewCnt", coltype='INTEGER'),
#         SqliteColumn(colname="TaskWaitingCnt", coltype='INTEGER'),
#         SqliteColumn(colname="TaskDownloadingCnt", coltype='INTEGER'),
#         SqliteColumn(colname="UpdateTime", coltype='REAL',
#                      nullable=False).set_index_new(),
#     ),
#     "IDownTask":
#     SqliteTable(
#         "IDownTask",
#         True,
#         SqliteColumn(
#             colname="Id",
#             coltype='INTEGER',
#             nullable=False,
#             is_primary_key=True,
#             is_auto_increament=True,
#             is_unique=True).set_index_new(),
#         SqliteColumn(colname="ClientId", nullable=False).set_index_new(),
#         SqliteColumn(colname="Platform", nullable=False),
#         SqliteColumn(colname="TaskId", nullable=False).set_index_new(),
#         SqliteColumn(colname="ParentTaskId").set_index_new(),
#         SqliteColumn(colname="Status").set_index_new(),
#         SqliteColumn(colname="BatchTotalCount"),
#         SqliteColumn(colname="BatchCompleteCount").set_index_new(),
#         SqliteColumn(colname="TaskType", coltype='INTEGER', nullable=False),
#         SqliteColumn(colname="TokenType", coltype='INTEGER').set_index_new(),
#         SqliteColumn(colname="AppType", coltype='INTEGER').set_index_new(),
#         SqliteColumn(colname="Input"),
#         SqliteColumn(colname="PreGlobalTelCode"),
#         SqliteColumn(colname="PreAccount"),
#         SqliteColumn(colname="GlobalTelCode"),
#         SqliteColumn(colname="Phone"),
#         SqliteColumn(colname="Account"),
#         SqliteColumn(colname="Password"),
#         SqliteColumn(colname="Url"),
#         SqliteColumn(colname="Host"),
#         SqliteColumn(colname="Cookie"),
#         SqliteColumn(colname="CmdRcvMsg"),
#         SqliteColumn(colname="Result"),
#         SqliteColumn(
#             colname="CreateTime",
#             coltype='DATETIME',
#             defaultval="datetime('1970-01-01 00:00:00')"),
#         SqliteColumn(colname="Sequence", coltype='INTEGER',
#                      defaultval=0).set_index_new(),
#         SqliteColumn(colname="OtherFields").set_index_new(),
#         SqliteColumn(colname="UpdateTime", coltype='REAL',
#                      nullable=False).set_index_new(),
#     )
# }
_dbmngrs: dict = {}


class TestDb:
    def __init__(self):
        self.mngr: SqliteConnManager = SqliteConnManager(
            dbdir=r'./_database',
            dbname='aaa.db',
            maxdbfisize=1024 * 1024,
        )
        for tb in tables.values():
            self.mngr.append_table(tb)

        # print("ok")


@table_locker("TableA")
def write1(num):
    db = TestDb()
    _dbmngrs[num] = db.mngr
    # while True:
    #     print(f"t{num} waiting")
    #     time.sleep(1)
    while True:

        tt1 = time.time()
        flag = 0
        flag1 = 0
        sqlsearch = """select count() from TableA"""
        while flag1 < 1000:
            # t1 = time.time()
            flag = 0
            conn: SqlConn = db.mngr.connect_write()
            try:
                logger.info("t{} got write conn".format(num))
                # for i in range(1):
                #     time.sleep(1)
                #     logger.info('t{} sleep 1'.format(num))
                with __locker:
                    while flag < 10000:
                        t = time.time()
                        sql = """insert into TableA(Col2,Col3) values(?,?)"""
                        # res = db.execute_modify(sql)
                        res = conn.execute(sql, (
                            str(flag),
                            flag,
                        ))
                        # logger.info("{}       {}".format(flag, res))
                        flag += 1
                    conn.commit()
            finally:
                conn.close()

            with __locker2:
                count = 0
                dbcnt = 0
                # for sa in db.mngr.execute_search_all(sqlsearch, True):
                #     count += sa[0][0]
                #     dbcnt += 1
                for con in db.mngr.connect_all():
                    try:
                        con: SqliteConn = con
                        cursor = con.cursor
                        cursor.execute(sqlsearch)
                        result = cursor.fetchall()
                        count += result[0][0]
                        dbcnt += 1
                    finally:
                        con.close()
            logger.info(
                "t{} got allconn, data count={}     , dbcount={}".format(
                    num, count, dbcnt))

            # t2 = time.time()
            # logger.info("{} - {} = {}".format(t2, t1, t2 - t1))
            flag1 += 1

        tt2 = time.time()
        logger.info("{} : {} - {} = {}".format(num, tt2, tt1, tt2 - tt1))

    logger.info("{} ok".format(num))


def test():
    for i in range(1):
        t1 = threading.Thread(target=write1, args=(i, ))
        t1.start()
    # t2.start()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    try:

        dbdir = r"F:\WorkSpace\Projects_Others\IMEIDB\imeidb\output"
        dbfi = 'tacdb.sqlite3'
        _db = SqliteConnManager(dbdir, dbfi)

        test()
        while True:
            time.sleep(1)

    except Exception:
        try:
            logger.critical("Program error: %s" % traceback.format_exc())
        except Exception:
            print("Program error: %s" % traceback.format_exc())
    finally:
        time.sleep(5)
