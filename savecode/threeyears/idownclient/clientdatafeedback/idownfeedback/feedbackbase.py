"""
返回数据的基类
create by judy 2018/10/22
"""
import datetime
import enum
import io
import json
import os
import threading
from abc import ABCMeta, abstractmethod

import pytz
from commonbaby.helpers import helper_crypto, helper_str

from datacontract.idowndataset import Task
from datacontract.outputdata import (EStandardDataType, OutputData,
                                     OutputDataSeg)

# from idownclient.config_output import muti_seg_count
# get_write_lines函数弃用，muti_seg_count参数现在不是从config_output里来的
muti_seg_count = 1000


class EGender(enum.Enum):
    """统一性别枚举值"""
    Female = 1
    Male = 2
    Unknown = 3


class EResourceType(enum.Enum):
    """标识资源类型\n
    0图片 1视频 2音频 3网站（分享链接） 4其他"""

    Picture = 0
    Video = 1
    Audio = 2
    Url = 3
    Other_Text = 4


class ESign(enum.Enum):
    """对RESOURCE预定义的sign标记枚举"""
    Null = 0
    PicUrl = 1  # 标记当前数据为一个头像图片


class DriveTreeData:
    """表示一个目录树结构中的数据（文件夹或文件）。\n
    treedataid:当前目录树对象在当前树结构中的的唯一标识\n
    path:当前DriveTreeData的完整路径\n"""

    __metaclass = ABCMeta

    @property
    def is_dir(self) -> bool:
        """指示当前数据是否为一个目录"""
        return self._is_dir()

    @abstractmethod
    def _is_dir(self) -> bool:
        raise NotImplementedError()

    @property
    def parent(self):
        """当前DriveTreeData的父目录，
        没有父级（本身就是根级）则为None"""
        return self._parent

    @parent.setter
    def parent(self, value):
        """当前DriveTreeData的父目录，
        没有父级（本身就是根级）则为None"""
        if not isinstance(value, DriveTreeData):
            raise Exception(
                "Invalid property value set for DriveTreeData.parent")
        self._parent = value

    def __init__(self, treedataid: str, path: str = '/'):
        if treedataid is None:
            raise Exception("Invalid param 'treedataid' for DriveTreeData")
        if not isinstance(path, str) or path == "":
            raise Exception("Invalid param 'path' for DriveTreeData")

        self._treedataid: str = treedataid
        self._path: str = path

        # 父级对象
        self._parent: DriveTreeData = None

        # 子级对象
        self._subitems: dict = {}
        self._subitems_locker = threading.RLock()

        # 用于存储已序列化好的json结构
        self._jsondata: dict = {}
        self._jsondata_locker = threading.RLock()
        self._jsondata_ok: bool = False

    def append_item(self, item):
        """向当前网盘数据添加一个子级数据"""
        if not isinstance(item, DriveTreeData):
            raise Exception("Invalid param 'item' for DriveTreeData")
        item: DriveTreeData = item
        with self._subitems_locker:
            if self._subitems.__contains__(item._treedataid):
                # 一般情况下，任何网盘都不允许同一文件夹下有重名文件
                # 所以此处暂时不添加，也不报错，真遇到了id一样的再想办法处理下
                return
            self._subitems[item._treedataid] = item

    def _get_tree_json(self) -> dict:
        """创建当前DriveTreeData的json目录树结构"""
        if self._jsondata_ok:
            return self._jsondata
        with self._jsondata_locker:
            if self._jsondata_ok:
                return self._jsondata
            self._jsondata['key'] = self._treedataid
            for i in self._get_current_tree_json().items():
                key = i[0]
                val = i[1]
                if self._jsondata.__contains__(key):
                    continue
                self._jsondata[key] = val
            if self.is_dir and any(self._subitems):
                tmplist: list = []
                for i in self._subitems.values():
                    i: DriveTreeData = i
                    d: dict = i._get_current_tree_json()
                    if not isinstance(d, dict):
                        # raise Exception(
                        #     "Get subitem json dict error, invalid json dict: treedataid={}".
                        #     format(self._treedataid))
                        continue
                    if any(d):
                        tmplist.append(d)
                if any(tmplist):
                    self._jsondata['items'] = tmplist
            self._jsondata_ok = True
        return self._jsondata

    @abstractmethod
    def _get_current_tree_json(self) -> dict:
        '''子类实现时，拼接一个字典，存放当前DriveTreeData的
        除了self._treedataid以外的相关信息，键和要统一！
        例如：\n
        {
            "name":"xxx",
            "url":"xxxx"
        }'''
        raise NotImplementedError()


