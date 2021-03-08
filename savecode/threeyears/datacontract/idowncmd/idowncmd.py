"""
idown_cmd的字段文件
"""
import json
from .iscancmd import StratagyScan
from .iscoutcmd import StratagyScout

from ..ecommandstatus import ECommandStatus
from ..outputdata import DataSeg, EStandardDataType, OutputData, OutputDataSeg


class Target(object):
    def __init__(self, target_json: dict):
        # 均无默认值
        self.tasktype: int = target_json.get('tasktype')
        self.taskid: str = target_json.get('taskid')
        self.batchid: str = target_json.get('batchid')
        self.apptype: int = 0
        tmpapptype = target_json.get('apptype')
        if tmpapptype is not None:
            self.apptype = int(tmpapptype)
        self.account: str = target_json.get('account')
        self.phone: str = target_json.get('phone')

    def __len__(self) -> int:
        res = 0
        if not self.tasktype is None:
            res += 1
        if not self.taskid is None:
            res += 1
        if not self.batchid is None:
            res += 1
        if not self.apptype is None:
            res += 1
        if not self.account is None:
            res += 1
        if not self.phone is None:
            res += 1
        return res


class Switch(object):
    def __init__(self, switch_json):
        self.download_switch = switch_json.get('download_switch')
        self.monitor_switch = switch_json.get('monitor_switch')

    def fill_defswitch(self, defswitch):
        """
        使用默认配置补齐switch
        :param defswitch:
        :return:
        """
        if self.download_switch is None:
            self.download_switch = defswitch.download_switch
        if self.monitor_switch is None:
            self.monitor_switch = defswitch.monitor_switch


class Stratagy(object):
    def __init__(self, stratagy_json):
        # 新增type字段，当修改默认配置的时候，目前只能idown能修改，modify by judy 2020/08/12
        self.type: str = stratagy_json.get('type', 'idown')
        self.circulation_mode: int = stratagy_json.get('circulation_mode')
        if isinstance(self.circulation_mode, str):
            self.circulation_mode = int(self.circulation_mode)
        self.time_start: str = stratagy_json.get('time_start')
        self.time_end: str = stratagy_json.get('time_end')
        self.concur_num: int = stratagy_json.get('concur_num')
        if isinstance(self.concur_num, str):
            self.concur_num = int(self.concur_num)
        self.interval: float = stratagy_json.get('interval')
        if type(self.interval) in [int, float]:
            self.interval = float(self.interval)
        self.period = stratagy_json.get('period')
        self.cookie_keeplive = stratagy_json.get('cookie_keeplive')
        self.data_limit_time = stratagy_json.get('data_limit_time')
        self.data_limit_size = stratagy_json.get('data_limit_size')
        self.priority = stratagy_json.get('priority')

    def fill_defstratagy(self, defstratagy):
        """
        使用默认配置补齐stratagy
        :param defstratagy:
        :return:
        """
        if self.circulation_mode is None:
            self.circulation_mode = defstratagy.circulation_mode
        if self.time_start is None:
            self.time_start = defstratagy.time_start
        if self.time_end is None:
            self.time_end = defstratagy.time_end
        if self.concur_num is None:
            self.concur_num = defstratagy.concur_num
        if self.interval is None:
            self.interval = defstratagy.interval
        if self.period is None:
            self.period = defstratagy.period
        if self.cookie_keeplive is None:
            self.cookie_keeplive = defstratagy.cookie_keeplive
        if self.data_limit_time is None:
            self.data_limit_time = defstratagy.data_limit_time
        if self.data_limit_size is None:
            self.data_limit_size = defstratagy.data_limit_size
        if self.priority is None:
            self.priority = defstratagy.priority


class MailService(object):
    @property
    def imap_isssl(self):
        if self._imap_isssl == 1:
            return True
        else:
            return False

    @property
    def pop3_isssl(self):
        if self._pop3_isssl == 1:
            return True
        else:
            return False

    def __init__(self, mailserverjson):
        self.apptype = mailserverjson.get('apptype')
        self.crosswall = mailserverjson.get('crosswall')
        self.service_name = mailserverjson.get('service_name')
        self.imap_host = mailserverjson.get('imap_host')
        self.imap_port = mailserverjson.get('imap_port')
        self._imap_isssl = int(mailserverjson.get('imap_isssl', 0))
        self.pop3_host = mailserverjson.get('pop3_host')
        self.pop3_port = mailserverjson.get('pop3_port')
        self._pop3_isssl = int(mailserverjson.get('pop3_isssl', 0))


