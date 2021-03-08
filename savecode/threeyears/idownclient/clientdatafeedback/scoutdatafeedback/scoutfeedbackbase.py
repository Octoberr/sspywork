"""
scout的回馈文件
create by judy 19/06/13
"""

from abc import abstractmethod

from datacontract.iscoutdataset.iscouttask import EObjectType, IscoutTask

from .scoutjsonable import ScoutJsonable


class ScoutFeedBackBase(ScoutJsonable):
    """侦察数据基类"""
    @property
    def periodnum(self) -> int:
        """当前数据所属的自动周期执行的周期数，默认为0，要用的话需要外部手动赋值一下"""
        return self._periodnum

    @periodnum.setter
    def periodnum(self, value) -> int:
        """当前数据所属的自动周期执行的周期数，默认为0，要用的话需要外部手动赋值一下"""
        if not isinstance(value, int) or value < 0:
            raise Exception("Invalid period number")
        self._periodnum = value
        return self._periodnum

    @property
    def value(self) -> any:
        """属性，当前数据的值，例如一个domain数据类型的值为'aaa.com'"""
        return self._value

    @property
    def parentobj(self):
        """
        返回 ScoutFeedBackBase\n
        父级侦察对象，用于隔级数据关联。
        比如 用domain1侦察出ip1，需要用ip1去进行下一步侦察，
        但是在对ip1进行端口扫描的时候，需要用到domain1（使用域名进行扫描更准确）
        就需要父级侦察对象。
        """
        return self._parentobj

    @parentobj.setter
    def parentobj(self, value):
        """
        返回 ScoutFeedBackBase\n
        父级侦察对象，用于隔级数据关联。
        比如 用domain1侦察出ip1，需要用ip1去进行下一步侦察，
        但是在对ip1进行端口扫描的时候，需要用到domain1（使用域名进行扫描更准确）
        就需要父级侦察对象。
        """
        if not isinstance(value, ScoutFeedBackBase):
            raise Exception("Invalid parent iscout object: {}".format(value))
        self._parentobj = value

    def __init__(self, tsk: IscoutTask, level: int, objtype: EObjectType,
                 value: any, suffix: str):
        # ScoutFeedBackBase过来的必须有suffix，因为必然要输出
        if not isinstance(suffix, str) or suffix == '':
            raise Exception("Invalid suffix for creating ScoutFeedBck")
        ScoutJsonable.__init__(self, suffix)

        # 这里兼容iscan的扫描任务，modify by swm 20200319
        # if not isinstance(tsk, IscoutTask):
        #     raise Exception("Invalid IScoutTask for creating ScoutFeedBack")
        if not isinstance(level, int) or level < 0:
            raise Exception("Invalid level for creating ScoutFeedBack")
        if not isinstance(objtype, EObjectType):
            raise Exception("Invalid objtype for creating ScoutFeedBack")
        if value is None:
            raise Exception("Invalid value for creating ScoutFeedBack")

        # 父级侦察对象，用于隔级数据关联
        # 比如 用domain1侦察出ip1，需要用ip1去进行下一步侦察，
        # 但是在对ip1进行端口扫描的时候，需要用到domain1（使用域名进行扫描更准确）
        # 就需要父级侦察对象
        self._parentobj: ScoutFeedBackBase = None

        self._task: IscoutTask = tsk
        self._level: int = level  # 0表示根节点，第一级为1，第二级为2，类推..
        self._objtype: EObjectType = objtype
        self._value: any = value

        self._periodnum: int = self._task.periodnum
        # 默认的relationfrom是cmd里面的，但是却也是允许外面修改的
        self.relationfrom = self._task.cmd.stratagyscout.relationfrom

        # init output dict
        self._outputdict: dict = {}
        self._outputdict['taskid'] = self._task.taskid
        self._outputdict['batchid'] = self._task.batchid
        self._outputdict['source'] = self._task.source
        # 因为默认的是1
        self._outputdict['periodnum'] = self._task.periodnum
        self._outputdict['time'] = self._task.time_now
        # 这里兼容重点区域搜索的ip字段，多输出一个ip字段应该不会影响scout的数据结构，modify by judy 20200323
        self._outputdict['ip'] = self._value
        # 这里要修改，因为使用的应该不是task的obj，应该是传入的obj这样才不会有问题
        self._outputdict['parentobj'] = self._value
        self._outputdict['parentobjtype'] = objtype.value
        # 新加字段level
        self._outputdict['level'] = self._level
        # 新增加字段relationfrom
        self._outputdict['relationfrom'] = self.relationfrom

    def get_outputdict(self) -> dict:
        """返回输出数据字段字典，用于构造json数据体"""
        self._get_outputdict_sub(self._outputdict)
        return self._outputdict

    @abstractmethod
    def _get_outputdict_sub(self, rootdict: dict):
        """子类实现时，yield返回键值对，
        键为目标类型的侦察结果类型的键，值为任意字典或列表。
        rootdict:json数据主体结构字典"""
        raise NotImplementedError()

    @abstractmethod
    def _subitem_count(self) -> int:
        """子类实现 返回当前根节点的 子数据 总条数，
        用于 文件分割"""
        raise NotImplementedError()

    def _set_parentobj(self, obj):
        """将指定 obj 的 parentobj 设为 self"""
        if not isinstance(obj, ScoutFeedBackBase):
            return
        obj.parentobj = self
