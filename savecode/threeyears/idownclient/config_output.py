"""
config for output
根据输出标准配置输出器
and
输出文件夹的配置
modify by judy 2019/01/29
"""

from datacontract import PlatformMatcher
from outputmanagement import OutputConfig, Outputfile

from .config_task import clienttaskconfig

# idownclient的默认输出目录为./_clientoutput
# outputdir = './_serverinput'
outputdir = clienttaskconfig.outputpath_str

# idownclient程序默认的零时存放目录为./_clienttmppath
tmpdir = clienttaskconfig.tmppath_str

outputconfig = OutputConfig(
    outputers=[
        Outputfile(
            description="zplus_client_output",
            platform="zplus",
            datamatcher=PlatformMatcher("zplus"),
            outputdir=outputdir,
            tmpdir=tmpdir,
            maxsegcount=1000,
        ),
        Outputfile(
            description="zplan_client_output",
            platform="zplan",
            datamatcher=PlatformMatcher("zplan"),
            outputdir=outputdir,
            tmpdir=tmpdir,
            maxsegcount=1000,
        ),
    ]
)