class OrderData:
    """表示带有订单self._order字段的数据"""
    _transjsonpath = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'translation.json'))
    _transjsonloaded: bool = False
    _translocker = threading.RLock()
    _transjson: dict = None

    def __init__(self):
        self._order: dict = {}
        self._order_locker = threading.Lock()
        self._order_res = {}

        self._load_transjson()

    def _load_transjson(self):
        if OrderData._transjsonloaded:
            return
        with OrderData._translocker:
            if OrderData._transjsonloaded:
                return
            succ = self.__load_transjson()
            if succ:
                OrderData._transjsonloaded = True

    def __load_transjson(self):
        with open(OrderData._transjsonpath, 'rb') as f:
            string = f.read().decode('utf-8')
            OrderData._transjson = json.loads(string)
            return True

    def append_order(self, **kwargs):
        """将订单以键值对的形式添加到当前数据的详情字典中"""
        if kwargs is None or len(kwargs) < 1:
            return
        with self._order_locker:
            self._order.update(kwargs)

    def append_orders(self, kwargs: dict):
        """将订单以字典的形式添加到当前数据的详情字典中"""
        if not isinstance(kwargs, dict) or len(kwargs) < 1:
            return
        with self._order_locker:
            self._order.update(kwargs)

    def _format_order(self):
        """将 self._order 这个字典展平成只有1级的，并
        翻译其所有可翻译的键，然后按照标准格式化并返回
        纯文本。
        例:
        { "orderid":"a", "b":"b", "c": ["c1","c2"], "d": [{"d1":"d1","d2":"d2"}]...}
        ↓格式化为
        订单号:a
        b:b
        c:["c1","c2"]
        d1:d1
        d2:d2
        """

        dic: dict = OrderData._transjson
        if dic is None:
            dic = {}
        orders = self.__order_iter(self._order)
        new_dic = {}
        for key, value in orders.items():
            if dic.__contains__(key):
                new_dic[dic[key]] = orders[key]
            else:
                new_dic[key] = orders[key]
        order_str = ''
        for key, value in new_dic.items():
            order_str = order_str + key + ':' + str(value) + '\n'
        return order_str

    def __order_iter(self, order, key='order'):
        """内部格式化函数，递归"""
        if isinstance(order, dict):
            for key, value in order.items():
                if isinstance(value, dict):
                    self.__order_iter(value, key)
                elif isinstance(value, list):
                    for value1 in value:
                        if isinstance(value1, dict):
                            self.__order_iter(value1, key)
                        elif isinstance(value1, list):
                            self.__order_iter(value1, key)
                        else:
                            self._order_res[key] = value
                else:
                    self._order_res[key] = value
        elif isinstance(order, list):
            for li in order:
                if isinstance(li, dict) or isinstance(li, list):
                    self.__order_iter(li)
                else:
                    break
            self._order_res[key] = order
        else:
            self._order_res[key] = order
        return self._order_res


class DetailedData:
    """表示带有详情self._detail字段的数据"""

    def __init__(self):
        self._detail: dict = {}
        self._detail_locker = threading.Lock()

    def append_detail(self, **kwargs):
        """将详情以键值对的形式添加到当前数据的详情字典中"""
        if kwargs is None or len(kwargs) < 1:
            return
        with self._detail_locker:
            self._detail.update(kwargs)

    def append_details(self, kwargs: dict):
        """将详情以字典的形式添加到当前数据的详情字典中"""
        if not isinstance(kwargs, dict) or len(kwargs) < 1:
            return
        with self._detail_locker:
            self._detail.update(kwargs)


