"""universal data cstructures"""

# -*- coding:utf-8 -*-

from .appconfig import ALL_APPS
from .apps.appbase import AppConfig, EAppClassify
from .automateddataset import (AutomatedTask, AutotaskBack, AutotaskBatchBack,
                               EAutoType)
from .clientstatus import Client, StatusBasic, StatusTask, StatusTaskInfo
from .datamatcher import (
    ClientidMatcher, DataMatcher, ExtMatcher, KeyMatcher, PlatformMatcher)
from .dataseg import DataSeg
from .eclientbusiness import EClientBusiness
from .ecommandstatus import ECommandStatus
from .etaskstatus import ETaskStatus
from .idowncmd import CmdFeedBack, IdownCmd
from .idowncmd.cmdfeedback import CmdFeedBack
from .idowndataset.datafeedback import (EBackResult, ECommandStatus, TaskBack,
                                        TaskBatchBack)
from .idowndataset.task import ETaskStatus, ETaskType, ETokenType, Task
from .inputdata import InputData
from .iscandataset import EScanType, IscanBtaskBack, IscanTask, IscanTaskBack
from .iscandataset.iscandatafeedback import IscanBtaskBack, IscanTaskBack
from .iscandataset.iscantask import EScanType, IscanTask
from .iscoutdataset import (EObjectType, IscoutBtaskBack, IscoutTask,
                            IscoutTaskBack)
from .outputdata import EStandardDataType, OutputData, OutputDataSeg
from .taskbackbase import TaskBackBase
# 新增prg日志
from .prglog import PrglogBase
