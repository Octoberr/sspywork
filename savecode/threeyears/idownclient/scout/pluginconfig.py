"""
scouter插件的一些配置，
可能会有点多这是使用静态结构体的方式来配置
create by judy 2019/07/16
"""


class PluginConfig(object):
    def __init__(
            self,
            sonarapi,
            iplog_time_limit: int
            ):
        # sonar的地址,具体插件前面的地址，外网应该是公网地址
        self.sonarapi = sonarapi
        self.iplog_time_limit = iplog_time_limit
