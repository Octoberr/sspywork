"""配置输出器"""

# -*- coding:utf-8 -*-

import os

from datacontract import ClientidMatcher, KeyMatcher, PlatformMatcher
from outputmanagement import OutputConfig, Outputfile

# idownserver统一数据回传路径，默认为程序根目录下./_returndata/
outputdir = r"./_returndata"

# idownserver统一临时目录
tmpdir = r"./_servertmp"

outputconfig = OutputConfig(
    outputers=[
        Outputfile(
            description="zplus_returndata",
            platform="zplus",
            datamatcher=PlatformMatcher("zplus"),
            outputdir=outputdir,
            tmpdir=tmpdir,
            maxsegcount=1000,
        ),
        Outputfile(
            description="zplan",
            platform="zplan",
            datamatcher=PlatformMatcher("zplan"),
            outputdir=outputdir,
            tmpdir=tmpdir,
            maxsegcount=1000,
        ),
    ]
)
