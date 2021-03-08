"""
此client信息的配置文件
create by judy 20181112
"""

from idownclient.clientstatus.configclient import ConfigClient

basic_client_config = ConfigClient(
    clientid="clientid1",
    systemver="linux",
    ip="192.168.90.63",
    mac="mac",
    country="EN",
    crosswall="1",
    platform="zplan",
    apptype="[]",
    tasktype="[]",
    appclassify="[]",
    cpusize="cpusize",
    bandwidthd="100",
    period=15,
    clientbusiness="[1, 2, 4]",
)

# client的ip必须填正确的ip或者约定好的ip
# clientbusiness的字段说明
# 0：未指定/启用所有业务
# 1：启用 IDownTask任务，邮件控守相关
# 2：启用 IScanTask任务，重点区域侦查
# 4：启用 IScout任务， 特定目标侦查
# 5：启用自动任务， geoname等原始数据下载，由Server配置是否开启
# client默认第一次启动会去mmdb官网下载mmdb数据库，IDownTask的任务完全不需要这个库，还有我们在做内网测试的时候无法去下载mmdb这个库
# 以及自动更新可能会出问题，那么就直接加一个手动控制是否自动更新的开关配置， 默认为使用自动更新，可以手动关闭
auto_update_mmdb = False
