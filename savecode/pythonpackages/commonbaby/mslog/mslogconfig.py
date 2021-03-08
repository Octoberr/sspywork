"""The settings for log message formatting.
    The 'fmtr' should be a method that returns a string"""

# -*- coding:utf-8 -*-

import os
import sys
import threading

from .. import charsets
from ..helpers import helper_time
from .msloglevel import MsLogLevel, MsLogLevels


class MsLogMessageConfig(object):
    """The settings for log message formatting.
    The 'fmtr' should be a method that returns a string"""

    formatter = None

    def __init__(self, fmtr=None):
        """The 'fmtr' should be a method that returns a string
        fmtr: A method that returns string"""
        if fmtr is None:
            pass
        self.formatter = fmtr

    def __default_formatter(self,
                            msg: str,
                            loggername: str,
                            lvl: MsLogLevel = MsLogLevels.DEBUG,
                            exc: Exception = None):
        """msg: The log message.
        exc: The Exception object(if exists)
格式符	说明
%a	星期的英文单词的缩写：如星期一， 则返回 Mon
%A	星期的英文单词的全拼：如星期一，返回 Monday
%b	月份的英文单词的缩写：如一月， 则返回 Jan
%B	月份的引文单词的缩写：如一月， 则返回 January
%c	返回datetime的字符串表示，如03/08/15 23:01:26
%d	返回的是当前时间是当前月的第几天
%f	微秒的表示： 范围: [0,999999]
%H	以24小时制表示当前小时
%I	以12小时制表示当前小时
%j	返回 当天是当年的第几天 范围[001,366]
%m	返回月份 范围[0,12]
%M	返回分钟数 范围 [0,59]
%P	返回是上午还是下午–AM or PM
%S	返回秒数 范围 [0,61]。。。手册说明的
%U	返回当周是当年的第几周 以周日为第一天
%W	返回当周是当年的第几周 以周一为第一天
%w	当天在当周的天数，范围为[0, 6]，6表示星期天
%x	日期的字符串表示 ：03/08/15
%X	时间的字符串表示 ：23:22:08
%y	两个数字表示的年份 15
%Y	四个数字表示的年份 2015
%z	与utc时间的间隔 （如果是本地时间，返回空字符串）
%Z	时区名称（如果是本地时间，返回空字符串）"""
        tid = threading.current_thread().ident()

        # 精确到毫秒...
        time_stamp = helper_time.get_time_millionsec()
        # [2018-01-22 10:59:46] [INFO] [592] [aaa] this is logger aaa
        new_msg = '[%s] [%s] [%d] [%s] %s' % (time_stamp, lvl.name, tid,
                                              loggername, msg)
        if exc is not None:
            new_msg = new_msg + '\r\nex:%s' % exc.args
        return new_msg


class MsLogConfig(object):
    """The base config class\n
    debug: whether to enable debug mode."""

    level = MsLogLevels.DEBUG

    def __init__(self, lvl: MsLogLevel = MsLogLevels.DEBUG, debug: bool = False):
        if lvl is None:
            lvl = MsLogLevels.DEBUG
        self.level: MsLogLevel = lvl
        self.debug: bool = debug


class MsFileLogConfig(MsLogConfig):
    """The settings for creating a file dependent logger\n
    lvl: The log level\n
    sep_logfile: True to separate logfile by logger name, otherwise False\n
    fi_dir: the directory that log file write in, default is os.path.join(os.getcwd(), "_Log")\n
    fi_name: the log file name, default is log.log\n
    enc: the encoding to write file, default is utf8\n
    fd_dt_fmtr: the time format str for separating the folder if separate_logfile=True\n
    max_fi_size: the max size per log file\n
    max_fi_count: the max file count per log file\n
    debug: whether to enable debug mode."""

    # the MsLogMessageConfig object
    message_config: MsLogMessageConfig = MsLogMessageConfig()
    # True to separate logfile by logger name, otherwise False
    separate_logfile: bool = False
    # the directory that log file write in
    log_file_dir: str = os.path.join(os.getcwd(), "_Log")
    # the file name of the log file
    log_file_name = 'log.log'
    # the encoding to write file
    log_file_enc: charsets.EncodingInfo = charsets.utf8
    # the time format str for separating the folder if separate_logfile=True
    folder_date_formatter: str = '%Y-%m-%d %H:%M:%S'
    # the max size per log file
    log_file_maxsize = 5 * 1024 * 1024
    # the max file count per log file
    log_file_maxcount = 10

    def __init__(self,
                 lvl: MsLogLevel = MsLogLevels.DEBUG,
                 sep_logfile: bool = False,
                 fi_dir: str = None,
                 fi_name: str = None,
                 enc: charsets.EncodingInfo = charsets.utf8,
                 fd_dt_fmtr: str = '%Y-%m-%d %H:%M:%S',
                 max_fi_size: int = 5 * 1024 * 1024,
                 max_fi_count: int = 10,
                 debug: bool = False):
        """"""
        MsLogConfig.__init__(self, lvl=lvl, debug=debug)
        if isinstance(sep_logfile, bool):
            self.separate_logfile = sep_logfile
        if fi_dir is not None:
            self.log_file_dir = fi_dir
        if fi_name is not None:
            self.log_file_name = fi_name
        if enc is not None and isinstance(enc, charsets.EncodingInfo):
            self.log_file_enc = enc
        if fd_dt_fmtr is not None:
            self.folder_date_formatter = fd_dt_fmtr
        if max_fi_size > 0:
            self.log_file_maxsize = max_fi_size
        if max_fi_count > 0:
            self.log_file_maxcount = max_fi_count


class MsConsoleLogConfig(MsLogConfig):
    """The settings for console log\n
    debug: whether to enable debug mode."""

    def __init__(self, lvl: MsLogLevel = MsLogLevels.DEBUG, debug: bool = False):
        MsLogConfig.__init__(self, lvl=lvl, debug=debug)