class Resource:
    """表示一个资源数据。\n
    url:当前资源的唯一标识\n
    rsctype:EResourceType资源类型"""

    @property
    def sign(self):
        '''当前Resource资源的特殊标记，统一使用resourcefeedback.ESign枚举值'''
        return self.__sign

    @sign.setter
    def sign(self, value):
        '''当前Resource资源的特殊标记，统一使用resourcefeedback.ESign枚举值'''
        if not isinstance(value,
                          ESign) or not self._sign_map.__contains__(value):
            raise Exception("Value must be Esign or value is invalid")
        self.__sign = value

    def __init__(self,
                 url: str,
                 rsctype: EResourceType = EResourceType.Other_Text):
        if not isinstance(url, str) or url == "":
            raise Exception("Invalid param 'url' for Resource")
        if not isinstance(rsctype, EResourceType):
            raise Exception("Invalid param 'rsctype' for Resource")

        self._url: str = url
        self._resourcetype: EResourceType = rsctype
        self.filename: str = None

        self.__sign: ESign = ESign.Null
        self._sign_map: dict = {
            ESign.Null: None,
            ESign.PicUrl: "picurl",
        }


class ResourceData:
    """表示一个可能附带资源的数据，即带有resources列表字段的数据类型，
    其中可能关联了多个Resource数据。"""

    _sign_map: dict = {
        ESign.Null: "0",
        ESign.PicUrl: "picurl",
    }

    def __init__(self):
        self._resources: list = []  # 格式详情参见数据标准

    def append_resource(self, rsc: Resource):
        """将一个RESOURCE资源数据关联到当前数据的resources列表"""
        if not issubclass(type(rsc), Resource) or \
                helper_str.is_none_or_empty(rsc._url) or \
                not isinstance(rsc._resourcetype, EResourceType):
            raise Exception(
                "Invalid param 'rsc' Resource for append_resource: {}".format(
                    rsc))
        tmp = {
            "url": rsc._url,
            "type": rsc._resourcetype.value,
        }
        if isinstance(rsc.sign, ESign) and not rsc.sign == ESign.Null:
            tmp['sign'] = ResourceData._sign_map[rsc.sign]
        if not helper_str.is_none_or_empty(rsc.filename):
            tmp['name'] = rsc.filename
        self._resources.append(tmp)