class StratagyMail(object):
    @property
    def stratagymail_dict(self):
        return self.__stratagymail_dict

    def __init__(self, stratagymail_json):
        self.eml_download_limit = stratagymail_json.get('eml_download_limit')
        self.eml_folders_filter = stratagymail_json.get('eml_folders_filter')
        self.eml_failures_times = stratagymail_json.get('eml_failures_times')
        self.eml_priority_protocol = stratagymail_json.get('eml_priority_protocol')
        self.mail_service: MailService = None
        _mail_service = stratagymail_json.get('mail_service')
        if _mail_service is not None:
            self.mail_service = MailService(_mail_service)

        # 需要一份完整的dict
        self.__stratagymail_dict = stratagymail_json

    def fill_defstratagymail(self, defstratagymail):
        """
        填充默认的配置
        :param defstratagymail:
        :return:
        """
        if self.eml_download_limit is None:
            self.eml_download_limit = defstratagymail.eml_download_limit
            self.__stratagymail_dict[
                'eml_download_limit'] = self.eml_download_limit

        if self.eml_folders_filter is None:
            self.eml_folders_filter = defstratagymail.eml_folders_filter
            self.__stratagymail_dict[
                'eml_folders_filter'] = self.eml_folders_filter

        if self.eml_failures_times is None:
            self.eml_failures_times = defstratagymail.eml_failures_times
            self.__stratagymail_dict[
                'eml_failures_times'] = self.eml_failures_times

        if self.eml_priority_protocol is None:
            self.eml_priority_protocol = defstratagymail.eml_priority_protocol
            self.__stratagymail_dict[
                'eml_priority_protocol'] = self.eml_priority_protocol


