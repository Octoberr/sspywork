"""
client 信息配置
create by judy 20181112
"""


class ConfigClient(object):

    def __init__(self,
                 clientid,
                 systemver,
                 ip,
                 mac,
                 country,
                 crosswall,
                 platform,
                 apptype,
                 tasktype,
                 appclassify,
                 cpusize,
                 bandwidthd,
                 period,
                 clientbusiness):
        self.clientid = clientid
        self.systemver = systemver
        self.ip = '127.0.0.1'
        if ip is not None and ip != '':
            self.ip = ip
        self.mac = mac
        self.country = country
        self.crosswall = crosswall
        self.platform = platform
        self.apptype = apptype
        self.tasktype = tasktype
        self.appclassify = appclassify
        self.cpusize = cpusize
        self.bandwidthd = bandwidthd
        # cpu和下载速度的采集时间段
        self.period = period
        self.clientbusiness = clientbusiness


