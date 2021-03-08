"""inputer configs"""

# -*- coding:utf-8 -*-

from .inputerbase import InputerBase


class InputConfig:
    """输入器配置。\n
    dicinputers: 所有实例化好的Inputer对象，以Inputer的唯一名称为字典键。\n
    maxdealingqueecount: 处理队列最大长度，超过此长度数量的数据正在处理且未结束，则停止读取新数据，默认为1000个，范围1~65535。"""

    def __init__(self, dicinputers: dict, maxdealingqueuecount=1000):
        if not isinstance(dicinputers, dict) or len(dicinputers) < 1:
            raise Exception("No inputer specified")
        if not isinstance(maxdealingqueuecount, int) or maxdealingqueuecount < 1 or maxdealingqueuecount > 65535:
            raise Exception(
                "Param 'maxdealingqueuecount' must be int and a positive number > 1 and < 65535")

        for inputer in dicinputers.values():
            if not issubclass(inputer.__class__, InputerBase):
                raise Exception("Specified inputer is invalid")

        self._inputers: dict = dicinputers
        self._max_q_count: int = maxdealingqueuecount
