"""Ms log level"""

# -*- coding:utf-8 -*-


class MsLogLevel(object):
    """Represents a log level"""

    level: int = 1
    name: str = None

    # TRACE = 0
    # DEBUG = 1
    # INFO = 2
    # WARN = 3
    # ERROR = 4
    # CRITICAL = 5

    def __init__(self, lvl: int, name: str):
        self.level = lvl
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, MsLogLevel):
            return self.level == other.level
        if isinstance(other, int):
            return self.level == other
        else:
            # this will raise an exception
            return self == other

    def __lt__(self, other):
        if isinstance(other, MsLogLevel):
            return self.level < other.level
        if isinstance(other, int):
            return self.level < other
        else:
            # this will raise an exception
            return self < other

    def __gt__(self, other):
        if isinstance(other, MsLogLevel):
            return self.level > other.level
        if isinstance(other, int):
            return self.level > other
        else:
            # this will raise an exception
            return self > other


class MsLogLevels(object):
    """The log level set"""

    TRACE = MsLogLevel(0, "Trace")
    DEBUG = MsLogLevel(1, "Debug")
    INFO = MsLogLevel(2, "Info")
    WARN = MsLogLevel(3, "Warn")
    ERROR = MsLogLevel(4, "Error")
    CRITICAL = MsLogLevel(5, "Critical")
