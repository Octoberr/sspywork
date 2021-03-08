"""facebook"""

# -*- coding:utf-8 -*-

import ast
import re
import threading

from commonbaby.helpers import helper_num
from commonbaby.httpaccess.httpaccess import HttpAccess

from datacontract.iscoutdataset import IscoutTask
from idownclient.config_detectiontools import dtools

from ..scoutplugbase import ScoutPlugBase


class FbBase(ScoutPlugBase):
    """facebook base"""

    _SOURCE: str = 'facebook'

    _msgr_charsets = [
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d",
        "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r",
        "s", "t", "u", "v", "w", "x", "y", "z"
    ]

    # "0QV1N": {
    # 	"type": "js",
    # 	"src": "https:\/\/static.xx.fbcdn.net\/rsrc.php\/v3iAQx4\/yQ\/l\/en_US\/jc_vqatS9bx.js",
    # 	"crossOrigin": 1
    # },
    # "zfpfZ": {
    #     "type": "js",
    #     "src": "https://static.xx.fbcdn.net/rsrc.php/v3iSTO4/yV/l/zh_CN/hBASmfNFHNQ.js?_nc_x=skm-RbyIKcn"
    # },
    # re_js_resoures = re.compile(
    #     r'"([^"]{5})"\s*?:\s*?{\s*?"type"\s*?:\s*?"js"\s*?,\s*?"src"\s*?:\s*?"([^"]+?)"\s*?,.+?}',
    #     re.S)
    re_js_resoures = re.compile(
        r'"([^"]{5})"\s*?:\s*?{\s*?"type"\s*?:\s*?"js"\s*?,\s*?"src"\s*?:\s*?"([^"]+?)"\s*?}',
        re.S)

    # groups:[{uid:"1848937661865980",mercury_thread:{participants:
    # ["100009104290443","100025013568208","100026181915516","10002
    # 6452972928","100026747347163","100026797006177","100026837840
    # 717","100027011440525","100027859862248"],image_src:null,name
    # :"666"},participants_to_render:[{id:100009104290443,image_src
    # :"https://scontent.xx.fbcdn.net/v/t1.0-1/p32x32/39984019_2055
    # 328048113985_7771220001821818880_n.jpg?_nc_cat=0&oh=2f2d0083c
    # 16bc7e82a4e1cfb0a146fe7&oe=5C2E6971",name:"Cabdulahi Warsame
    # Xaashi",short_name:"Cabdulahi Warsame Xaashi"},{id:1000250135
    # 68208,image_src:"https://scontent.xx.fbcdn.net/v/t1.0-1/p32x3
    # 2/35156799_177879269722524_3153009726208344064_n.jpg?_nc_cat=
    # 0&oh=e5231b43f0a3e44f4d8ffc2ab2313187&oe=5C2C00D9",name:"Qanc
    # iye Xaliye",short_name:"Qanciye Xaliye"},{id:100026181915516,
    # image_src:"https://scontent.xx.fbcdn.net/v/t1.0-1/p32x32/3989
    # 1731_157027741846622_9181879135197200384_n.jpg?_nc_cat=0&oh=c
    # baee3257757785cf8db919edb0efe52&oe=5C30CC92",name:"Maxamed Ca
    # bdulaahi Isxaaq",short_name:"Maxamed Cabdulaahi Isxaaq"},{id:
    # 100026452972928,image_src:"https://scontent.xx.fbcdn.net/v/t1
    # .0-1/p32x32/34643045_118334392391659_9135586633356148736_n.jp
    # g?_nc_cat=0&oh=eac8dcbec5b8d5f50eeb22ee9866ee63&oe=5C34DEFB",
    # name:"Wizz Asad Yare",short_name:"Wizz Asad Yare"}],text:""}]
    # ,list:["100009104290443-2","

    re_groups_homepage = re.compile(r'groups:\[(.*?)\],list:\[', re.S)

    @property
    def phone_combined(self) -> str:
        """返回 国际区号（若有）+电话号码"""
        if not isinstance(self._phone, str) or self._phone == "":
            return self._phone
        res = self._phone
        if isinstance(self._globaltelcode, str) and self._globaltelcode != '':
            res = self._globaltelcode + self._phone
        return res

    @property
    def uname_str(self):
        """返回当前task对应的 phone/account/username
        的其中一个（哪个有反哪个），或返回 None"""
        # 为了尽量避免出现在使用不同令牌资源进行登陆后获取到的用户账号不一致的情况，
        # 设定使用的账号优先级为
        # phone > userid > account > username
        if isinstance(self.phone_combined,
                      str) and not self.phone_combined == "":
            return self.phone_combined
        elif isinstance(self._userid, str) and not self._userid == "":
            return self._userid
        elif isinstance(self._account, str) and not self._account == "":
            return self._account
        elif isinstance(self._username, str) and not self._username == "":
            return self._username
        else:
            return None

    @property
    def phone(self) -> str:
        return self._phone

    @phone.setter
    def phone(self, value):
        self._phone = value

    def __init__(self, task: IscoutTask, loggername: str = None):
        ScoutPlugBase.__init__(self, loggername=loggername)

        if not isinstance(task, IscoutTask):
            raise Exception("Invalid IscoutTask")

        self._dtools = dtools

        self.task: IscoutTask = task
        self._ha: HttpAccess = HttpAccess()

        self._userid: str = None  # 网站对用户的唯一识别标识
        self._account: str = None  # 可以用于登陆的账号名
        self._username: str = None  # 用户昵称
        self._globaltelcode: str = None  # 国际区号
        self._phone: str = None  # 电话
        self.phone: str = None
        self._url: str = None
        self._host: str = None
        self._cookie: str = None

        self.is_new_facebook = False  # 是不是新版facebook
        # web needed fileds
        self._pc = None
        self._rev = None
        self.lsd = None
        self._req = helper_num.MakeNumber(FbBase._msgr_charsets, 20)
        self.fb_dtsg = None
        self.fb_dtsg_ag = None
        self.jazoest = None
        self._spin_r = None
        self._spin_t = None
        self._spin_b = None
        self.hsi = None
        self._s = None

        self.docid = None
        self.ajaxpipe_token = None  # 新版没有这个参数
        self.quickling_ver = None
        self.docid_profile = None
        self.docid_contact = None
        self.docid_group = None
        self.homepage = None

        # 缓存所有init页面里的资源js脚本，，用于查找各种docid
        self._jspages: dict = {}
        self._jspages_listpage = None
        self._jspages_itemurls: dict = {}
        self._jspages_ok: bool = False
        self._jspages_locker = threading.Lock()

        # sms login contract fields...
        self.hash_ = None
        self.sms_redir = None

        # data
        self.is_messenger_only_user: bool = False  # 是否仅为messenger用户
        self.is_deactived_allowed_on_messenger: bool = False  # 是否为messenger禁用用户？
        # 以下数据暂时不存在多线程并发问题，后面需要的话加个锁
        # self._contacts: dict = {}  # 好友列表，以好友userid为key
        # self._chatlogs: dict = {}  # 聊天记录，以好友userid为key
        # self._groups: dict = {}  # 群组，以群组id为key
        # self._resources: dict = {}  # 资源，需存库去重，实现增量下载
        self._exist_msgtypes: dict = {}  # 消息类型有哪些，方便调试

    def _parse_js(self, expr):
        """
        解析非标准JSON的Javascript字符串，等同于json.loads(JSON str)
        :param expr:非标准JSON的Javascript字符串
        :return:Python字典
        """
        res = None
        try:
            m = ast.parse(expr)
            a = m.body[0]
            res = self.__parse(a)
        except Exception:
            res = None
        return res

    def __parse(self, node):
        if isinstance(node, ast.Expr):
            return self.__parse(node.value)
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Dict):
            return dict(
                zip(map(self.__parse, node.keys), map(self.__parse,
                                                      node.values)))
        elif isinstance(node, ast.List):
            return map(self.__parse, node.elts)
        else:
            raise NotImplementedError(node.__class__)
