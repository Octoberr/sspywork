"""
sqlite中的相关操作
create by judy 209/02/18
"""
import threading

from commonbaby.mslog import MsLogger, MsLogManager

from datacontract.automateddataset import AutomatedTask
from datacontract.idowndataset import Task
from datacontract.iscandataset import IscanTask
from datacontract.iscoutdataset import IscoutTask
from datacontract.outputdata import EStandardDataType
from .sqliteconfig import SqliteConfig
from .tbunexpdbdata import TbUnEXPDBData
from .tbautotask import TbAutoTask
from .tbungeonamedata import TbUnGeoNameData
from .tbdata import TbData
from .tbinputdata import TbInputData
from .tbiscantask import TbIscanTask
from .tbiscouttask import TbIscoutTask
from .tbunshodandata import TbUnShodanData

# from .tbmailservice import TbMail
from .tbtask import TbTask
from .tbtaskcmd import TbTaskCmd
from .tbtaskuserinfo import TbTaskUserInfo
from ..sqlcondition import SqlConditions

__sqlite_initialed_locker = threading.RLock()
__sqlite_initialed = lambda: False


def _check_static_initial(func):
    """"""

    def check(*args, **kwargs):
        """"""

        if not callable(__sqlite_initialed):
            return func(*args, **kwargs)

        if not __sqlite_initialed():
            with __sqlite_initialed_locker:
                if not __sqlite_initialed():
                    raise Exception("需要先调用DbSqlite.static_init()后才能开始操作数据库")
        return func(*args, **kwargs)

    check.__doc__ = func.__doc__
    return check


