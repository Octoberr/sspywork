"""
存储账号的历史登陆记录信息
create by judy
2018/10/31
"""
from commonbaby.helpers import helper_crypto, helper_str

from datacontract.idowndataset import Task
from datacontract.outputdata import EStandardDataType
from .feedbackbase import FeedDataBase, InnerDataBase


class IdownLoginLog_ONE(InnerDataBase):
    def __init__(self, task: Task, apptype: int, userid):
        super(IdownLoginLog_ONE, self).__init__(task, apptype)
        if userid is None:
            raise Exception('userid cant be None')
        self._userid = userid
        # self.sip = None
        # self.sport = None
        # self.dip = None
        # self.dport = None
        # self.smac = None
        # self.dmac = None
        self.ip: str = None
        self.country = None
        self.region = None
        self.logintime = None
        self.logintype = None
        self.issimulator = None
        self.devicemodel = None
        self.platform = None
        self.apiversion = None
        self.appname = None
        self.appversion = None
        self.activetime = None

    def _get_output_fields(self) -> dict:
        """"""
        self.append_to_fields('userid', self._userid)
        self.append_to_fields('ip', self.ip)
        self.append_to_fields('country', self.country)
        self.append_to_fields('region', self.region)
        self.append_to_fields('logintime', self.logintime)
        self.append_to_fields('logintype', self.logintype)
        self.append_to_fields('issimulator', self.issimulator)
        self.append_to_fields('devicemodel', self.devicemodel)
        self.append_to_fields('platform', self.platform)
        self.append_to_fields('apiversion', self.apiversion)
        self.append_to_fields('appname', self.appname)
        self.append_to_fields('appversion', self.appversion)
        self.append_to_fields('activetime', self.activetime)
        return self._fields

    def _get_write_lines(self):
        lines = ''
        lines += 'userid:{}\r\n'.format(self._userid)
        if self.ip is not None:
            lines += 'ip:{}\r\n'.format(self.ip)
        if self.country is not None:
            lines += 'country:{}\r\n'.format(helper_str.base64format(self.country))
        if self.region is not None:
            lines += 'region:{}\r\n'.format(helper_str.base64format(self.region))
        if self.logintime is not None:
            lines += 'logintime:{}\r\n'.format(self.logintime)
        if self.logintype is not None:
            lines += 'logintype:{}\r\n'.format(helper_str.base64format(self.logintype))
        if self.issimulator is not None:
            lines += 'issimulator:{}\r\n'.format(self.issimulator)
        if self.devicemodel is not None:
            lines += 'devicemodel:{}\r\n'.format(helper_str.base64format(self.devicemodel))
        if self.platform is not None:
            lines += 'platform:{}\r\n'.format(helper_str.base64format(self.platform))
        if self.apiversion is not None:
            lines += 'apiversion:{}\r\n'.format(helper_str.base64format(self.apiversion))
        if self.appname is not None:
            lines += 'appname:{}\r\n'.format(helper_str.base64format(self.appname))
        if self.appversion is not None:
            lines += 'appversion:{}\r\n'.format(helper_str.base64format(self.appversion))
        if self.activetime is not None:
            lines += 'activetime:{}\r\n'.format(helper_str.base64format(self.activetime))
        return lines

    def get_display_name(self):
        res: str = ""
        if not self.ip is None:
            res += "{} ".format(self.ip)
        if not self.logintime is None:
            res += "{} ".format(self.logintime)
        return res.strip()

    def get_uniqueid(self):
        return helper_crypto.get_md5_from_str(self._get_write_lines())


class IdownLoginLog(FeedDataBase):
    def __init__(self, clientid: str, tsk, apptype: int):
        FeedDataBase.__init__(self, '.idown_loginlog',
                              EStandardDataType.LoginLog, tsk, apptype,
                              clientid, True)

    def get_uniqueid(self):
        alllines = ""
        for lines in self._get_write_lines():
            alllines += lines
        return helper_crypto.get_md5_from_str(alllines)
