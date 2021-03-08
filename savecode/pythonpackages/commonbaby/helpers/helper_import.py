"""help for path management"""

# -*- coding:utf-8 -*-

import os
import sys


def add_sys_paths(currpath, parentlevel: int = 2):
    """Add parent directories to sys.path based on the 'currpath',
    the default depth is 2. The default 'currpath' is os.getcwd()"""
    if currpath is None:
        currpath = os.getcwd()
    curr_dir = os.path.realpath(os.path.abspath(currpath))
    if not curr_dir in sys.path:
        sys.path.insert(0, curr_dir)

    if parentlevel <= 0:
        return

    pdir = curr_dir
    i = range(parentlevel)
    while i > 0:
        i = i - 1
        pdir = os.path.dirname(pdir)
        if not pdir in sys.path:
            sys.path.insert(0, pdir)
