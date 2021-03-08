"""Argument None error"""

# -*- coding:utf-8 -*-


class ArgumentNoneError(Exception):
    """Represents an Argument None error"""

    def __init__(self, argname: str):
        super(ArgumentNoneError,
              self).__init__("Argument '%s' cannot be None." % argname)
