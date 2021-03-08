"""messenger base"""

# -*- coding:utf-8 -*-

import ast
import re
import threading
import traceback
from datetime import datetime

from commonbaby.helpers import helper_num, helper_str

from datacontract.idowndataset import Task
from ..spidersocialbase import SpiderSocialBase


class MessengerBase(SpiderSocialBase):
    """手动构造 partial class （把一个类拆分成多个功能模块）...一个文件太大了\n
    这个Base中存放所有公用字段、属性等"""

    _msgr_charsets = [
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d",
        "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r",
        "s", "t", "u", "v", "w", "x", "y", "z"
    ]

    # "0QV1N": {
    # 	"type": "js",
    # 	"src": "https:\/\/static.xx.fbcdn.net\/rsrc.php\/v3iAQx4\/yQ\/l\/en_US\/jc_vqatS9bx.js"
    # },
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

    def __init__(self, task: Task, appcfg, clientid):
        super(MessengerBase, self).__init__(task, appcfg, clientid)

        self._ha._managedCookie.add_cookies(".facebook.com", self.task.cookie)
        self.phone = "%s%s" % (self.task.globaltelcode, self.task.phone)

        # web needed fileds
        self._pc = None
        self._rev = None
        self.lsd = None
        self._req = helper_num.MakeNumber(MessengerBase._msgr_charsets, 20)
        self.fb_dtsg = None
        self.fb_dtsg_ag = None
        self.jazoest = None
        self._spin_r = None
        self._spin_t = None
        self._spin_b = None
        self.docid = None
        self.ajaxpipe_token = None
        self.quickling_ver = None
        self.docid_profile = None
        self.docid_contact = None
        self.docid_contact_next = None
        self.docid_group = None  # 没用了
        self.docid_init = None
        self.homepage = None

        # messenger页面参数
        self.device_id = None
        self.schema_version = None
        self.epoch_id = None
        self.aid = None
        self.appid = None
        self.js_res = []  # 每次处理的js结果列表
        self.last_applied_cursor = None
        self.threads_ranges_time = None  # 联系人翻页时间戳，无下一页为0
        self.threads_ranges_id = None  # 联系人翻页id，无下一页为0
        self.ws = None
        self.message_identifier = 1  # 一个递增的数字，每发送一次加1
        self.request_id = 2  # ls_rep请求的递增id，从2开始

        # 处理联系人的相关参数（要返回fb联系人和会话）
        self.fb_contact_id = []  # 保存会话中的联系人是fb好友时的id，用来判断messenger会话对象是否为好友
        self.messenger_thread_id = []  # 保存messenger会话id，用于去重
        self.is_get_chatlog = False  # 是否拉取聊天记录的标志。一开始返回fb联系人的时候不用拉（因为返回的都是没聊过天的）

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
        self._username: str = None
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

    def _parse_n(self, n):
        """处理js里面的的 n`` """
        # function n(a) {
        # if (a.length !== 1)
        #     throw b("unrecoverableViolation")("only literal strings supported", "messenger_web_product");
        # a = a[0];
        # var c = parseInt(a.substr(-8), 16);
        # a = parseInt(a.substr(0, a.length - 8), 16);
        # return [a >>> 1 ^ -(c & 1), ((c >>> 1) + (a & 1) * 2147483648 ^ -(c & 1)) >>> 0]
        # }
        a = re.search(r'n`(\w+)`', n).group(1)
        c = int(a[-8:], 16)
        if a[:-8] == '':
            a = 0
        else:
            a = int(a[:-8], 16)
        # 没有负数的情况，直接用>>代替js中的>>>
        return [a >> 1 ^ -(c & 1), ((c >> 1) + (a & 1) * 2147483648 ^ -(c & 1)) >> 0]

    def J(self, a: list):
        """a: n``转换的list, 可以转换thread_id和时间，完整js代码未复现"""
        return a[0] * 4294967296 + a[1]

    def _parse_js_one_v1(self, js_one: str):
        """处理ajax请求返回的js， 字符串参数转换成列表"""
        param_list = [i.strip() for i in js_one.split(',')]
        my_list = []
        temp = ''
        for param in param_list:
            if temp == '':
                if param.startswith('"'):
                    if not param.endswith('"') or param.endswith('\\"'):
                        temp = param
                        continue
                my_list.append(param)
            else:
                temp += ","
                temp += param
                if param.endswith('"') and not param.endswith('\\"'):
                    my_list.append(temp)
                    temp = ''
                    continue
        return my_list

    def _parse_js_one_v2(self, js_one: str):
        """处理wss请求返回的js， 字符串参数转换成列表, 转义字符要多一层"""
        param_list = [i.strip() for i in js_one.split(',')]
        my_list = []
        temp = ''
        for param in param_list:
            if temp == '':
                if param.startswith('\\"'):
                    if not param.endswith('\\"') or param.endswith('\\\\\\"'):
                        temp = param
                        continue
                my_list.append(param)
            else:
                temp += ","
                temp += param
                if param.endswith('\\"') and not param.endswith('\\\\\\"'):
                    my_list.append(temp)
                    temp = ''
                    continue
        return my_list

