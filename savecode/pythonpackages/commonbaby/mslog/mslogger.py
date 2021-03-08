"""The logger object."""

# -*- coding:utf-8 -*-

import threading
import traceback

from .msloglevel import MsLogLevel, MsLogLevels
from .mslogmsg import MsLogMessage
from .mslogwriter import MsLogWriter


class MsLogger(object):
    """The logger object."""

    # the logger's name
    name: str = None
    # the logger's enabled log level
    # Trace < Debug < Warn < Error < Critical
    level: MsLogLevel = MsLogLevels.DEBUG

    # the locker for synchronizing the add_writer() and log()
    __locker = threading.Lock()

    # all the log writers in current MsLogger instance
    #__writers = None

    def __init__(self,
                 name: str,
                 lvl: MsLogLevel = MsLogLevels.DEBUG,
                 *logwriters: MsLogWriter):
        self.name = name
        self.level = lvl
        self.__writers = []
        if len(logwriters) < 1:
            return
        for wtr in logwriters:
            self.add_writer(wtr)

    def add_writer(self, *wrters: MsLogWriter) -> None:
        """Add new log writer which belongs to current log instance, when
        do logging using current log instance, it will enumerate all the
        writers in the list, and call the 'writer.do_log() method recursively'.
        writer: The writers to be added"""
        with self.__locker:
            if len(wrters) < 1:
                return
            for wrtr in wrters:
                if not isinstance(wrtr, MsLogWriter):
                    continue
                self.__writers.append(wrtr)

    def trace(self, msg: str):
        """Do log writing on MsLogLevel.Trace"""
        self.log(msg, MsLogLevels.TRACE)

    def debug(self, msg: str):
        """Do log writing on MsLogLevel.Debug"""
        self.log(msg, MsLogLevels.DEBUG)

    def info(self, msg: str):
        """Do log writing on MsLogLevel.Info"""
        self.log(msg, MsLogLevels.INFO)

    def warn(self, msg: str):
        """Do log writing on MsLogLevel.Warn"""
        self.log(msg, MsLogLevels.WARN)

    def error(self, msg: str):
        """Do log writing on MsLogLevel.Error"""
        self.log(msg, MsLogLevels.ERROR)

    def critical(self, msg: str):
        """Do log writing on MsLogLevel.Critical"""
        self.log(msg, MsLogLevels.CRITICAL)

    def log(self,
            msg: str,
            lvl: MsLogLevel = MsLogLevels.DEBUG,
            eventid: int = -1,
            formatter=None):
        """his method will enqueue the log message into a queue, the backgroud thread
        will do the real log action
        msg: The log message
        lvl: The log level
        eventid: The event id, which usually is the thread id, if not specified,
        will use thread id
        formatter: A method that recieves the arguments including
        msg,lvl,eventid and format them, finally returns a str message"""
        # return directly if no writer in current logger instance
        if (self.__writers is None) or (len(self.__writers) < 1):
            return
        # return directly if level not enabled
        if (lvl is not None) and (lvl.level < self.level.level):
            return
        # get thread id if not specified
        if eventid == -1:
            eventid = threading.current_thread().ident

        msmsg = MsLogMessage(self.name, msg, eventid, lvl, formatter)

        #self.__locker.acquire()

        for wtr in self.__writers:
            try:
                wtr.log(msmsg)
            except Exception:
                traceback.print_exc()

        #self.__locker.release()
