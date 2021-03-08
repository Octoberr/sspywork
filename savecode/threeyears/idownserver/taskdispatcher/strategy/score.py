"""strategy object"""

# -*- coding:utf-8 -*-


class Score:
    """表示一个采集端分配好的策略分数"""

    @property
    def isforced(self):
        """self._isforced属性"""
        return self._isforeced

    @isforced.setter
    def isforced(self, value):
        """isforeced.setter"""
        if not isinstance(value, bool):
            raise Exception("Property isforced set value is invalid.")
        self._isforeced = value

    @property
    def score(self):
        """self._score属性"""
        return self._score

    @score.setter
    def score(self, value):
        """score.setter"""
        if not type(value) in [int, float] or value < 0:
            raise Exception("Property score set value is invalid.")
        self._score = value

    def __init__(self, ip: str):
        if not isinstance(ip, str):
            raise Exception("Score ip is invalid.")

        self._ip: str = ip
        self._score: float = 0
        self._isforeced: bool = False
