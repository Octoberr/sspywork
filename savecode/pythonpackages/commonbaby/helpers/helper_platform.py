"""helper for platform differ"""

# -*- coding:utf-8 -*-

import platform


def get_sys_linesep() -> str:
    """Since using the os.linesep will cause extra \\r under windows,
    so use this method to prevent it."""
    linesep = '\n'
    if platform.system().lower().__contains__("linux"):
        linesep = '\n'
    elif platform.system().lower().__contains__("mac os"):  #for mac os
        linesep = '\r'
    return linesep


LINE_SEP = get_sys_linesep()