class IdownCmd(OutputData, OutputDataSeg):
    """
    这个用来解析完整的cmd命令，
    或者是从数据库中查询出来的默认cmd
    应该在这里就补齐配置默认配置
    """

    @property
    def cmd_str(self):
        """
        client保存cmd的原始数据
        :return:
        """
        return self._cmd_str

    @property
    def filled_cmd_str(self):
        """
        得到填充好的默认的json字符串
        跟cmd_str的区别就是，上面是原始的数据，后面是填充了的数据
        根据需要调用即可
        :return:
        """
        return json.dumps(self.__filled_dict, ensure_ascii=False)

    @property
    def cmdstatus(self) -> ECommandStatus:
        return self._cmdstatus

    @cmdstatus.setter
    def cmdstatus(self, value):
        if not isinstance(value, ECommandStatus):
            raise Exception("Invalid ECommandStatus for IDownCmd")
        self._cmdstatus = value

    @property
    def cmdrcvmsg(self) -> str:
        """当前cmd的描述信息"""
        return self._cmdrcvmsg

    @cmdrcvmsg.setter
    def cmdrcvmsg(self, value):
        """当前cmd的描述信息"""
        self._cmdrcvmsg = value

    @property
    def source(self) -> str:
        """数据来源"""
        return self._source

    @source.setter
    def source(self, value: str):
        """数据来源"""
        if not isinstance(value, str):
            raise Exception("Invalid value for idowncmd.source")
        self._source = value

    @property
    def sequence(self):
        """
        cmd处理队列
        :return:
        """
        return self._sequence + 1

    @classmethod
    def parse_from_dict(cls, fields: dict, platform=None):
        """使用字段字典初始化IDownCmd"""
        if not fields.__contains__("cmdid") or not fields.__contains__("cmd"):
            raise Exception("Invalid init fields for IDownCmd: {}".format(fields))

        source: str = fields.get("source")
        clientid: str = fields.get("clientid")
        if platform is None:
            platform = fields.get("platform")
        status: ECommandStatus = None
        tmpstatus = fields.get('status')
        if not tmpstatus is None:
            status = ECommandStatus(int(tmpstatus))

        return IdownCmd.parse(fields["cmd"], fields["cmdid"], platform, source, clientid, status)

    @classmethod
    def parse(
            cls,
            cmd_str: str,
            cmd_id: str = None,
            platform: str = None,
            source: str = None,
            clientid: str = None,
            status: ECommandStatus = None,
    ):
        """初始化IDownCmd"""
        return IdownCmd(cmd_str, cmd_id, platform, source, clientid, status)

    def __init__(
            self,
            cmd_str: str,
            cmd_id: str = None,
            platform: str = None,
            source: str = None,
            clientid: str = None,
            status: ECommandStatus = None,
    ):
        """
        这里为了使用统一，那么就只处理cmd，其他的字段采用传进来的方式
        如果cmid为None那么表示为默认的设置
        如果platform为None，这里会给一个默认的，然后也可以在外面赋值
        :param cmd_str:
        """
        if not isinstance(cmd_str, str):
            raise Exception("Invalid cmdstr for IDownCmd")

        # 这里只接受cmd_str的字符串
        all_cmd_dict: dict = json.loads(cmd_str)
        # 平台信息，单独的cmd的时候需要带在，默认表示zplus，可以带在信息里
        self.platform = platform
        if self.platform is None:
            self.platform = 'zplus'
        self._source = source  # 数据来源标识source
        # 其他通用字段
        self._cmdstatus: ECommandStatus = status
        if not status is None and not isinstance(status, ECommandStatus):
            self._cmdstatus = ECommandStatus(int(status))
        self._cmdrcvmsg: str = None
        self._clientid: str = clientid

        self.cmd_id = cmd_id
        # 你这句 replace 把哥坑惨了
        # 他object里就要有空格呢
        # 额， 我咋知道，obj里面还能有空格的
        # self._cmd_str = cmd_str.replace(' ', '').replace('\r', '').replace(
        #     '\n', '').replace('\t', '')
        self._cmd_str = cmd_str.strip()

        # 这里需要保存一份补齐的完整设置，万一是默认的配置就需要存储
        self.__filled_dict = all_cmd_dict

        OutputData.__init__(self, self.platform, EStandardDataType.IDownCmd)
        OutputDataSeg.__init__(self)

        # ------------------------------------增加一个sequence，初始化为0
        self._sequence = 0
        # ------------------------------------------搬下来了
        _target: dict = all_cmd_dict.get('target')
        self.target: Target = None
        if _target is not None and len(_target) > 0:
            self.target = Target(_target)
        # attr_modify
        self.attr_modify: dict = all_cmd_dict.get('attr_modify')

        # --------------------------------------------------------这三个值需要dict单独使用
        # cmd下载控制
        self.switch_control: Switch = None
        _cmd_switch = all_cmd_dict.get('switch_control')
        if _cmd_switch is not None:
            self.switch_control: Switch = Switch(_cmd_switch)

        # 通用下载配置
        self.stratagy: Stratagy = None
        _cmd_stratagy = all_cmd_dict.get('stratagy')
        if _cmd_stratagy is not None:
            self.stratagy = Stratagy(_cmd_stratagy)

        # 邮件下载配置
        self.stratagymail: StratagyMail = None
        _cmd_stratagy_mail = all_cmd_dict.get('stratagymail')
        if _cmd_stratagy_mail is not None:
            self.stratagymail = StratagyMail(_cmd_stratagy_mail)

        # ---------------------------------------------------------这个先不急，先不要影响前面写的没有测试的东西
        # scan相关设置
        self.stratagyscan: StratagyScan = None
        _cmd_stratagy_scan = all_cmd_dict.get('stratagyscan')
        if not _cmd_stratagy_scan is None:
            self.stratagyscan = StratagyScan(_cmd_stratagy_scan)

        # -----------------------------------------------------
        # scout相关设置
        self.stratagyscout: StratagyScout = None
        _cmd_stratagy_scout = all_cmd_dict.get('stratagyscout')
        if not _cmd_stratagy_scout is None:
            self.stratagyscout = StratagyScout(_cmd_stratagy_scout)

    def fill_defcmd(self, defcmd):
        """
        补齐默认配置
        :param defcmd:
        :return:
        """
        if self.switch_control is None:
            self.switch_control: Switch = defcmd.switch_control
        else:
            self.switch_control.fill_defswitch(defcmd.switch_control)
        # 这样switch_control就一定是有值的
        self.__filled_dict['switch_control'] = self.switch_control.__dict__
        # -----------------------------------------------------
        if self.stratagy is None:
            self.stratagy: Stratagy = defcmd.stratagy
        else:
            self.stratagy.fill_defstratagy(defcmd.stratagy)
        # 这里同理，会补齐默认的值
        self.__filled_dict['stratagy'] = self.stratagy.__dict__
        # ----------------------------------------------------------
        if self.stratagymail is None:
            self.stratagymail: StratagyMail = defcmd.stratagymail
        else:
            self.stratagymail.fill_defstratagymail(defcmd.stratagymail)
        self.__filled_dict[
            'stratagymail'] = self.stratagymail.stratagymail_dict
        # --------------------------------------------------------------scan
        if self.stratagyscan is None:
            self.stratagyscan: StratagyScan = defcmd.stratagyscan
        else:
            self.stratagyscan.fill_defstratagyscan(defcmd.stratagyscan)
        self.__filled_dict[
            'stratagyscan'] = self.stratagyscan.stratagyscan_dict
        # ----------------------------------------------------------------scout
        if self.stratagyscout is None:
            self.stratagyscout: StratagyScout = defcmd.stratagyscout
        else:
            self.stratagyscout.fill_defscout(defcmd.stratagyscout)
        self.__filled_dict['stratagyscout'] = self.stratagyscout.stratagyscout

    def has_stream(self) -> bool:
        return False

    def get_stream(self):
        return None

    def get_output_segs(self) -> iter:
        """"""
        self.segindex = 1
        if self.owner_data is None:
            self.owner_data = self
        yield self

    def get_output_fields(self) -> dict:
        self.append_to_fields("platform", self._platform)
        self.append_to_fields("cmdid", self.cmd_id)
        self.append_to_fields("cmd", self.cmd_str)
        self.append_to_fields("source", self._source)
        return self._fields

    def __repr__(self):
        return "{}".format(self.cmd_id)
