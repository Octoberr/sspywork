"""
cmd的一些处理
目前没有多少就写在一个文件里
以后大了再单独分出去
create by judy
2019/05/15
"""
import json
import traceback

from datacontract import CmdFeedBack, IdownCmd
from idownclient.clientdbmanager import DbManager
from outputmanagement import OutputManagement


class CmdProcess(object):

    def __init__(self):
        pass
        # self.DbManager = DbManager
        # 默认配置
        # self._defaultcmd: str = self.DbManager.get_default_idown_cmd().get('cmd')
        # self._cmd_dict = json.loads(self._defaultcmd)

    @classmethod
    def modify_default_idown_cmd(cls, icmd):
        """
        当cmd没有target，那么就表示默认的cmd中的信息
        更新数据库中的默认数据
        :return:
        """
        DbManager.update_default_idown_cmd(icmd)
        return

    @staticmethod
    def _get_target_sql(target: dict):
        """
        根据target插入或者更新
        获取where后面的语句
        :param target:
        :return:
        """
        pars = []
        sqlbase: str = ''' WHERE '''
        for k, v in target.items():
            sqlbase += f'{k}=? AND '
            pars.append(v)
        rsql = sqlbase.rstrip().rstrip('AND')
        return rsql, pars

    @staticmethod
    def _get_mail_service_update_sql(u_dict: dict):
        """
        获取修改mailservice的sql
        :param u_dict:
        :return:
        """
        pars = []
        rsql = f''' WHERE service_name=?'''
        lsql = '''UPDATE mailservice SET '''
        for k, v in u_dict.items():
            lsql += f'{k}=?,'
            pars.append(v)
        pars.append(u_dict.pop('service_name'))
        sql = lsql.rstrip(',') + rsql
        return sql, tuple(pars)

    @classmethod
    def modify_mail_service(cls, mailservices: list):
        """
        根据命令修改邮件服务配置，类似imap, pop3, 端口啥的
        应该是只有邮件下载才有
        :return:
        """
        for ser_one in mailservices:
            try:
                opera = int(ser_one.pop('operation'))
                if opera == 1:
                    sql, pars = cls._get_mail_service_update_sql(ser_one)
                    DbManager.update_service_by_sql(sql, pars)
                elif opera == 2:
                    DbManager.insert_a_piece_of_data(
                        ser_one.get('service_name'),
                        ser_one.get('imap_host'),
                        ser_one.get('imap_port'),
                        ser_one.get('pop3_host'),
                        ser_one.get('pop3_port')
                    )
                elif opera == 3:
                    DbManager.delete_one_mail_service(ser_one.get('service_name'))
                else:
                    raise Exception('Unknown mail_service operation')
            except:
                raise Exception(f'Process mail service error, err:{traceback.format_exc()}')

    @staticmethod
    def _get_attr_update_sql(attr: dict):
        """
        修改task的属性，根据要修改的值来做
        :param attr:
        :return:
        """
        pars = []
        sqlbase: str = '''UPDATE task SET '''
        for k, v in attr.items():
            sqlbase += f'{k}=?,'
            pars.append(v)
        lsql = sqlbase.rstrip(',')
        return lsql, pars

    @classmethod
    def modify_task_attr(cls, attr_modify: dict, target: dict):
        """
        修改任务属性
        :param cmdr: cmd的字符串
        :return:
        """
        # cmd_dict = json.loads(cmdr)
        # attr_modify = cmd_dict.get('attr_modify')
        # target = cmd_dict.get('target')
        lsql, lpars = cls._get_attr_update_sql(attr_modify)
        rsql, rpars = cls._get_target_sql(target)
        sql = lsql + rsql
        params = tuple(lpars + rpars)
        DbManager.update_task_by_sql(sql, params)
        return

    @classmethod
    def update_task_cmd(cls, cmdid, icmd):
        """
        更新某个任务的设置
        :param cmdid:
        :param cmdstr:
        :return:
        """
        # 1、先存储cmdstr(自动去重)
        DbManager.store_task_cmd(cmdid, icmd.cmd_str)
        # 2、 更新task的cmdid信息
        lsql = '''
        UPDATE task SET cmdid=?
        '''
        lpars = (cmdid,)
        # cmddict = json.loads(cmdstr)
        # target = cmddict.get('target')
        rsql, rpars = cls._get_target_sql(icmd.target)
        sql = lsql + rsql
        params = lpars + tuple(rpars)
        DbManager.update_task_by_sql(sql, params)
        return

    @classmethod
    def write_cmd_back(cls, icmd, state, recvmsg: str):
        """
        idown cmd 的回馈
        :return:
        """
        cmd_back = CmdFeedBack.create_from_cmd(icmd, state, recvmsg)
        OutputManagement.output(cmd_back)
        return

    @classmethod
    def get_task_cmdid(cls, icmd: IdownCmd):
        """
        这里是根据target去拿取原始任务的cmdid
        :param icmd:
        :return:
        """
        # 两种拿取方法 1、taskid和batchid
        # 2、apptype 和 account
        taskid = icmd.target.taskid
        batchid = icmd.target.batchid
        if taskid and batchid is not None:
            sql = '''
            select cmdid from task where taskid=? and batchid=?
            '''
            pars = (taskid, batchid)
            res = DbManager.query_task_by_sql(sql, pars)
            if len(res) == 0:
                raise Exception('Unknown taskid and bathid, cant get result')
            # 查出来的结果只能是唯一的
            cmdid = res[0].get('cmdid')
            return cmdid

    @classmethod
    def update_origin_cmd(cls, icmd: IdownCmd, o_cmdid):
        """
        去cmd表拿cmdstr
        然后把拿到的cmdstr用现在的cmd更新下，然后再保存回去
        :param icmd:
        :param o_cmdid:
        :return:
        """
        ocmd_res = DbManager.query_cmd_by_cmdid(o_cmdid)
        if ocmd_res is None:
            raise Exception('Wrong cmdid, cant get cmdstr')
        ocmdstr = ocmd_res.get('cmd')
        ocmd_dict = json.loads(ocmdstr)
        # 目前来看更新switch_control, stratagy, stratagymail
        if icmd.switch_control is not None:
            scdic = ocmd_dict.get('switch_control')
            if scdic is None:
                ocmd_dict['switch_control'] = icmd.switch_control.__dict__
            else:
                scdic.update(icmd.switch_control.__dict__)
        if icmd.stratagy is not None:
            stdic = ocmd_dict.get('stratagy')
            if stdic is None:
                ocmd_dict['stratagy'] = icmd.stratagy.__dict__
            else:
                stdic.update(icmd.stratagy.__dict__)
        if icmd.stratagymail is not None:
            # 这个地方有争议，先这样用着，by swm 191224
            stmdict = ocmd_dict.get('stratagymail')
            if stmdict is None:
                ocmd_dict['stratagymail'] = icmd.stratagymail.stratagymail_dict
            else:
                stmdict.update(icmd.stratagymail.stratagymail_dict)
        dcmd_str = json.dumps(ocmd_dict, ensure_ascii=False)
        # 保存回去
        DbManager.store_task_cmd(o_cmdid, dcmd_str)
        return
