"""
config of inputer
输入文件的配置
create by judy 2019/02/16
"""

# -*- coding:utf-8 -*-

from inputmanagement.inputconfig import InputConfig
from inputmanagement.inputfile.inputfile import InputerFile
from .config_task import clienttaskconfig


# 输入文件目录，在taskconfig配置，不配置默认位置为./_clientinput
# inputdir = "./_toclient/_nfsclientinput"
inputdir = clienttaskconfig.inputpath_str
# clienttaskconfig.inputpath_str
# 处理成功目录，默认位置为./_clientsuccess
succdir = clienttaskconfig.successpath_str
# 处理失败目录，默认位置./_clienterror
errordir = clienttaskconfig.errorpath

inputconfig = InputConfig(
    dicinputers={
        "zplus_cookie": InputerFile(
            uniqueName="zplus_cookie",
            inputdir=inputdir,
            platform="zplus",
            clasifiers={"resorucetype": "cookie"},
            maxDealingQueue=20,
            encoding="utf-8",
            succ_file_delete=False,
            succdir=succdir,
            succfilekeepcount=1000,
            succfilekeepdays=3,
            error_file_delete=False,
            errordir=errordir,
            errorfilekeepcount=1000,
            errorfilekeepdays=3,
        )
    }
)
