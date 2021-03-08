"""represents a component info"""

from datacontract.iscoutdataset.iscouttask import IscoutTask


class Component(object):
    """represents a Component.\n
    task: IScoutTask\n
    level: the recursion level\n
    name: str 组件名称"""

    def __init__(self, task: IscoutTask, level: int, name: str):
        # if not isinstance(task, IscoutTask):
        #     raise Exception("Invalid iscouttask")
        if not isinstance(level, int):
            raise Exception("Invalid level")
        if not isinstance(name, str) or name == '':
            raise Exception("Invalid name for Component info")

        self._task: IscoutTask = task
        self._level: int = level

        # current fields
        self._name: str = name
        self.category: str = None
        self.url: str = None
        self.ver: str = None

    def get_outputdict(self) -> dict:
        """
        修改下output的方式，每个结构体有自己的输出，便于主节点好调用
        modify by judy 2020/03/31
        :return:
        """
        component = {}
        component["name"] = self._name
        if isinstance(self.category, str) and not self.category == "":
            component["category"] = self.category
        if isinstance(self.ver, str) and not self.ver == "":
            component["version"] = self.ver
        if isinstance(self.url, str) and not self.url == "":
            component["url"] = self.url
        return component
