"""helper for time\n
UTCTime:
UTCTime values take the form of either "YYMMDDhhmm[ss]Z" or "YYMMDDhhmm[ss](+|-)hhmm". 
The first form indicates (by the literal letter "Z") UTC time. The second form indicates 
a time that differs from UTC by plus or minus the hours and minutes represented by the final "hhmm".

These forms differ from GeneralizedTime in several notable ways: the year is represented by two 
digits rather than four, fractional seconds cannot be represented (note that seconds are still 
optional), and values not ending with either a literal "Z" or the form "(+|-)hhmm" are not permitted.

The value notation is the keyword UTCTime. For example, if
    NewTime  ::=  UTCTime
then "9912312359Z" represents the time one minutes before the end of the year 1999 (with no 
seconds indicated) in UTC time, and "991231235959+0200" represents the time one second before 
the end of 1999 two hours ahead of UTC time."""

# -*- coding:utf-8 -*-

import datetime
import math
import pytz
import time


def all_timezones() -> list:
    """return a list contains all timezone names"""
    return pytz.all_timezones


def get_time_millionsec(utc: bool = False) -> str:
    """Get time.time() accurated to millisecond using
    format: '1999-01-01 01:01:01.666'.
    utc: specify if use utc time"""
    # 精确到毫秒...
    ct = time.time()
    if utc:
        ct = datetime.datetime.utcnow().timestamp()
    local_time = time.localtime(ct)
    data_head = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    data_secs = (ct - int(ct)) * 1000
    time_stamp = "%s.%03d" % (data_head, data_secs)
    return time_stamp


def get_time_sec(utc: bool = False) -> str:
    """Get time.time() accurated to seconds using
    format: '1999-01-01 01:01:01' """
    if utc:
        return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    else:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_time_sec_tz(timezone: str = 'Asia/Shanghai') -> str:
    """return the timestamp in specified timezone.\n
    use 'helper_time.all_timezones' to see timezone names"""
    return datetime.datetime.now(
        pytz.timezone(timezone)).strftime('%Y-%m-%d %H:%M:%S')


def get_time_date(utc: bool = False) -> str:
    """Get time.time() accurated to date using
    format: '1999-01-01'"""
    ct = time.time()
    if utc:
        ct = datetime.datetime.utcnow().timestamp()
    local_time = time.localtime(ct)
    data_head = time.strftime("%Y-%m-%d", local_time)
    return data_head


def ts_since_1970(count: int = 13) -> int:
    """Get timespan of the time since 1970-01-01 00:00:00 to now, 
    and return it. The 'count' indecates the count of the 
    number which returns."""
    ts = int(round(time.time() * 1000))
    if isinstance(count, int) and count > 0 and count < 13:
        n = abs(count - len(str(ts)))
        while n > 0:
            ts = int(round(ts / 10))
            n -= 1

    return ts


def ts_since_1970_tz(count: int = 13, timezone: str = "Asia/Shanghai") -> int:
    """return the timestamp in specified timezone.\n
    use 'helper_time.all_timezones' to see timezone names"""
    if not isinstance(timezone, str) or timezone == "":
        timezone = "Asia/Shanghai"
    return datetime.datetime.now(pytz.timezone(timezone)).timestamp()


def timespan_to_datestr(ts: [int, float]) -> str:
    return timespan_to_datestr_tz(ts)


def timespan_to_datestr_tz(ts: [int, float],
                           timezone: str = 'Asia/Shanghai') -> str:
    """timespan to '%Y-%m-%d %H:%M:%S', use datetime.utcfromtimestamp"""
    if not type(ts) in [int, float]:
        raise Exception("ts must be [int,float] timespan")
    while (ts / 1000000000) > 10:
        ts = ts / 10
    # lctm1 = time.localtime(ts)
    # res1 = time.strftime('%Y-%m-%d %H:%M:%S', lctm1)
    # lctm = datetime.datetime.utcfromtimestamp(ts)
    # res = lctm.strftime("%Y-%m-%d %H:%M:%S")
    tz = None
    if not timezone is None and timezone != "":
        tz = pytz.timezone(timezone)
    res = datetime.datetime.fromtimestamp(ts, tz).strftime("%Y-%m-%d %H:%M:%S")
    return res


if __name__ == '__main__':
    t1 = ts_since_1970(10)
    t2 = ts_since_1970(12)
    tm = get_time_date()
    t3 = timespan_to_datestr_tz(1496508846636)
    print(tm)

    a = 0
