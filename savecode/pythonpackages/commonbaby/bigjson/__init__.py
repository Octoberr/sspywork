"""
big json reader from: 
https://github.com/henu/bigjson

么法用。。。"""

# -*- coding:utf-8 -*-

from .filereader import FileReader


def load(file):
    reader = FileReader(file)
    return reader.read()
