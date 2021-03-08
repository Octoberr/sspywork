"""
统一定义的数据库接口
以后更换数据库直接修改子类方法
create by judy 2019/02/18
"""
import threading

from datacontract.automateddataset import AutomatedTask
from datacontract.idowndataset import Task
from datacontract.iscandataset import IscanTask
from datacontract.iscoutdataset import IscoutTask
from datacontract.outputdata import EStandardDataType
from .dbsqlite.dbsqlite import DbSqlite
from .sqlcondition import SqlConditions
from ..clientdatafeedback import FeedDataBase, UniqueData
from ..config_db import sqlitecfg


class DbManager(object):
    _currdb = DbSqlite
    _static_initialed: bool = False
    _static_init_locker = threading.Lock()

    def __init__(self):
        if DbManager._static_initialed:
            return
        with DbManager._static_init_locker:
            if DbManager._static_initialed:
                return

            DbManager._currdb.static_init(sqlitecfg)
            DbManager._static_initialed = True

    @classmethod
    def insert_task_to_sqlit(cls, dt: Task):
        """
        将有效的任务放入数据库的task表
        :param dt:
        :return:
        """
        return cls._currdb.insert_task_to_sqlit(dt)

    @classmethod
    def query_task(cls, conds: SqlConditions):
        """
        根据任务状态来取出task表的任务，
        根据不同的状态来查询不同的任务数据
        :param key:
        :param value:
        :return:
        """
        return cls._currdb.query_task(conds)

    @classmethod
    def update_status_by_taskid(cls, key: str, value: int, batchid, taskid):
        """
        更新task表的任务状态，根据batchid定位数据
        :param key:
        :param value:
        :param taskid:
        :return:
        """
        return cls._currdb.update_status_by_taskid(key, value, batchid, taskid)

    @classmethod
    def update_task_resource(cls, tsk: Task):
        """
        更新Task任务信息
        :param tsk:
        :return:
        """
        return cls._currdb.update_task_resource(tsk)

    @classmethod
    def query_task_by_sql(cls, sql, pars):
        """
        根据特定的sql查询任务
        查询已有账号的登陆凭证，同步不用task之间的登陆凭证
        :param sql:
        :param pars:
        :return:
        """
        return cls._currdb.query_task_by_sql(sql, pars)

    @classmethod
    def update_task_by_sql(cls, sql, pars):
        """
        用sql更新当前task表
        :param sql:
        :param pars:
        :return:
        """
        return cls._currdb.update_task_by_sql(sql, pars)

    @classmethod
    def save_idown_userinfo(cls, taskid, batchid, userid, clientid):
        cls._currdb.save_idown_userinfo(taskid, batchid, userid, clientid)
        return

    @classmethod
    def query_idown_userinfo(cls, taskid, batchid):
        return cls._currdb.query_idown_userinfo(taskid, batchid)

    # -----------------------------------------------------idowntask

    @classmethod
    def input_insert(cls, tsk):
        """
        将交互输入的验证码存入数据库的inputdata表，
        验证码在取得后就删除在数据库中的记录
        :param tsk:
        :return:
        """
        return cls._currdb.input_insert(tsk)

    @classmethod
    def query_input(cls, task):
        """

        查询数据库的inputdata表，寻找验证码
        根据传入的taskid = parentid,
        查询完成后即时删除这条数据
        :param task:
        :return:
        """
        return cls._currdb.query_input(task)

    # ---------------------------------------------------------------验证码表

    @classmethod
    def insert_uniquely_identifies(cls, data: FeedDataBase):
        """
        向数据库存入数据唯一标识，用于去重。返回是否插入成功True/False
        :param data:
        :return:
        """
        return cls._currdb.insert_uniquely_identifies(data)

    @classmethod
    def is_data_exists(cls, data: UniqueData, datatype: EStandardDataType):
        """
        检查数据是否已存在。返回True/False
        :param data:
        :return:
        """
        return cls._currdb.is_data_exists(data, datatype)

    # -------------------------------------------------------------唯一标识表

    @classmethod
    def get_default_idown_cmd(cls):
        """
        获取idown任务的默认配置
        :return:
        """
        return cls._currdb.get_default_idown_cmd()

    @classmethod
    def get_default_iscan_cmd(cls):
        """
        获取iscan任务的默认配置
        :return:
        """
        return cls._currdb.get_default_iscan_cmd()

    @classmethod
    def get_default_iscout_cmd(cls):
        """
        获取iscout任务的默认配置
        :return:
        """
        return cls._currdb.get_default_iscout_cmd()

    @classmethod
    def store_task_cmd(cls, cmdid, cmdstr):
        """
        补齐默认配置并保存
        :param cmdid:
        :param cmdstr:
        :return:
        """
        return cls._currdb.store_task_cmd(cmdid, cmdstr)

    @classmethod
    def query_cmd_by_cmdid(cls, cmdid):
        """
        根据cmdid查询cmd表
        :param cmdid:
        :return:
        """
        return cls._currdb.query_cmd_by_cmdid(cmdid)

    @classmethod
    def update_default_idown_cmd(cls, icmdr):
        """
        更新idowncmd表的默认配置
        :param icmdr:
        :return:
        """
        return cls._currdb.update_default_idown_cmd(icmdr)

    # ------------------------------------------------------------cmd表
    @classmethod
    def update_service_by_sql(cls, sql, pars):
        """
        通过cmd中的设置更新数据
        :param sql:
        :return:
        """
        return cls._currdb.update_service_by_sql(sql, pars)

    @classmethod
    def insert_a_piece_of_data(
        cls, service_name, imap_host, imap_port, pop3_host, pop3_port
    ):
        """
        增加一条邮件服务设置
        :param service_name:
        :param imap_host:
        :param imap_port:
        :param pop3_host:
        :param pop3_port:
        :return:
        """
        return cls._currdb.insert_a_piece_of_data(
            service_name, imap_host, imap_port, pop3_host, pop3_port
        )

    @classmethod
    def delete_one_mail_service(cls, mail):
        """
        删除某个邮件服务配置
        :param mail:
        :return:
        """
        return cls._currdb.delete_one_mail_service(mail)

    # ------------------------------------------------------------mail service 表

    @classmethod
    def query_iscan_task(cls, conds: SqlConditions):
        """
        查询iscan的任务
        :param key:
        :param value:
        :return:
        """
        return cls._currdb.query_iscan_task(conds)

    @classmethod
    def insert_iscantask(cls, iscantsk: IscanTask):
        """
        存储一条iscan的任务
        :param iscantsk:
        :return:
        """
        return cls._currdb.insert_iscantask(iscantsk)

    @classmethod
    def update_iscan_status(cls, key: str, value: int, taskid):
        """
        更新iscantask表的下载状态
        :param key:
        :param value:
        :param taskid:
        :return:
        """
        return cls._currdb.update_iscan_status(key, value, taskid)

    @classmethod
    def update_iscan_query_data(cls, query_date, query_page, taskid):
        """
        下载国家完整数据专用，是为了项目中途停止能够继续下载
        :param query_date:
        :param query_page:
        :param taskid:
        :return:
        """
        return cls._currdb.update_iscan_query_data(query_date, query_page, taskid)

    # ----------------------------------------------------------------------iscan的东西

    @classmethod
    def query_iscout_task(cls, conds: SqlConditions):
        """
        查询iscout的任务
        :param key:
        :param value:
        :return:
        """
        return cls._currdb.query_iscout_task(conds)

    @classmethod
    def insert_iscouttask(cls, iscouttsk: IscoutTask):
        """
        存储一条iscout的任务
        :param iscouttsk:
        :return:
        """
        return cls._currdb.insert_iscouttask(iscouttsk)

    @classmethod
    def update_iscout_status(cls, key: str, value: int, batchid, taskid):
        """
        更新iscouttask表的下载状态
        :param key:
        :param value:
        :param batchid:
        :return:
        """
        return cls._currdb.update_iscout_status(key, value, batchid, taskid)

    @classmethod
    def update_iscout_info(cls, tsk: IscoutTask):
        """
        下载完成后更新iscout表的所有信息，为循环下载做准备
        :param tsk:
        :return:
        """
        return cls._currdb.update_iscout_info(tsk)

    # -------------------------------------------------------------------------iscout的表

    @classmethod
    def query_auto_task(cls, conds: SqlConditions):
        """
        查询autotask任务
        :param key:
        :param value:
        :return:
        """
        return cls._currdb.query_auto_task(conds)

    @classmethod
    def insert_auot_task(cls, autotask: AutomatedTask):
        """
        插入一条autotask任务
        :param autotask:
        :return:
        """
        return cls._currdb.insert_autotask(autotask)

    @classmethod
    def update_auto_status(cls, key: str, value: int, batchid, taskid):
        """
        更新autotask的任务状态
        :param key:
        :param value:
        :param taskid:
        :return:
        """
        return cls._currdb.update_auto_status(key, value, batchid, taskid)

    @classmethod
    def is_expdbdata_duplicate(cls, data_identification):
        """
        expdb
        是否为重复数据
        重复->True
        不重复->false
        :param data_identification:这个表示为数据的唯一标识符号
        :return:
        """
        return cls._currdb.is_expdbdata_duplicate(data_identification)

    @classmethod
    def save_expdbdata_identification(cls, data_identification):
        """
        expdb
        保存一条数据的唯一标识
        :param data_identification:
        :return:
        """
        return cls._currdb.save_expdbdata_identification(data_identification)

    @classmethod
    def is_geodata_duplicate(cls, data_identification):
        """
        geodata
        是否为重复数据
        重复->True
        不重复->false
        :param data_identification:这个表示为数据的唯一标识符号
        :return:
        """
        return cls._currdb.is_geodata_duplicate(data_identification)

    @classmethod
    def save_geodata_identification(cls, data_identification):
        """
        保存一条数据的唯一标识
        :param data_identification:
        :return:
        """
        return cls._currdb.save_geodata_identification(data_identification)

    @classmethod
    def is_shodandata_duplicate(cls, data_identification, time_str):
        """
        shodan data
        是否为重复数据
        重复->True
        不重复->false
        :param data_identification:这个表示为数据的唯一标识符号
        :param time_str:shodan采集这条数据的时间
        :return:
        """
        return cls._currdb.is_shodandata_duplicate(data_identification, time_str)

    @classmethod
    def save_shodandata_identification(cls, data_identification, time_str):
        """
        保存一条数据的唯一标识
        :param data_identification:
        :param time_str: shodan采集当条数据的时间
        :return:
        """
        return cls._currdb.save_shodandata_identification(data_identification, time_str)

    @classmethod
    def delete_shodan_table(cls):
        """
        当次的数据只使用与当次的任务，与下一次任务并无交集
        所以在使用完成后需要删除数据
        :return:
        """
        return cls._currdb.delete_shodan_data()