class DbSqlite(object):
    _logger: MsLogger = MsLogManager.get_logger("DbSqlite")

    _static_initialed = False
    _init_locker = threading.Lock()
    _config: SqliteConfig = None

    # 各表
    __tables: dict = {}
    _tbdata: TbData = None
    _tbinputdata: TbInputData = None
    _tbtask: TbTask = None
    _tbtask_cmd: TbTaskCmd = None
    # _tbmailservice: TbMail = None
    _tbiscantask: TbIscanTask = None
    _tbiscouttask: TbIscoutTask = None
    _tbautotask: TbAutoTask = None
    _tbunexpdbdata: TbUnEXPDBData = None
    _tbungeodata: TbUnGeoNameData = None
    _tbunshodandata: TbUnShodanData = None
    _tbidownuserinfo: TbTaskUserInfo = None

    def __init__(self):
        pass

    @staticmethod
    def static_init(cfg: SqliteConfig):
        """由于在client端数据库文件只有一个，所以管理器只需要一个，所以检查是否初始化。"""
        if DbSqlite._static_initialed:
            return

        with DbSqlite._init_locker:
            if DbSqlite._static_initialed:
                return
            DbSqlite._config: SqliteConfig = cfg

            DbSqlite._tbdata = TbData(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbdata._tbname] = DbSqlite._tbdata

            DbSqlite._tbinputdata = TbInputData(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbinputdata._tbname] = DbSqlite._tbinputdata

            DbSqlite._tbtask = TbTask(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbtask._tbname] = DbSqlite._tbtask

            DbSqlite._tbtask_cmd = TbTaskCmd(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbtask_cmd._tbname] = DbSqlite._tbtask_cmd

            # DbSqlite._tbmailservice = TbMail(DbSqlite._config)
            # DbSqlite.__tables[DbSqlite._tbmailservice._tbname] = DbSqlite._tbmailservice

            DbSqlite._tbiscantask = TbIscanTask(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbiscantask._tbname] = DbSqlite._tbiscantask

            DbSqlite._tbiscouttask = TbIscoutTask(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbiscouttask._tbname] = DbSqlite._tbiscouttask

            DbSqlite._tbautotask = TbAutoTask(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbautotask._tbname] = DbSqlite._tbautotask

            DbSqlite._tbunexpdbdata = TbUnEXPDBData(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbunexpdbdata._tbname] = DbSqlite._tbunexpdbdata

            DbSqlite._tbungeodata = TbUnGeoNameData(DbSqlite._config)
            DbSqlite.__tables[DbSqlite._tbungeodata._tbname] = DbSqlite._tbungeodata

            DbSqlite._tbunshodandata = TbUnShodanData(DbSqlite._config)
            DbSqlite.__tables[
                DbSqlite._tbunshodandata._tbname
            ] = DbSqlite._tbunshodandata

            DbSqlite._tbidownuserinfo = TbTaskUserInfo(DbSqlite._config)
            DbSqlite.__tables[
                DbSqlite._tbidownuserinfo._tbname
            ] = DbSqlite._tbidownuserinfo

            DbSqlite._static_initialed = True

    @staticmethod
    @_check_static_initial
    def insert_task_to_sqlit(dt: Task):
        DbSqlite._tbtask.insert_task_to_sqlit(dt)
        return

    @staticmethod
    @_check_static_initial
    def query_task(conds: SqlConditions):
        res = DbSqlite._tbtask.query_task(conds)
        return res

    @staticmethod
    @_check_static_initial
    def update_status_by_taskid(key: str, value: int, batchid, taskid):
        DbSqlite._tbtask.update_status_by_taskid(key, value, batchid, taskid)
        return

    @staticmethod
    @_check_static_initial
    def update_task_resource(tsk: Task):
        DbSqlite._tbtask.update_task_resource(tsk)
        return

    @staticmethod
    @_check_static_initial
    def query_task_by_sql(sql, pars):
        res = DbSqlite._tbtask.query_task_by_sql(sql, pars)
        return res

    @staticmethod
    @_check_static_initial
    def update_task_by_sql(sql, pars):
        DbSqlite._tbtask.update_task_by_sql(sql, pars)
        return

    # idownuserinfo
    @staticmethod
    @_check_static_initial
    def save_idown_userinfo(taskid, batchid, userid, clientid):
        DbSqlite._tbidownuserinfo.save_idown_userinfo(taskid, batchid, userid, clientid)
        return

    @staticmethod
    @_check_static_initial
    def query_idown_userinfo(taskid, batchid):
        return DbSqlite._tbidownuserinfo.query_idown_userinfo(taskid, batchid)

    # ------------------------------------------------------------------上面是idowntask
    @staticmethod
    @_check_static_initial
    def input_insert(tsk: Task):
        DbSqlite._tbinputdata.input_insert(tsk)
        return

    @staticmethod
    @_check_static_initial
    def query_input(task):
        res = DbSqlite._tbinputdata.query_input(task)
        return res

    # ---------------------------------------------------------------------验证码表
    @staticmethod
    @_check_static_initial
    def insert_uniquely_identifies(data):
        res = DbSqlite._tbdata.insert_uniquely_identifies(data)
        return res

    @staticmethod
    @_check_static_initial
    def is_data_exists(data, datatype: EStandardDataType):
        res = DbSqlite._tbdata.is_data_exists(data, datatype)
        return res

    # -----------------------------------------------------------------------下载唯一数据表

    @staticmethod
    @_check_static_initial
    def get_default_idown_cmd():
        res = DbSqlite._tbtask_cmd.get_default_idown_cmd()
        return res

    @staticmethod
    @_check_static_initial
    def get_default_iscan_cmd():
        res = DbSqlite._tbtask_cmd.get_default_iscan_cmd()
        return res

    @staticmethod
    @_check_static_initial
    def get_default_iscout_cmd():
        res = DbSqlite._tbtask_cmd.get_default_iscout_cmd()
        return res

    @staticmethod
    @_check_static_initial
    def store_task_cmd(cmdid, cmdstr):
        DbSqlite._tbtask_cmd.store_task_cmd(cmdid, cmdstr)
        return

    @staticmethod
    @_check_static_initial
    def query_cmd_by_cmdid(cmdid):
        res = DbSqlite._tbtask_cmd.query_cmd_by_cmdid(cmdid)
        return res

    @staticmethod
    @_check_static_initial
    def update_default_idown_cmd(icmd):
        DbSqlite._tbtask_cmd.update_default_idown_cmd(icmd)
        return

    # -------------------------------------------------------------------cmd表
    # @staticmethod
    # @_check_static_initial
    # def update_service_by_sql(sql, pars):
    #     DbSqlite._tbmailservice.update_service_by_sql(sql, pars)
    #     return
    #
    # @staticmethod
    # @_check_static_initial
    # def insert_a_piece_of_data(service_name, imap_host, imap_port, pop3_host, pop3_port):
    #     DbSqlite._tbmailservice.insert_a_piece_of_data(service_name, imap_host, imap_port, pop3_host, pop3_port)
    #     return
    #
    # @staticmethod
    # @_check_static_initial
    # def delete_one_mail_service(mail):
    #     DbSqlite._tbmailservice.delete_one_mail_service(mail)
    #     return

    # -------------------------------------------------------------------mailservice的增删查改

    @staticmethod
    @_check_static_initial
    def query_iscan_task(conds: SqlConditions):
        return DbSqlite._tbiscantask.query_iscan_task(conds)

    @staticmethod
    @_check_static_initial
    def insert_iscantask(iscantsk: IscanTask):
        DbSqlite._tbiscantask.insert_iscantask(iscantsk)
        return

    @staticmethod
    @_check_static_initial
    def update_iscan_status(key: str, value: int, taskid):
        DbSqlite._tbiscantask.update_iscan_status(key, value, taskid)
        return

    @staticmethod
    @_check_static_initial
    def update_iscan_query_data(query_date, query_page, taskid):
        DbSqlite._tbiscantask.update_iscan_query_data(query_date, query_page, taskid)
        return

        # -----------------------------------------------------------------------iscantask的表

    @staticmethod
    @_check_static_initial
    def query_iscout_task(conds: SqlConditions):
        return DbSqlite._tbiscouttask.query_iscout_task(conds)

    @staticmethod
    @_check_static_initial
    def insert_iscouttask(iscouttsk: IscoutTask):
        DbSqlite._tbiscouttask.insert_iscouttask(iscouttsk)
        return

    @staticmethod
    @_check_static_initial
    def update_iscout_status(key: str, value: int, batchid, taskid):
        DbSqlite._tbiscouttask.update_iscout_status(key, value, batchid, taskid)
        return

    @staticmethod
    @_check_static_initial
    def update_iscout_info(tsk: IscoutTask):
        DbSqlite._tbiscouttask.update_iscout_info(tsk)
        return

    # -----------------------------------------------------------------------------------上面为iscouttask
    @staticmethod
    @_check_static_initial
    def query_auto_task(conds: SqlConditions):
        return DbSqlite._tbautotask.query_auto_task(conds)

    @staticmethod
    @_check_static_initial
    def insert_autotask(task: AutomatedTask):
        DbSqlite._tbautotask.insert_autotask(task)
        return

    @staticmethod
    @_check_static_initial
    def update_auto_status(key: str, value: int, batchid, taskid):
        DbSqlite._tbautotask.update_auto_status(key, value, batchid, taskid)
        return

    @staticmethod
    @_check_static_initial
    def is_expdbdata_duplicate(data_identification) -> bool:
        res = DbSqlite._tbunexpdbdata.identify_count(data_identification)
        return res

    @staticmethod
    @_check_static_initial
    def save_expdbdata_identification(data_identification) -> bool:
        res = DbSqlite._tbunexpdbdata.insert_identify(data_identification)
        return res

    @staticmethod
    @_check_static_initial
    def is_geodata_duplicate(data_identification) -> bool:
        res = DbSqlite._tbungeodata.identify_count(data_identification)
        return res

    @staticmethod
    @_check_static_initial
    def save_geodata_identification(data_identification) -> bool:
        res = DbSqlite._tbungeodata.insert_identify(data_identification)
        return res

    # ---------------------------------------------------------------上面为autotask, 增加auto数据的唯一标识，为Server控制

    @staticmethod
    @_check_static_initial
    def is_shodandata_duplicate(data_identification, time_str) -> bool:
        res = DbSqlite._tbunshodandata.identify_count(data_identification, time_str)
        return res

    @staticmethod
    @_check_static_initial
    def save_shodandata_identification(data_identification, time_str) -> bool:
        res = DbSqlite._tbunshodandata.insert_identify(data_identification, time_str)
        return res

    @staticmethod
    @_check_static_initial
    def delete_shodan_data():
        res = DbSqlite._tbunshodandata.delete_table()
        return

    # ----------------------------------------------------------------用于处理shodan下载完整国家数据去除重复，提高性能


def __get_sqlite_initailed():
    return DbSqlite._static_initialed


__sqlite_initialed = __get_sqlite_initailed