class UniqueData:
    """表示一个可以去重的，有唯一ID标识的数据"""

    __metaclass = ABCMeta

    def __init__(self, task: Task, apptype: int):
        if not isinstance(apptype, int):
            raise Exception("AppType is invalid in Uniquedata")
        if not isinstance(task, Task):
            raise Exception("Task is invalid in Uniquedata")

        self._datatype_str_unique: str = type(self).__name__  # 数据类型
        self._task: Task = task
        self._apptype = apptype

    @abstractmethod
    def get_write_lines(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def get_uniqueid(self):
        """子类实现时，返回当前数据的唯一标识id，用于去重数据，和增量下载。
        默认实现为返回当前数据的hash值"""
        # return helper_crypto.get_md5_from_str(
        #     self._task.taskid.decode('utf-8'))
        hs = self.__hash__()
        return hs

    @abstractmethod
    def get_display_name(self):
        """返回当前数据的显示名称"""
        return self.get_uniqueid()


class InnerDataBase(UniqueData, OutputDataSeg):
    """表示多段数据类型的一段数据"""

    __metaclass = ABCMeta

    def __init__(self, task: Task, apptype: int):
        UniqueData.__init__(self, task, apptype)
        OutputDataSeg.__init__(self)
        # 用于将一些爬取过程中有用的东西记录下来
        self.remarks = None

    def get_write_lines(self) -> str:
        """返回当前数据段构建的字段内容文本"""
        lines: str = ''
        lines += self._get_write_lines()
        if not lines.endswith('\r\n\r\n'):
            lines = lines.strip() + '\r\n\r\n'
        return lines

    @abstractmethod
    def _get_write_lines(self) -> str:
        """子类返回当前数据段构建的字段内容文本"""
        return ''

    @abstractmethod
    def get_uniqueid(self):
        """子类实现时，返回当前数据的唯一标识id，用于去重数据，和增量下载"""
        return helper_crypto.get_md5_from_str(self.get_write_lines())

    def get_output_fields(self) -> dict:
        """返回当前数据段应输出的所有字段字典"""
        self._get_output_fields()
        return self._fields

    @abstractmethod
    def _get_output_fields(self) -> dict:
        """子类实现时，返回当前数据段应输出的所有字段字典"""
        raise NotImplementedError()


class FeedDataBase(UniqueData, OutputData, OutputDataSeg):
    """
    datatype: 数据类型唯一标识\n
    suffix: 数据类型后缀\n
    task: 关联当前数据的task任务\n
    apptype: 当前生成此数据的插件的apptype"""

    __metaclass = ABCMeta

    @property
    def innerdata_len(self):
        with self.__innerdata_locker:
            return len(self.__innerdatas)

    @property
    def io_stream(self) -> io.RawIOBase:
        """当前数据的数据体，二进制流"""
        return self._get_io_stream()

    @io_stream.setter
    def io_stream(self, value):
        """当前数据的数据体，二进制流"""
        self._set_io_stream(value)

    @abstractmethod
    def _get_io_stream(self) -> io.RawIOBase:
        """子类实现时，返回当前数据的文件体，二进制流"""
        return self._io_stream

    @abstractmethod
    def _set_io_stream(self, value):
        """子类实现时，设置当前数据的文件体，二进制流"""
        self._io_stream = value

    def __init__(self,
                 suffix,
                 datatype: EStandardDataType,
                 task: Task,
                 apptype: int,
                 clientid: str,
                 is_muti_seg: bool = False):
        UniqueData.__init__(self, task, apptype)
        OutputData.__init__(self, self._task.platform, datatype)
        OutputDataSeg.__init__(self)

        if not isinstance(clientid, str) or clientid == "":
            raise Exception("Invalid param 'clientid' for FeedDataBase")
        self._clientid: str = clientid

        # 东8区时间
        self.time = datetime.datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

        if not isinstance(suffix, str) or suffix == "":
            raise Exception("Suffix is invalid.")

        self._is_muti_seg: bool = False
        if isinstance(is_muti_seg, bool):
            self._is_muti_seg = is_muti_seg

        self._suffix: str = suffix  # 文件后缀

        self.__innerdatas: list = []  # 内部多段数据
        self.__innerdata_locker = threading.Lock()

        self._io_stream = None  # 从网上下载回来的数据流
        # 统一使用ha来获取head里面的length
        # resp = ha.get_response()
        # lengthn = resp.headers.get('Content-Length')
        # responseio = ResponseIO(resp)
        self.stream_length = 0  # 下载的文件流大小，用来做文件大小过滤
        self.remarks = None  # 用于将一些爬取过程中有用的东西记录下来

    def __iter__(self):
        return self.__innerdatas.__iter__()

    def first_innerdata(self):
        """若当前数据的innerdata集合不为空，则返回Innerdata集合中的第一个元素。
        否则返回None"""
        if self.innerdata_len > 0:
            return self.__innerdatas[0]
        return None

    def append_innerdata(self, innerdata: InnerDataBase):
        """添加一个内部数据结构体到当前总数据结构体中"""
        if not isinstance(innerdata, InnerDataBase):
            raise Exception("Inner data is invalid.")
        with self.__innerdata_locker:
            innerdata.owner_data = self
            self.__innerdatas.append(innerdata)

    def remove_innerdata(self, innerdata: InnerDataBase):
        '''将指定的InnerDataBase对象从当前数据的子数据段集合中移除'''
        if not isinstance(innerdata, InnerDataBase):
            return
        with self.__innerdata_locker:
            if innerdata in self.__innerdatas:
                self.__innerdatas.remove(innerdata)

    @abstractmethod
    def get_output_segs(self) -> iter:
        """子类实现时，返回当前数据包含的数据段iterable"""
        if any(self.__innerdatas):
            segidx = 1
            with self.__innerdata_locker:
                for seg in self.__innerdatas:
                    seg: InnerDataBase = seg
                    seg.append_to_fields('clientid', self._clientid)
                    seg.append_to_fields('taskid', self._task.taskid)
                    seg.append_to_fields('batchid', self._task.batchid)
                    seg.append_to_fields('apptype', self._apptype)
                    seg.append_to_fields('time', self.time)
                    seg.append_to_fields('casenode', self._task.casenode)
                    seg.append_to_fields('source', self._task.source)
                    seg.segindex = segidx
                    segidx += 1
                    yield seg
        else:
            self.segindex = 1
            if self.owner_data is None:
                self.owner_data = self
            yield self

    def get_output_fields(self) -> dict:
        """返回当前数据段应输出的所有字段字典"""
        self.append_to_fields('clientid', self._clientid)
        self.append_to_fields('taskid', self._task.taskid)
        self.append_to_fields('batchid', self._task.batchid)
        self.append_to_fields('apptype', self._apptype)
        self.append_to_fields('time', self.time)
        self.append_to_fields('casenode', self._task.casenode)
        self.append_to_fields('source', self._task.source)
        for field in self._task._other_fields.items():
            self.append_to_fields(field[0], field[1])
        return self._get_output_fields()

    @abstractmethod
    def _get_output_fields(self) -> dict:
        """子类实现时，返回当前数据段应输出的所有字段字典"""
        raise NotImplementedError()

    def get_write_lines(self) -> iter:
        """"""
        lines: str = ''
        if any(self.__innerdatas):
            with self.__innerdata_locker:
                segcount: int = 0
                for innerdata in self.__innerdatas:
                    innerdata: InnerDataBase = innerdata
                    lines += self._get_common_fields_lines()
                    lines += innerdata.get_write_lines()
                    if not lines.endswith('\r\n\r\n'):
                        lines = lines.strip() + '\r\n\r\n'
                    segcount += 1
                    if segcount >= muti_seg_count:
                        yield lines.encode('utf-8')
                        lines = ''
                        segcount = 0
                if not helper_str.is_none_or_empty(lines):
                    yield lines.encode('utf-8')

        elif isinstance(self.io_stream, io.IOBase):
            lines += self._get_common_fields_lines()
            lines += self._get_write_lines()
            if not lines.endswith('\r\n\r\n'):
                lines = lines.strip() + '\r\n\r\n'
            yield lines.encode('utf-8')
        else:
            lines += self._get_common_fields_lines()
            lines += self._get_write_lines()
            if not lines.endswith('\r\n\r\n'):
                lines = lines.strip() + '\r\n\r\n'
            yield lines.encode('utf-8')

    @abstractmethod
    def _get_write_lines(self) -> str:
        """子类按数据类型返回子类应有的字段"""
        return ''

    def _get_common_fields_lines(self):
        """以每行一个字段的形式返回当前数据中的基本共有字段"""
        lines: str = ''
        lines += 'taskid:{}\r\n'.format(self._task.taskid)
        lines += 'apptype:{}\r\n'.format(self._task.apptype)
        lines += 'time:{}\r\n'.format(self.time)
        for field in self._task._other_fields.items():
            if field[0] is None or field[1] is None:
                continue
            lines += "{}:{}\r\n".format(field[0],
                                        helper_str.base64format(field[1]))
        return lines

    def get_stream(self):
        return self.io_stream
