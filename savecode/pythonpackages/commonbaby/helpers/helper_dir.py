"""help for directory operation"""

# -*- coding:utf-8 -*-

import os


def remove_dirs(di):
    """recursively remove the given directory, including sub files and directories.
    Only use 'os' package"""
    try:
        if not os.path.exists(di):
            return

        di = di.replace('\\', '/')
        if os.path.isfile(di):
            os.remove(di)
        else:
            for d in os.listdir(di):
                remove_dirs(os.path.join(di, d))
            if os.path.exists(di):
                os.rmdir(di)
    except Exception as ex:
        raise ex


def enumerte_dirfullpaths(di: str) -> iter:
    """get directory full pathsin given directory, not recursively."""
    if not os.path.exists(di):
        return
    di = os.path.abspath(di)
    for name in os.listdir(di):
        fullname = os.path.join(di, name)
        if not os.path.isdir(fullname):
            continue
        yield fullname


def enumerte_dirpaths(di: str) -> iter:
    """get directory path names in given directory, not recursively."""
    if not os.path.exists(di):
        return
    di = os.path.abspath(di)
    for name in os.listdir(di):
        fullname = os.path.join(di, name)
        if not os.path.isfile(fullname):
            continue
        yield fullname


def enumerte_filefullpaths(di: str) -> iter:
    """get file full paths in given directory, not recursively."""
    if not os.path.exists(di):
        return
    di = os.path.abspath(di)
    for name in os.listdir(di):
        fullname = os.path.join(di, name)
        if not os.path.isfile(fullname):
            continue
        yield fullname


def enumerte_filepaths(di: str) -> iter:
    """get file names in given directory, not recursively."""
    if not os.path.exists(di):
        return
    di = os.path.abspath(di)
    for name in os.listdir(di):
        fullname = os.path.join(di, name)
        if not os.path.isdir(fullname):
            continue
        yield name