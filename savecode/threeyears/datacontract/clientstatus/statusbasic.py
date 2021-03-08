"""client basic status data"""

# -*- coding:utf-8 -*-

from datetime import datetime

import pytz

from datacontract.idowndataset.datafeedback import EStandardDataType
from ..outputdata import OutputData, OutputDataSeg


class StatusBasic(OutputData, OutputDataSeg):
    """表示一个采集端服务器基础状态数据.\n
    clientid: 区分客户端的唯一标识（后面可能改为ip+mac或其他东西）"""

    @property
    def timestr(self):
        """返回 yyyy-MM-dd HH:mm:ss格式的时间字符串"""
        return self._time

    @property
    def time(self):
        """返回时间戳毫秒数"""
        if not type(self._time) in [int, float]:
            self._time = datetime.now(pytz.timezone('Asia/Shanghai')).timestamp()
        return self._time

    def __init__(self, allfields: dict):
        # 采集端所属平台， 对于状态数据来说是非必要的
        self.platform: str = self._judge(allfields, 'platform', dft='none')
        OutputData.__init__(self, self.platform, EStandardDataType.StatusBasic)
        OutputDataSeg.__init__(self)

        if not isinstance(allfields, dict) or len(allfields) < 1:
            raise Exception("All fields is None when initial StatusBasic")

        self._clientid = self._judge(allfields, 'clientid', error=True)

        # 基本信息
        # 当前数据产生的时间 必要 在生成文件时再赋值
        self._time = self._judge(allfields, 'time')
        if self._time is None:
            self._time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')

        # 采集端操作系统版本 必要
        self.systemver: str = self._judge(allfields, 'systemver', error=True)
        self.ip: str = self._judge(allfields, 'ip', error=True)  # 采集端局域网ip 必要
        self.mac: str = self._judge(
            allfields, 'mac', error=True)  # 采集端mac地址 必要
        # 是否翻墙 必要 0/1
        self.crosswall: int = self._judge(
            allfields, 'crosswall', 0, error=True)
        self.country: str = self._judge(
            allfields, 'country', error=True)  # 采集端服务器所在国家（使用二位国家码） 必要
        # 列表中使用datacontract.appconfig.py中为每个app插件配置的apptype数值，非必要
        # 采集端app偏好列表 非必要
        self.apptype: list = self._judge(allfields, 'apptype', dft='[]')
        # 采集端业务偏好（见task.py tasktype） 非必要
        __tasktype = self._judge(allfields, 'tasktype', dft='[]')
        self.tasktype: list = eval(__tasktype)
        # 采集端app大类偏好（Mail/Shopping/Travel/Trip/Social），
        # 列表中使用datacontract.appconfig.py中的EAppClassify的枚举数值，非必要
        __appclassify = self._judge(allfields, 'appclassify', dft='[]')
        self.appclassify: list = eval(__appclassify)

        # 采集端启用的/支持的任务类型
        self.clientbusiness: list = eval(
            self._judge(allfields, 'clientbusiness', dft='[]'))

        # 状态信息 必要
        self.cpusize: float = self._judge(
            allfields, 'cpusize', error=True)  # cpu总频率，单位GHz
        self.cpuperc: float = self._judge(
            allfields, 'cpuperc', error=True)  # cpu占用率，cpu percent，百分比0.xx
        self.memsize: float = self._judge(
            allfields, 'memsize', error=True)  # 内存总大小，单位GB
        self.memperc: float = self._judge(
            allfields, 'memperc', error=True)  # 内存占用率，memory percent，百分比0.xx
        self.bandwidthd: float = self._judge(
            allfields, 'bandwidthd', error=True)  # 总下行带宽，bandwidth_down，单位Kb/s
        self.bandwidthdperc: float = self._judge(
            allfields, 'bandwidthdperc',
            error=True)  # 当前时刻下行带宽占用率，bandwidth percent，百分比0.xx
        self.disksize: float = self._judge(
            allfields, 'disksize', error=True)  # 当前存储盘硬盘大小，单位GB
        self.diskperc: float = self._judge(
            allfields, 'diskperc', error=True)  # 存储盘硬盘已使用百分比0.xx

        # 控制端独有
        self.updatetime: float = self._judge(
            allfields, 'updatetime',
            dft=0)  # 时间戳，要用东8区的时间，当前采集端的此类状态数据更新时间

    def get_basic_info_lines(self):
        lines = ''
        lines += 'time:{}\r\n'.format(self.timestr)
        lines += 'clientid:{}\r\n'.format(self._clientid)
        lines += 'systemver:{}\r\n'.format(self.systemver)
        lines += 'ip:{}\r\n'.format(self.ip)
        lines += 'mac:{}\r\n'.format(self.mac)
        lines += 'country:{}\r\n'.format(self.country)
        lines += 'crosswall:{}\r\n'.format(self.crosswall)
        if self.platform is not None:
            lines += 'platform:{}\r\n'.format(self.platform)
        if self.apptype is not None:
            lines += 'apptype:{}\r\n'.format(self.apptype)
        if self.tasktype is not None:
            lines += 'tasktype:{}\r\n'.format(self.tasktype)
        if self.appclassify is not None:
            lines += 'appclassify:{}\r\n'.format(self.appclassify)
        lines += 'cpusize:{}\r\n'.format(self.cpusize)
        lines += 'cpuperc:{}\r\n'.format(self.cpuperc)
        lines += 'memsize:{}\r\n'.format(self.memsize)
        lines += 'memperc:{}\r\n'.format(self.memperc)
        lines += 'bandwidthd:{}\r\n'.format(self.bandwidthd)
        lines += 'bandwidthdperc:{}\r\n'.format(self.bandwidthdperc)
        lines += 'disksize:{}\r\n'.format(self.disksize)
        lines += 'diskperc:{}\r\n'.format(self.diskperc)
        lines += 'clientbusiness:{}\r\n'.format(self.clientbusiness)
        contentb = lines.encode('utf-8')
        return contentb

    def has_stream(self) -> bool:
        return False

    def get_stream(self):
        return None

    def get_output_segs(self) -> iter:
        """"""
        self.segindex = 1
        yield self

    def get_output_fields(self) -> iter:
        """"""
        self.append_to_fields('time', self.timestr)
        self.append_to_fields('clientid', self._clientid)
        self.append_to_fields('systemver', self.systemver)
        self.append_to_fields('ip', self.ip)
        self.append_to_fields('mac', self.mac)
        self.append_to_fields('country', self.country)
        self.append_to_fields('crosswall', self.crosswall)
        self.append_to_fields('platform', self.platform)
        self.append_to_fields('apptype', self.apptype)
        self.append_to_fields('tasktype', self.tasktype)
        self.append_to_fields('appclassify', self.appclassify)
        self.append_to_fields('cpusize', self.cpusize)
        self.append_to_fields('cpuperc', self.cpuperc)
        self.append_to_fields('memsize', self.memsize)
        self.append_to_fields('memperc', self.memperc)
        self.append_to_fields('bandwidthd', self.bandwidthd)
        self.append_to_fields('bandwidthdperc', self.bandwidthdperc)
        self.append_to_fields('disksize', self.disksize)
        self.append_to_fields('diskperc', self.diskperc)
        self.append_to_fields('clientbusiness', self.clientbusiness)
        # todo
        # 当前采集端启用的模块(下载0， 扫描1，侦查2)
        return self._fields
