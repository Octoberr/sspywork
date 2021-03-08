"""table client"""

# -*- coding:utf-8 -*-

import threading
import time
import traceback

from commonbaby.helpers import helper_time
from commonbaby.sql import (SqlConn, SqliteColumn, SqliteConn,
                            SqliteConnManager, SqliteIndex, SqliteTable,
                            table_locker)

from datacontract import (Client, EClientBusiness, ECommandStatus, ETaskStatus,
                          StatusBasic, StatusTask, StatusTaskInfo)

from .sqlite_config import SqliteConfig
from .tbsqlitebase import TbSqliteBase


class TbClient(TbSqliteBase):
    """Client表及相关操作"""

    __tb_Clients: SqliteTable = SqliteTable(
        'Clients',
        True,
        SqliteColumn(
            colname='Id',
            coltype='INTEGER',
            nullable=False,
            is_primary_key=True,
            is_auto_increament=True,
            is_unique=True).set_index_new(),
        SqliteColumn(colname='ClientId', nullable=False).set_index_new(),
        SqliteColumn(colname='SystemVer'),
        SqliteColumn(colname='IP'),
        SqliteColumn(colname='Mac'),
        SqliteColumn(colname='CrossWall', coltype='INTEGER'),
        SqliteColumn(colname='Country'),
        SqliteColumn(colname='Platform'),
        SqliteColumn(
            colname='AppType',
            defaultval='[]',
            description='一个python列表字符串 "[1001,1002]"，使用apptype的值'),
        SqliteColumn(
            colname='TaskType',
            defaultval='[]',
            description='一个python列表字符串 "[1,2]"，使用ETaskType的值'),
        SqliteColumn(
            colname='AppClassify',
            defaultval='[]',
            description='一个python列表字符串 "[1,2,3]"，使用appclassify的值'),
        SqliteColumn(
            colname='ClientBusiness',
            defaultval='[]',
            description='一个python列表字符串 "[1,2,3]"，使用EClientBusiness的值'),
        SqliteColumn(colname='CpuSize', coltype='REAL'),
        SqliteColumn(colname='CpuPerc', coltype='REAL'),
        SqliteColumn(colname='MemSize', coltype='REAL'),
        SqliteColumn(colname='MemPerc', coltype='REAL'),
        SqliteColumn(colname='BandWidthd', coltype='REAL'),
        SqliteColumn(colname='BandWidthdPerc', coltype='REAL'),
        SqliteColumn(colname='DiskSize', coltype='REAL'),
        SqliteColumn(colname='DiskPerc', coltype='REAL'),
        SqliteColumn(colname='TaskNewCnt', coltype='INTEGER'),
        SqliteColumn(colname='TaskWaitingCnt', coltype='INTEGER'),
        SqliteColumn(colname='TaskDownloadingCnt', coltype='INTEGER'),
        SqliteColumn(colname='UpdateTime', coltype='REAL',
                     nullable=False).set_index_new(),
    )

    def __init__(self, dbcfg: SqliteConfig):
        """"""
        TbSqliteBase.__init__(self, TbClient.__tb_Clients._tbname, dbcfg)

    def _append_tables(self):
        self._conn_mngr.append_table(TbClient.__tb_Clients)

    @table_locker(__tb_Clients._tbname)
    def save_client_status_basic(self, client: StatusBasic) -> bool:
        """保存采集端基础状态"""
        res = False
        conn: SqliteConn = None
        cursor = None
        client: StatusBasic = client
        try:
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE ClientId=?'''
            for conn in self.connect_all(5):
                conn: SqliteConn = conn
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (client._clientid, ))
                    result = cursor.fetchall()

                    # 这里只要找到了就是库里有的，然后只更新UpdateTime比当前库中大的
                    if result[0][0] > 0:
                        res = True
                        # update
                        cmd = f'''UPDATE {self._tbname} set
                            SystemVer=?,
                            IP=?,
                            Mac=?,
                            CrossWall=?,
                            Country=?,
                            Platform=?,
                            AppType=?,
                            TaskType=?,
                            AppClassify=?,
                            ClientBusiness=?,
                            CpuSize=?,
                            CpuPerc=?,
                            MemSize=?,
                            MemPerc=?,
                            BandWidthd=?,
                            BandWidthdPerc=?,
                            DiskSize=?,
                            DiskPerc=?,
                            UpdateTime=?
                            WHERE ClientId=? and UpdateTime<=?'''
                        result = cursor.execute(cmd, (
                            client.systemver,
                            client.ip,
                            client.mac,
                            client.crosswall,
                            client.country,
                            client.platform,
                            str(client.apptype),
                            str(client.tasktype),
                            str(client.appclassify),
                            str(client.clientbusiness),
                            client.cpusize,
                            client.cpuperc,
                            client.memsize,
                            client.memperc,
                            client.bandwidthd,
                            client.bandwidthdperc,
                            client.disksize,
                            client.diskperc,
                            client.time,
                            client._clientid,
                            client.time,
                        ))

                        if not result is None and result.rowcount > 0:
                            pass

                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break

            if not res:
                try:
                    conn = self.connect_write(5)
                    cmd = f'''INSERT INTO {self._tbname}(
                        ClientId,
                        SystemVer,
                        IP,
                        Mac,
                        CrossWall,
                        Country,
                        Platform,
                        AppType,
                        TaskType,
                        AppClassify,
                        ClientBusiness,
                        CpuSize,
                        CpuPerc,
                        MemSize,
                        MemPerc,
                        BandWidthd,
                        BandWidthdPerc,
                        DiskSize,
                        DiskPerc,
                        UpdateTime) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'''
                    cursor = conn.cursor
                    result = cursor.execute(cmd, (
                        client._clientid,
                        client.systemver,
                        client.ip,
                        client.mac,
                        client.crosswall,
                        client.country,
                        client.platform,
                        str(client.apptype),
                        str(client.tasktype),
                        str(client.appclassify),
                        str(client.clientbusiness),
                        client.cpusize,
                        client.cpuperc,
                        client.memsize,
                        client.memperc,
                        client.bandwidthd,
                        client.bandwidthdperc,
                        client.disksize,
                        client.diskperc,
                        client.time,
                    ))

                    if not result is None and result.rowcount > 0:  # or len(result) < 1:
                        res = True
                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error(
                "Save client status basic error: %s" % traceback.format_exc())
        finally:
            if not conn is None:
                conn.close()
        return res

    @table_locker(__tb_Clients._tbname)
    def save_client_status_task(self, client: StatusTask):
        """保存采集端任务统计数据"""
        res = False
        conn: SqliteConn = None
        cursor = None
        client: StatusTask = client
        try:
            cmd = f'''SELECT COUNT(1) FROM {self._tbname} WHERE ClientId=?'''
            for conn in self.connect_all(5):
                try:
                    cursor = conn.cursor
                    cursor.execute(cmd, (client._clientid, ))
                    result = cursor.fetchall()
                    if result[0][0] > 0:
                        res = True
                        # update
                        cmd = f'''UPDATE {self._tbname} set
                            TaskNewCnt=?,
                            TaskWaitingCnt=?,
                            TaskDownloadingCnt=?,
                            UpdateTime=?
                            WHERE ClientId=? and UpdateTime<=?;'''
                        result = cursor.execute(cmd, (
                            client.tasknewcnt,
                            client.taskwaitingcnt,
                            client.taskdownloadingcnt,
                            client.time,
                            client._clientid,
                            client.time,
                        ))

                        # 这句没用，就是调试看看结果..
                        if result is None or result.rowcount > 1:  # or len(result) < 1:
                            pass

                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()
                    if res:
                        break
            if not res:
                try:
                    # insert
                    conn = self.connect_write(5)
                    cmd = f'''INSERT INTO {self._tbname}(
                        ClientId,
                        TaskNewCnt,
                        TaskWaitingCnt,
                        TaskDownloadingCnt,
                        UpdateTime) VALUES(?,?,?,?,?)'''
                    cursor = conn.cursor
                    result = cursor.execute(
                        cmd, (client._clientid, client.tasknewcnt,
                              client.taskwaitingcnt, client.taskdownloadingcnt,
                              client.time))
                    if not result is None and result.rowcount > 0:
                        res = True

                except Exception as ex:
                    conn._conn.rollback()
                    raise ex
                else:
                    conn.commit()
                finally:
                    if not conn is None:
                        conn.close()

        except Exception:
            self._logger.error(
                "Save client status task error: %s" % traceback.format_exc())

        return res

    @table_locker(__tb_Clients._tbname)
    def get_client_status(self, clientid: str) -> dict:
        """获取指定采集端信息数据，返回数据行"""
        res: dict = None
        conn: SqliteConn = None
        cursor = None
        try:
            for conn in self._conn_mngr.connect_all():
                try:

                    conn._conn.row_factory = SqliteConn._row_dict_factory
                    cursor = conn.cursor

                    cmd = f'''SELECT
                        ClientId,
                        SystemVer,
                        IP,
                        Mac,
                        CrossWall,
                        Country,
                        Platform,
                        AppType,
                        TaskType,
                        AppClassify,
                        ClientBusiness,
                        CpuSize,
                        CpuPerc,
                        MemSize,
                        MemPerc,
                        BandWidthd,
                        BandWidthdPerc,
                        DiskSize,
                        DiskPerc,
                        TaskNewCnt,
                        TaskWaitingCnt,
                        TaskDownloadingCnt,
                        UpdateTime
                        FROM {self._tbname} WHERE ClientId=?'''

                    cursor.execute(cmd, (clientid, ))

                    result = cursor.fetchall()
                    if result is None or len(result) < 1:
                        continue

                    fields: dict = {}
                    for i in range(len(result[0])):
                        fields[cursor.description[i][0].lower()] = result[0][i]

                    if isinstance(fields, dict) and len(fields) > 0:
                        res = fields
                        break

                    # result = cursor.fetchall()

                    # for row in result:
                    #     res = row  # 只取第一行
                    #     break

                    if not res is None:
                        break

                except Exception:
                    self._logger.error(
                        "Get client status error: %s" % traceback.format_exc())
                finally:
                    if not conn is None:
                        conn.close()
                    if not res is None:
                        break

        except Exception:
            self._logger.error(
                "Get client status error: %s" % traceback.format_exc())
        return res

    @table_locker(__tb_Clients._tbname)
    def get_client_status_all(self, interval: float = 15) -> iter:
        """获取所有采集端任务状态数据。\n
        interval: 指定心跳间隔，即只读取最近n秒内更新的采集端状态，单位秒。"""
        res: Client = None
        conn: SqliteConn = None
        cursor = None
        try:
            # 如果心跳间隔不对，则使用默认值
            if not type(interval) in [int, float] or interval < 2:
                interval = 15

            for conn in self._conn_mngr.connect_all():
                # conn = DbSqlite._conn_mngr.connect_write()
                conn._conn.row_factory = self._dict_factory
                cursor = conn.cursor

                cmd = f'''SELECT 
                    ClientId,
                    SystemVer,
                    IP,
                    Mac, 
                    CrossWall,
                    Country,
                    Platform,
                    AppType,
                    TaskType,
                    AppClassify,
                    ClientBusiness,
                    CpuSize,
                    CpuPerc,
                    MemSize,
                    MemPerc,
                    BandWidthd,
                    BandWidthdPerc,
                    DiskSize,
                    DiskPerc,
                    TaskNewCnt,
                    TaskWaitingCnt,
                    TaskDownloadingCnt,
                    UpdateTime 
                    FROM {self._tbname} WHERE UpdateTime>=?'''

                # helper_time.ts_since_1970_tz()单位为秒，减去心跳间隔15秒，
                # 就是15秒内状态有更新的才认为是上线的，有效的客户端
                it = helper_time.ts_since_1970_tz() - interval
                cursor.execute(cmd, (it, ))
                result = cursor.fetchall()

                for row in result:
                    # if len(row) != 15:
                    #     continue
                    fields: dict = {}
                    for i in range(len(row)):
                        fields[cursor.description[i][0].lower()] = row[i]

                    sb: StatusBasic = StatusBasic(fields)
                    st: StatusTask = StatusTask(fields)
                    res: Client = Client(sb, st)
                    yield res

        except Exception:
            self._logger.error(
                "Get all client status error: %s" % traceback.format_exc())
        finally:
            if not conn is None:
                conn.close()
